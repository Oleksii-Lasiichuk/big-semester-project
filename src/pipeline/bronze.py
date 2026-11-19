"""Bronze: raw files as they are, plus ingestion metadata. No cleaning."""
from pyspark.sql import functions as F
from pyspark.sql import types as T

from .io import RAW_DIR


def _meta(df):
    return df.withColumn("_ingested_at", F.current_timestamp()).withColumn("_source_file", F.input_file_name())


def alerts(spark):
    df = spark.read.option("header", True).csv(f"{RAW_DIR}/raw/alerts/official_data_en.csv")
    return _meta(df)


def tg_posts(spark):
    schema = T.StructType([T.StructField(c, t) for c, t in [
        ("channel", T.StringType()), ("post_id", T.LongType()), ("datetime", T.StringType()),
        ("text", T.StringType()), ("views", T.LongType()), ("url", T.StringType())]])
    return _meta(spark.read.schema(schema).json(f"{RAW_DIR}/telegram/*.jsonl"))


def llm_events(spark):
    return _meta(spark.read.json(f"{RAW_DIR}/llm/events_llm.jsonl"))


def af_regex(spark):
    return _meta(spark.read.option("header", True).option("inferSchema", True).csv(f"{RAW_DIR}/llm/kpszsu_daily.csv"))


WEATHER_VARS = ["temperature_2m", "relative_humidity_2m", "precipitation", "snowfall", "cloud_cover", "cloud_cover_low",
                "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"]


def weather_hourly(spark):
    """Raw Open-Meteo JSON (one file per oblast, arrays per variable) flattened to one row per oblast-hour."""
    raw = _meta(spark.read.option("multiLine", True).json(f"{RAW_DIR}/raw/weather/*.json"))
    zipped = F.arrays_zip(*[F.col(f"hourly.{c}").alias(c) for c in ["time"] + WEATHER_VARS])
    return (raw.select("oblast_id", "_ingested_at", "_source_file", F.explode(zipped).alias("h"))
            .select("oblast_id", F.col("h.time").alias("time_utc"),
                    *[F.col(f"h.{c}").cast("double").alias(c) for c in WEATHER_VARS],
                    "_ingested_at", "_source_file"))
