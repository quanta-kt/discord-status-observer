from PIL import Image, ImageDraw


Color = tuple[int, int, int]


def _color(color_value: int) -> Color:
    return (
        (color_value & 0xFF0000) >> 16,
        (color_value & 0x00FF00) >> 8,
        (color_value & 0x0000FF) >> 0,
    )


GRAPH_IMAGE_WIDTH = 1000
GRAPH_IMAGE_HEIGHT = 1000
GRAPH_IMAGE_SIZE = (GRAPH_IMAGE_WIDTH, GRAPH_IMAGE_HEIGHT)
GRAPH_IMAGE_FILL_COLOR = 0
GRAPH_ARCH_WIDTH = round(GRAPH_IMAGE_HEIGHT * 0.2)

ONLINE_COLOR = _color(0x3BA55C)
IDLE_COLOR = _color(0xFAA61A)
DND_COLOR = _color(0xED4245)
OFFLINE_COLOR = _color(0x4E545E)


def generate_pie_graph(values: list[tuple[float, Color]]) -> Image:
    img = Image.new("RGBA", GRAPH_IMAGE_SIZE, color=GRAPH_IMAGE_FILL_COLOR)
    draw = ImageDraw.ImageDraw(img)

    consumed = 0.0
    for val, color in values:

        arc_angle = val * 360

        draw.arc(
            (0, 0, *GRAPH_IMAGE_SIZE),
            consumed,
            consumed + arc_angle,
            fill=color,
            width=GRAPH_ARCH_WIDTH,
        )

        consumed += arc_angle

    return img


def generate_status_pie_graph(
    online: float = 0.0,
    idle: float = 0.0,
    dnd: float = 0.0,
    offline: float = 0.0,
) -> Image:

    values = [
        (online, ONLINE_COLOR),
        (idle, IDLE_COLOR),
        (dnd, DND_COLOR),
        (offline, OFFLINE_COLOR),
    ]

    return generate_pie_graph(values)
