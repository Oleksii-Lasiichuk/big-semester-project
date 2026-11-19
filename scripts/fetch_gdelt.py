"""Download GDELT 1.0 daily event exports and keep events involving Ukraine or Russia.

Each daily file (~8 MB zipped, ~200k events) is read in memory and filtered: an event is kept when an actor's
country is UKR/RUS or the event location is in Ukraine/Russia (FIPS UP/RS). Output: one gzip CSV per day with
the original 58 columns, data/raw/gdelt/YYYYMMDD.csv.gz. Days already downloaded are skipped.

Usage: python scripts/fetch_gdelt.py --start 2022-02-24 --end 2026-11-18 --workers 4
"""
import argparse
import csv
import gzip
import io
import sys
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "gdelt"
URL = "https://data.gdeltproject.org/events/{d}.export.CSV.zip"
# column positions in the 58-column GDELT 1.0 event export
A1_COUNTRY, A2_COUNTRY, GEO_COUNTRY = 7, 17, 51
COUNTRIES, FIPS = {"UKR", "RUS"}, {"UP", "RS"}
csv.field_size_limit(10_000_000)


def fetch_day(d):
    out = OUT / f"{d}.csv.gz"
    if out.exists():
        return d, -1, 0
    for attempt in range(5):
        try:
            with urllib.request.urlopen(URL.format(d=d), timeout=120) as r:
                raw = r.read()
            break
        except Exception as e:
            if "404" in str(e):
                return d, 0, 0
            time.sleep(10 * (attempt + 1))
    else:
        print(f"{d}: failed", file=sys.stderr)
        return d, 0, 0
    total = kept = 0
    tmp = out.with_suffix(".tmp")
    with zipfile.ZipFile(io.BytesIO(raw)) as z, gzip.open(tmp, "wt", encoding="utf-8", newline="") as g:
        w = csv.writer(g, delimiter="\t")
        with z.open(z.namelist()[0]) as f:
            for row in csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"), delimiter="\t"):
                total += 1
                if len(row) < 58:
                    continue
                if row[A1_COUNTRY] in COUNTRIES or row[A2_COUNTRY] in COUNTRIES or row[GEO_COUNTRY] in FIPS:
                    w.writerow(row)
                    kept += 1
    tmp.rename(out)
    return d, total, kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2022-02-24")
    ap.add_argument("--end", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    d0, d1 = date.fromisoformat(a.start), date.fromisoformat(a.end)
    days = [(d0 + timedelta(i)).strftime("%Y%m%d") for i in range((d1 - d0).days + 1)]
    t0, n = time.time(), 0
    with ThreadPoolExecutor(a.workers) as ex:
        for d, total, kept in ex.map(fetch_day, days):
            n += 1
            if total > 0 and n % 25 == 0:
                print(f"{n}/{len(days)} {d}: kept {kept}/{total} ({time.time() - t0:.0f}s)", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
