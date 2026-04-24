#!/usr/bin/env python3
"""Share the Wealth CLI."""

import argparse
from pathlib import Path

from rich.console import Console

console = Console()


def cmd_etl_run(args) -> None:
    from share_the_wealth.warehouse.etl import run_etl
    console.print("[bold]Running ETL (warehouse snapshot)…[/bold]\n")
    r = run_etl()
    if r.get("ok"):
        console.print(
            f"[green]✓[/green] Snapshot written — "
            f"funds={r.get('funds')} fallback={r.get('funds_fallback')}"
        )
    else:
        console.print(f"[red]✗[/red] {r.get('errors', 'unknown')}")


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
    console.print("[bold]Share the Wealth[/bold] - Mirror hedge fund 13F holdings\n")
    console.print("[bold]Commands:[/bold]")
    console.print("  [cyan]stw run[/cyan]           Start web UI (http://localhost:8007)")
    console.print("  [cyan]stw run --reload[/cyan]  Auto-reload on file changes (dev)")
    console.print("  [cyan]stw etl run[/cyan]       Write SQLite warehouse snapshot")
    console.print("  [cyan]stw help[/cyan]          Show this help\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Share the Wealth - Mirror hedge fund 13F holdings")
    sub = parser.add_subparsers(dest="cmd", required=True)

    help_p = sub.add_parser("help", help="Show help")
    help_p.set_defaults(func=lambda a: cmd_help())

    run_p = sub.add_parser("run", help="Start web UI server")
    run_p.add_argument("--host", default="0.0.0.0", help="Host to bind")
    run_p.add_argument("-p", "--port", type=int, default=8007, help="Port")
    run_p.add_argument("--reload", action="store_true", help="Auto-reload on file changes")
    run_p.set_defaults(func=lambda a: cmd_run(a.host, a.port, a.reload))

    etl_p = sub.add_parser("etl", help="Warehouse ETL snapshot")
    etl_sub = etl_p.add_subparsers(dest="etl_cmd", required=True)
    etl_run_p = etl_sub.add_parser("run", help="Fetch funds and persist to SQLite")
    etl_run_p.set_defaults(func=cmd_etl_run)

    args = parser.parse_args()
    args.func(args)
