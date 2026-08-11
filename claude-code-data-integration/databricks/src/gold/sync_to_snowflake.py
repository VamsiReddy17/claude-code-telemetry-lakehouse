"""Push gold tables from Databricks to Snowflake via Spark connector.

Requires cluster libraries: spark-snowflake / snowflake-jdbc
and secrets: snowflake-creds scope.
"""

from __future__ import annotations

import argparse
import os

from pyspark.sql import SparkSession


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--tables", default="daily_user_usage,compliance_transcript_lines")
    return p.parse_args()


def sf_options() -> dict:
    # Prefer Databricks secrets; fall back to env for local skeleton docs
    return {
        "sfURL": os.environ.get("SNOWFLAKE_ACCOUNT", "") + ".snowflakecomputing.com",
        "sfUser": os.environ.get("SNOWFLAKE_USER", ""),
        "sfPassword": os.environ.get("SNOWFLAKE_PASSWORD", ""),
        "sfDatabase": os.environ.get("SNOWFLAKE_DATABASE", "CLAUDE_TELEMETRY"),
        "sfSchema": os.environ.get("SNOWFLAKE_SCHEMA_GOLD", "GOLD"),
        "sfWarehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "CLAUDE_TELEM_WH"),
        "sfRole": os.environ.get("SNOWFLAKE_ROLE", "CLAUDE_TELEM_ROLE"),
    }


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.getOrCreate()
    opts = sf_options()

    for table in [t.strip() for t in args.tables.split(",") if t.strip()]:
        df = spark.table(f"{args.catalog}.gold.{table}")
        (
            df.write.format("snowflake")
            .options(**opts)
            .option("dbtable", table.upper())
            .mode("overwrite")
            .save()
        )
        print(f"Synced {args.catalog}.gold.{table} → Snowflake GOLD.{table.upper()}")


if __name__ == "__main__":
    main()
