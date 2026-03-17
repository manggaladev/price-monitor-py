"""
Logging configuration for the price monitor application.
Provides colored console output and file logging.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from price_monitor.config import settings


def setup_logger(
    name: str = "price_monitor",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Setup logger with console and file handlers.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file

    Returns:
        Configured logger instance
    """
    log_level = level or settings.log_level
    log_path = log_file or settings.log_file

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with Rich
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=True,
        show_path=True,
        rich_tracebacks=True,
        markup=True,
    )
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_path:
        log_file_path = Path(log_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()


def log_scraper_start(url: str, site: str) -> None:
    """Log scraper start."""
    logger.info(f"[bold blue]Scraping started[/] - Site: {site}, URL: {url}")


def log_scraper_success(url: str, price: float, site: str) -> None:
    """Log successful price fetch."""
    logger.info(f"[bold green]Price fetched[/] - {site}: {price:,.0f} | {url}")


def log_scraper_error(url: str, error: str, site: str) -> None:
    """Log scraper error."""
    logger.error(f"[bold red]Scraping failed[/] - {site}: {error} | {url}")


def log_price_alert(product_name: str, current_price: float, target_price: float, url: str) -> None:
    """Log price alert."""
    logger.warning(
        f"[bold yellow]PRICE ALERT![/] {product_name} - "
        f"Current: {current_price:,.0f}, Target: {target_price:,.0f} | {url}"
    )


def log_notification_sent(product_name: str, channel: str) -> None:
    """Log notification sent."""
    logger.info(f"[bold green]Notification sent[/] via {channel}: {product_name}")
