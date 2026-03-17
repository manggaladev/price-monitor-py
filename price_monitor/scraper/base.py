"""
Base scraper class for e-commerce price monitoring.
Provides abstract interface and common utilities for all scrapers.
"""

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from price_monitor.config import settings
from price_monitor.utils.logger import logger


@dataclass
class ScraperResult:
    """Result of a scraping operation."""

    success: bool
    price: Optional[float] = None
    name: Optional[str] = None
    available: bool = True
    currency: str = "Rp"
    error: Optional[str] = None
    raw_price: Optional[str] = None


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.

    Provides common functionality for HTTP requests, retry logic,
    and error handling. Subclasses must implement `get_price()`.
    """

    def __init__(
        self,
        user_agent: Optional[str] = None,
        request_delay: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize scraper with configuration.

        Args:
            user_agent: Custom user agent string
            request_delay: Delay between requests in seconds
            max_retries: Maximum retry attempts
        """
        self.user_agent = user_agent or settings.user_agent
        self.request_delay = request_delay or settings.request_delay
        self.max_retries = max_retries or settings.max_retries
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def _make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs,
    ) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic and rate limiting.

        Args:
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests

        Returns:
            Response object or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                # Add random delay to avoid detection
                delay = self.request_delay + random.uniform(0, 2)
                if attempt > 0:
                    delay += attempt * 2  # Exponential backoff
                    logger.debug(f"Retry attempt {attempt + 1}/{self.max_retries}")
                time.sleep(delay)

                response = self.session.request(method, url, timeout=30, **kwargs)

                # Check for rate limiting or blocking
                if response.status_code == 429:
                    logger.warning(f"Rate limited, waiting longer...")
                    time.sleep(60)
                    continue

                if response.status_code == 403:
                    logger.warning(f"Access forbidden, may be blocked")
                    # Try with different headers
                    self._rotate_headers()
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.Timeout:
                logger.error(f"Request timeout for {url}")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

        return None

    def _rotate_headers(self) -> None:
        """Rotate request headers to avoid detection."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        ]
        self.session.headers["User-Agent"] = random.choice(user_agents)

    def _parse_html(self, response: requests.Response) -> BeautifulSoup:
        """Parse HTML response using BeautifulSoup."""
        return BeautifulSoup(response.text, "lxml")

    def _extract_json_ld(self, soup: BeautifulSoup, key: str) -> Optional[str]:
        """
        Extract data from JSON-LD structured data.

        Args:
            soup: BeautifulSoup object
            key: Key to extract from JSON-LD

        Returns:
            Extracted value or None
        """
        try:
            import json

            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if key in data:
                        return data[key]
                    # Check nested @graph
                    if "@graph" in data:
                        for item in data["@graph"]:
                            if key in item:
                                return item[key]
        except Exception as e:
            logger.debug(f"Failed to extract JSON-LD: {e}")
        return None

    def _extract_meta(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """
        Extract content from meta tag.

        Args:
            soup: BeautifulSoup object
            property_name: Meta property name (e.g., 'og:title')

        Returns:
            Meta content or None
        """
        meta = soup.find("meta", property=property_name) or soup.find(
            "meta", attrs={"name": property_name}
        )
        return meta.get("content") if meta else None

    @abstractmethod
    def get_price(self, url: str) -> ScraperResult:
        """
        Get price from product URL.

        Must be implemented by subclasses.

        Args:
            url: Product URL

        Returns:
            ScraperResult with price information
        """
        pass

    @abstractmethod
    def get_product_name(self, url: str) -> Optional[str]:
        """
        Get product name from URL.

        Must be implemented by subclasses.

        Args:
            url: Product URL

        Returns:
            Product name or None
        """
        pass

    def __del__(self):
        """Cleanup session on object destruction."""
        if hasattr(self, "session"):
            self.session.close()
