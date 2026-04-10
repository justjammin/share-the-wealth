#!/usr/bin/env python3
"""
Share the Wealth CLI - track, map, and execute politician trades.
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from share_the_wealth.sources import TradeFetcher, PriceService
from share_the_wealth.analysis import FundAnalyzer
from share_the_wealth.execution import Broker

console = Console()
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_FUNDS_PATH = PROJECT_ROOT / "my_funds.txt"


def load_funds(path: Path | None = None) -> list[str]:
    path = path or DEFAULT_FUNDS_PATH
    if not path.exists():
        return ["SPY", "QQQ", "VOO", "VTI"]
    return [
        line.strip().upper()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def cmd_track(limit: int) -> None:
    fetcher = TradeFetcher()
    console.print("[bold]Fetching recent Congress trades...[/bold]\n")
    trades = fetcher.fetch_all(limit_per_chamber=limit)
    if not trades:
        console.print("[yellow]No trades found. Check FMP_API_KEY in .env[/yellow]")
        return

    table = Table(title="Recent Politician Trades")
    table.add_column("Date", style="dim")
    table.add_column("Politician", style="cyan")
    table.add_column("Chamber")
    table.add_column("Symbol", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Amount", style="dim")

    for t in trades[:50]:
        table.add_row(
            t.transaction_date[:10] if t.transaction_date else "-",
            t.politician_name[:25] if t.politician_name else "-",
            t.chamber,
            t.symbol,
            t.transaction_type,
            str(t.amount_range or "-")[:20],
        )
    console.print(table)
    console.print(f"\n[dim]Total: {len(trades)} trades[/dim]")


def cmd_map(funds_path: Path | None, limit: int) -> None:
    funds = load_funds(funds_path)
    fetcher = TradeFetcher()
    analyzer = FundAnalyzer()

    console.print(f"[bold]Your funds:[/bold] {', '.join(funds)}\n")
    console.print("[bold]Fetching recent Congress trades...[/bold]\n")

    trades = fetcher.fetch_all(limit_per_chamber=limit)
    if not trades:
        console.print("[yellow]No trades found.[/yellow]")
        return

    purchases = [t for t in trades if "Purchase" in t.transaction_type or "Buy" in str(t.transaction_type)]
    sales = [t for t in trades if "Sale" in t.transaction_type or "Sell" in str(t.transaction_type)]

    console.print("[bold green]PURCHASES to mirror:[/bold green]\n")
    for t in purchases[:15]:
        mapped = analyzer.map_trade_to_funds(t, funds)
        if mapped:
            m = mapped[0]
            console.print(f"  {t.symbol} ({t.politician_name}) → [green]{m.executable_symbol}[/green] ({m.match_reason}) conf={m.confidence:.2f}")
        else:
            console.print(f"  [dim]{t.symbol} ({t.politician_name}) → No match in your funds[/dim]")

    console.print("\n[bold red]SALES to mirror:[/bold red]\n")
    for t in sales[:15]:
        mapped = analyzer.map_trade_to_funds(t, funds)
        if mapped:
            m = mapped[0]
            console.print(f"  {t.symbol} ({t.politician_name}) → [red]{m.executable_symbol}[/red] ({m.match_reason}) conf={m.confidence:.2f}")
        else:
            console.print(f"  [dim]{t.symbol} ({t.politician_name}) → No match in your funds[/dim]")


def cmd_execute(funds_path: Path | None, dry_run: bool, order_size: float) -> None:
    from share_the_wealth.config import Settings

    funds = load_funds(funds_path)
    fetcher = TradeFetcher()
    analyzer = FundAnalyzer()
    broker = Broker()

    if not Settings.ALPACA_API_KEY or not Settings.ALPACA_SECRET_KEY:
        console.print("[red]Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env[/red]")
        return

    acc = broker.get_account()
    if not acc:
        console.print("[red]Could not connect to Alpaca. Check API keys.[/red]")
        return

    trades = fetcher.fetch_all(limit_per_chamber=30)
    purchases = [t for t in trades if "Purchase" in t.transaction_type or "Buy" in str(t.transaction_type)]

    console.print(f"[bold]Account:[/bold] ${acc['portfolio_value']:.2f} | Buying power: ${acc['buying_power']:.2f}")
    console.print(f"[bold]Order size per trade:[/bold] ${order_size:.2f}\n")

    executed = []
    for t in purchases[:10]:
        mapped = analyzer.map_trade_to_funds(t, funds)
        if not mapped or mapped[0].confidence < 0.7:
            continue
        m = mapped[0]
        if m.executable_symbol not in [x["symbol"] for x in executed]:
            if dry_run:
                console.print(f"  [dim]Would buy[/dim] ${order_size:.2f} of {m.executable_symbol} (mirroring {t.symbol} by {t.politician_name})")
            else:
                result = broker.place_order_by_dollars(m.executable_symbol, order_size, "buy")
                if result.success:
                    console.print(f"  [green]✓[/green] Bought ${order_size:.2f} of {m.executable_symbol}")
                else:
                    console.print(f"  [red]✗[/red] {m.executable_symbol}: {result.message}")
            executed.append({"symbol": m.executable_symbol})


def cmd_etl_run(args) -> None:
    from share_the_wealth.warehouse.etl import run_etl
    console.print("[bold]Running ETL (warehouse snapshot)…[/bold]\n")
    r = run_etl()
    if r.get("ok"):
        console.print(
            f"[green]✓[/green] Snapshot written (run_id={r['run_id']}) — "
            f"politicians_fallback={r['politicians_fallback']} funds_fallback={r['funds_fallback']}"
        )
    else:
        console.print(f"[red]✗[/red] {r.get('error', 'unknown')}")


def cmd_run(host: str, port: int, reload: bool = False) -> None:
    import uvicorn
    if reload:
        uvicorn.run(
            "share_the_wealth.api.app:create_app",
            host=host,
            port=port,
            reload=True,
            factory=True,
        )
    else:
        from share_the_wealth.api import create_app
        uvicorn.run(create_app(), host=host, port=port)


def cmd_help() -> None:
    console.print("[bold]Share the Wealth[/bold] - Track politician trades, mirror with your funds\n")
    console.print("[bold]Commands:[/bold]")
    console.print("  [cyan]stw track[/cyan]     Show recent Congress trades")
    console.print("  [cyan]stw map[/cyan]       Map trades to your funds (my_funds.txt)")
    console.print("  [cyan]stw execute[/cyan]   Execute mirrored trades via Alpaca")
    console.print("  [cyan]stw run[/cyan]       Start web UI (http://localhost:8007)")
    console.print("  [cyan]stw etl run[/cyan]   Write SQLite warehouse snapshot (APIs + dummy fallback)")
    console.print("  [cyan]stw run --reload[/cyan]  Auto-reload on file changes (dev)")
    console.print("  [cyan]stw help[/cyan]     Show this help\n")
    console.print("[bold]Options:[/bold]")
    console.print("  track -n 50        Limit trades per chamber")
    console.print("  map -f funds.txt   Custom funds list")
    console.print("  execute --dry-run Preview without placing orders")
    console.print("  execute -s 100    Order size in dollars\n")
    console.print("[dim]Also: make help | just help[/dim]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Share the Wealth - Mirror politician trades")
    sub = parser.add_subparsers(dest="cmd", required=True)

    help_p = sub.add_parser("help", help="Show help and options")
    help_p.set_defaults(func=lambda a: cmd_help())

    track_p = sub.add_parser("track", help="Show recent politician trades")
    track_p.add_argument("-n", "--limit", type=int, default=25, help="Trades per chamber")
    track_p.set_defaults(func=lambda a: cmd_track(a.limit))

    map_p = sub.add_parser("map", help="Map politician trades to your funds")
    map_p.add_argument("-f", "--funds", type=Path, default=None, help="Path to funds list (default: my_funds.txt)")
    map_p.add_argument("-n", "--limit", type=int, default=25, help="Trades per chamber")
    map_p.set_defaults(func=lambda a: cmd_map(a.funds, a.limit))

    exec_p = sub.add_parser("execute", help="Execute mirrored trades via Alpaca")
    exec_p.add_argument("--dry-run", action="store_true", help="Preview without placing orders")
    exec_p.add_argument("-f", "--funds", type=Path, default=None, help="Path to funds list")
    exec_p.add_argument("-s", "--size", type=float, default=100.0, help="Dollar amount per order")
    exec_p.set_defaults(func=lambda a: cmd_execute(a.funds, a.dry_run, a.size))

    run_p = sub.add_parser("run", help="Start web UI server")
    run_p.add_argument("--host", default="0.0.0.0", help="Host to bind")
    run_p.add_argument("-p", "--port", type=int, default=8007, help="Port")
    run_p.add_argument("--reload", action="store_true", help="Auto-reload on file changes (for dev)")
    run_p.set_defaults(func=lambda a: cmd_run(a.host, a.port, a.reload))

    etl_p = sub.add_parser("etl", help="Warehouse ETL snapshot")
    etl_sub = etl_p.add_subparsers(dest="etl_cmd", required=True)
    etl_run_p = etl_sub.add_parser("run", help="Fetch politicians + funds and persist to SQLite")
    etl_run_p.set_defaults(func=cmd_etl_run)

    args = parser.parse_args()
    args.func(args)
