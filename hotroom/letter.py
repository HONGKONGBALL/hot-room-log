"""Room statistics and the evidence-sheet letter."""

from decimal import Decimal

from .calc import (
    BAND_LABEL,
    SEVERITY,
    compute,
    format_1,
    format_effect,
    format_meas,
)


def enrich(row):
    metrics = compute(row["temp_c"], row["rh_percent"])
    return {
        "id": row["id"],
        "room_id": row["room_id"],
        "taken_at": row["taken_at"],
        "temp_c": row["temp_c"],
        "rh_percent": row["rh_percent"],
        "note": row["note"],
        "humidex": metrics["humidex"],
        "dew_point_c": metrics["dew_point_c"],
        "humidity_effect": metrics["humidity_effect"],
        "band": metrics["band"],
        "band_key": metrics["band_key"],
        "temp_text": format_meas(row["temp_c"]),
        "rh_text": format_meas(row["rh_percent"]),
        "dew_text": format_1(metrics["dew_point_c"]),
        "humidex_text": format_1(metrics["humidex"]),
        "effect_text": format_effect(metrics["humidity_effect"]),
        "note_text": row["note"] or "",
    }


def great_count(readings):
    return sum(1 for reading in readings if reading["band_key"] in ("great", "dangerous"))


def period_text(readings):
    first = readings[0]["taken_at"][:10]
    last = readings[-1]["taken_at"][:10]
    if first == last:
        return first
    return f"{first} to {last}"


def pick_highest(readings):
    """Highest humidex. On a tie, the most recent reading wins."""
    return max(readings, key=lambda reading: (reading["humidex"], reading["taken_at"], reading["id"]))


def band_count_text(readings):
    totals = {key: 0 for key in SEVERITY}
    for reading in readings:
        totals[reading["band_key"]] += 1
    parts = [f"{BAND_LABEL[key]} {totals[key]}" for key in SEVERITY if totals[key]]
    return ", ".join(parts)


def readings_phrase(count):
    if count == 1:
        return "1 reading"
    return f"{count} readings"


def summarize(readings):
    if not readings:
        return None
    latest = readings[-1]
    highest = pick_highest(readings)
    return {
        "count": len(readings),
        "count_text": readings_phrase(len(readings)),
        "period": period_text(readings),
        "latest": latest,
        "highest": highest,
        "great": great_count(readings),
        "great_line": f"{great_count(readings)} of {len(readings)}",
        "counts_text": band_count_text(readings),
        "highest_line": (
            f"{format_1(highest['humidex'])} ({highest['band']}) on {highest['taken_at']}"
        ),
        "latest_line": (
            f"{format_1(latest['humidex'])} ({latest['band']}) on {latest['taken_at']}"
        ),
    }


def build_letter(room_name, readings):
    count = len(readings)
    first = readings[0]["taken_at"][:10]
    last = readings[-1]["taken_at"][:10]
    word = "reading" if count == 1 else "readings"
    if first == last:
        when = f"On {first}, we recorded {count} temperature and humidity {word} in this room."
    else:
        when = (
            f"From {first} to {last}, we recorded {count} temperature and humidity "
            f"{word} in this room."
        )
    intro = f"We are students who use {room_name}. {when}"

    highest = pick_highest(readings)
    detail = (
        f"The highest humidex was {format_1(highest['humidex'])} ({highest['band']}) "
        f"on {highest['taken_at']}, when the air temperature was "
        f"{format_meas(highest['temp_c'])} °C and the relative humidity was "
        f"{format_meas(highest['rh_percent'])} %."
    )
    if Decimal(format_1(highest["humidity_effect"])) > 0:
        detail += (
            f" Humidity added {format_1(highest['humidity_effect'])} humidex points "
            "on top of the air temperature."
        )

    counts = f"Readings by humidex comfort band: {band_count_text(readings)}."
    if highest["band_key"] == "comfortable":
        ask = "All readings were in the Comfortable band, so no change is requested at this time."
    else:
        ask = (
            "Could you please check the ventilation, fans or air-conditioning in this room? "
            "We can share the full list of readings."
        )
    closing = "Thank you,\n[your name]"
    return "\n\n".join(
        ["Dear [recipient],", intro, detail, counts, ask, closing]
    )
