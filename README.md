# Share the Wealth

Track what politicians (Congress) and hedge funds are trading, then mirror those moves with your own portfolio. Python backend with a web UI.

## What It Does

1. **Politicians** – Fetches recent Congress stock trades (Senate + House) via [Financial Modeling Prep](https://site.financialmodelingprep.com)
2. **Hedge Funds** – Curated 13F-style holdings (Berkshire, Pershing Square, Tiger Global)
3. **My Portfolio** – Aggregates mirrored positions from politicians + funds you enable
4. **AI Insights** – Claude-powered analysis of your mirrored portfolio (optional)

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

## Usage

After `./setup.sh`:

| Command | Usage |
|---------|-------|
| `make track` / `just track` | Show Congress trades |
| `make map` / `just map` | Map trades to funds |
| `make execute` / `just execute` | Preview orders |
| `make server` / `just server` | Web UI |
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
│   ├── config/         # Settings (env)
│   ├── models/         # PoliticianTrade, MappedTrade, HedgeFund, OrderResult
│   ├── sources/        # TradeFetcher, HedgeFundFetcher, HedgeFundRepository, PriceService
│   ├── analysis/       # FundAnalyzer
│   ├── execution/      # Broker (Alpaca)
│   ├── ai/             # AIAnalyst (Anthropic)
│   ├── api/            # FastAPI app, routes, services, state
│   └── cli/             # CLI commands
└── my_funds.txt        # Your ETFs/stocks for mapping
```

## Disclaimer

For educational and research use. Past trades do not guarantee future returns. Use paper trading first. Not financial advice.
