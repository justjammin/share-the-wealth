#!/usr/bin/env python3
"""
Entry point for Share the Wealth CLI.

Usage:
  python main.py track              # Show recent politician trades
  python main.py map                # Map trades to your funds
  python main.py execute --dry-run  # Preview orders
  python main.py execute            # Execute mirrored trades via Alpaca
"""

from share_the_wealth.cli import main

if __name__ == "__main__":
    main()
