from pathlib import Path
import pandas as pd

IN_PATH = Path("data/processed/daily.parquet")
OUT_DIR = Path("data/processed")
OUT_PATH = OUT_DIR / "monthly.parquet"


# ---- Helpers ----
def _count_valid(s: pd.Series) -> int:
    return int(s.notna().sum())


def build_monthly(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure expected core columns exist
    required = {"station_name", "year", "month"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in daily.parquet: {missing}")

    # Canonical measure columns (adjust here if you change the schema)
    measures = [
        "precipitation",
        "temperature_min",
        "temperature_mean",
        "temperature_max",
        "humidity_min",
        "humidity_mean",
        "humidity_max",
        "wind_speed_mean",
        "wind_speed_max",
        "wind_direction_max",
        "solar_radiation",
        "pressure_mean",
    ]
    measures = [c for c in measures if c in df.columns]  # tolerate missing columns

    # Make sure types are ok (avoid groupby weirdness)
    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")

    # Total days observed in that month (rows in daily for that station-month)
    # Note: if you have duplicate days, this will count duplicates. If you want strictly unique days:
    # total_days = df.groupby(keys)["date"].nunique()
    keys = ["station_name", "year", "month"]

    total_days = (
        df.groupby(keys, dropna=False)
          .size()
          .rename("n_days_rows")
          .reset_index()
    )

    # Base aggregations
    agg_map = {}
    for c in measures:
        if c == "precipitation":
            # For precipitation, sum is meaningful; mean can be misleading, but keep both if you want
            agg_map[c] = ["sum", "max", "mean"]
        elif c in ("wind_direction_max",):
            # Direction is circular; mean is not meaningful.
            # We keep mode-like proxy via median, plus max availability. (Simple and defensible.)
            agg_map[c] = ["median"]
        else:
            agg_map[c] = ["mean", "min", "max", "std"]

    monthly = (
        df.groupby(keys, dropna=False)
          .agg(agg_map)
    )

    # Flatten multi-index columns
    monthly.columns = [
        f"{col}_{stat}" for col, stat in monthly.columns.to_flat_index()
    ]
    monthly = monthly.reset_index()

    # Valid-day counts per variable (coverage)
    valid_counts = {}
    for c in measures:
        valid_counts[f"{c}_n_valid_days"] = (
            df.groupby(keys, dropna=False)[c].apply(_count_valid)
        )
    valid_counts_df = pd.DataFrame(valid_counts).reset_index()

    # Rainy days (precipitation > 0) — only if precipitation exists
    rainy_days_df = None
    if "precipitation" in df.columns:
        rainy_days_df = (
            df.assign(_rainy=(pd.to_numeric(df["precipitation"], errors="coerce") > 0))
              .groupby(keys, dropna=False)["_rainy"]
              .sum()
              .rename("precipitation_rainy_days")
              .reset_index()
        )

    # Merge all together
    out = monthly.merge(total_days, on=keys, how="left")
    out = out.merge(valid_counts_df, on=keys, how="left")
    if rainy_days_df is not None:
        out = out.merge(rainy_days_df, on=keys, how="left")

    # Coverage ratios (optional but useful)
    for c in measures:
        vc = f"{c}_n_valid_days"
        if vc in out.columns:
            out[f"{c}_coverage"] = out[vc] / out["n_days_rows"]

    # Sort for readability
    out = out.sort_values(["station_name", "year", "month"]).reset_index(drop=True)

    return out


def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing input parquet: {IN_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(IN_PATH)

    monthly = build_monthly(df)
    monthly.to_parquet(OUT_PATH, index=False)

    print(f"[OK] monthly rows: {len(monthly)}")
    print(f"[OK] written: {OUT_PATH}")


if __name__ == "__main__":
    main()