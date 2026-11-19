"""Gold: model-ready feature tables.

oblast_day   one row per (day, oblast) for oblasts with alert data
national_day one row per day

Leakage rule: anything derived from events (alerts, launches, strikes, casualties, news) enters only as a value from
previous days (lag >= 1). Weather, moon, weekday and holidays enter for the same day, because they are known or
forecast in advance. Targets are given both for the same day and for the next day (y_next_*).
Day = report_day (18:00-18:00 Kyiv), named after the morning it ends in.
"""
from pyspark.sql import Window
from pyspark.sql import functions as F

EXCLUDED_OBLASTS = ["UA44", "UA43", "UA85"]  # Luhansk, Crimea, Sevastopol: permanent alerts not in the data
START, END_ALERTS = "2022-03-15", "2026-09-06"


def _lags(df, part, cols, lags=(1, 2, 7), means=(7, 28)):
    w = Window.partitionBy(*part).orderBy("day") if part else Window.orderBy("day")
    for c in cols:
        for k in lags:
            df = df.withColumn(f"{c}_lag{k}", F.lag(c, k).over(w))
        for k in means:
            df = df.withColumn(f"{c}_mean{k}", F.avg(c).over(w.rowsBetween(-k, -1)))
    return df


def _days_since(df, flag_col, out_col, part=None):
    """Days since the last day where flag_col is true (strictly before today)."""
    w = (Window.partitionBy(*part) if part else Window).orderBy("day").rowsBetween(Window.unboundedPreceding, -1)
    last = F.max(F.when(F.col(flag_col), F.col("day"))).over(w)
    return df.withColumn(out_col, F.datediff("day", last))


def _days_until(df, flag_col, out_col):
    w = Window.orderBy("day").rowsBetween(1, Window.unboundedFollowing)
    nxt = F.min(F.when(F.col(flag_col), F.col("day"))).over(w)
    return df.withColumn(out_col, F.datediff(nxt, "day"))


def national_day(spark, s):
    """s: dict of silver DataFrames."""
    days = spark.sql(f"select explode(sequence(to_date('2022-02-24'), current_date())) as day")

    af = s["af_nightly"].select(F.col("night").alias("day"), "launched", "shot_down", "hit_locations",
                                F.col("quality").alias("af_quality"))
    alerts = (s["alerts_oblast_hourly"].where(~F.col("oblast_id").isin(EXCLUDED_OBLASTS))
              .groupBy(F.col("report_day").alias("day"))
              .agg((F.sum("alert_minutes_share") / 60 / 24).alias("alert_hours_share_avg"),
                   F.sum("alert_starts").alias("alert_starts_total")))
    strikes = (s["strikes_on_russia"].groupBy(F.col("event_day").alias("day"))
               .agg(F.count("*").alias("ua_strike_events"),
                    F.sum(F.when(F.col("target_type") == "oil_refinery_or_depot", 1).otherwise(0)).alias("ua_strike_oil"),
                    F.sum(F.when(F.col("target_type") == "airfield", 1).otherwise(0)).alias("ua_strike_airfield"),
                    F.sum(F.when(F.col("confidence") == "high", 1).otherwise(0)).alias("ua_strike_high_conf")))
    cas = (s["casualty_daily"].groupBy(F.col("event_day").alias("day"))
           .agg(F.sum("killed").alias("civ_killed"), F.sum("injured").alias("civ_injured")))
    energy = (s["energy_events"].groupBy(F.col("event_day").alias("day"))
              .agg(F.sum("energy_strike_posts").alias("energy_strike_posts"), F.sum("outage_posts").alias("outage_posts")))
    dip = s["diplomacy_daily"].withColumnRenamed("event_day", "day")
    gd = s["gdelt_daily"].withColumnRenamed("event_date", "day")
    gd = gd.select("day", *[c for c in gd.columns if c.endswith(("_events", "_tone", "_goldstein"))])

    df = days
    for t in [af, alerts, strikes, cas, energy, dip, gd]:
        df = df.join(t, "day", "left")
    count_cols = [c for c in df.columns if c.endswith(("_events", "_posts", "_oil", "_airfield", "_high_conf"))
                  or c in ("civ_killed", "civ_injured", "peace_talks_positive", "peace_talks_negative",
                           "threat_or_ultimatum", "sanctions", "aid_to_ukraine", "mentions_trump", "mentions_putin",
                           "mentions_zelensky", "alert_starts_total")]
    gdelt_cols = set(gd.columns) - {"day"}  # a missing GDELT file is unknown, not zero
    df = df.fillna(0, subset=[c for c in count_cols if c not in gdelt_cols])

    event_cols = [c for c in df.columns if c not in ("day", "af_quality")]
    df = _lags(df, None, event_cols, lags=(1, 2, 3, 7), means=(3, 7, 28))

    # calendar: moon, darkness, weekday, holidays, diplomacy events
    df = df.join(s["dim_night"].withColumnRenamed("night", "day"), "day", "left")
    hol = s["holidays"].groupBy(F.col("date").alias("day")).agg(
        F.max(F.when(F.col("country").isin("UA", "both"), 1).otherwise(0)).alias("holiday_ua"),
        F.max(F.when(F.col("country").isin("RU", "both"), 1).otherwise(0)).alias("holiday_ru"))
    df = df.join(hol, "day", "left").fillna(0, subset=["holiday_ua", "holiday_ru"])
    df = df.withColumn("is_holiday", (F.col("holiday_ua") + F.col("holiday_ru")) > 0)
    df = _days_until(df, "is_holiday", "days_to_holiday")
    cal = s["diplomacy_calendar"].groupBy(F.col("date").alias("day")).agg(
        F.lit(True).alias("dip_event"),
        F.max(F.col("type").isin("summit", "talks", "call", "visit").cast("int")).alias("dip_talks"),
        F.max(F.col("type").isin("ultimatum", "sanctions").cast("int")).alias("dip_pressure"),
        F.max((F.col("type") == "military_milestone").cast("int")).alias("military_milestone"))
    df = df.join(cal, "day", "left").fillna(False, subset=["dip_event"]).fillna(0, subset=["dip_talks", "dip_pressure", "military_milestone"])
    df = _days_since(df, "dip_event", "days_since_dip_event")
    df = _days_until(df, "dip_event", "days_to_dip_event")
    big = df.withColumn("big_attack", F.coalesce(F.col("launched") >= 300, F.lit(False)))
    df = _days_since(big, "big_attack", "days_since_big_attack")

    w = Window.orderBy("day")
    df = (df.withColumn("y_next_launched", F.lead("launched", 1).over(w))
            .withColumn("y_next_big_attack", F.lead(F.col("launched") >= 300, 1).over(w).cast("int"))
            .withColumn("y_next_alert_hours_share_avg", F.lead("alert_hours_share_avg", 1).over(w)))
    return df


def oblast_day(spark, s, nat):
    dims = s["dim_oblast"].where(~F.col("oblast_id").isin(EXCLUDED_OBLASTS)) \
                          .select("oblast_id", "lat", "lon", "frontline", F.col("occupation").alias("occupation"))
    days = spark.sql(f"select explode(sequence(to_date('{START}'), to_date('{END_ALERTS}'))) as day")
    grid = days.crossJoin(dims)

    h = s["alerts_oblast_hourly"].withColumn(
        "night_hour", F.hour(F.from_utc_timestamp("hour_utc", "Europe/Kyiv")).isin(*list(range(18, 24)), *list(range(0, 7))))
    alerts = (h.groupBy(F.col("report_day").alias("day"), "oblast_id")
              .agg((F.sum("alert_minutes_share") / 60).alias("alert_hours_share"),
                   (F.sum("alert_minutes_any") / 60).alias("alert_hours_any"),
                   (F.sum(F.when(F.col("night_hour"), F.col("alert_minutes_share"))) / 60).alias("night_alert_hours_share"),
                   F.sum("alert_starts").alias("alert_starts")))
    cas = s["casualty_daily"].select(F.col("event_day").alias("day"), "oblast_id",
                                     F.col("killed").alias("obl_killed"), F.col("injured").alias("obl_injured"))
    en = s["energy_events"].where(F.col("oblast_id").isNotNull()).select(
        F.col("event_day").alias("day"), "oblast_id", F.col("energy_strike_posts").alias("obl_energy_strike_posts"),
        F.col("outage_posts").alias("obl_outage_posts"))
    att = (s["tg_events"].where(F.col("event_type") == "russian_attack_on_ukraine")
           .withColumn("oblast_id", F.explode("ua_oblast_ids"))
           .groupBy(F.col("event_day").alias("day"), "oblast_id").agg(F.count("*").alias("obl_attack_posts")))
    go = s["gdelt_oblast_daily"].select(F.col("event_date").alias("day"), "oblast_id",
                                        F.col("conflict_events").alias("obl_gdelt_conflict"), F.col("tone").alias("obl_gdelt_tone"))
    w = s["weather_night"].withColumnRenamed("night", "day").drop("n_hours")

    df = grid
    for t in [alerts, cas, en, att, go]:
        df = df.join(t, ["day", "oblast_id"], "left")
    obl_cols = ["alert_hours_share", "alert_hours_any", "night_alert_hours_share", "alert_starts", "obl_killed",
                "obl_injured", "obl_energy_strike_posts", "obl_outage_posts", "obl_attack_posts", "obl_gdelt_conflict"]
    df = df.fillna(0, subset=obl_cols)
    df = _lags(df, ["oblast_id"], obl_cols, lags=(1, 2, 7), means=(7, 28))
    df = df.join(w, ["day", "oblast_id"], "left")

    # national context: only lagged columns and same-day calendar columns
    keep = [c for c in nat.columns if "_lag" in c or "_mean" in c] + [
        "moon_phase_day", "moon_illumination", "darkness_hours", "weekday", "iso_week", "holiday_ua", "holiday_ru",
        "days_to_holiday", "dip_event", "dip_talks", "dip_pressure", "military_milestone", "days_since_dip_event",
        "days_to_dip_event", "days_since_big_attack"]
    df = df.join(nat.select("day", *[F.col(c).alias(f"nat_{c}") for c in keep]), "day", "left")

    wo = Window.partitionBy("oblast_id").orderBy("day")
    return (df.withColumn("y_next_alert_hours_share", F.lead("alert_hours_share", 1).over(wo))
              .withColumn("y_next_night_alert_hours_share", F.lead("night_alert_hours_share", 1).over(wo)))
