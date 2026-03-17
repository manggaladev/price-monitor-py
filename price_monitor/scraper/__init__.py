"""
Web scrapers for e-commerce price monitoring.
"""

from price_monitor.scraper.base import BaseScraper, ScraperResult
from price_monitor.scraper.tokopedia import TokopediaScraper
from price_monitor.scraper.amazon import AmazonScraper
from price_monitor.scraper.utils import (
    get_scraper,
    get_scraper_for_site,
    get_supported_sites,
    is_supported_site,
    register_scraper,
)

__all__ = [
    # Base
    "BaseScraper",
    "ScraperResult",
    # Scrapers
    "TokopediaScraper",
    "AmazonScraper",
    # Utils
    "get_scraper",
    "get_scraper_for_site",
    "get_supported_sites",
    "is_supported_site",
    "register_scraper",
]
