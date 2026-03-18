"""
Notification services for price monitoring.
"""

from price_monitor.notifier.telegram import (
    TelegramNotifier,
    telegram_notifier,
    send_price_alert,
    send_telegram_message,
)
from price_monitor.notifier.email import (
    EmailNotifier,
    email_notifier,
)


def send_notification(
    product_name: str,
    current_price: float,
    target_price: float,
    url: str,
    site: str = "",
    currency: str = "Rp",
    channels: list[str] = None,
) -> dict[str, bool]:
    """
    Send notification through multiple channels.

    Args:
        product_name: Product name
        current_price: Current price
        target_price: Target price
        url: Product URL
        site: Site name
        currency: Currency symbol
        channels: List of channels to send (default: ['telegram'])

    Returns:
        Dict of channel -> success status
    """
    if channels is None:
        channels = ["telegram"]

    results = {}

    if "telegram" in channels:
        results["telegram"] = send_price_alert(
            product_name=product_name,
            current_price=current_price,
            target_price=target_price,
            url=url,
            site=site,
            currency=currency,
        )

    if "email" in channels:
        results["email"] = email_notifier.send_price_alert(
            product_name=product_name,
            current_price=current_price,
            target_price=target_price,
            url=url,
            site=site,
            currency=currency,
        )

    return results


__all__ = [
    # Telegram
    "TelegramNotifier",
    "telegram_notifier",
    "send_telegram_message",
    "send_price_alert",
    # Email
    "EmailNotifier",
    "email_notifier",
    # Combined
    "send_notification",
]
