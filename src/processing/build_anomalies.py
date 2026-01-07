from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

# -----------------
# Config (MVP)
# -----------------
IN_PATH = Path("data/processed/monthly.parquet")
OUT_PATH = Path("data/processed/monthly_anomalies.parquet")

SCALE = 1.4826
ZCAP = 10
PCTL = 0.99

MIN_DAYS_ROWS = 28
MIN_MEAN_COVERAGE = 0.70
MIN_FEATURES_PRESENT = 6
TOP_K = 5

CORE_FEATURES = [
    "precipitation_sum",
    "precipitation_rainy_days",
    "temperature_min_mean",
    "temperature_mean_mean",
    "temperature_max_mean",
    "humidity_mean_mean",
    "wind_speed_mean_mean",
    "solar_radiation_mean",
    "pressure_mean_mean",
]

FEATURE_TO_COVERAGE = {
    "precipitation_sum": "precipitation_coverage",
    "precipitation_rainy_days": "precipitation_coverage",
    "temperature_min_mean": "temperature_min_coverage",
    "temperature_mean_mean": "temperature_mean_coverage",
    "temperature_max_mean": "temperature_max_coverage",
    "humidity_mean_mean": "humidity_mean_coverage",
    "wind_speed_mean_mean": "wind_speed_mean_coverage",
    "solar_radiation_mean": "solar_radiation_coverage",
    "pressure_mean_mean": "pressure_mean_coverage",
}


# -----------------
# Helpers
# -----------------
def compute_baseline(group: pd.DataFrame, features: list[str]) -> pd.Series:
    med = group[features].median()
    mad = (group[features] - med).abs().median() * SCALE
    mad = mad.replace(0, np.nan)  # avoid division by zero
    return pd.concat([med.add_suffix("_median"), mad.add_suffix("_mad")])


def top_features_row(row: pd.Series, features: list[str]) -> str:
    contrib = []
    for f in features:
        z = row.get(f"{f}_z")
        if pd.notna(z):
            raw = row.get(f)
            contrib.append((f, float(abs(z)), float(z), None if pd.isna(raw) else float(raw)))
    contrib.sort(key=lambda x: x[1], reverse=True)
    return json.dumps(contrib[:TOP_K])


def main() -> None:
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing input: {IN_PATH}")

    df = pd.read_parquet(IN_PATH)

    # ---- Sanity checks
    for c in ["station_name", "year", "month", "n_days_rows"]:
        if c not in df.columns:
            raise ValueError(f"Missing required column in monthly.parquet: {c}")

    # ---- Feature + coverage columns present
    core = [c for c in CORE_FEATURES if c in df.columns]
    if len(core) < 4:
        raise ValueError(f"Too few CORE_FEATURES found in data. Found: {core}")

    cov_cols = [FEATURE_TO_COVERAGE[c] for c in core if FEATURE_TO_COVERAGE.get(c) in df.columns]

    # ---- Gating
    df["n_features_present"] = df[core].notna().sum(axis=1)

    if not cov_cols:
        raise ValueError("No coverage columns found. Expected *_coverage columns in monthly.parquet.")

    df["mean_coverage_core"] = df[cov_cols].mean(axis=1, skipna=True)

    days_ok = df["n_days_rows"] >= MIN_DAYS_ROWS
    feat_ok = df["n_features_present"] >= MIN_FEATURES_PRESENT
    cov_ok = df["mean_coverage_core"] >= MIN_MEAN_COVERAGE

    df["is_evaluable"] = days_ok & feat_ok & cov_ok

    df["gate_reason"] = "OK"
    df.loc[~days_ok, "gate_reason"] = "LOW_DAYS"
    df.loc[days_ok & ~feat_ok, "gate_reason"] = "FEW_FEATURES"
    df.loc[days_ok & feat_ok & ~cov_ok, "gate_reason"] = "LOW_COVERAGE"

    df_e = df[df["is_evaluable"]].copy()
    print(f"[OK] evaluable rows: {len(df_e)} / {len(df)}")

    # ---- Baseline per station (median + MAD)
    # include_groups=False silences pandas deprecation (works on recent pandas)
    try:
        baseline = (
            df_e.groupby("station_name", group_keys=False)
            .apply(compute_baseline, features=core, include_groups=False)
        )
    except TypeError:
        baseline = (
            df_e.groupby("station_name", group_keys=False)
            .apply(compute_baseline, features=core)
        )

    df_z = df_e.merge(baseline.reset_index(), on="station_name", how="left")

    # ---- Robust z-scores
    z_cols: list[str] = []
    for f in core:
        zc = f"{f}_z"
        df_z[zc] = (df_z[f] - df_z[f"{f}_median"]) / df_z[f"{f}_mad"]
        z_cols.append(zc)

    # ---- Cap z-scores (fix for near-zero dispersion vars dominating)
    for zc in z_cols:
        df_z[zc] = df_z[zc].clip(-ZCAP, ZCAP)

    # ---- Anomaly score
    df_z["n_features_used"] = df_z[z_cols].notna().sum(axis=1)
    df_z["anomaly_score"] = df_z[z_cols].abs().mean(axis=1, skipna=True)

    # ---- Threshold per station (p99)
    thresholds = (
        df_z.groupby("station_name")["anomaly_score"]
        .quantile(PCTL)
        .rename("threshold_p99")
        .reset_index()
    )

    df_a = df_z.merge(thresholds, on="station_name", how="left")
    df_a["is_anomaly"] = df_a["anomaly_score"] >= df_a["threshold_p99"]

    # ---- Explanations
    df_a["top_features"] = df_a.apply(lambda r: top_features_row(r, core), axis=1)

    # ---- Save output
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    cols_to_save = [
        "station_name", "year", "month",
        "anomaly_score", "threshold_p99", "is_anomaly",
        "n_days_rows", "n_features_present", "n_features_used",
        "mean_coverage_core", "gate_reason",
        "top_features",
    ]
    cols_to_save = [c for c in cols_to_save if c in df_a.columns]

    df_a[cols_to_save].to_parquet(OUT_PATH, index=False)

    pct = df_a["is_anomaly"].mean() * 100
    print(f"[OK] anomalies: {pct:.2f}%")
    print(f"[OK] written: {OUT_PATH}")


if __name__ == "__main__":
    main()