import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
import datetime
from collections import namedtuple

from observer import config
from observer.data.repository import StatusLogRepository
from observer.data.models import StatusLog, Status, metadata


@pytest_asyncio.fixture
@pytest.mark.asyncio
async def engine():
    try:
        engine = create_async_engine(config.TEST_DATABASE_URI)

        # Drop and re-create all the tables before test
        async with engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)
            await conn.run_sync(metadata.create_all)

        yield engine

    finally:
        await engine.dispose()


@pytest.fixture
def repository(engine: AsyncEngine) -> StatusLogRepository:
    return StatusLogRepository(engine)


@pytest.mark.asyncio
async def test_can_insert(repository: StatusLogRepository, engine: AsyncEngine):
    """Test that `log_status_change` correctly inserts to the database"""
    now = datetime.datetime(
        year=2023,
        month=1,
        day=1,
        hour=4,
        minute=2,
    )

    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.idle,
        after=Status.online,
        timestamp=now,
    )

    async with engine.connect() as conn:
        result = await conn.execute(StatusLog.select())

    (obj,) = result
    assert obj.user_id == 1
    assert obj.guild_id == 2
    assert obj.before == Status.idle
    assert obj.after == Status.online
    assert obj.time == now


@pytest.mark.asyncio
async def test_stats(repository: StatusLogRepository):
    """Test that correct stats are produced for basic logs"""
    now = datetime.datetime(
        year=2023,
        month=1,
        day=1,
        hour=4,
        minute=2,
    )

    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.idle,
        after=Status.online,
        timestamp=now,
    )

    now += datetime.timedelta(minutes=15)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.online,
        after=Status.idle,
        timestamp=now,
    )  # online  15m

    now += datetime.timedelta(minutes=16)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.idle,
        after=Status.offline,
        timestamp=now,
    )  # idle    16m

    now += datetime.timedelta(minutes=9)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.offline,
        after=Status.dnd,
        timestamp=now,
    )  # offline  9m

    now += datetime.timedelta(minutes=64)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.dnd,
        after=Status.idle,
        timestamp=now,
    )  # dnd     64m

    now += datetime.timedelta(minutes=23)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before="idle",
        after=Status.online,
        timestamp=now,
    )  # idle    23m

    now += datetime.timedelta(minutes=38)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.online,
        after=Status.offline,
        timestamp=now,
    )  # online  38m

    # invalid (before = null)
    now += datetime.timedelta(days=2)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=None,
        after=Status.online,
        timestamp=now,
    )

    # invalid (before does not match previous entry's after)
    now += datetime.timedelta(minutes=10)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.idle,
        after=Status.online,
        timestamp=now,
    )

    now += datetime.timedelta(minutes=10)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.online,
        after=Status.dnd,
        timestamp=now,
    )  # online 10m

    result = await repository.get_user_stats(user_id=1, guild_id=2)

    assert len(result) == 4

    online = next(item for item in result if item.status == Status.online).time
    offline = next(item for item in result if item.status == Status.offline).time
    idle = next(item for item in result if item.status == Status.idle).time
    dnd = next(item for item in result if item.status == Status.dnd).time

    # Expected stats
    # online  | 63m
    # offline | 9m
    # idle    | 39m
    # dnd     | 64m

    assert online.total_seconds() == datetime.timedelta(minutes=63).total_seconds()

    assert offline.total_seconds() == datetime.timedelta(minutes=9).total_seconds()

    assert idle.total_seconds() == datetime.timedelta(minutes=39).total_seconds()

    assert dnd.total_seconds() == datetime.timedelta(minutes=64).total_seconds()


@pytest.mark.asyncio
async def test_stats_with_startup_and_shutdown(repository: StatusLogRepository):
    """Ensure stats behave as expected with bot startup and shutdown entries

    On bot startup, an entry with null `before` and currently known status as `after`
    is inserted to create a clear border between logs from different sessions.
    On bot shutdown, an entry with null `after` and currently known status as `before`
    is inserted for the same purpose.
    """

    # Mock discord.Member
    Member = namedtuple("Member", ["id", "guild_id", "status"])

    members = [
        Member(
            id=1,
            guild_id=2,
            status=Status.online,
        ),
    ]

    startup_time = datetime.datetime.now()
    await repository.log_initial_statuses(members, 2, startup_time)  # startup

    change_time = startup_time + datetime.timedelta(minutes=20)
    await repository.log_status_change(1, 2, Status.online, Status.offline, change_time)

    members = [
        Member(
            id=1,
            guild_id=2,
            status=Status.offline,
        ),
    ]

    shutdown_time = change_time + datetime.timedelta(minutes=20)
    await repository.log_statuses_before_shutdown(members, 2, shutdown_time)  # shutdown

    result = await repository.get_user_stats(1, 2)

    # Expected stats
    # online   20m
    # offline  20m

    assert len(result) == 2

    online = next(item for item in result if item.status == Status.online).time
    offline = next(item for item in result if item.status == Status.offline).time

    assert online.total_seconds() == datetime.timedelta(minutes=20).total_seconds()
    assert offline.total_seconds() == datetime.timedelta(minutes=20).total_seconds()


@pytest.mark.asyncio
async def test_stats_with_early_logs(repository: StatusLogRepository):
    """Test that stats behave as expected with early logs

    An "early log" is a log entry made not in response to an actual
    status change event but when user request the stats.
    This ensures that the duration of most recent status of user is shown on the graph
    without having to change the status.
    """
    now = datetime.datetime.now()

    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=None,
        after=Status.online,
        timestamp=now,
    )

    now += datetime.timedelta(minutes=15)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.online,
        after=Status.idle,
        timestamp=now,
    )  # online  15m

    now += datetime.timedelta(minutes=16)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.idle,
        after=Status.dnd,
        timestamp=now,
    )  # idle    16m

    now += datetime.timedelta(minutes=2)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.dnd,
        after=Status.dnd,
        timestamp=now,
    )  # dnd 2m; early log

    # Expected stats
    # online 15m
    # idle   16m
    # dnd    2m

    result = await repository.get_user_stats(1, 2)

    assert len(result) == 3

    online = next(item for item in result if item.status == Status.online).time
    idle = next(item for item in result if item.status == Status.idle).time
    dnd = next(item for item in result if item.status == Status.dnd).time

    assert online.total_seconds() == datetime.timedelta(minutes=15).total_seconds()
    assert idle.total_seconds() == datetime.timedelta(minutes=16).total_seconds()
    assert dnd.total_seconds() == datetime.timedelta(minutes=2).total_seconds()

    now += datetime.timedelta(minutes=15)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.dnd,
        after=Status.offline,
        timestamp=now,
    )  # dnd 15m

    now += datetime.timedelta(minutes=3)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.offline,
        after=None,
        timestamp=now,
    )  # offline  3m

    # Expected stats
    # online  15m
    # idle    16m
    # dnd     17m (2 + 15)
    # offline 3m

    result = await repository.get_user_stats(1, 2)

    assert len(result) == 4

    online = next(item for item in result if item.status == Status.online).time
    idle = next(item for item in result if item.status == Status.idle).time
    dnd = next(item for item in result if item.status == Status.dnd).time
    offline = next(item for item in result if item.status == Status.offline).time

    assert online.total_seconds() == datetime.timedelta(minutes=15).total_seconds()
    assert idle.total_seconds() == datetime.timedelta(minutes=16).total_seconds()
    assert dnd.total_seconds() == datetime.timedelta(minutes=17).total_seconds()
    assert offline.total_seconds() == datetime.timedelta(minutes=3).total_seconds()
