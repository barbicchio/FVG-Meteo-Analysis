import math
from datetime import date


def to_float(x):
    if x in ("-", "", None):
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    try:
        return float(x)
    except Exception:
        return None


def to_int(x):
    if x in ("-", "", None):
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    try:
        return int(x)
    except Exception:
        return None


def build_date(year, month, day):
    if year is None or month is None or day is None:
        return None
    try:
        return date(int(year), int(month), int(day))
    except Exception:
        return None