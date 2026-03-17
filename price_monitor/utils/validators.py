"""
Utility functions for validation and URL parsing.
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

from price_monitor.utils.logger import logger


# Supported e-commerce sites and their patterns
SUPPORTED_SITES = {
    "tokopedia": {
        "domains": ["tokopedia.com", "tokopedia.co.id"],
        "url_pattern": r"https?://(?:www\.)?tokopedia\.com/[\w-]+/[\w-]+",
    },
    "amazon": {
        "domains": ["amazon.com", "amazon.co.id", "amazon.co.uk", "amazon.sg"],
        "url_pattern": r"https?://(?:www\.)?amazon\.(?:com|co\.id|co\.uk|sg)/.*(?:dp|gp/product)/[\w]+",
    },
    "shopee": {
        "domains": ["shopee.co.id", "shopee.sg", "shopee.com"],
        "url_pattern": r"https?://(?:www\.)?shopee\.(?:co\.id|sg|com)/.*-i\.(\d+)\.(\d+)",
    },
    "lazada": {
        "domains": ["lazada.co.id", "lazada.com"],
        "url_pattern": r"https?://(?:www\.)?lazada\.(?:co\.id|com)/products/.*",
    },
    "bukalapak": {
        "domains": ["bukalapak.com"],
        "url_pattern": r"https?://(?:www\.)?bukalapak\.com/products/[\w-]+",
    },
}


def validate_url(url: str) -> bool:
    """
    Validate if URL is properly formatted.

    Args:
        url: URL string to validate

    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def get_site_from_url(url: str) -> Optional[str]:
    """
    Determine the e-commerce site from URL.

    Args:
        url: Product URL

    Returns:
        Site name (e.g., 'tokopedia', 'amazon') or None if unsupported
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")

        for site_name, site_info in SUPPORTED_SITES.items():
            if any(d in domain for d in site_info["domains"]):
                return site_name

        logger.warning(f"Unsupported site for URL: {url}")
        return None
    except Exception as e:
        logger.error(f"Error parsing URL {url}: {e}")
        return None


def validate_product_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate product URL and extract site information.

    Args:
        url: Product URL to validate

    Returns:
        Tuple of (is_valid, site_name, error_message)
    """
    if not validate_url(url):
        return False, None, "Invalid URL format"

    site = get_site_from_url(url)
    if not site:
        supported = ", ".join(SUPPORTED_SITES.keys())
        return False, None, f"Unsupported site. Supported sites: {supported}"

    # Check URL pattern
    site_info = SUPPORTED_SITES.get(site, {})
    pattern = site_info.get("url_pattern", "")

    if pattern and not re.match(pattern, url, re.IGNORECASE):
        logger.warning(f"URL may not be a valid product page: {url}")

    return True, site, None


def parse_price(price_str: str) -> Optional[float]:
    """
    Parse price string to float.

    Handles various formats like:
    - Rp 1.000.000
    - $1,234.56
    - 1.234.567
    - 1,234,567

    Args:
        price_str: Price string to parse

    Returns:
        Parsed price as float, or None if parsing failed
    """
    if not price_str:
        return None

    try:
        # Remove currency symbols and text
        cleaned = re.sub(r"[Rp$\s]", "", price_str.strip())

        # Handle different thousand/decimal separators
        # If contains both . and , -> last one is decimal
        if "." in cleaned and "," in cleaned:
            # Determine which is decimal separator
            last_dot = cleaned.rfind(".")
            last_comma = cleaned.rfind(",")
            if last_dot > last_comma:
                # Dot is decimal (e.g., 1,234.56)
                cleaned = cleaned.replace(",", "")
            else:
                # Comma is decimal (e.g., 1.234,56)
                cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            # Could be thousand separator or decimal
            # If only one comma and after 2 digits -> decimal
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        else:
            # Only dots - likely thousand separator
            cleaned = cleaned.replace(".", "")

        return float(cleaned) if cleaned else None

    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse price '{price_str}': {e}")
        return None


def format_price(price: float, currency: str = "Rp") -> str:
    """
    Format price with currency symbol and thousand separators.

    Args:
        price: Price value
        currency: Currency symbol (default: Rp)

    Returns:
        Formatted price string
    """
    return f"{currency} {price:,.0f}".replace(",", ".")


def sanitize_filename(name: str) -> str:
    """
    Sanitize string for use as filename.

    Args:
        name: String to sanitize

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", name)
    # Replace spaces with underscores
    sanitized = re.sub(r"\s+", "_", sanitized)
    # Limit length
    return sanitized[:200]
