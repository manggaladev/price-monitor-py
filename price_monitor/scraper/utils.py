"""
Utility functions for scrapers.
"""

import re
from typing import Optional, Type

from price_monitor.scraper.base import BaseScraper
from price_monitor.scraper.tokopedia import TokopediaScraper
from price_monitor.scraper.amazon import AmazonScraper
from price_monitor.utils.validators import get_site_from_url


# Registry of available scrapers
SCRAPER_REGISTRY: dict[str, Type[BaseScraper]] = {
    "tokopedia": TokopediaScraper,
    "amazon": AmazonScraper,
}


def get_scraper(url: str) -> Optional[BaseScraper]:
    """
    Get appropriate scraper instance for a URL.

    Args:
        url: Product URL

    Returns:
        Scraper instance or None if unsupported
    """
    site = get_site_from_url(url)
    if not site:
        return None

    scraper_class = SCRAPER_REGISTRY.get(site)
    if not scraper_class:
        return None

    return scraper_class()


def get_scraper_for_site(site: str) -> Optional[BaseScraper]:
    """
    Get scraper instance by site name.

    Args:
        site: Site name (e.g., 'tokopedia', 'amazon')

    Returns:
        Scraper instance or None if not found
    """
    scraper_class = SCRAPER_REGISTRY.get(site.lower())
    if not scraper_class:
        return None
    return scraper_class()


def register_scraper(site: str, scraper_class: Type[BaseScraper]) -> None:
    """
    Register a new scraper.

    Args:
        site: Site name
        scraper_class: Scraper class
    """
    SCRAPER_REGISTRY[site.lower()] = scraper_class


def is_supported_site(url: str) -> bool:
    """
    Check if URL is from a supported site.

    Args:
        url: Product URL

    Returns:
        True if site is supported
    """
    site = get_site_from_url(url)
    return site is not None and site in SCRAPER_REGISTRY


def get_supported_sites() -> list[str]:
    """Get list of supported site names."""
    return list(SCRAPER_REGISTRY.keys())
