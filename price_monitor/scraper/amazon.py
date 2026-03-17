"""
Amazon scraper implementation.
Supports multiple Amazon regional domains.
"""

import json
import re
from typing import Optional

from price_monitor.scraper.base import BaseScraper, ScraperResult
from price_monitor.utils.logger import logger
from price_monitor.utils.validators import parse_price


class AmazonScraper(BaseScraper):
    """
    Scraper for Amazon products.

    Supports multiple Amazon domains:
    - amazon.com
    - amazon.co.id (Indonesia)
    - amazon.co.uk (UK)
    - amazon.sg (Singapore)
    """

    SITE_NAME = "amazon"
    SUPPORTED_DOMAINS = [
        "amazon.com",
        "amazon.co.id",
        "amazon.co.uk",
        "amazon.sg",
        "amazon.de",
        "amazon.jp",
    ]

    # Currency symbols for different regions
    REGIONAL_CURRENCIES = {
        "amazon.com": "$",
        "amazon.co.id": "Rp",
        "amazon.co.uk": "£",
        "amazon.sg": "S$",
        "amazon.de": "€",
        "amazon.jp": "¥",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Amazon requires specific headers
        self.session.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
        )

    def get_price(self, url: str) -> ScraperResult:
        """
        Get price from Amazon product page.

        Strategy:
        1. Extract ASIN from URL
        2. Try JSON-LD structured data
        3. Try HTML price elements
        4. Check availability

        Args:
            url: Amazon product URL

        Returns:
            ScraperResult with price information
        """
        asin = self._extract_asin(url)
        if not asin:
            return ScraperResult(
                success=False,
                error="Could not extract ASIN from URL",
            )

        response = self._make_request(url)
        if not response:
            return ScraperResult(
                success=False,
                error="Failed to fetch page",
            )

        # Detect currency from URL domain
        currency = self._get_currency_from_url(url)
        soup = self._parse_html(response)

        # Check availability
        available = self._check_availability(soup)

        # Try JSON-LD first
        price = self._extract_price_from_json_ld(soup)
        if price:
            name = self._extract_name_from_json_ld(soup)
            return ScraperResult(
                success=True,
                price=price,
                name=name,
                available=available,
                currency=currency,
            )

        # Try HTML price elements
        price = self._extract_price_from_html(soup)
        if price:
            name = self._extract_name_from_html(soup)
            return ScraperResult(
                success=True,
                price=price,
                name=name,
                available=available,
                currency=currency,
            )

        # Check if out of stock
        if not available:
            return ScraperResult(
                success=True,
                price=None,
                available=False,
                currency=currency,
            )

        return ScraperResult(
            success=False,
            error="Could not extract price from page",
        )

    def get_product_name(self, url: str) -> Optional[str]:
        """Get product name from Amazon URL."""
        response = self._make_request(url)
        if not response:
            return None

        soup = self._parse_html(response)

        # Try JSON-LD
        name = self._extract_name_from_json_ld(soup)
        if name:
            return name

        # Try HTML title
        name = self._extract_name_from_html(soup)
        if name:
            return name

        return None

    def _extract_asin(self, url: str) -> Optional[str]:
        """
        Extract Amazon ASIN from URL.

        Examples:
        - https://amazon.com/dp/B08N5KWB9H/ -> B08N5KWB9H
        - https://amazon.com/gp/product/B08N5KWB9H/ -> B08N5KWB9H
        - https://amazon.com/product/B08N5KWB9H/ -> B08N5KWB9H
        """
        patterns = [
            r"/dp/([A-Z0-9]{10})",
            r"/gp/product/([A-Z0-9]{10})",
            r"/product/([A-Z0-9]{10})",
            r"/([A-Z0-9]{10})(?:/|\?|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _get_currency_from_url(self, url: str) -> str:
        """Get currency symbol based on Amazon domain."""
        for domain, currency in self.REGIONAL_CURRENCIES.items():
            if domain in url:
                return currency
        return "$"  # Default to USD

    def _check_availability(self, soup) -> bool:
        """Check if product is available."""
        # Look for "out of stock" indicators
        unavailable_selectors = [
            "#availability span:contains('Out of Stock')",
            "#availability span:contains('Currently unavailable')",
            "#availability span:contains('out of stock')",
            ".a-color-price:contains('Out of Stock')",
        ]

        for selector in unavailable_selectors:
            if soup.select_one(selector):
                return False

        # Look for "in stock" indicators
        in_stock = soup.find(
            "div", id="availability", string=re.compile(r"(?i)in stock|available")
        )
        if in_stock:
            return True

        # Check for add to cart button
        add_to_cart = soup.find("input", id="add-to-cart-button")
        if add_to_cart:
            return True

        # Default to True if we can't determine
        return True

    def _extract_price_from_json_ld(self, soup) -> Optional[float]:
        """Extract price from JSON-LD structured data."""
        try:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                data = json.loads(script.string or "{}")

                # Check for Product type
                if data.get("@type") == "Product":
                    offers = data.get("offers", {})
                    price_str = offers.get("price")
                    if price_str:
                        return float(price_str)

                    # Check priceSpecification
                    price_spec = offers.get("priceSpecification", {})
                    price_str = price_spec.get("price")
                    if price_str:
                        return float(price_str)

                # Check for @graph structure
                if "@graph" in data:
                    for item in data["@graph"]:
                        if item.get("@type") == "Product":
                            offers = item.get("offers", {})
                            price_str = offers.get("price")
                            if price_str:
                                return float(price_str)

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.debug(f"JSON-LD parsing error: {e}")

        return None

    def _extract_name_from_json_ld(self, soup) -> Optional[str]:
        """Extract product name from JSON-LD."""
        try:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                data = json.loads(script.string or "{}")

                if data.get("@type") == "Product":
                    return data.get("name")

                if "@graph" in data:
                    for item in data["@graph"]:
                        if item.get("@type") == "Product":
                            return item.get("name")

        except (json.JSONDecodeError, TypeError):
            pass

        return None

    def _extract_price_from_html(self, soup) -> Optional[float]:
        """Extract price from HTML elements."""
        # Amazon price selectors (in order of preference)
        price_selectors = [
            # Sale price
            ".a-price .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            # Regular price
            "#priceblock_ourprice_lbl + .a-span12 .a-color-price",
            "#priceblock_ourprice",
            ".a-price-whole",
            # Kindle price
            "#kindle-price",
            # List price
            ".a-text-strike",
            # General price class
            ".a-color-price",
        ]

        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # Skip "FREE" prices
                if "free" in text.lower():
                    continue

                price = parse_price(text)
                if price and price > 0:
                    return price

        # Alternative: try to get price from whole and fraction parts
        whole = soup.select_one(".a-price-whole")
        fraction = soup.select_one(".a-price-fraction")

        if whole:
            price_text = whole.get_text(strip=True)
            if fraction:
                price_text += "." + fraction.get_text(strip=True)
            price = parse_price(price_text)
            if price and price > 0:
                return price

        return None

    def _extract_name_from_html(self, soup) -> Optional[str]:
        """Extract product name from HTML."""
        name_selectors = [
            "#productTitle",
            "#title span",
            ".product-title",
            "h1.a-size-large",
        ]

        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name:
                    return name

        return None
