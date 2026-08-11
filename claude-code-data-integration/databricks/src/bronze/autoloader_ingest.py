"""Bronze Autoloader: ADLS JSONL OTel logs → Delta table."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--source-path", required=True)
    p.add_argument("--checkpoint-path", required=True)
    p.add_argument("--schema", default="bronze")
    p.add_argument("--table", default="claude_code_otel_raw")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.getOrCreate()

    spark.sql(f"CREATE CATALOG IF NOT EXISTS {args.catalog}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.{args.schema}")

    target = f"{args.catalog}.{args.schema}.{args.table}"

    (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{args.checkpoint_path}/schema")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("rescueDataColumn", "_rescued_data")
        .option("badRecordsPath", args.source_path.replace("/bronze/otel/logs", "/quarantine/bad_records"))
        .load(args.source_path)
        .withColumn("ingest_ts", F.lit(datetime.now(timezone.utc).isoformat()))
        .withColumn("source_file", F.col("_metadata.file_path"))
        .writeStream.format("delta")
        .option("checkpointLocation", f"{args.checkpoint_path}/data")
        .option("mergeSchema", "true")
        .trigger(availableNow=True)
        .table(target)
    )

    print(f"Bronze ingest complete → {target}")


if __name__ == "__main__":
    main()
