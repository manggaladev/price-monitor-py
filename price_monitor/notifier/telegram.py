"""
Telegram notification service.
Sends price alerts via Telegram Bot API.
"""

import asyncio
from typing import Optional

import requests

from price_monitor.config import settings
from price_monitor.utils.logger import logger


class TelegramNotifier:
    """
    Telegram notification client using Bot API.

    Sends messages through Telegram bot to specified chat.
    """

    API_URL = "https://api.telegram.org/bot{token}/{method}"
    MAX_MESSAGE_LENGTH = 4096

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token (defaults to settings)
            chat_id: Target chat/user ID (defaults to settings)
        """
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured. Notifications will be disabled.")

    @property
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return bool(self.bot_token and self.chat_id)

    def _get_api_url(self, method: str) -> str:
        """Get full API URL for a method."""
        return self.API_URL.format(token=self.bot_token, method=method)

    def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> bool:
        """
        Send a text message.

        Args:
            text: Message text (supports HTML/Markdown)
            parse_mode: Parse mode (HTML, Markdown, MarkdownV2)
            disable_notification: Send silently without notification

        Returns:
            True if message was sent successfully
        """
        if not self.is_configured:
            logger.warning("Telegram not configured, skipping message")
            return False

        # Truncate message if too long
        if len(text) > self.MAX_MESSAGE_LENGTH:
            text = text[: self.MAX_MESSAGE_LENGTH - 3] + "..."

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }

        try:
            response = requests.post(
                self._get_api_url("sendMessage"),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                logger.debug(f"Telegram message sent to {self.chat_id}")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_price_alert(
        self,
        product_name: str,
        current_price: float,
        target_price: float,
        url: str,
        site: str = "",
        currency: str = "Rp",
    ) -> bool:
        """
        Send price alert notification.

        Args:
            product_name: Product name
            current_price: Current price
            target_price: Target price
            url: Product URL
            site: Site name (e.g., 'Tokopedia')
            currency: Currency symbol

        Returns:
            True if notification was sent successfully
        """
        # Calculate savings
        savings = target_price - current_price
        savings_pct = (savings / target_price) * 100 if target_price > 0 else 0

        # Format prices
        current_str = f"{currency} {current_price:,.0f}".replace(",", ".")
        target_str = f"{currency} {target_price:,.0f}".replace(",", ".")
        savings_str = f"{currency} {savings:,.0f}".replace(",", ".")

        # Truncate product name if too long
        if len(product_name) > 100:
            product_name = product_name[:97] + "..."

        message = (
            f"📉 <b>PRICE ALERT!</b>\n\n"
            f"<b>{product_name}</b>\n"
            f"{'🏪 ' + site if site else ''}\n\n"
            f"💰 Current: <b>{current_str}</b>\n"
            f"🎯 Target: {target_str}\n"
            f"💚 Savings: {savings_str} ({savings_pct:.1f}%)\n\n"
            f"🔗 <a href=\"{url}\">View Product</a>\n\n"
            f"<i>Price dropped below your target!</i>"
        )

        return self.send_message(message)

    def send_daily_summary(
        self,
        products_checked: int,
        price_drops: int,
        alerts_sent: int,
    ) -> bool:
        """
        Send daily summary notification.

        Args:
            products_checked: Number of products checked
            price_drops: Number of price drops detected
            alerts_sent: Number of alerts sent

        Returns:
            True if notification was sent successfully
        """
        message = (
            f"📊 <b>Daily Summary</b>\n\n"
            f"✅ Products checked: {products_checked}\n"
            f"📉 Price drops: {price_drops}\n"
            f"🔔 Alerts sent: {alerts_sent}\n\n"
            f"<i>Price Monitor Bot</i>"
        )

        return self.send_message(message)

    def send_error_alert(self, error_message: str, context: str = "") -> bool:
        """
        Send error notification.

        Args:
            error_message: Error message
            context: Additional context

        Returns:
            True if notification was sent successfully
        """
        message = (
            f"⚠️ <b>Error Alert</b>\n\n"
            f"{error_message}\n"
            f"{f'Context: {context}' if context else ''}\n\n"
            f"<i>Please check the logs for details.</i>"
        )

        return self.send_message(message)

    def test_connection(self) -> tuple[bool, str]:
        """
        Test Telegram bot connection.

        Returns:
            Tuple of (success, message)
        """
        if not self.is_configured:
            return False, "Telegram not configured"

        try:
            response = requests.get(
                self._get_api_url("getMe"),
                timeout=10,
            )
            result = response.json()

            if result.get("ok"):
                bot_info = result.get("result", {})
                bot_name = bot_info.get("first_name", "Unknown")
                username = bot_info.get("username", "unknown")
                return True, f"Connected to @{username} ({bot_name})"
            else:
                return False, f"API Error: {result.get('description')}"

        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {e}"


# Global notifier instance
notifier = TelegramNotifier()


def send_telegram_message(text: str) -> bool:
    """
    Convenience function to send Telegram message.

    Args:
        text: Message text

    Returns:
        True if sent successfully
    """
    return notifier.send_message(text)


def send_price_alert(
    product_name: str,
    current_price: float,
    target_price: float,
    url: str,
    site: str = "",
    currency: str = "Rp",
) -> bool:
    """
    Convenience function to send price alert.

    Args:
        product_name: Product name
        current_price: Current price
        target_price: Target price
        url: Product URL
        site: Site name
        currency: Currency symbol

    Returns:
        True if sent successfully
    """
    return notifier.send_price_alert(
        product_name=product_name,
        current_price=current_price,
        target_price=target_price,
        url=url,
        site=site,
        currency=currency,
    )
