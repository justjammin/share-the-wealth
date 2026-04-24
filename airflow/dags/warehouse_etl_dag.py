"""
Hourly warehouse ETL for Share the Wealth.

Requires: pip install -e . from repo root, PYTHONPATH including repo root,
and env vars (e.g. FMP_API_KEY, WAREHOUSE_PATH) available to the Airflow worker/scheduler.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def _run_warehouse_etl() -> None:
    from share_the_wealth.warehouse.etl import run_etl

    result = run_etl()
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "ETL failed"))


with DAG(
    dag_id="share_the_wealth_warehouse_etl",
    default_args={
        "owner": "share-the-wealth",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Load politicians + hedge funds into SQLite (live APIs + dummy fallback)",
    schedule=timedelta(hours=1),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["share-the-wealth", "etl"],
) as dag:
    PythonOperator(
        task_id="run_etl",
        python_callable=_run_warehouse_etl,
    )
