#!/usr/bin/env python3
"""
Database initialization script.

Run this script to create all database tables.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

from price_monitor.database import init_db
from price_monitor.utils.logger import logger

console = Console()


def main():
    """Initialize database."""
    console.print("[cyan]Initializing database...[/]")

    try:
        init_db()
        console.print("[green]✓ Database initialized successfully![/]")
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize database: {e}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
