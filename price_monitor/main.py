"""
Price Monitor - E-commerce price monitoring CLI.

A command-line interface for managing product price monitoring.
"""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from price_monitor import __version__
from price_monitor.config import settings
from price_monitor.database import (
    NotificationLogCRUD,
    PriceHistoryCRUD,
    ProductCRUD,
    init_db,
)
from price_monitor.notifier.telegram import TelegramNotifier, telegram_notifier
from price_monitor.scraper.utils import get_scraper, is_supported_site
from price_monitor.scheduler import scheduler
from price_monitor.utils.validators import format_price, get_site_from_url

console = Console()


def print_header():
    """Print application header."""
    console.print()
    console.print("[bold cyan]═══════════════════════════════════════════[/]")
    console.print("[bold cyan]       PRICE MONITOR v{}[/]".format(__version__))
    console.print("[bold cyan]═══════════════════════════════════════════[/]")
    console.print()


@click.group()
@click.version_option(version=__version__, prog_name="price-monitor")
def cli():
    """
    Price Monitor - E-commerce price monitoring tool.

    Monitor product prices from Tokopedia, Amazon, and other sites.
    Get notified when prices drop below your target.
    """
    init_db()


@cli.command()
@click.argument("url")
@click.option("--target", "-t", required=True, type=float, help="Target price for notification")
@click.option("--interval", "-i", default=None, type=int, help="Check interval in minutes (default: 360)")
@click.option("--name", "-n", default=None, help="Product name (auto-detected if not provided)")
@click.option("--notes", default=None, help="Additional notes")
def add(url: str, target: float, interval: Optional[int], name: Optional[str], notes: Optional[str]):
    """
    Add a product to monitor.

    Example:
        price-monitor add https://tokopedia.com/product/xyz --target 100000
    """
    print_header()

    # Check if URL is supported
    if not is_supported_site(url):
        console.print("[red]Error: Unsupported site.[/]")
        console.print("Supported sites: tokopedia, amazon, shopee, lazada, bukalapak")
        sys.exit(1)

    # Check if product already exists
    existing = ProductCRUD.get_by_url(url)
    if existing:
        console.print(f"[yellow]Product already exists (ID: {existing.id})[/]")
        console.print(f"  Name: {existing.name or 'Unknown'}")
        console.print(f"  Target: {format_price(existing.target_price)}")
        sys.exit(1)

    site = get_site_from_url(url)
    check_interval = interval or settings.default_check_interval

    # Try to get product info
    console.print(f"[cyan]Fetching product information from {site}...[/]")

    scraper = get_scraper(url)
    if scraper:
        try:
            result = scraper.get_price(url)
            if result.success:
                detected_name = result.name or name or "Unknown Product"
                current_price = result.price
                currency = result.currency
                available = result.available

                console.print(f"[green]✓ Product found![/]")
                console.print(f"  Name: {detected_name}")
                console.print(f"  Current Price: {format_price(current_price) if current_price else 'N/A'}")
                console.print(f"  Available: {'Yes' if available else 'No'}")
            else:
                detected_name = name or "Unknown Product"
                current_price = None
                currency = "Rp"
                available = True
                console.print(f"[yellow]⚠ Could not fetch product info: {result.error}[/]")
        except Exception as e:
            detected_name = name or "Unknown Product"
            current_price = None
            currency = "Rp"
            available = True
            console.print(f"[yellow]⚠ Error fetching product: {e}[/]")
    else:
        detected_name = name or "Unknown Product"
        current_price = None
        currency = "Rp"
        available = True

    # Create product
    product = ProductCRUD.create(
        url=url,
        target_price=target,
        name=detected_name,
        site=site,
        check_interval=check_interval,
        notes=notes,
    )

    console.print()
    console.print("[green]═══════════════════════════════════════════[/]")
    console.print("[green bold]Product added successfully![/]")
    console.print("[green]═══════════════════════════════════════════[/]")
    console.print()
    console.print(f"  ID: {product.id}")
    console.print(f"  Name: {product.name}")
    console.print(f"  Site: {product.site}")
    console.print(f"  URL: {product.url[:60]}..." if len(product.url) > 60 else f"  URL: {product.url}")
    console.print(f"  Target Price: {format_price(target)}")
    console.print(f"  Check Interval: {check_interval} minutes")
    console.print()


@cli.command("list")
@click.option("--all", "-a", "show_all", is_flag=True, help="Show inactive products too")
def list_products(show_all: bool):
    """List all monitored products."""
    print_header()

    products = ProductCRUD.get_all(active_only=not show_all)

    if not products:
        console.print("[yellow]No products found.[/]")
        console.print("Add a product with: price-monitor add <url> --target <price>")
        return

    table = Table(title=f"Monitored Products ({len(products)} total)")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="white", max_width=35)
    table.add_column("Site", style="green")
    table.add_column("Current", style="yellow", justify="right")
    table.add_column("Target", style="magenta", justify="right")
    table.add_column("Status", style="bold")
    table.add_column("Last Checked", style="dim")

    for p in products:
        current = format_price(p.current_price) if p.current_price else "-"
        target = format_price(p.target_price)

        if not p.is_active:
            status = "[dim]PAUSED[/]"
        elif p.current_price and p.current_price <= p.target_price:
            status = "[green]🎯 TARGET REACHED![/]"
        elif p.current_price:
            status = "[blue]Above Target[/]"
        else:
            status = "[yellow]Pending[/]"

        last_checked = p.last_checked.strftime("%Y-%m-%d %H:%M") if p.last_checked else "Never"
        name = p.name[:35] + "..." if p.name and len(p.name) > 35 else p.name or "Unknown"

        table.add_row(
            str(p.id),
            name,
            p.site or "-",
            current,
            target,
            status,
            last_checked,
        )

    console.print(table)


@cli.command()
@click.argument("product_id", type=int)
def remove(product_id: int):
    """Remove a product from monitoring."""
    print_header()

    product = ProductCRUD.get_by_id(product_id)
    if not product:
        console.print(f"[red]Error: Product {product_id} not found.[/]")
        sys.exit(1)

    if click.confirm(f"Remove '{product.name}' (ID: {product_id})?"):
        ProductCRUD.delete(product_id)
        console.print(f"[green]Product {product_id} removed successfully.[/]")
    else:
        console.print("[yellow]Cancelled.[/]")


@cli.command()
@click.argument("product_id", type=int)
@click.option("--target", "-t", type=float, help="New target price")
@click.option("--interval", "-i", type=int, help="New check interval in minutes")
@click.option("--name", "-n", help="New product name")
@click.option("--notes", help="New notes")
@click.option("--pause", is_flag=True, help="Pause monitoring")
@click.option("--resume", is_flag=True, help="Resume monitoring")
def update(
    product_id: int,
    target: Optional[float],
    interval: Optional[int],
    name: Optional[str],
    notes: Optional[str],
    pause: bool,
    resume: bool,
):
    """Update a product's settings."""
    print_header()

    product = ProductCRUD.get_by_id(product_id)
    if not product:
        console.print(f"[red]Error: Product {product_id} not found.[/]")
        sys.exit(1)

    update_data = {}
    if target is not None:
        update_data["target_price"] = target
    if interval is not None:
        update_data["check_interval"] = interval
    if name is not None:
        update_data["name"] = name
    if notes is not None:
        update_data["notes"] = notes
    if pause:
        update_data["is_active"] = False
    if resume:
        update_data["is_active"] = True

    if not update_data:
        console.print("[yellow]No updates specified.[/]")
        return

    ProductCRUD.update(product_id, **update_data)
    console.print(f"[green]Product {product_id} updated successfully.[/]")


@cli.command()
@click.argument("product_id", type=int)
def check(product_id: int):
    """Check a product's price immediately."""
    print_header()

    product = ProductCRUD.get_by_id(product_id)
    if not product:
        console.print(f"[red]Error: Product {product_id} not found.[/]")
        sys.exit(1)

    console.print(f"[cyan]Checking price for: {product.name}...[/]")

    scheduler.check_product_now(product_id)

    # Get updated product
    product = ProductCRUD.get_by_id(product_id)
    if product and product.current_price:
        console.print(f"[green]Current price: {format_price(product.current_price)}[/]")
        if product.current_price <= product.target_price:
            console.print("[bold green]🎯 Price is at or below target![/]")
    else:
        console.print("[yellow]Could not retrieve current price.[/]")


@cli.command()
def run():
    """Start the scheduler (foreground mode)."""
    print_header()

    console.print("[cyan]Starting price monitor scheduler...[/]")
    console.print("[dim]Press Ctrl+C to stop.[/]")
    console.print()

    scheduler.start()

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/]")
        scheduler.stop()


@cli.command("run-once")
def run_once():
    """Check all products once without starting scheduler."""
    print_header()

    console.print("[cyan]Running one-time check for all products...[/]")
    console.print()

    scheduler.run_once()

    console.print()
    console.print("[green]Check completed.[/]")


@cli.command()
@click.argument("product_id", type=int)
def history(product_id: int):
    """Show price history for a product."""
    print_header()

    product = ProductCRUD.get_by_id(product_id)
    if not product:
        console.print(f"[red]Error: Product {product_id} not found.[/]")
        sys.exit(1)

    history = PriceHistoryCRUD.get_by_product(product_id, limit=50)

    if not history:
        console.print("[yellow]No price history found.[/]")
        return

    table = Table(title=f"Price History: {product.name}")
    table.add_column("Date/Time", style="cyan")
    table.add_column("Price", style="green", justify="right")
    table.add_column("Available", style="yellow")
    table.add_column("Notes", style="dim")

    for h in history:
        price = format_price(h.price)
        available = "✓" if h.available else "✗"
        notes = h.notes or ""
        checked = h.checked_at.strftime("%Y-%m-%d %H:%M")

        table.add_row(checked, price, available, notes[:30])

    console.print(table)


@cli.command()
def test():
    """Test notification configuration."""
    print_header()

    # Test Telegram
    console.print("[cyan]Testing Telegram notification...[/]")

    if telegram_notifier.is_configured:
        success, message = telegram_notifier.test_connection()
        if success:
            console.print(f"[green]✓ Telegram: {message}[/]")

            # Send test message
            if click.confirm("Send test message?"):
                telegram_notifier.send_message("🔔 Test message from Price Monitor Bot!")
                console.print("[green]Test message sent![/]")
        else:
            console.print(f"[red]✗ Telegram: {message}[/]")
    else:
        console.print("[yellow]⚠ Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)[/]")

    console.print()

    # Show configuration
    console.print("[cyan]Configuration:[/]")
    console.print(f"  Database: {settings.database_url}")
    console.print(f"  Telegram: {'✓ Configured' if telegram_notifier.is_configured else '✗ Not configured'}")
    console.print(f"  Default Interval: {settings.default_check_interval} minutes")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
