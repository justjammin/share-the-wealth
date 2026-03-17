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

After `./setup.sh` and `source venv/bin/activate`:

| Command | Shorthand |
|---------|-----------|
| `stw track` | `make track` or `just track` |
| `stw map` | `make map` or `just map` |
| `stw execute --dry-run` | `make execute` or `just execute` |
| `stw execute` | `make execute-live` or `just execute-live` |
| `stw run` | `make server` or `just server` |

**Web UI:** `stw run` (or `make server`) → http://localhost:8000

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
│   ├── sources/        # TradeFetcher, HedgeFundRepository, PriceService
│   ├── analysis/       # FundAnalyzer
│   ├── execution/      # Broker (Alpaca)
│   ├── ai/             # AIAnalyst (Anthropic)
│   ├── api/            # FastAPI app, routes, services, state
│   └── cli/             # CLI commands
└── my_funds.txt        # Your ETFs/stocks for mapping
```

## Disclaimer

For educational and research use. Past trades do not guarantee future returns. Use paper trading first. Not financial advice.
