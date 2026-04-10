# Share the Wealth

Track what politicians (Congress) and hedge funds are trading, then mirror those moves with your own portfolio. Python backend with a web UI.

## What It Does

1. **Politicians** – Fetches recent Congress stock trades (Senate + House) via [Financial Modeling Prep](https://site.financialmodelingprep.com)
2. **Hedge Funds** – Curated 13F-style holdings (Berkshire, Pershing Square, Tiger Global)
3. **My Portfolio** – Aggregates mirrored positions from politicians + funds you enable
4. **AI Insights** – Claude-powered analysis of your mirrored portfolio (optional)

## Documentation

- **[Architecture](docs/architecture.md)** — ETL (silver layer, Docker, Airflow), RAG, risk scoring, env vars, and implementation phasing.
- **[Airflow setup](docs/airflow-setup.md)** — local `airflow standalone`, Docker notes, and the hourly DAG in `airflow/dags/`.
- **Embeddings (RAG):** Implemented with **[sentence-transformers](https://www.sbert.net/)** (`all-MiniLM-L6-v2` by default) — **$0 embedding API cost**, runs locally on CPU; first request downloads ~80MB. Claude (Anthropic) still generates answers. Optional: OpenAI embeddings via `OPENAI_API_KEY` if you add that path later.

## Setup

**One-liner (recommended):**
```bash
./setup.sh
source venv/bin/activate
```

**Or with Make/just:**
```bash
make setup    # or: just setup
source venv/bin/activate
```

### API Keys (`.env`)

| Key | Purpose |
|-----|---------|
| `FMP_API_KEY` | Congress trades – [Financial Modeling Prep](https://site.financialmodelingprep.com/register) |
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | Trading (optional) – [Alpaca](https://alpaca.markets) |
| `ANTHROPIC_API_KEY` | AI Insights (optional) – [Anthropic](https://console.anthropic.com) |
| `USE_LOCAL_RAG` | `true` (default) — use local sentence-transformers for RAG retrieval; see [Architecture](docs/architecture.md) |
| `ST_EMBEDDING_MODEL` | Optional override — default `sentence-transformers/all-MiniLM-L6-v2` |
| `WAREHOUSE_PATH` | SQLite file for the silver snapshot (default `data/warehouse.db`) |
| `READ_FROM_WAREHOUSE` | `true` (default) — serve politicians/funds from the last successful ETL when present |
| `ETL_STALE_SECONDS` | After this many seconds since last success, UI shows a stale warning (default `7200`) |

### Warehouse ETL (SQLite)

- **`stw etl run`** or **`just etl`** — pulls politicians + hedge funds (same logic as the API, including dummy fallback) and writes **`WAREHOUSE_PATH`**.
- **`GET /api/etl/status`** — last run, stale flag, errors (used by the web UI banner).
- **`POST /api/etl/run`** — same as CLI (for automation).
- **↻ Fresh** on the web UI runs a budgeted FMP refresh, then **updates the warehouse** if successful.

With **`READ_FROM_WAREHOUSE=true`**, the app reads from the warehouse when a successful snapshot exists; otherwise it uses the in-process FMP cache as before.

### Docker

```bash
cp .env.example .env   # if you do not have .env yet
docker compose build
docker compose --env-file .env up
```

Open http://localhost:8007 — the DB lives in the `warehouse_data` volume (`/data/warehouse.db` in the container). Run a one-off ETL: `docker compose run --rm app python -c "from share_the_wealth.warehouse.etl import run_etl; print(run_etl())"`.

## Usage

After `./setup.sh`:

| Command | Usage |
|---------|-------|
| `make track` / `just track` | Show Congress trades |
| `make map` / `just map` | Map trades to funds |
| `make execute` / `just execute` | Preview orders |
| `make server` / `just server` | Web UI |
| `just etl` | Write SQLite warehouse snapshot |
| `./bin/stw help` | Help (no venv activate needed) |

**Or** `source venv/bin/activate` then use `stw` directly.

**Web UI:** `make server` → http://localhost:8007

## Data Sources

| Data | API | Fallback |
|------|-----|----------|
| Congress trades | Financial Modeling Prep (FMP_API_KEY) | Curated politicians |
| Hedge fund 13F | [Forms13F](https://forms13f.com) (free, no key) | Curated funds |
| Prices | yfinance | - |

## Project Structure

```
share-the-wealth/
├── api.py              # API server entry point
├── main.py             # CLI entry point
├── static/
│   └── index.html      # Web UI
├── share_the_wealth/
│   ├── warehouse/      # SQLite silver + ETL (run_etl)
│   ├── config/         # Settings (env)
│   ├── models/         # PoliticianTrade, MappedTrade, HedgeFund, OrderResult
│   ├── sources/        # TradeFetcher, HedgeFundFetcher, HedgeFundRepository, PriceService
│   ├── analysis/       # FundAnalyzer
│   ├── execution/      # Broker (Alpaca)
│   ├── ai/             # AIAnalyst (Anthropic), local_embeddings, rag_retriever
│   ├── api/            # FastAPI app, routes, services, state
│   └── cli/             # CLI commands
└── my_funds.txt        # Your ETFs/stocks for mapping
```

## Disclaimer

For educational and research use. Past trades do not guarantee future returns. Use paper trading first. Not financial advice.
