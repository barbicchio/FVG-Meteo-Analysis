from pathlib import Path
import pandas as pd

from src.processing.load_raw import load_all_raw_records
from src.processing.validate import record_to_daily_observation


OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    rows = []

    for raw in load_all_raw_records():
        obs = record_to_daily_observation(raw)
        if obs is not None:
            rows.append(obs.model_dump())

    df = pd.DataFrame(rows)

    out_path = OUT_DIR / "daily.parquet"
    df.to_parquet(out_path, index=False)

    print(f"[OK] Written {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()