from pathlib import Path
import json


RAW_JSON_DIR = Path("data/raw/arpa")


def load_all_raw_records():
    for path in RAW_JSON_DIR.glob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            station_data = json.load(f)

        # station_data: { "1999": [ {...}, {...} ], ... }
        for year_str, records in station_data.items():
            if not isinstance(records, list):
                continue

            for rec in records:
                yield rec