"""Silver validation: reconciliation, keys, ranges, reference integrity. Each check returns one result row."""
from pyspark.sql import functions as F

from .io import read


def _res(table, check, passed, detail):
    return {"table": table, "check": check, "passed": bool(passed), "detail": str(detail)}


def _unique(df, table, keys):
    dup = df.groupBy(*keys).count().where("count > 1").count()
    return _res(table, f"unique({','.join(keys)})", dup == 0, f"{dup} duplicate keys")


def _not_null(df, table, cols):
    out = []
    for c in cols:
        n = df.where(F.col(c).isNull()).count()
        out.append(_res(table, f"not_null({c})", n == 0, f"{n} nulls"))
    return out


def run(spark):
    r = []
    t = lambda layer, name: read(spark, layer, name)  # noqa: E731

    # alerts: bronze = silver + quarantine + exact duplicates
    b, s, q = t("bronze", "alerts"), t("silver", "alerts"), t("silver", "quarantine_alerts")
    nb, ns, nq = b.count(), s.count(), q.count()
    r.append(_res("alerts", "bronze = silver + quarantine + duplicates", nb >= ns + nq,
                  f"bronze {nb}, silver {ns}, quarantine {nq}, duplicates removed {nb - ns - nq}"))
    r.append(_unique(s, "alerts", ["alert_id"]))
    r += _not_null(s, "alerts", ["oblast_id", "started_utc", "finished_utc"])
    h = t("silver", "alerts_oblast_hourly")
    over = h.where("alert_minutes_any > 60.001 or alert_minutes_any <= 0").count()
    r.append(_res("alerts_oblast_hourly", "0 < alert_minutes_any <= 60", over == 0, f"{over} rows outside"))
    sh = h.where("alert_minutes_share > alert_minutes_any + 0.001 or alert_minutes_share < 0").count()
    r.append(_res("alerts_oblast_hourly", "0 <= share <= any", sh == 0, f"{sh} rows outside"))
    r.append(_unique(h, "alerts_oblast_hourly", ["oblast_id", "hour_utc"]))
    tot_iv = t("silver", "alerts_oblast_intervals").select(
        F.sum(F.unix_timestamp("finished_utc") - F.unix_timestamp("started_utc")) / 60).first()[0]
    tot_h = h.select(F.sum("alert_minutes_any")).first()[0]
    r.append(_res("alerts_oblast_hourly", "minutes reconcile with intervals", abs(tot_iv - tot_h) < 1,
                  f"intervals {tot_iv:,.0f} min, hourly {tot_h:,.0f} min"))

    # telegram
    p, ev = t("silver", "tg_posts"), t("silver", "tg_events")
    r.append(_unique(p, "tg_posts", ["channel", "post_id"]))
    r.append(_unique(ev, "tg_events", ["channel", "post_id"]))
    llm, qe = t("bronze", "llm_events"), t("silver", "quarantine_tg_events")
    n_err = qe.where("rule = 'llm_error'").count()
    r.append(_res("tg_events", "bronze llm = silver + llm errors", llm.count() == ev.count() + n_err,
                  f"bronze {llm.count()}, silver {ev.count()}, errors {n_err}"))
    orphan = ev.join(p, ["channel", "post_id"], "left_anti").count()
    r.append(_res("tg_events", "every event has a post", orphan == 0, f"{orphan} orphans"))
    dim = t("silver", "dim_oblast").select("oblast_id")
    bad_obl = ev.select(F.explode("ua_oblast_ids").alias("oblast_id")).join(dim, "oblast_id", "left_anti").count()
    r.append(_res("tg_events", "oblast ids exist in dim_oblast", bad_obl == 0, f"{bad_obl} unknown"))
    mil = ev.where("killed_civ is not null and event_type not in ('russian_attack_on_ukraine','casualties_update')").count()
    r.append(_res("tg_events", "civilian counts only for Russian attacks", mil == 0, f"{mil} rows"))
    future = ev.where("event_day > to_date(posted_utc) + 1").count()
    r.append(_res("tg_events", "event_day not after publication", future == 0, f"{future} rows"))
    cp, ci = t("silver", "casualty_posts"), t("silver", "casualty_incidents")
    unlinked = cp.where("not is_aggregate and incident_id is null").count()
    r.append(_res("casualty_posts", "every non-aggregate post linked to an incident", unlinked == 0, f"{unlinked} unlinked"))
    r.append(_unique(ci, "casualty_incidents", ["incident_id"]))
    r.append(_unique(t("silver", "casualty_daily"), "casualty_daily", ["event_day", "oblast_id"]))
    sr = t("silver", "strikes_on_russia")
    r.append(_unique(sr, "strikes_on_russia", ["event_day", "region_uk", "target_type"]))

    # air force nightly
    af = t("silver", "af_nightly")
    r.append(_unique(af, "af_nightly", ["night"]))
    bad = af.where("launched < 0 or launched > 1500").count()
    r.append(_res("af_nightly", "0 <= launched <= 1500", bad == 0, f"{bad} rows"))
    sg = af.where("flag_shot_gt_launched and quality <> 'low'").count()
    r.append(_res("af_nightly", "shot_down > launched marked low quality", sg == 0,
                  f"{af.where('flag_shot_gt_launched').count()} nights flagged, {sg} not marked"))

    # weather
    w = t("silver", "weather_night")
    r.append(_unique(w, "weather_night", ["oblast_id", "night"]))
    partial = w.where("n_hours < 12 or n_hours > 14").count()  # 12 or 14 on daylight-saving nights
    r.append(_res("weather_night", "12-14 hours per night", partial <= 2 * 27, f"{partial} incomplete nights (range edges)"))
    rng = w.where("cloud_cover_mean < 0 or cloud_cover_mean > 100 or temp_mean_c < -40 or temp_mean_c > 45").count()
    r.append(_res("weather_night", "physical ranges", rng == 0, f"{rng} rows"))
    return r
