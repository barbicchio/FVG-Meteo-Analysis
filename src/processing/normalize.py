from src.utils.casting import to_float, to_int

FIELD_MAP = {
    "Pioggia mm": "precipitation",
    "Temp. min °C": "temperature_min",
    "Temp. med °C": "temperature_mean",
    "Temp. max °C": "temperature_max",
    "Umidita' min %": "humidity_min",
    "Umidita' med %": "humidity_mean",
    "Umidita' max %": "humidity_max",
    "Vento med km/h": "wind_speed_mean",
    "Vento max km/h": "wind_speed_max",
    "Dir. V. max °N": "wind_direction_max",
    "Radiaz. KJ/m2": "solar_radiation",
    "Press. med hPa": "pressure_mean",
}


def normalize_record(raw: dict) -> dict:
    data = {}

    for raw_key, field in FIELD_MAP.items():
        val = raw.get(raw_key)
        if field == "wind_direction_max":
            data[field] = to_int(val)
        else:
            data[field] = to_float(val)

    return data