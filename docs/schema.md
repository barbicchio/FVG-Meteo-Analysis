# Dataset Schema — Daily Meteorological Observations (FVG)

## Scope
Daily aggregated meteorological observations from fixed weather stations in Friuli Venezia Giulia.

## Granularity
- **Temporal:** daily  
- **Spatial:** station-level

## Update frequency
Monthly (historical archive)

## Schema version
v1.1

---

## Core identifiers & time

| Column name | Type | Unit | Nullable | Allowed range / domain | Source | Description | Notes |
|------------|------|------|----------|------------------------|--------|-------------|-------|
| `date` | date | ISO-8601 | no | valid calendar date | derived | Calendar date of observation | Derived from year/month/day |
| `year` | int | year | no | ≥ 1900 | raw | Year of observation | Retained for grouping |
| `month` | int | month | no | 1–12 | raw | Month of observation | — |
| `day` | int | day | no | 1–31 | raw | Day of month | Not all combinations valid |
| `station_name` | string | — | no | controlled vocabulary | raw | Name of meteorological station | Canonicalized string |

---

## Precipitation

| Column name | Type | Unit | Nullable | Allowed range / domain | Source | Description | Notes |
|------------|------|------|----------|------------------------|--------|-------------|-------|
| `precipitation` | float | mm | yes | ≥ 0 | raw | Total daily precipitation | Missing when sensor unavailable |

---

## Temperature

| Column name | Type | Unit | Nullable | Allowed range / domain | Source | Description | Notes |
|------------|------|------|----------|------------------------|--------|-------------|-------|
| `temperature_min` | float | °C | yes | -50 – +50 | raw | Daily minimum air temperature | Physical bounds |
| `temperature_mean` | float | °C | yes | -50 – +50 | raw | Daily mean air temperature | — |
| `temperature_max` | float | °C | yes | -50 – +50 | raw | Daily maximum air temperature | — |

---

## Humidity

| Column name | Type | Unit | Nullable | Allowed range / domain | Source | Description | Notes |
|------------|------|------|----------|------------------------|--------|-------------|-------|
| `humidity_min` | float | % | yes | 0 – 100 | raw | Daily minimum relative humidity | — |
| `humidity_mean` | float | % | yes | 0 – 100 | raw | Daily mean relative humidity | — |
| `humidity_max` | float | % | yes | 0 – 100 | raw | Daily maximum relative humidity | — |

---

## Wind

| Column name | Type | Unit | Nullable | Allowed range / domain | Source | Description | Notes |
|------------|------|------|----------|------------------------|--------|-------------|-------|
| `wind_speed_mean` | float | km/h | yes | ≥ 0 | raw | Daily mean wind speed | — |
| `wind_speed_max` | float | km/h | yes | ≥ 0 | raw | Daily maximum wind speed | — |
| `wind_direction_max` | int | degrees (°N) | yes | 0 – 360 | raw | Wind direction at maximum speed | Meteorological convention |

---

## Radiation & pressure

| Column name | Type | Unit | Nullable | Allowed range / domain | Source | Description | Notes |
|------------|------|------|----------|------------------------|--------|-------------|-------|
| `solar_radiation` | float | kJ/m² | yes | ≥ 0 | raw | Total daily solar radiation | Zero possible in winter |
| `pressure_mean` | float | hPa | yes | 800 – 1050 | raw | Daily mean atmospheric pressure | Station-level pressure |

---

## Missing values policy

- Raw missing values represented as `"-"` in the source are normalized to `null`
- No imputation is performed at raw or processed data level
- Missingness is preserved as meaningful information

---

## Data quality assumptions & invariants

- `(station_name, date)` must be unique
- Temperature values outside physical bounds are flagged as invalid
- Humidity values constrained to `[0, 100]`
- Negative precipitation values are invalid
- Temporal gaps are expected due to sensor downtime

---

## Out-of-scope but relevant metadata

The following station-level metadata are known to affect interpretation of the data but are not available in the current source and are therefore out of scope for this dataset version:
- Geographic coordinates (latitude, longitude)
- Station altitude (affects pressure and temperature)
- Sensor type and calibration history
- Station relocation or maintenance events

These limitations should be considered when performing spatial analysis or long-term trend studies.

---

# Monthly Dataset Schema (`monthly.parquet`)

## Overview
`monthly.parquet` is a derived analytical dataset built from `daily.parquet`.
Each row represents the aggregated climatic behavior of **one station in one calendar month**.

- **Unit of analysis:** station × year × month  
- **Purpose:** climate analysis, anomaly detection, similarity, clustering, drift  
- **Missing data:** preserved (no imputation); coverage metrics provided

---

## Primary Keys
- `station_name` — meteorological station name  
- `year` — calendar year  
- `month` — calendar month (1–12)

---

## Temporal Coverage
- `n_days_rows` — number of daily records available for the station-month

---

## Temperature (°C)
For each of:
- `temperature_min`
- `temperature_mean`
- `temperature_max`

Provided metrics:
- `_mean`, `_min`, `_max`, `_std`
- `_n_valid_days`
- `_coverage`

---

## Precipitation (mm)
- `precipitation_sum` — total monthly precipitation  
- `precipitation_max` — maximum daily precipitation  
- `precipitation_mean` — mean daily precipitation  
- `precipitation_rainy_days` — days with precipitation > 0  
- `precipitation_n_valid_days`, `precipitation_coverage`

---

## Humidity (%)
For each of:
- `humidity_min`
- `humidity_mean`
- `humidity_max`

Provided metrics:
- `_mean`, `_min`, `_max`, `_std`
- `_n_valid_days`, `_coverage`

---

## Wind
**Speed (km/h)** for:
- `wind_speed_mean`
- `wind_speed_max`

Provided metrics:
- `_mean`, `_min`, `_max`, `_std`
- `_n_valid_days`, `_coverage`

**Direction (degrees from North):**
- `wind_direction_max_median`
- `wind_direction_max_n_valid_days`
- `wind_direction_max_coverage`

---

## Solar Radiation (kJ/m²)
- `_mean`, `_min`, `_max`, `_std`
- `_n_valid_days`, `_coverage`

---

## Atmospheric Pressure (hPa)
- `_mean`, `_min`, `_max`, `_std`
- `_n_valid_days`, `_coverage`

---

## Notes
- No imputation or smoothing is applied.
- Coverage metrics enable filtering of unreliable months.
- `monthly.parquet` is the main dataset for downstream analysis.


## Schema changelog

- **v1.0** — Initial canonical schema definition  
- **v1.1** — Added allowed ranges and explicit data quality invariants
- **v1.2** — Added Montly schema definition