from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


SCHEMA_VERSION = "v1.1"


class DailyObservation(BaseModel):
    """
    Canonical representation of a daily meteorological observation.
    """

    # ---- Core identifiers & time ----
    date: date = Field(description="Calendar date of observation (ISO-8601).")

    year: int = Field(ge=1900, description="Year of observation.")
    month: int = Field(ge=1, le=12, description="Month of observation (1–12).")
    day: int = Field(ge=1,le=31,description="Day of month (1–31).")

    station_name: str = Field(min_length=1, description="Canonicalized name of the meteorological station.")

    # ---- Precipitation ----
    precipitation: Optional[float] = Field(ge=0, description="Total daily precipitation in millimeters." )

    # ---- Temperature ----
    temperature_min: Optional[float] = Field(ge=-50, le=50, description="Daily minimum air temperature in °C." )
    temperature_mean: Optional[float] = Field(ge=-50, le=50, description="Daily mean air temperature in °C." )
    temperature_max: Optional[float] = Field(ge=-50, le=50, description="Daily maximum air temperature in °C.")

    # ---- Humidity ----
    humidity_min: Optional[float] = Field(ge=0, le=100, description="Daily minimum relative humidity in percent.")
    humidity_mean: Optional[float] = Field(ge=0, le=100, description="Daily mean relative humidity in percent.")
    humidity_max: Optional[float] = Field(ge=0, le=100, description="Daily maximum relative humidity in percent.")

    # ---- Wind ----
    wind_speed_mean: Optional[float] = Field(ge=0, description="Daily mean wind speed in km/h.")
    wind_speed_max: Optional[float] = Field(ge=0, description="Daily maximum wind speed in km/h.")
    wind_direction_max: Optional[int] = Field(ge=0, le=360, description="Wind direction (degrees from North) at maximum wind speed.")

    # ---- Radiation & pressure ----
    solar_radiation: Optional[float] = Field(ge=0, description="Total daily solar radiation in kJ/m².")
    pressure_mean: Optional[float] = Field(ge=800, le=1050, description="Daily mean atmospheric pressure in hPa.")


    # Model configuration
    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        validate_assignment=True,
        str_strip_whitespace=True,
    )