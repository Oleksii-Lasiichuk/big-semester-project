import sys
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pipeline import silver  # noqa: E402
from pipeline.io import get_spark  # noqa: E402


@pytest.fixture(scope="session")
def spark():
    s = get_spark()
    s.sparkContext.setLogLevel("ERROR")
    return s


def ts(s):
    return datetime.fromisoformat(s)


def test_report_day_window(spark):
    # 18:00 Kyiv (15:00 UTC in summer) starts the next report day; 17:59 does not
    df = spark.createDataFrame([(ts("2025-07-18 14:59:00+00:00"),), (ts("2025-07-18 15:00:00+00:00"),)], ["t"])
    got = [r[0] for r in df.select(silver.report_day("t")).collect()]
    assert got == [date(2025, 7, 18), date(2025, 7, 19)]


def test_merge_intervals_overlap_and_gap(spark):
    rows = [("A", "oblast", ts("2025-01-01 10:00:00"), ts("2025-01-01 11:00:00")),
            ("A", "raion", ts("2025-01-01 10:30:00"), ts("2025-01-01 12:00:00")),
            ("A", "oblast", ts("2025-01-01 13:00:00"), ts("2025-01-01 13:30:00"))]
    df = spark.createDataFrame(rows, ["oblast_id", "level", "started_utc", "finished_utc"])
    got = sorted((r.started_utc, r.finished_utc) for r in silver.merge_intervals(df, ["oblast_id"]).collect())
    assert got == [(ts("2025-01-01 10:00:00"), ts("2025-01-01 12:00:00")),
                   (ts("2025-01-01 13:00:00"), ts("2025-01-01 13:30:00"))]


def test_hourly_minutes_split_across_hours(spark):
    df = spark.createDataFrame([("A", ts("2025-01-01 10:45:00"), ts("2025-01-01 12:15:00"))],
                               ["oblast_id", "started_utc", "finished_utc"])
    got = {r.hour_utc.hour: r.minutes for r in silver._hourly(df, ["oblast_id"]).collect()}
    assert got == {10: 15, 11: 60, 12: 15}


def test_strike_reclassification(spark):
    from pyspark.sql import functions as F
    llm = spark.createDataFrame(
        [("ch", 1, "ukrainian_strike_on_russia", ["Таганрог"]),
         ("ch", 2, "ukrainian_strike_on_russia", ["Луганськ"]),
         ("ch", 3, "ukrainian_strike_on_russia", ["Іркутськ"]),
         ("ch", 4, "ukrainian_strike_on_russia", [])],
        "channel string, post_id long, event_type string, ru_regions array<string>")
    for c, t in [("event_date", "string"), ("ua_oblasts", "array<string>"), ("weapons", "array<string>"),
                 ("launched", "long"), ("shot_down", "long"), ("killed", "long"), ("injured", "long"),
                 ("children_killed", "long"), ("target_type", "string"), ("is_count_update", "boolean"),
                 ("actors", "array<string>"), ("diplomacy_signal", "string"), ("summary_en", "string"),
                 ("relevant", "boolean"), ("url", "string"), ("model", "string")]:
        llm = llm.withColumn(c, F.lit(None).cast(t))
    llm = llm.withColumn("ua_oblasts", F.array().cast("array<string>"))
    posts = spark.createDataFrame([("ch", i, ts("2025-05-01 08:00:00"), date(2025, 5, 1), date(2025, 5, 1)) for i in range(1, 5)],
                                  "channel string, post_id long, posted_utc timestamp, posted_local_date date, report_day date")
    ev, _ = silver.tg_events(llm, posts)
    got = {r.post_id: r.event_type for r in ev.collect()}
    assert got == {1: "ukrainian_strike_on_russia", 2: "strike_on_occupied_territory",
                   3: "ukrainian_strike_on_russia", 4: "strike_unlocated"}


def test_incident_linking_repeated_toll():
    import pandas as pd
    t = pd.Timestamp
    pdf = pd.DataFrame([
        ("a", 1, "UA23", t("2026-11-02 10:00"), date(2026, 11, 2), 20.0, False),
        ("a", 2, "UA23", t("2026-11-03 10:00"), date(2026, 11, 3), 53.0, True),
        ("b", 3, "UA23", t("2026-11-08 10:00"), date(2026, 11, 8), 55.0, True),
        ("b", 4, "UA23", t("2026-11-16 10:00"), date(2026, 11, 16), 55.0, False),
        ("a", 5, "UA23", t("2026-12-20 10:00"), date(2026, 12, 20), 3.0, False),
    ], columns=["channel", "post_id", "oblast_id", "posted_utc", "event_day", "killed_civ", "is_update"])
    out = silver._link_incidents(pdf)
    assert out.incident_id.nunique() == 2
    assert out.incident_id.iloc[0] == out.incident_id.iloc[3] != out.incident_id.iloc[4]
