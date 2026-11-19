"""Run bronze -> silver locally (Parquet under data/lake/) or on Databricks (Delta tables).

Usage: python scripts/run_pipeline.py [--only alerts,telegram,af,weather]
"""
import argparse
import sys
import time
from pathlib import Path

# repo root: --root on Databricks (serverless runs the script without __file__), else this file's parent
_root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else str(Path(__file__).resolve().parents[1])
sys.path.insert(0, str(Path(_root) / "src"))
from pipeline import bronze, gold, silver, validation  # noqa: E402
from pipeline.io import get_spark, read, write  # noqa: E402

STEPS = ["reference", "alerts", "telegram", "af", "weather", "gdelt", "context", "gold", "validate"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(STEPS))
    ap.add_argument("--root")
    steps = ap.parse_args().only.split(",")
    spark = get_spark()
    try:
        spark.sparkContext.setLogLevel("ERROR")
    except Exception:  # not available on serverless compute
        pass
    t0 = time.time()
    quarantine = []

    def log(msg):
        print(f"[{time.time() - t0:6.0f}s] {msg}", flush=True)

    if "reference" in steps:
        write(silver.dim_oblast(spark), "silver", "dim_oblast")
        write(silver.dim_ru_region(spark), "silver", "dim_ru_region")
        write(silver.dim_night(spark), "silver", "dim_night")
        log("reference tables")

    if "alerts" in steps:
        b = write(bronze.alerts(spark), "bronze", "alerts")
        good, q = silver.alerts(b, read(spark, "silver", "dim_oblast"))
        a = write(good, "silver", "alerts")
        write(q, "silver", "quarantine_alerts")
        iv = write(silver.alerts_oblast_intervals(a), "silver", "alerts_oblast_intervals")
        rd = write(silver.dim_raion(a), "silver", "dim_raion")
        riv = write(silver.alerts_raion_intervals(a, rd), "silver", "alerts_raion_intervals")
        write(silver.alerts_oblast_hourly(iv, riv, rd), "silver", "alerts_oblast_hourly")
        log("alerts")

    if "telegram" in steps:
        p = write(silver.tg_posts(write(bronze.tg_posts(spark), "bronze", "tg_posts")), "silver", "tg_posts")
        ev, q = silver.tg_events(write(bronze.llm_events(spark), "bronze", "llm_events"), p)
        ev = write(ev, "silver", "tg_events")
        write(q, "silver", "quarantine_tg_events")
        cp = write(silver.casualty_posts(ev, p), "silver", "casualty_posts")
        ci = write(silver.casualty_incidents(cp), "silver", "casualty_incidents")
        write(silver.casualty_daily(ci), "silver", "casualty_daily")
        write(silver.strikes_on_russia(ev), "silver", "strikes_on_russia")
        log("telegram")

    if "af" in steps:
        rx = write(bronze.af_regex(spark), "bronze", "af_regex")
        write(silver.af_nightly(rx, read(spark, "silver", "tg_events")), "silver", "af_nightly")
        log("air force nightly")

    if "weather" in steps:
        w = write(bronze.weather_hourly(spark), "bronze", "weather_hourly")
        write(silver.weather_night(w), "silver", "weather_night")
        log("weather")

    if "gdelt" in steps:
        g = write(silver.gdelt_events(write(bronze.gdelt_events(spark), "bronze", "gdelt_events")), "silver", "gdelt_events")
        write(silver.gdelt_daily(g), "silver", "gdelt_daily")
        write(silver.gdelt_oblast_daily(g), "silver", "gdelt_oblast_daily")
        log("gdelt")

    if "context" in steps:
        ev = read(spark, "silver", "tg_events")
        write(silver.holidays(spark), "silver", "holidays")
        write(silver.diplomacy_calendar(spark), "silver", "diplomacy_calendar")
        write(silver.diplomacy_daily(ev), "silver", "diplomacy_daily")
        write(silver.energy_events(ev), "silver", "energy_events")
        log("calendars, diplomacy, energy")

    if "gold" in steps:
        names = ["af_nightly", "alerts_oblast_hourly", "strikes_on_russia", "casualty_daily", "energy_events",
                 "diplomacy_daily", "gdelt_daily", "gdelt_oblast_daily", "dim_night", "holidays", "diplomacy_calendar",
                 "dim_oblast", "weather_night", "tg_events"]
        s = {n: read(spark, "silver", n) for n in names}
        nat = write(gold.national_day(spark, s), "gold", "national_day")
        write(gold.oblast_day(spark, s, nat), "gold", "oblast_day")
        log("gold")

    if "validate" in steps:
        res = validation.run(spark)
        write(spark.createDataFrame(res), "silver", "validation_results")
        failed = [r for r in res if not r["passed"]]
        for r in res:
            print(("PASS " if r["passed"] else "FAIL ") + f"{r['table']:28s} {r['check']:40s} {r['detail']}")
        log(f"validation: {len(res) - len(failed)}/{len(res)} passed")


if __name__ == "__main__":
    main()
