"""Baseline models on the gold tables (Spark ML gradient-boosted trees), compared with naive forecasts.

Tasks
  national: next night's number of launched drones and missiles (gold.national_day.y_next_launched)
  oblast:   next day's alert hours per oblast, raion-share measure (gold.oblast_day.y_next_alert_hours_share)

Every column of day d is known when day d ends (18:00 Kyiv), before the predicted night starts,
so all non-target columns are allowed as features. Validation is a time split.
Runs are logged to MLflow when it is available (Databricks), otherwise printed.

Usage: python scripts/train_baseline.py [--task national,oblast] [--test-start 2025-10-01]
"""
import argparse
import sys
from pathlib import Path

_root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else str(Path(__file__).resolve().parents[1])
sys.path.insert(0, str(Path(_root) / "src"))
from pyspark.ml import Pipeline  # noqa: E402
from pyspark.ml.feature import VectorAssembler  # noqa: E402
from pyspark.ml.regression import GBTRegressor  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402
from pyspark.sql.types import BooleanType, NumericType  # noqa: E402

from pipeline.io import get_spark, read, write  # noqa: E402

TASKS = {
    "national": dict(table="national_day", target="y_next_launched", today="launched", mean7="launched_mean7",
                     filter="af_quality = 'ok'"),
    "oblast": dict(table="oblast_day", target="y_next_alert_hours_share", today="alert_hours_share",
                   mean7="alert_hours_share_mean7", filter=None),
}


def features(df, target):
    drop = {target, "day"} | {c for c in df.columns if c.startswith("y_next")}
    cols = []
    for f in df.schema.fields:
        if f.name in drop:
            continue
        if isinstance(f.dataType, (NumericType, BooleanType)):
            cols.append(f.name)
    return cols


def mae(df, pred, target):
    return df.select(F.avg(F.abs(F.col(pred) - F.col(target)))).first()[0]


def run_task(spark, name, cfg, test_start, mlflow):
    df = read(spark, "gold", cfg["table"]).where(F.col(cfg["target"]).isNotNull())
    if cfg["filter"]:
        df = df.where(cfg["filter"])
    cols = features(df, cfg["target"])
    df = df.select("day", *([c for c in ["oblast_id"] if c in df.columns]), cfg["target"],
                   *[F.coalesce(F.col(c).cast("double"), F.lit(-1.0)).alias(c) for c in cols])
    # the model learns the deviation from the 7-day mean: trees cannot extrapolate a growing level
    df = df.where(F.col(cfg["mean7"]) >= 0).withColumn("resid", F.col(cfg["target"]) - F.col(cfg["mean7"]))
    train, test = df.where(F.col("day") < test_start), df.where(F.col("day") >= test_start)

    gbt = GBTRegressor(featuresCol="features", labelCol="resid", maxDepth=4, maxIter=100, stepSize=0.05,
                       subsamplingRate=0.8, featureSubsetStrategy="sqrt", minInstancesPerNode=20, seed=42)
    model = Pipeline(stages=[VectorAssembler(inputCols=cols, outputCol="features"), gbt]).fit(train)
    pred = (model.transform(test).withColumn("pred_gbt", F.greatest(F.lit(0.0), F.col(cfg["mean7"]) + F.col("prediction"))))

    res = {"n_train": train.count(), "n_test": test.count(), "n_features": len(cols),
           "mae_gbt": mae(pred, "pred_gbt", cfg["target"]),
           "mae_persistence": mae(pred, cfg["today"], cfg["target"]),
           "mae_mean7": mae(pred, cfg["mean7"], cfg["target"])}
    imp = sorted(zip(cols, model.stages[-1].featureImportances.toArray()), key=lambda x: -x[1])[:15]
    print(f"\n== {name}: predict {cfg['target']} | train < {test_start} <= test")
    for k, v in res.items():
        print(f"  {k:18s} {v:,.3f}" if isinstance(v, float) else f"  {k:18s} {v}")
    print("  top features:", ", ".join(f"{c} {v:.3f}" for c, v in imp))
    keep = ["day"] + (["oblast_id"] if "oblast_id" in pred.columns else []) + [cfg["target"], cfg["today"], cfg["mean7"], "pred_gbt"]
    write(pred.select(*keep), "gold", f"predictions_{name}")
    if mlflow:
        with mlflow.start_run(run_name=f"gbt_{name}"):
            mlflow.log_params({"task": name, "target": cfg["target"], "test_start": test_start, "maxDepth": 4,
                               "maxIter": 100, "n_features": len(cols)})
            mlflow.log_metrics({k: v for k, v in res.items() if isinstance(v, float)})
            mlflow.log_dict({c: float(v) for c, v in imp}, "top_features.json")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="national,oblast")
    ap.add_argument("--test-start", default="2025-10-01")
    ap.add_argument("--root")
    a = ap.parse_args()
    spark = get_spark()
    try:
        import mlflow
        from pipeline.io import ON_DATABRICKS
        if not ON_DATABRICKS:
            mlflow = None
        else:
            mlflow.autolog(disable=True)  # Spark ML autologging fails on serverless (no spark.mlflow.* conf)
            mlflow.set_registry_uri("databricks-uc")
            user = spark.sql("select current_user()").first()[0]
            mlflow.set_experiment(f"/Users/{user}/airwar_baseline")
    except ImportError:
        mlflow = None
    if mlflow is None:
        try:
            import mlflow as _m
            _m.autolog(disable=True)
        except ImportError:
            pass
    for t in a.task.split(","):
        run_task(spark, t, TASKS[t], a.test_start, mlflow)


if __name__ == "__main__":
    main()
