"""Humidex, dew point and comfort bands.

Rounding is half away from zero, to the requested decimal places, applied to
the full-precision value via Decimal ROUND_HALF_UP on repr(value).
"""

import math
from decimal import Decimal, ROUND_HALF_UP

# Band text and background colours are defined in the stylesheet.
BANDS = (
    ("comfortable", "Comfortable", "Below 30"),
    ("some", "Some discomfort", "30 to 39.9"),
    ("great", "Great discomfort", "40 to 45"),
    ("dangerous", "Dangerous", "Above 45"),
)
BAND_LABEL = {key: label for key, label, _range in BANDS}
SEVERITY = ("dangerous", "great", "some", "comfortable")


def _quantize(value, places):
    quantum = Decimal("1").scaleb(-places)
    return Decimal(repr(float(value))).quantize(quantum, rounding=ROUND_HALF_UP)


def round_1(value):
    number = _quantize(value, 1)
    result = float(number)
    if result == 0:
        return 0.0
    return result


def format_1(value):
    return f"{_quantize(value, 1):.1f}"


def format_meas(value):
    number = _quantize(value, 1)
    if number == number.to_integral_value():
        return str(int(number))
    return f"{number:.1f}"


def format_effect(value):
    number = _quantize(value, 1)
    if number == 0:
        return "0.0"
    if number < 0:
        return f"{number:.1f}"
    return f"+{number:.1f}"


def format_places(value, places):
    return f"{_quantize(value, places):.{places}f}"


def json_meas(value):
    number = _quantize(value, 1)
    if number == number.to_integral_value():
        return int(number)
    return float(number)


def json_1(value):
    return float(_quantize(value, 1))


def band_for(humidex):
    if humidex < 30:
        key = "comfortable"
    elif humidex < 40:
        key = "some"
    elif humidex <= 45:
        key = "great"
    else:
        key = "dangerous"
    return key, BAND_LABEL[key]


def compute(temp_c, rh_percent):
    """Return derived values for one temperature and relative humidity."""
    temperature = float(temp_c)
    humidity = float(rh_percent)
    es = 6.105 * math.exp(17.27 * temperature / (237.7 + temperature))
    vapour = (humidity / 100.0) * es
    gamma = math.log(humidity / 100.0) + 17.27 * temperature / (237.7 + temperature)
    humidex = round_1(temperature + 0.5555 * (vapour - 10))
    dew_point = round_1(237.7 * gamma / (17.27 - gamma))
    effect = round_1(humidex - temperature)
    key, label = band_for(humidex)
    return {
        "temp_c": temperature,
        "rh_percent": humidity,
        "es": es,
        "e": vapour,
        "gamma": gamma,
        "humidex": humidex,
        "dew_point_c": dew_point,
        "humidity_effect": effect,
        "band": label,
        "band_key": key,
    }


def working_steps(temperature, humidity, result):
    """Four display steps. Intermediates are rounded; the results are not recomputed from them."""
    temp_text = format_meas(temperature)
    rh_text = format_meas(humidity)
    es_text = format_places(result["es"], 2)
    e_text = format_places(result["e"], 2)
    gamma_text = format_places(result["gamma"], 4)
    return [
        (
            f"Saturation vapour pressure: es = 6.105 × exp(17.27 × {temp_text} "
            f"÷ (237.7 + {temp_text})) = {es_text} hPa"
        ),
        f"Vapour pressure: e = {rh_text} ÷ 100 × {es_text} = {e_text} hPa",
        (
            f"Humidex: {temp_text} + 0.5555 × ({e_text} − 10) = "
            f"{format_1(result['humidex'])}"
        ),
        (
            f"Dew point: gamma = ln({rh_text} ÷ 100) + 17.27 × {temp_text} "
            f"÷ (237.7 + {temp_text}) = {gamma_text}; "
            f"Td = 237.7 × {gamma_text} ÷ (17.27 − {gamma_text}) = "
            f"{format_1(result['dew_point_c'])} °C"
        ),
    ]


def compare_sentence(humidex_a, humidex_b):
    left = Decimal(format_1(humidex_a))
    right = Decimal(format_1(humidex_b))
    if right == left:
        return "Both conditions have the same humidex."
    gap = format_1(abs(right - left))
    if right > left:
        return f"Condition B feels {gap} humidex points hotter than condition A."
    return f"Condition B feels {gap} humidex points cooler than condition A."
