"""
Task scheduler using APScheduler.
Handles periodic price checks and notifications.
"""

import signal
import sys
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from price_monitor.config import settings
from price_monitor.database import ProductCRUD, PriceHistoryCRUD, init_db
from price_monitor.notifier import send_notification
from price_monitor.scraper.utils import get_scraper
from price_monitor.utils.logger import logger


class PriceMonitorScheduler:
    """
    Scheduler for periodic price monitoring.

    Uses APScheduler to run price checks at specified intervals.
    """

    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BackgroundScheduler()
        self._running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        # Initialize database
        init_db()

        # Load and schedule all active products
        self._schedule_all_products()

        # Add periodic job to check for new products
        self.scheduler.add_job(
            self._refresh_schedules,
            trigger=IntervalTrigger(minutes=30),
            id="_refresh_schedules",
            name="Refresh product schedules",
            replace_existing=True,
        )

        # Start scheduler
        self.scheduler.start()
        self._running = True

        logger.info("Scheduler started successfully")

    def stop(self):
        """Stop the scheduler."""
        if self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Scheduler stopped")

    def _schedule_all_products(self):
        """Load all active products and schedule jobs for them."""
        products = ProductCRUD.get_all(active_only=True)

        for product in products:
            self._schedule_product(product.id, product.check_interval)

        logger.info(f"Scheduled {len(products)} products for monitoring")

    def _schedule_product(self, product_id: int, interval_minutes: int):
        """Schedule a single product for monitoring."""
        job_id = f"check_product_{product_id}"

        # Remove existing job if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Add new job
        self.scheduler.add_job(
            self._check_product,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            name=f"Check product {product_id}",
            args=[product_id],
            replace_existing=True,
        )

        logger.debug(f"Scheduled product {product_id} with interval {interval_minutes} minutes")

    def _refresh_schedules(self):
        """Refresh schedules for all products."""
        logger.debug("Refreshing product schedules...")

        products = ProductCRUD.get_all(active_only=True)
        scheduled_ids = {int(j.id.split("_")[-1]) for j in self.scheduler.get_jobs() if j.id.startswith("check_product_")}
        active_ids = {p.id for p in products}

        # Add new products
        for product in products:
            if product.id not in scheduled_ids:
                self._schedule_product(product.id, product.check_interval)
                logger.info(f"Added new product {product.id} to schedule")

        # Remove inactive products
        for job_id in scheduled_ids - active_ids:
            self.scheduler.remove_job(f"check_product_{job_id}")
            logger.info(f"Removed inactive product {job_id} from schedule")

    def _check_product(self, product_id: int):
        """
        Check price for a single product.

        Args:
            product_id: Product ID to check
        """
        logger.debug(f"Checking product {product_id}...")

        # Get product from database
        product = ProductCRUD.get_by_id(product_id)
        if not product:
            logger.warning(f"Product {product_id} not found, removing from schedule")
            self.scheduler.remove_job(f"check_product_{product_id}")
            return

        if not product.is_active:
            logger.debug(f"Product {product_id} is inactive, skipping")
            return

        # Get scraper for the product
        scraper = get_scraper(product.url)
        if not scraper:
            logger.error(f"No scraper available for {product.url}")
            return

        try:
            # Scrape price
            result = scraper.get_price(product.url)

            if not result.success:
                logger.error(f"Failed to scrape {product.name}: {result.error}")
                # Record failed attempt
                PriceHistoryCRUD.create(
                    product_id=product.id,
                    price=0,
                    available=False,
                    notes=result.error,
                )
                return

            current_price = result.price
            logger.info(f"Product '{product.name}' - Current: Rp {current_price:,.0f}, Target: Rp {product.target_price:,.0f}")

            # Update product name if empty and we got one
            if not product.name and result.name:
                ProductCRUD.update(product.id, name=result.name)

            # Record price history
            PriceHistoryCRUD.create(
                product_id=product.id,
                price=current_price,
                available=result.available,
            )

            # Update current price and last checked
            ProductCRUD.update(
                product.id,
                current_price=current_price,
                last_checked=datetime.utcnow(),
            )

            # Check if price is at or below target
            if result.available and current_price <= product.target_price:
                logger.warning(f"🎯 Price alert triggered for {product.name}!")

                # Send notification
                send_notification(
                    product_name=product.name or result.name or "Unknown Product",
                    current_price=current_price,
                    target_price=product.target_price,
                    url=product.url,
                    site=product.site or "",
                )

                # Update last notified
                ProductCRUD.update(product.id, last_notified=datetime.utcnow())

        except Exception as e:
            logger.error(f"Error checking product {product_id}: {e}", exc_info=True)

    def run_once(self):
        """Run a single check for all active products."""
        init_db()

        products = ProductCRUD.get_all(active_only=True)

        logger.info(f"Running one-time check for {len(products)} products...")

        for product in products:
            self._check_product(product.id)

        logger.info("One-time check completed")

    def check_product_now(self, product_id: int):
        """Immediately check a specific product."""
        init_db()
        self._check_product(product_id)


# Global scheduler instance
scheduler = PriceMonitorScheduler()


def run_scheduler():
    """Run the scheduler in foreground (blocking)."""
    scheduler.start()

    logger.info("Scheduler running. Press Ctrl+C to stop.")

    try:
        # Keep main thread alive
        while scheduler._running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        scheduler.stop()


if __name__ == "__main__":
    run_scheduler()
