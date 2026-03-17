"""
Email notification service.
Sends price alerts via SMTP.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from price_monitor.config import settings
from price_monitor.utils.logger import logger


class EmailNotifier:
    """
    Email notification client using SMTP.

    Sends HTML and plain text emails for price alerts.
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        email_from: Optional[str] = None,
        email_to: Optional[str] = None,
    ):
        """
        Initialize Email notifier.

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            email_from: Sender email address
            email_to: Recipient email address
        """
        self.smtp_host = smtp_host or settings.smtp_host
        self.smtp_port = smtp_port or settings.smtp_port
        self.smtp_user = smtp_user or settings.smtp_user
        self.smtp_password = smtp_password or settings.smtp_password
        self.email_from = email_from or settings.email_from
        self.email_to = email_to or settings.email_to

        if not self._is_configured:
            logger.warning("Email credentials not configured. Email notifications will be disabled.")

    @property
    def _is_configured(self) -> bool:
        """Check if email is properly configured."""
        return all(
            [
                self.smtp_host,
                self.smtp_port,
                self.smtp_user,
                self.smtp_password,
                self.email_from,
                self.email_to,
            ]
        )

    def send_email(
        self,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body (optional)

        Returns:
            True if email was sent successfully
        """
        if not self._is_configured:
            logger.warning("Email not configured, skipping email")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = self.email_to

            # Add plain text part
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))

            # Add HTML part
            msg.attach(MIMEText(body_html, "html"))

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.email_from, self.email_to, msg.as_string())

            logger.debug(f"Email sent to {self.email_to}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email: {e}")
            return False
        except Exception as e:
            logger.error(f"Email error: {e}")
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
        Send price alert email.

        Args:
            product_name: Product name
            current_price: Current price
            target_price: Target price
            url: Product URL
            site: Site name
            currency: Currency symbol

        Returns:
            True if email was sent successfully
        """
        savings = target_price - current_price
        savings_pct = (savings / target_price) * 100 if target_price > 0 else 0

        # Format prices
        current_str = f"{currency} {current_price:,.0f}".replace(",", ".")
        target_str = f"{currency} {target_price:,.0f}".replace(",", ".")
        savings_str = f"{currency} {savings:,.0f}".replace(",", ".")

        subject = f"📉 Price Alert: {product_name[:50]}"

        # Plain text version
        body_text = (
            f"PRICE ALERT!\n\n"
            f"Product: {product_name}\n"
            f"Site: {site}\n\n"
            f"Current Price: {current_str}\n"
            f"Target Price: {target_str}\n"
            f"Savings: {savings_str} ({savings_pct:.1f}%)\n\n"
            f"URL: {url}\n\n"
            f"Price dropped below your target!"
        )

        # HTML version
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">📉 PRICE ALERT!</h1>
            </div>
            <div style="padding: 20px; background-color: #f9f9f9;">
                <h2 style="color: #333;">{product_name}</h2>
                {f'<p style="color: #666;">🏪 {site}</p>' if site else ''}
                
                <table style="width: 100%; margin: 20px 0;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Current Price:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; color: #4CAF50; font-size: 1.2em;"><strong>{current_str}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">Target Price:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{target_str}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">You Save:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; color: #4CAF50;"><strong>{savings_str}</strong> ({savings_pct:.1f}%)</td>
                    </tr>
                </table>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{url}" style="background-color: #2196F3; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">View Product</a>
                </p>
                
                <p style="color: #666; font-size: 0.9em; text-align: center;">
                    <em>Price dropped below your target!</em>
                </p>
            </div>
            <div style="background-color: #333; color: #999; padding: 10px; text-align: center; font-size: 0.8em;">
                <p>Price Monitor Bot - Automated price tracking</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(subject, body_html, body_text)

    def test_connection(self) -> tuple[bool, str]:
        """
        Test SMTP connection.

        Returns:
            Tuple of (success, message)
        """
        if not self._is_configured:
            return False, "Email not configured"

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
            return True, "SMTP connection successful"
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {e}"
        except Exception as e:
            return False, f"Connection error: {e}"


# Global email notifier instance
email_notifier = EmailNotifier()
