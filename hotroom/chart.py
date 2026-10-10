"""Geometry for the inline humidex chart."""

import math

from .calc import format_1
from .letter import pick_highest

PLOT_LEFT = 56
PLOT_RIGHT = 624
PLOT_TOP = 16
PLOT_BOTTOM = 228


def _coord(value):
    return f"{value:.2f}"


def chart_model(readings):
    humidexes = [reading["humidex"] for reading in readings]
    lowest = min(humidexes)
    highest_value = max(humidexes)
    y_min = min(20, math.floor(lowest) - 2)
    y_max = max(55, math.ceil(highest_value) + 2)
    plot_w = PLOT_RIGHT - PLOT_LEFT
    plot_h = PLOT_BOTTOM - PLOT_TOP
    span = y_max - y_min

    def y_at(humidex):
        return PLOT_TOP + (y_max - humidex) / span * plot_h

    def x_at(index, count):
        if count == 1:
            return PLOT_LEFT + plot_w / 2
        return PLOT_LEFT + plot_w * index / (count - 1)

    count = len(readings)
    strips = []
    ranges = (
        ("comfortable", y_min, min(30, y_max)),
        ("some", max(30, y_min), min(40, y_max)),
        ("great", max(40, y_min), min(45, y_max)),
        ("dangerous", max(45, y_min), y_max),
    )
    for key, low, high in ranges:
        if high <= low:
            continue
        top = y_at(high)
        strips.append(
            {
                "key": key,
                "x": _coord(PLOT_LEFT),
                "y": _coord(top),
                "width": _coord(plot_w),
                "height": _coord(y_at(low) - top),
            }
        )

    points = []
    for index, reading in enumerate(readings):
        points.append(
            {
                "cx": _coord(x_at(index, count)),
                "cy": _coord(y_at(reading["humidex"])),
                "taken_at": reading["taken_at"],
                "humidex": format_1(reading["humidex"]),
                "band_key": reading["band_key"],
                "band": reading["band"],
            }
        )

    y_labels = []
    for mark in (30, 40, 45):
        if y_min <= mark <= y_max:
            y_labels.append({"text": str(mark), "y": _coord(y_at(mark))})

    polyline = None
    if count >= 2:
        polyline = " ".join(f"{point['cx']},{point['cy']}" for point in points)

    top_reading = pick_highest(readings)
    noun = "reading" if count == 1 else "readings"
    description = (
        f"{count} {noun} from {readings[0]['taken_at']} to {readings[-1]['taken_at']}; "
        f"highest {format_1(top_reading['humidex'])} ({top_reading['band']})."
    )
    return {
        "strips": strips,
        "points": points,
        "polyline": polyline,
        "y_labels": y_labels,
        "first_time": readings[0]["taken_at"],
        "last_time": readings[-1]["taken_at"],
        "first_x": points[0]["cx"],
        "last_x": points[-1]["cx"],
        "description": description,
        "axis_top": _coord(PLOT_TOP),
        "axis_bottom": _coord(PLOT_BOTTOM),
        "axis_left": _coord(PLOT_LEFT),
        "axis_right": _coord(PLOT_RIGHT),
    }
