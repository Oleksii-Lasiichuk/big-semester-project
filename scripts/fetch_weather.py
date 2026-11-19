"""Download hourly historical weather (Open-Meteo archive, ERA5) for every oblast centre.

Output: data/raw/weather/<oblast_id>.json (raw API response, times in UTC).
Usage: python scripts/fetch_weather.py --start 2022-02-20 --end 2026-11-15
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pipeline.reference import OBLASTS  # noqa: E402

VARS = ["temperature_2m", "relative_humidity_2m", "precipitation", "snowfall", "cloud_cover", "cloud_cover_low",
        "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"]
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "weather"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2022-02-20")
    ap.add_argument("--end", required=True)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for oid, name, _, centre, lat, lon, *_ in OBLASTS:
        path = OUT / f"{oid}.json"
        if path.exists():
            continue
        url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
               f"&start_date={a.start}&end_date={a.end}&hourly={','.join(VARS)}&timezone=UTC")
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    data = json.load(r)
                break
            except Exception as e:
                print(f"{oid}: {e!r}, retrying", file=sys.stderr)
                time.sleep(30 * (attempt + 1))
        else:
            raise SystemExit(f"failed: {oid}")
        data["oblast_id"], data["centre"] = oid, centre
        path.write_text(json.dumps(data))
        print(f"{oid} {centre}: {len(data['hourly']['time'])} hours")
        time.sleep(3)


if __name__ == "__main__":
    main()
