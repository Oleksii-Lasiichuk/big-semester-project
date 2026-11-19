"""Spark session and table I/O, identical API locally (Parquet files) and on Databricks (Delta tables)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ON_DATABRICKS = "DATABRICKS_RUNTIME_VERSION" in os.environ
CATALOG = os.environ.get("PIPELINE_CATALOG", "workspace")
SCHEMA_PREFIX = "airwar"  # schemas: airwar_bronze, airwar_silver, airwar_gold
LOCAL_LAKE = ROOT / "data" / "lake"
RAW_DIR = os.environ.get("PIPELINE_RAW_DIR", str(ROOT / "data"))


def get_spark():
    from pyspark.sql import SparkSession
    if ON_DATABRICKS:
        return SparkSession.builder.getOrCreate()
    java21 = "/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home"
    if os.path.isdir(java21):
        os.environ.setdefault("JAVA_HOME", java21)
    import sys
    os.environ["PYSPARK_PYTHON"] = os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    src = str(ROOT / "src")  # Python workers import pipeline.* for pandas UDFs
    os.environ["PYTHONPATH"] = src + os.pathsep + os.environ.get("PYTHONPATH", "")
    return (SparkSession.builder.master("local[*]").appName("airwar")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.driver.memory", "6g")
            .config("spark.sql.shuffle.partitions", "16")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate())


def table_name(layer, name):
    return f"{CATALOG}.{SCHEMA_PREFIX}_{layer}.{name}"


def write(df, layer, name):
    if ON_DATABRICKS:
        df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_name(layer, name))
    else:
        df.write.mode("overwrite").parquet(str(LOCAL_LAKE / layer / name))
    return read(df.sparkSession, layer, name)


def read(spark, layer, name):
    if ON_DATABRICKS:
        return spark.table(table_name(layer, name))
    return spark.read.parquet(str(LOCAL_LAKE / layer / name))
