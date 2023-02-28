import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
import datetime

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
def repository(engine: AsyncEngine):
    return StatusLogRepository(engine)


@pytest.mark.asyncio
async def test_insert(repository: StatusLogRepository, engine: AsyncEngine):
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
        before="idle",
        after=Status.online,
        timestamp=now,
    )

    now += datetime.timedelta(minutes=15)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.online,
        after="idle",
        timestamp=now,
    )  # online  15m

    now += datetime.timedelta(minutes=16)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before="idle",
        after=Status.offline,
        timestamp=now,
    )  # idle    16m

    now += datetime.timedelta(minutes=9)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.offline,
        after="dnd",
        timestamp=now,
    )  # offline  9m

    now += datetime.timedelta(minutes=64)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before="dnd",
        after="idle",
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

    # invalid (change does not match previous record we have)
    now += datetime.timedelta(days=2)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=None,
        after=Status.online,
        timestamp=now,
    )

    now += datetime.timedelta(minutes=10)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before="idle",
        after=Status.online,
        timestamp=now,
    )

    now += datetime.timedelta(minutes=10)
    await repository.log_status_change(
        user_id=1,
        guild_id=2,
        before=Status.online,
        after="dnd",
        timestamp=now,
    )  # online 10m

    result = await repository.get_user_stats(user_id=1, guild_id=2)

    assert len(result) == 4

    online = next(item for item in result if item.status == Status.online).time
    offline = next(item for item in result if item.status == Status.offline).time
    idle = next(item for item in result if item.status == Status.idle).time
    dnd = next(item for item in result if item.status == Status.dnd).time

    assert (
        online.total_seconds() == datetime.timedelta(hours=1, minutes=3).total_seconds()
    )

    assert offline.total_seconds() == datetime.timedelta(minutes=9).total_seconds()

    assert idle.total_seconds() == datetime.timedelta(minutes=39).total_seconds()

    assert dnd.total_seconds() == datetime.timedelta(hours=1, minutes=4).total_seconds()
