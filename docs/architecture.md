# Share the Wealth — Architecture

This document describes the **target architecture** (ETL, data, AI/RAG, risk) aligned with current project decisions. The codebase may not implement all of this yet; treat this as the north star for incremental delivery.

---

## 1. Goals

| Goal | Approach |
|------|----------|
| **Reliability** | Serve from a **silver** warehouse; live APIs are optional enhancement paths. |
| **Analytics** | ~2 months rolling history in the DB; purge older raw/detail per policy. |
| **Cost control** | Hourly batch ingestion; **Fresh** pulls budgeted (existing FMP pattern). |

---

## 2. Data layers (silver-first)

We standardize on **silver** for v1: **normalized tables** only (no bronze/raw JSON store until needed for audit/replay).

- **Silver:** One row per fact (trade, holding line, position snapshot component) with clean IDs, tickers, dates, foreign keys.
- **Gold / serving:** Views or materialized tables the API reads for “latest snapshot” and UI lists.

**Retention:** Purge data older than **90 days** where applicable; keep **latest snapshot** semantics clear for the UI.

**POC / API gaps:** When FMP or Forms13F is unavailable, **seed silver** from curated fixtures (dummy data) so the app and ETL pipeline remain demonstrable.

---

## 3. Sources

| Domain | Primary source | Notes |
|--------|----------------|--------|
| Congress trades | **FMP** (`senate-latest`, `house-latest`) | `FMP_API_KEY`; limit per subscription (e.g. 25). |
| Hedge fund 13F | **Forms13F** API (`forms13f.com`) | Per-fund CIK; existing client path. |
| Prices | Existing price service | Short-lived; can stay outside ETL v1 or write a small daily snapshot later. |

---

## 4. ETL

- **Schedule:** **Hourly** (Airflow DAG or equivalent).
- **Orchestration:** **Apache Airflow** in **Docker**; metadata DB can be **SQLite** for local/POC (single scheduler; not for large multi-worker production).
- **App warehouse:** **SQLite** file (e.g. `warehouse.db`) separate from Airflow’s metadata DB (`airflow.db`) to avoid mixing concerns.
- **Run record:** Persist **last run status**, **finished_at**, **error** (sanitized) for logs and UI.

**Hybrid reads:** API defaults to **warehouse**; **Fresh** triggers a **budgeted** live pull that updates or overlays data (design detail: single writer vs queue—pick at implementation).

---

## 5. API & UI contract

- **Stale data:** If last successful ETL is too old or last run **failed**, show **“stale as of …”** and a **warning bar** (failed runs).
- **Latency:** Multi-second RAG/risk on first load is **acceptable**; cache last **risk** result + `as_of` for snappy repeat visits.

---

## 6. AI: Anthropic + RAG + risk

### 6.1 LLM (chat, synthesis, narrative risk)

- **Provider:** **Anthropic API** (`ANTHROPIC_API_KEY`).
- **Uses:** RAG answers, portfolio analyst chat, narrative dimension of **risk** (e.g. political/regulatory framing), disclaimers in system prompts.

### 6.2 What is an embeddings provider?

**Embropic answers questions with words; it does not ship a standard “turn this paragraph into a vector” project** the way some stacks expect for RAG. For **retrieval**, we need **embeddings**:

1. **Embedding:** A model turns a chunk of text into a **vector** (a long list of numbers) that roughly captures “meaning.”
2. **Index:** We store many vectors (one per chunk of DB-derived text).
3. **Query:** The user’s question is embedded with the **same** model; we find the **nearest** vectors (similarity search).
4. **RAG:** We send those **retrieved chunks** + the question to **Claude** so answers stay **grounded** in your data.

The **embeddings provider** is whoever runs that embedding model: e.g. **OpenAI** (`text-embedding-3-small`), **Voyage AI**, **Cohere**, or a **local** model (`sentence-transformers`). It is **separate** from Anthropic in most setups; env vars might look like `OPENAI_API_KEY` or `VOYAGE_API_KEY` for embeddings only, while `ANTHROPIC_API_KEY` powers generation.

**Implemented in this repo:** **sentence-transformers** with default **`sentence-transformers/all-MiniLM-L6-v2`** — **$0** embedding API cost; first run downloads ~80MB; CPU-friendly. Claude (Anthropic) still performs generation. **Alternative:** OpenAI `text-embedding-3-small` can be wired later if you want a hosted embedding API instead.

**Corpus v1:** **DB-derived text only** (no user PDFs). After each ETL success, refresh or incrementally update chunks + embeddings tied to `snapshot_id` / `as_of`.

### 6.3 Vector storage (POC)

- Lightweight: **Chroma**, **Qdrant** (Docker), or **sqlite-vss** / pgvector if you add Postgres later.

### 6.4 Risk scorer

- **Dimensions (all in v1):** concentration, volatility proxy, sector/style concentration, political/regulatory **narrative** (LLM-assisted on top of structured facts).
- **Output:** **Composite score** (e.g. 0–100) **plus** per-dimension breakdown (not a single opaque number).
- **Disclaimers:** **Yes** — static + dynamic copy on risk panel and on RAG/chat responses (“not financial advice,” informational only), consistent with site footer.

---

## 7. Docker layout (conceptual)

One Compose stack may include:

- App API (FastAPI) + static UI
- SQLite volumes (`warehouse.db`, optional vector store path)
- Airflow (webserver + scheduler; SQLite metadata for POC)
- Optional: Qdrant/Chroma for vectors

**Kubernetes** is out of scope for POC; revisit when you need HA or multi-environment ops.

---

## 8. Environment variables (summary)

| Variable | Purpose |
|----------|---------|
| `FMP_API_KEY` | Congress trade API |
| `ANTHROPIC_API_KEY` | Claude — chat, RAG generation, risk narrative |
| `USE_LOCAL_RAG` / `ST_EMBEDDING_MODEL` / `RAG_TOP_K` | Local sentence-transformers RAG (defaults; see `share_the_wealth/ai/`) |
| *(existing)* | Alpaca, etc., per trading features |

---

## 9. Implementation phasing (suggested)

1. ~~Silver schema + SQLite + seed from fixtures; API reads DB.~~ **Done:** `share_the_wealth/warehouse/`, `WAREHOUSE_PATH`, `READ_FROM_WAREHOUSE`, `stw etl run`, `GET/POST /api/etl/status|run`, UI ETL banner, **↻ Fresh** persists snapshot.
2. ~~ETL job (hourly) + `etl_run` table + UI stale/failed bar.~~ **Partial:** `etl_run` + stale/failed UI; schedule via **cron** / host timer (`stw etl run`) or add Airflow later.
3. ~~Embeddings + vector store + RAG endpoint wired to Anthropic.~~ **Done:** local sentence-transformers + `AIAnalyst` RAG path.
4. Risk endpoint: structured JSON + UI + disclaimers.
5. Airflow DAG calling the same extract/transform modules as the CLI.
6. **Docker:** `Dockerfile` + `docker-compose.yml` for the app + volume for `warehouse.db`.

---

## 10. Open choices (when you implement)

- **Embeddings:** Local sentence-transformers is the default; optional OpenAI path can be added later.
- **Fresh:** Synchronous API pull vs enqueue priority ETL run.
- **Exact purge rules:** Which tables trim at 90d vs keep “current only” rows indefinitely.

---

*Last aligned with project decisions: ETL hourly, silver-first, Docker, SQLite warehouse + Airflow metadata SQLite, hybrid Fresh, DB-only RAG corpus, Anthropic for generation, full risk dimensions + disclaimers, latency OK.*
