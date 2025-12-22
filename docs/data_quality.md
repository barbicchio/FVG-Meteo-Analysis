# Data Quality Report

## Scope and reference schema

All data quality checks described in this document are **derived directly from the canonical schema** defined in:

👉 [`docs/schema.md`](schema.md)

Schema version referenced: **v1.1**

This report audits **raw data only**.  
No cleaning, imputation, or transformation is performed at this stage.

---

## Dataset overview

- Temporal coverage: **1991–2024** (estimated from raw data)  
  Note: temporal coverage varies per single station.
- Number of stations: <!-- TODO: fill from notebook -->
- Total records (raw): <!-- TODO: fill from notebook -->

---

## Missing values

Missing values are represented in the raw data as:
- `"-"` (string sentinel)
- empty strings
- `NaN`

All are treated as missing.

### Overall missingness

| Column | % Missing |
|------|-----------:|
| `precipitation` | 39.70 |
| `pressure_mean` | 30.14 |
| `wind_direction_max` | 28.52 |
| `wind_speed_mean` | 28.22 |
| `wind_speed_max` | 26.73 |
| `solar_radiation` | 23.81 |
| `humidity_mean` | 16.52 |
| `humidity_min` | 15.10 |
| `humidity_max` | 14.90 |
| `temperature_max` | 12.94 |
| `temperature_min` | 12.52 |
| `temperature_mean` | 12.46 |
| `date` | 2.13 |
| `day` | 2.13 |
| `month` | 0.69 |
| `year` | 0.00 |
| `station_name` | 0.00 |

### Missingness by station / year

Key observations:
- Missingness is substantial for **precipitation (~40%)**, **pressure (~30%)**, and **wind variables (~26–29%)**, suggesting either sensor availability differences across stations/years or incomplete historical coverage.
- `date/day` missingness (~2.13%) indicates that some records cannot be positioned reliably on the timeline (invalid or missing day/month components after minimal parsing).

**Assessment**
- Missingness is likely **systematic / structural** for some variables (e.g., precipitation, pressure, wind), rather than random.
- Impact on downstream analysis:
  - Time-series and station-to-station comparisons will be biased if high-missingness stations/periods are included without explicit filtering.
  - Variables with >25% missingness require careful handling (e.g., feature exclusion, station filtering, or model strategies tolerant to missing data).

---

## Range violations

Range checks are performed according to the **Allowed range / domain** defined in the schema.

| Column | Observed min | Observed max | Violations |
|------|--------------:|--------------:|-----------:|
| `temperature_min` | -21.5 | 28.5 | 0 |
| `temperature_mean` | -19.6 | 31.6 | 0 |
| `temperature_max` | -18.2 | 38.5 | 0 |
| `humidity_min` | 0.0 | 100.0 | 0 |
| `humidity_mean` | 7.0 | 100.0 | 0 |
| `humidity_max` | 7.0 | 100.0 | 0 |
| `pressure_mean` | 774.7 | 1044.0 | 79 |

**Assessment**
- Temperature and humidity appear consistent with plausible bounds under the current schema.
- `pressure_mean` shows **79 violations** with observed minimum **774.7 hPa**, below the schema lower bound (800 hPa).

Policy decision:
- Values outside physical bounds will be **flagged and excluded** during processing.

**Important note (pressure)**
- Pressure is strongly altitude-dependent. Values around **775–800 hPa** can be plausible for high-elevation stations.
- Therefore, the current schema lower bound (800 hPa) may be too strict for station-level pressure.
- Action item:
  - Either (A) relax the lower bound (e.g., **750 hPa**) or (B) keep 800 hPa and treat these as invalid **only if** metadata indicates sea-level normalization (currently unavailable).

---

## Duplicate records

Schema invariant:
> `(station_name, date)` must be unique

Findings:
- Duplicate rows (same key by `station_name` + `date`): **1426**

Policy decision:
- Duplicates will be resolved deterministically (e.g., keeping the first occurrence) and documented.

Action item:
- Quantify:
  - number of duplicate keys (unique `(station_name, date)` duplicates)
  - whether duplicates are identical or conflicting across measurements

---

## Temporal gaps

Expected granularity: **daily per station**

### Current result (from preliminary gap computation)
The current computation based on `dates.diff()` over **valid dates only** yields, for the listed stations, `max_gap_days = 1` and `missing_total_days = 0`.

**Why this is likely misleading**
This method only detects gaps **between consecutive observed valid dates**. It can miss “true” missing periods when:
- many records have **missing/invalid `date`** (and are dropped by `dropna(subset=["date"])`)
- the dataset contains one record per day *when present*, but missingness manifests as **missing records** that are not represented by any date (i.e., the expected calendar days are absent altogether)
- coverage differs per station and period, and the method needs an expected calendar to compare against

### Correct metric to report (recommended)
For each station, compute:
- **coverage_days** = number of unique valid observed dates
- **expected_days** = number of days between min(date) and max(date) (inclusive)
- **missing_total_days** = expected_days − coverage_days
- optionally: longest consecutive missing run by comparing observed dates vs full daily date range

Key observations:
- Temporal coverage varies per station (known).
- `date` missingness (~2.13%) already indicates that some time positioning is impossible without dropping rows or keeping them as undated.

Impact:
- Stations with severe temporal coverage issues may be excluded from time-series analyses, or analyzed only in well-covered periods.

Action item:
- Replace the current “diff-only” approach with **coverage-based** gap computation and report per-station coverage.

---

## Schema validation (Pydantic)

Validation performed using the Pydantic model `DailyObservation`
derived from schema **v1.1**.

Findings:
- % rows with ≥1 schema violation: <!-- TODO: fill from notebook -->
- Most frequent violating fields:
  - likely dominated by missingness and type inconsistencies for high-missing columns (precipitation/pressure/wind)
  - pressure lower-bound violations (if enforced as 800 hPa)

**Assessment**
- Violations are mainly due to:
  - missing values
  - schema range constraints (pressure lower bound)
  - type inconsistencies resolved to NaN during minimal parsing

---

## Summary of decisions

| Issue | Decision |
|-----|----------|
| Missing values | Preserved, no imputation |
| Range violations | Flag and exclude (pressure bound under review due to altitude plausibility) |
| Duplicates | Deterministic resolution |
| Temporal gaps | Documented via coverage-based computation (diff-only method is insufficient) |

---

## Limitations

- Station metadata (lat/lon, altitude, calibration) not available
- Pressure values are station-level and not sea-level adjusted

These limitations should be considered when interpreting results.