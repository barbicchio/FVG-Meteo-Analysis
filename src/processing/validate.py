from src.schema.observations import DailyObservation
from src.utils.casting import build_date
from src.processing.normalize import normalize_record


def record_to_daily_observation(raw: dict):
    year = raw.get("anno")
    month = raw.get("mese")
    day = raw.get("giorno*")

    obs_date = build_date(year, month, day)
    if obs_date is None:
        return None

    data = {
        "date": obs_date,
        "year": int(year),
        "month": int(month),
        "day": int(day),
        "station_name": raw.get("stazione"),
    }

    data.update(normalize_record(raw))

    try:
        return DailyObservation(**data)
    except Exception:
        return None