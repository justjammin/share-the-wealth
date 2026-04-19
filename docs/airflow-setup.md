# Apache Airflow setup (hourly ETL)

Two practical options. Both assume the app is installed so `from share_the_wealth.warehouse.etl import run_etl` works (`pip install -e .` from the repo root).

---

## Option A — Local (fastest POC)

Uses Airflow’s **standalone** mode (scheduler + web UI + SQLite metadata in `AIRFLOW_HOME`).

1. **Install** (same venv as the app or a dedicated venv):

   ```bash
   pip install "apache-airflow==2.10.*" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.12.txt"
   ```

   (Pick a [constraints URL](https://airflow.apache.org/docs/apache-airflow/stable/installation/installing-from-pypi.html) that matches your Python version.)

2. **Point Airflow at your DAGs** (from repo root):

   ```bash
   export AIRFLOW_HOME="$PWD/.airflow"
   export PYTHONPATH="$PWD:${PYTHONPATH}"
   mkdir -p "$AIRFLOW_HOME/dags"
   ln -sf "$PWD/airflow/dags/warehouse_etl_dag.py" "$AIRFLOW_HOME/dags/"
   ```

3. **Initialize DB + admin user** (first time only):

   ```bash
   airflow db migrate
   airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin
   ```

   Or use **`airflow standalone`** once — it creates a user and prints credentials.

4. **Run processes** (two terminals, or use `standalone`):

   ```bash
   airflow scheduler
   ```

   ```bash
   airflow webserver --port 8080
   ```

   Or a single dev process:

   ```bash
   airflow standalone
   ```

5. Open **http://localhost:8080**, enable the DAG `share_the_wealth_warehouse_etl`, trigger a manual run to verify.

6. **Environment for ETL:** ensure `.env` is loaded or export `FMP_API_KEY`, `WAREHOUSE_PATH`, etc. Airflow inherits the shell env when you start `scheduler`/`webserver` from that shell. For `WAREHOUSE_PATH`, use an absolute path (e.g. `$(pwd)/data/warehouse.db`).

---

## Option B — Docker (official Compose)

Airflow publishes a **full** `docker-compose.yaml` (Postgres/Redis, multiple services). Do **not** duplicate it here — download the version that matches the Airflow release you want:

- [Running Airflow in Docker](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)

Rough integration steps:

1. Download their `docker-compose.yaml` into a directory (e.g. `airflow-docker/`).

2. **Mount** this repo and install the app in a **custom image**, or mount site-packages. Typical pattern: Dockerfile `FROM apache/airflow:2.10.4` + `COPY` your project + `RUN pip install -e /opt/project`.

3. **Mount DAGs:** `./airflow/dags` → `/opt/airflow/dags`.

4. **Persist warehouse:** volume or bind-mount the same `data/warehouse.db` the FastAPI app uses (or a shared path like `/data/warehouse.db`) and set `WAREHOUSE_PATH` on the worker/scheduler containers.

5. Set **`PYTHONPATH`** or install the package so `import share_the_wealth` resolves inside containers.

6. **Constraints:** install Airflow with the official constraints file for your Python version to avoid dependency conflicts.

---

## DAG file

The repo includes:

`airflow/dags/warehouse_etl_dag.py`

Schedule: **hourly** (`timedelta(hours=1)`). Adjust `start_date` if the DAG does not appear (must be in the past).

---

## Cron alternative (no Airflow)

If you only need “every hour” with no UI:

```cron
0 * * * * cd /path/to/share-the-wealth && /path/to/venv/bin/stw etl run >> /tmp/stw-etl.log 2>&1
```

---

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| `ModuleNotFoundError: share_the_wealth` | `PYTHONPATH` = repo root, or `pip install -e .` in the Airflow environment |
| ETL writes wrong DB | `WAREHOUSE_PATH` absolute path, same as the web app |
| DAG not listed | File in `AIRFLOW_HOME/dags/`, no syntax errors, `airflow dags list` |
