"""
Tokopedia scraper implementation.
Uses requests + BeautifulSoup with JSON-LD data extraction.
"""

import json
import re
from typing import Optional

from price_monitor.scraper.base import BaseScraper, ScraperResult
from price_monitor.utils.logger import logger
from price_monitor.utils.validators import parse_price


class TokopediaScraper(BaseScraper):
    """
    Scraper for Tokopedia products.

    Tokopedia uses heavy JavaScript, but some data is available
    in JSON-LD structured data and meta tags.
    """

    SITE_NAME = "tokopedia"
    SUPPORTED_DOMAINS = ["tokopedia.com", "tokopedia.co.id"]

    def get_price(self, url: str) -> ScraperResult:
        """
        Get price from Tokopedia product page.

        Strategy:
        1. Try JSON-LD structured data (most reliable)
        2. Try meta tags
        3. Try JSON data in script tags
        4. Fall back to HTML elements

        Args:
            url: Tokopedia product URL

        Returns:
            ScraperResult with price information
        """
        # Clean URL (remove tracking parameters)
        clean_url = self._clean_url(url)

        response = self._make_request(clean_url)
        if not response:
            return ScraperResult(
                success=False,
                error="Failed to fetch page",
            )

        soup = self._parse_html(response)

        # Try JSON-LD first (most reliable for pricing)
        price = self._extract_price_from_json_ld(soup)
        if price:
            name = self._extract_name_from_json_ld(soup)
            return ScraperResult(
                success=True,
                price=price,
                name=name,
                currency="Rp",
            )

        # Try extracting from window.__NEXT_DATA__ (Next.js data)
        price = self._extract_price_from_next_data(soup)
        if price:
            name = self._extract_name_from_next_data(soup)
            return ScraperResult(
                success=True,
                price=price,
                name=name,
                currency="Rp",
            )

        # Try meta tags
        price = self._extract_price_from_meta(soup)
        if price:
            name = self._extract_meta(soup, "og:title")
            return ScraperResult(
                success=True,
                price=price,
                name=name,
                currency="Rp",
            )

        # Try HTML elements (less reliable)
        price = self._extract_price_from_html(soup)
        if price:
            name = self._extract_name_from_html(soup)
            return ScraperResult(
                success=True,
                price=price,
                name=name,
                currency="Rp",
            )

        return ScraperResult(
            success=False,
            error="Could not extract price from page",
        )

    def get_product_name(self, url: str) -> Optional[str]:
        """Get product name from Tokopedia URL."""
        clean_url = self._clean_url(url)
        response = self._make_request(clean_url)
        if not response:
            return None

        soup = self._parse_html(response)

        # Try JSON-LD
        name = self._extract_name_from_json_ld(soup)
        if name:
            return name

        # Try Next.js data
        name = self._extract_name_from_next_data(soup)
        if name:
            return name

        # Try meta tags
        name = self._extract_meta(soup, "og:title")
        if name:
            # Clean up title (remove " | Tokopedia" suffix)
            name = re.sub(r"\s*\|\s*Tokopedia\s*$", "", name, flags=re.IGNORECASE)
            return name

        # Try HTML title
        title = soup.find("title")
        if title:
            name = title.string
            name = re.sub(r"\s*\|\s*Tokopedia\s*$", "", name or "", flags=re.IGNORECASE)
            return name.strip() if name else None

        return None

    def _clean_url(self, url: str) -> str:
        """Clean Tokopedia URL by removing tracking parameters."""
        # Remove query parameters that are not needed
        if "?" in url:
            base_url = url.split("?")[0]
            return base_url
        return url

    def _extract_price_from_json_ld(self, soup) -> Optional[float]:
        """Extract price from JSON-LD structured data."""
        try:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                data = json.loads(script.string or "{}")

                # Check for Product type directly
                if data.get("@type") == "Product":
                    offers = data.get("offers", {})
                    price_str = offers.get("price")
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
        """Extract product name from JSON-LD structured data."""
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

    def _extract_price_from_next_data(self, soup) -> Optional[float]:
        """Extract price from Next.js __NEXT_DATA__."""
        try:
            script = soup.find("script", id="__NEXT_DATA__")
            if not script:
                return None

            data = json.loads(script.string or "{}")
            props = data.get("props", {}).get("initialProps", {}).get("pageProps", {})

            # Navigate to product data
            product_data = props.get("data", {}).get("pdpGetPDP", {}).get("basicInfo", {})

            price_str = product_data.get("price") or product_data.get("priceValue")
            if price_str:
                return parse_price(str(price_str))

            # Alternative path
            variants = props.get("data", {}).get("pdpGetPDP", {}).get("variants", [])
            if variants:
                price_str = variants[0].get("price")
                if price_str:
                    return parse_price(str(price_str))

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"Next.js data parsing error: {e}")

        return None

    def _extract_name_from_next_data(self, soup) -> Optional[str]:
        """Extract product name from Next.js __NEXT_DATA__."""
        try:
            script = soup.find("script", id="__NEXT_DATA__")
            if not script:
                return None

            data = json.loads(script.string or "{}")
            props = data.get("props", {}).get("initialProps", {}).get("pageProps", {})
            product_data = props.get("data", {}).get("pdpGetPDP", {}).get("basicInfo", {})

            return product_data.get("name")

        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        return None

    def _extract_price_from_meta(self, soup) -> Optional[float]:
        """Extract price from meta tags."""
        # Try various meta tags
        meta_tags = [
            ("product:price:amount", None),
            ("price", None),
            ("twitter:data1", None),
            ("og:price:amount", None),
        ]

        for tag_name, attribute in meta_tags:
            meta = soup.find("meta", property=tag_name) or soup.find("meta", attrs={"name": tag_name})
            if meta:
                content = meta.get("content")
                if content:
                    price = parse_price(content)
                    if price:
                        return price

        return None

    def _extract_price_from_html(self, soup) -> Optional[float]:
        """Extract price from HTML elements (last resort)."""
        # Common price selectors for Tokopedia
        price_selectors = [
            '[data-testid="lblPDPDetailProductPrice"]',
            '[data-testid="lblProductPrice"]',
            '.price',
            '[class*="price"]',
        ]

        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and any(c.isdigit() for c in text):
                    price = parse_price(text)
                    if price and price > 0:
                        return price

        return None

    def _extract_name_from_html(self, soup) -> Optional[str]:
        """Extract product name from HTML elements."""
        name_selectors = [
            '[data-testid="lblPDPDetailProductName"]',
            '[data-testid="lblProductName"]',
            'h1[class*="title"]',
            'h1',
        ]

        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name:
                    return name

        return None
