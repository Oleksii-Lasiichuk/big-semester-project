"""Silver: cleaned, typed, deduplicated tables. Rejected rows go to a quarantine table with the rule that rejected them.

Time conventions
- All timestamps are stored in UTC.
- report_day: the 24 h window from 18:00 to 18:00 Kyiv time, named after the morning it ends in.
  It matches the Air Force reporting window ("у ніч на 19 листопада" = 18:00 18 Nov -> 08:00 19 Nov -> report_day 19 Nov).
"""
from datetime import date, datetime, timedelta

from pyspark.sql import Window
from pyspark.sql import functions as F

from .reference import OBLASTS, OBLAST_COLUMNS, OCCUPIED_PATTERNS, RU_REGIONS

KYIV = "Europe/Kyiv"
WAR_START = "2022-02-24"
MAX_ALERT_HOURS = 7 * 24
CAPS = {"killed": 200, "injured": 500, "children_killed": 100, "launched": 1500, "shot_down": 1500}


def report_day(ts_utc):
    return F.to_date(F.from_utc_timestamp(ts_utc, KYIV) + F.expr("INTERVAL 6 HOURS"))


def quarantine_rows(df, table, rule_col, key_cols):
    return (df.where(F.col(rule_col).isNotNull())
            .select(F.lit(table).alias("table"), F.col(rule_col).alias("rule"),
                    F.concat_ws("|", *[F.col(c).cast("string") for c in key_cols]).alias("record_key"),
                    F.to_json(F.struct(*df.columns)).alias("payload")))


# ------------------------------------------------------------------ reference
def dim_oblast(spark):
    return spark.createDataFrame(OBLASTS, OBLAST_COLUMNS)


def dim_ru_region(spark):
    return spark.createDataFrame(RU_REGIONS, ["region_uk", "pattern"])


# ------------------------------------------------------------------ alerts
def alerts(bronze, dim_obl):
    fmt = "yyyy-MM-dd HH:mm:ssXXX"
    a = (bronze.select(F.col("oblast").alias("name_en"), "raion", "hromada", "level",
                       F.to_timestamp("started_at", fmt).alias("started_utc"),
                       F.to_timestamp("finished_at", fmt).alias("finished_utc"))
         .join(dim_obl.select("oblast_id", "name_en"), "name_en", "left")
         .withColumn("duration_min", (F.unix_timestamp("finished_utc") - F.unix_timestamp("started_utc")) / 60))
    a = a.withColumn("rule", F.when(F.col("started_utc").isNull() | F.col("finished_utc").isNull(), "unparseable_time")
                     .when(F.col("oblast_id").isNull(), "unknown_oblast")
                     .when(F.col("duration_min") <= 0, "non_positive_duration")
                     .when(F.col("duration_min") > MAX_ALERT_HOURS * 60, "duration_gt_7d"))
    key = ["name_en", "raion", "hromada", "level", "started_utc", "finished_utc"]
    q = quarantine_rows(a, "alerts", "rule", key)
    good = (a.where(F.col("rule").isNull()).drop("rule").dropDuplicates(key)
            .withColumn("alert_id", F.sha2(F.concat_ws("|", *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in key]), 256))
            .withColumn("report_day", report_day("started_utc")))
    return good, q


def merge_intervals(df, keys):
    """Merge overlapping or touching [started_utc, finished_utc] intervals within each key."""
    w = Window.partitionBy(*keys).orderBy("started_utc", "finished_utc")
    prev_end = F.max("finished_utc").over(w.rowsBetween(Window.unboundedPreceding, -1))
    g = (df.withColumn("new", F.when(prev_end.isNull() | (F.col("started_utc") > prev_end), 1).otherwise(0))
         .withColumn("grp", F.sum("new").over(w.rowsBetween(Window.unboundedPreceding, 0))))
    return (g.groupBy(*keys, "grp")
            .agg(F.min("started_utc").alias("started_utc"), F.max("finished_utc").alias("finished_utc"),
                 F.count("*").alias("n_alerts"), F.array_sort(F.collect_set("level")).alias("levels"))
            .drop("grp"))


def alerts_oblast_intervals(alerts_df):
    """Any-part measure: an oblast is under alert while any part of it (oblast, raion or hromada alert) is."""
    return merge_intervals(alerts_df, ["oblast_id"])


def dim_raion(alerts_df):
    """Raions per oblast as they appear in the alerts data; Kyiv City is one unit."""
    r = alerts_df.where(F.col("raion").isNotNull()).select("oblast_id", "raion").distinct()
    kyiv = alerts_df.where(F.col("oblast_id") == "UA80").select("oblast_id", F.lit("Kyiv City").alias("raion")).distinct()
    return r.unionByName(kyiv).distinct()


def alerts_raion_intervals(alerts_df, raions):
    """Per-raion intervals: an oblast-wide alert applies to every raion of the oblast,
    raion and hromada alerts apply to their raion."""
    obl = (alerts_df.where(F.col("level") == "oblast").drop("raion")
           .join(raions, "oblast_id", "inner"))
    local = alerts_df.where(F.col("level") != "oblast")
    return merge_intervals(obl.unionByName(local.select(*obl.columns)), ["oblast_id", "raion"])


def _hourly(intervals, keys):
    hours = F.sequence(F.date_trunc("hour", "started_utc"),
                       F.date_trunc("hour", F.col("finished_utc") - F.expr("INTERVAL 1 SECOND")),
                       F.expr("INTERVAL 1 HOUR"))
    e = intervals.withColumn("hour_utc", F.explode(hours))
    overlap = (F.unix_timestamp(F.least("finished_utc", F.col("hour_utc") + F.expr("INTERVAL 1 HOUR")))
               - F.unix_timestamp(F.greatest("started_utc", "hour_utc"))) / 60
    starts = F.when(F.date_trunc("hour", "started_utc") == F.col("hour_utc"), 1).otherwise(0)
    return e.groupBy(*keys, "hour_utc").agg(F.sum(overlap).alias("minutes"), F.sum(starts).alias("starts"))


def alerts_oblast_hourly(oblast_intervals, raion_intervals, raions):
    """Per oblast and UTC hour:
    - alert_minutes_any: minutes when any part of the oblast was under alert (0-60);
    - alert_minutes_share: mean minutes under alert across the oblast's raions (0-60), i.e. population-free
      "how much of the oblast" measure that is comparable before and after the December 2025 switch to raion alerts."""
    anyp = _hourly(oblast_intervals, ["oblast_id"]).withColumnRenamed("minutes", "alert_minutes_any") \
                                                   .withColumnRenamed("starts", "alert_starts")
    n = raions.groupBy("oblast_id").agg(F.count("*").alias("n_raions"))
    share = (_hourly(raion_intervals, ["oblast_id", "raion"]).groupBy("oblast_id", "hour_utc")
             .agg(F.sum("minutes").alias("raion_minutes"), F.count("*").alias("raions_alerted"))
             .join(n, "oblast_id")
             .withColumn("alert_minutes_share", F.col("raion_minutes") / F.col("n_raions"))
             .select("oblast_id", "hour_utc", "alert_minutes_share", "raions_alerted", "n_raions"))
    return (anyp.join(share, ["oblast_id", "hour_utc"], "left")
            .withColumn("alert_minutes_share", F.coalesce("alert_minutes_share", F.lit(0.0)))
            .withColumn("report_day", report_day("hour_utc")))


# ------------------------------------------------------------------ telegram
def tg_posts(bronze):
    return (bronze.dropDuplicates(["channel", "post_id"])
            .withColumn("posted_utc", F.to_timestamp("datetime"))
            .withColumn("posted_local_date", F.to_date(F.from_utc_timestamp("posted_utc", KYIV)))
            .withColumn("report_day", report_day("posted_utc"))
            .withColumn("text_len", F.length("text"))
            .select("channel", "post_id", "posted_utc", "posted_local_date", "report_day", "text", "text_len", "views", "url"))


def _oblast_map():
    pairs = []
    for row in OBLASTS:
        pairs += [F.lit(row[1]), F.lit(row[0])]
    return F.create_map(*pairs)


def tg_events(bronze_llm, posts):
    """LLM output joined with posts, validated and reclassified."""
    cols = bronze_llm.columns
    llm = bronze_llm.withColumn("error", F.col("error") if "error" in cols else F.lit(None).cast("string"))
    e = llm.join(posts.select("channel", "post_id", "posted_utc", "posted_local_date", "report_day"),
                 ["channel", "post_id"], "inner")

    # event day: the LLM date if plausible (0-7 days before publication), otherwise the publication date
    ed = F.to_date("event_date")
    ok_date = ed.isNotNull() & (ed <= F.col("posted_local_date")) & (ed >= F.date_sub("posted_local_date", 7)) & (ed >= F.lit(WAR_START))
    e = e.withColumn("event_day", F.when(ok_date, ed).otherwise(F.col("posted_local_date"))) \
         .withColumn("event_date_imputed", ~ok_date)

    # out-of-range counts -> null + quarantine record
    rules = None
    for c, cap in CAPS.items():
        bad = F.col(c).isNotNull() & ((F.col(c) < 0) | (F.col(c) > cap))
        rules = F.when(bad, F.lit(f"{c}_out_of_range")) if rules is None else rules.when(bad, F.lit(f"{c}_out_of_range"))
        e = e.withColumn(f"{c}_bad", bad)
    e = e.withColumn("rule", F.when(F.col("error").isNotNull(), F.lit("llm_error")).otherwise(rules))
    q = quarantine_rows(e.drop(*[f"{c}_bad" for c in CAPS]), "tg_events", "rule", ["channel", "post_id"])
    for c in CAPS:
        e = e.withColumn(c, F.when(F.col(f"{c}_bad"), None).otherwise(F.col(c))).drop(f"{c}_bad")
    e = e.where(F.col("error").isNull()).drop("rule")
    e = e.withColumn("shot_down", F.when(F.col("shot_down") > F.col("launched"), None).otherwise(F.col("shot_down")))

    # strikes on Russia: keep only posts whose places map to a Russian region
    ru_text = F.lower(F.concat_ws(" | ", "ru_regions"))
    regions = F.filter(F.array(*[F.when(ru_text.rlike("(?iU)" + pat), F.lit(name)) for name, pat in RU_REGIONS]),
                       lambda x: x.isNotNull())
    e = e.withColumn("ru_regions_mapped", F.when(F.col("event_type") == "ukrainian_strike_on_russia", regions)
                     .otherwise(F.array().cast("array<string>")))
    occupied = ru_text.rlike("(?iU)" + OCCUPIED_PATTERNS)
    e = e.withColumn("event_type_llm", F.col("event_type")).withColumn(
        "event_type",
        F.when(F.col("event_type") != "ukrainian_strike_on_russia", F.col("event_type"))
         .when(F.size("ru_regions_mapped") > 0, F.lit("ukrainian_strike_on_russia"))
         .when(occupied, F.lit("strike_on_occupied_territory"))
         .otherwise(F.lit("strike_unlocated")))

    # oblast names -> ids
    m = _oblast_map()
    e = e.withColumn("ua_oblast_ids", F.array_distinct(F.filter(F.transform("ua_oblasts", lambda x: F.element_at(m, x)),
                                                                lambda x: x.isNotNull())))

    # civilian casualties only from Russian attacks with a named oblast (removes military losses, frontline reports)
    civ = F.col("event_type").isin("russian_attack_on_ukraine", "casualties_update") & (F.size("ua_oblast_ids") > 0)
    for c in ["killed", "injured", "children_killed"]:
        e = e.withColumn(f"{c}_civ", F.when(civ, F.col(c)))

    keep = ["channel", "post_id", "url", "posted_utc", "report_day", "event_day", "event_date_imputed", "relevant",
            "event_type", "event_type_llm", "ua_oblast_ids", "ru_regions", "ru_regions_mapped", "weapons",
            "launched", "shot_down", "killed_civ", "injured_civ", "children_killed_civ", "target_type",
            "is_count_update", "actors", "diplomacy_signal", "summary_en", "model"]
    return e.select(*keep), q


AGGREGATE_TEXT = r"(?iU)(за (минул\w+ )?(тиждень|місяць|рік)|з початку (року|місяця|тижня|війни|вторгнення)|протягом (тижня|місяця)|загалом з|за \d+ (днів|дні|тижн))"
UPDATE_TEXT = r"(?iU)(зросл|збільшил|наразі|вже\b|досі|відомо про|кількість (загиблих|жертв|постраждалих)|число (загиблих|жертв)|оновлен|тіла|з-під завал|рятувальн)"
LINK_DAYS = 14


def _link_incidents(pdf):
    """Within one oblast, ordered by time: a post joins the latest open incident if it is within LINK_DAYS
    and either says it is an update or repeats/raises that incident's toll; otherwise it opens a new incident."""
    import pandas as pd
    pdf = pdf.sort_values("posted_utc")
    inc_ids, incidents = [], []  # incident: dict(id, start, last, killed)
    for r in pdf.itertuples():
        k = r.killed_civ if pd.notna(r.killed_civ) else None
        joined = None
        for inc in reversed(incidents):
            if (r.posted_utc - inc["last"]).days > LINK_DAYS:
                break
            same_toll = k is not None and inc["killed"] and inc["killed"] <= k <= inc["killed"] * 2 + 10
            if (r.is_update and (k is None or same_toll or (r.event_day - inc["day"]).days <= 1)) or \
               (same_toll and k >= 5 and k == inc["killed"]):
                joined = inc
                break
        if joined is None:
            joined = {"id": f"{r.oblast_id}-{r.posted_utc:%Y%m%d%H%M}-{r.post_id}", "day": r.event_day,
                      "last": r.posted_utc, "killed": k or 0}
            incidents.append(joined)
        joined["last"] = r.posted_utc
        joined["killed"] = max(joined["killed"], k or 0)
        inc_ids.append(joined["id"])
    pdf["incident_id"] = inc_ids
    return pdf[["channel", "post_id", "incident_id"]]


def casualty_posts(events, posts):
    """Posts with civilian casualties in exactly one oblast, linked into incidents.
    Excludes cumulative reports (weekly, monthly, since-start totals)."""
    c = (events.where((F.col("killed_civ").isNotNull() | F.col("injured_civ").isNotNull()) & (F.size("ua_oblast_ids") == 1))
         .join(posts.select("channel", "post_id", "text"), ["channel", "post_id"])
         .withColumn("oblast_id", F.col("ua_oblast_ids")[0])
         .withColumn("is_aggregate", F.col("text").rlike(AGGREGATE_TEXT))
         .withColumn("is_update", F.coalesce("is_count_update", F.lit(False)) | F.col("text").rlike(UPDATE_TEXT)))
    single = c.where(~F.col("is_aggregate"))
    links = (single.select("channel", "post_id", "oblast_id", "posted_utc", "event_day", "killed_civ", "is_update")
             .groupBy("oblast_id")
             .applyInPandas(_link_incidents, "channel string, post_id long, incident_id string"))
    return (c.join(links, ["channel", "post_id"], "left")
            .select("channel", "post_id", "url", "posted_utc", "event_day", "oblast_id", "killed_civ", "injured_civ",
                    "children_killed_civ", "is_aggregate", "is_update", "incident_id"))


def casualty_incidents(cas_posts):
    """One row per incident: day of the first report, final (maximum) reported toll."""
    return (cas_posts.where(F.col("incident_id").isNotNull())
            .groupBy("incident_id", "oblast_id")
            .agg(F.min("event_day").alias("event_day"), F.max("event_day").alias("last_report_day"),
                 F.max("killed_civ").alias("killed"), F.max("injured_civ").alias("injured"),
                 F.max("children_killed_civ").alias("children_killed"),
                 F.count("*").alias("n_posts"), F.countDistinct("channel").alias("n_channels"),
                 F.collect_list("url").alias("post_urls")))


def casualty_daily(incidents):
    """Civilian casualties per oblast and day (sum of incidents first reported that day)."""
    return (incidents.groupBy("event_day", "oblast_id")
            .agg(F.sum("killed").alias("killed"), F.sum("injured").alias("injured"),
                 F.count("*").alias("n_incidents")))


def strikes_on_russia(events):
    s = events.where(F.col("event_type") == "ukrainian_strike_on_russia") \
              .withColumn("region_uk", F.explode("ru_regions_mapped"))
    return (s.groupBy("event_day", "region_uk", "target_type")
            .agg(F.count("*").alias("n_posts"), F.countDistinct("channel").alias("n_channels"),
                 F.array_sort(F.collect_set("channel")).alias("channels"),
                 F.first("summary_en", ignorenulls=True).alias("summary_en"),
                 F.collect_list("url").alias("post_urls"))
            .withColumn("confidence", F.when(F.col("n_channels") >= 2, "high").otherwise("low")))


# ------------------------------------------------------------------ Air Force nightly totals
def af_nightly(af_regex_bronze, events):
    rx = (af_regex_bronze
          .withColumn("night", F.to_date("night_of"))
          .withColumn("launched_rx", F.coalesce(F.col("launched_total"),
                                                F.when(F.col("launched_drones").isNotNull() | F.col("launched_missiles").isNotNull(),
                                                       F.coalesce("launched_drones", F.lit(0)) + F.coalesce("launched_missiles", F.lit(0)))))
          .groupBy("night")
          .agg(F.max("launched_rx").alias("launched_rx"), F.max("launched_drones").alias("launched_drones"),
               F.max("launched_missiles").alias("launched_missiles"), F.max("shot_down_total").alias("shot_down_rx"),
               F.max("hit_locations").alias("hit_locations"), F.first("launch_origins", ignorenulls=True).alias("launch_origins")))
    llm = (events.where((F.col("channel") == "kpszsu") & F.col("event_type").isin("air_defense_summary", "russian_attack_on_ukraine")
                        & (F.col("launched").isNotNull() | F.col("shot_down").isNotNull()))
           .groupBy(F.col("event_day").alias("night"))
           .agg(F.max("launched").alias("launched_llm"), F.max("shot_down").alias("shot_down_llm")))
    j = (rx.join(llm, "night", "full")
         .withColumn("rx_llm_rel_diff", F.abs(F.col("launched_rx") - F.col("launched_llm")) / F.col("launched_rx"))
         .withColumn("conflict", F.coalesce(F.col("rx_llm_rel_diff") > 0.1, F.lit(False))))
    # regex is exact when it agrees; on conflict the LLM reading of the whole post is used (regex tends to double-count)
    return (j.withColumn("launched", F.when(F.col("conflict"), F.col("launched_llm")).otherwise(F.coalesce("launched_rx", "launched_llm")))
            .withColumn("shot_down", F.when(F.col("conflict") & F.col("shot_down_llm").isNotNull(), F.col("shot_down_llm"))
                        .otherwise(F.coalesce("shot_down_rx", "shot_down_llm")))
            .withColumn("source", F.when(F.col("conflict"), "llm_conflict").when(F.col("launched_rx").isNotNull(), "regex")
                        .when(F.col("launched_llm").isNotNull(), "llm").otherwise("partial"))
            .withColumn("flag_shot_gt_launched", F.coalesce(F.col("shot_down") > F.col("launched"), F.lit(False)))
            # 2022 summaries often report cumulative or daytime kills, not one night: lower confidence
            .withColumn("quality", F.when(F.col("flag_shot_gt_launched") | (F.year("night") == 2022), "low").otherwise("ok"))
            .where(F.col("night") >= F.lit(WAR_START)))


# ------------------------------------------------------------------ weather and calendar
def weather_night(bronze_w):
    """Night weather per oblast: 18:00-06:59 Kyiv time, assigned to the report_day of that night."""
    w = (bronze_w.withColumn("ts", F.to_timestamp("time_utc", "yyyy-MM-dd'T'HH:mm"))
         .withColumn("local_hour", F.hour(F.from_utc_timestamp("ts", KYIV)))
         .where((F.col("local_hour") >= 18) | (F.col("local_hour") <= 6))
         .withColumn("night", report_day("ts")))
    return (w.groupBy("oblast_id", "night")
            .agg(F.count("*").alias("n_hours"),
                 F.round(F.avg("cloud_cover"), 1).alias("cloud_cover_mean"),
                 F.round(F.avg("cloud_cover_low"), 1).alias("cloud_low_mean"),
                 F.round(F.sum("precipitation"), 2).alias("precip_mm"),
                 F.round(F.sum("snowfall"), 2).alias("snowfall_cm"),
                 F.round(F.avg("wind_speed_10m"), 1).alias("wind_mean_kmh"),
                 F.round(F.max("wind_gusts_10m"), 1).alias("gust_max_kmh"),
                 F.round(F.avg("temperature_2m"), 1).alias("temp_mean_c"),
                 F.round(F.avg("relative_humidity_2m"), 1).alias("humidity_mean")))


def dim_night(spark, start=date(2022, 2, 24), end=None):
    """Calendar of nights: moon illumination at local midnight and darkness length in Kyiv."""
    from astral import LocationInfo, moon
    from astral.sun import sun
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(KYIV)
    kyiv = LocationInfo("Kyiv", "Ukraine", KYIV, 50.45, 30.52)
    end = end or date.today()
    rows, d = [], start
    while d <= end:
        prev = d - timedelta(days=1)
        s_prev, s_now = sun(kyiv.observer, prev, tzinfo=tz), sun(kyiv.observer, d, tzinfo=tz)
        dark_h = (s_now["sunrise"] - s_prev["sunset"]).total_seconds() / 3600
        ph = moon.phase(datetime(d.year, d.month, d.day, tzinfo=tz))  # 0 new .. 14 full .. 28
        illum = round((1 - __import__("math").cos(2 * __import__("math").pi * ph / 29.53)) / 2, 3)
        rows.append((d, round(ph, 2), illum, round(dark_h, 2), d.weekday(), d.isocalendar()[1]))
        d += timedelta(days=1)
    return spark.createDataFrame(rows, ["night", "moon_phase_day", "moon_illumination", "darkness_hours", "weekday", "iso_week"])
