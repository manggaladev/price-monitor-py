"""
CRUD operations for price monitoring database.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from price_monitor.database.models import (
    NotificationLog,
    PriceHistory,
    Product,
    get_session,
)


class ProductCRUD:
    """CRUD operations for Product model."""

    @staticmethod
    def create(
        url: str,
        target_price: float,
        name: Optional[str] = None,
        site: Optional[str] = None,
        check_interval: int = 360,
        notes: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> Product:
        """
        Create a new product.

        Args:
            url: Product URL
            target_price: Target price for notifications
            name: Product name (optional, can be fetched later)
            site: E-commerce site name
            check_interval: Check interval in minutes
            notes: Additional notes
            session: Database session

        Returns:
            Created product instance
        """
        if session is None:
            session = get_session()

        product = Product(
            url=url,
            name=name,
            site=site,
            target_price=target_price,
            check_interval=check_interval,
            notes=notes,
        )
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    @staticmethod
    def get_by_id(product_id: int, session: Optional[Session] = None) -> Optional[Product]:
        """Get product by ID."""
        if session is None:
            session = get_session()
        return session.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def get_by_url(url: str, session: Optional[Session] = None) -> Optional[Product]:
        """Get product by URL."""
        if session is None:
            session = get_session()
        return session.query(Product).filter(Product.url == url).first()

    @staticmethod
    def get_all(
        active_only: bool = False,
        session: Optional[Session] = None,
    ) -> List[Product]:
        """Get all products."""
        if session is None:
            session = get_session()
        query = session.query(Product)
        if active_only:
            query = query.filter(Product.is_active == True)
        return query.order_by(Product.created_at.desc()).all()

    @staticmethod
    def get_for_check(session: Optional[Session] = None) -> List[Product]:
        """
        Get products that need to be checked.

        Returns products that:
        - Are active
        - Haven't been checked in their check_interval
        """
        if session is None:
            session = get_session()

        now = datetime.utcnow()
        products = session.query(Product).filter(
            and_(
                Product.is_active == True,
                Product.last_checked.is_(None) | (
                    Product.last_checked + timedelta(minutes=Product.check_interval) <= now
                ),
            )
        ).all()
        return products

    @staticmethod
    def update(
        product_id: int,
        session: Optional[Session] = None,
        **kwargs,
    ) -> Optional[Product]:
        """
        Update product fields.

        Args:
            product_id: Product ID
            session: Database session
            **kwargs: Fields to update

        Returns:
            Updated product or None if not found
        """
        if session is None:
            session = get_session()

        product = session.query(Product).filter(Product.id == product_id).first()
        if product:
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            session.commit()
            session.refresh(product)
        return product

    @staticmethod
    def update_price(
        product_id: int,
        price: float,
        session: Optional[Session] = None,
    ) -> Optional[Product]:
        """
        Update product current price and record history.

        Args:
            product_id: Product ID
            price: New price
            session: Database session

        Returns:
            Updated product
        """
        if session is None:
            session = get_session()

        product = session.query(Product).filter(Product.id == product_id).first()
        if product:
            product.current_price = price
            product.last_checked = datetime.utcnow()
            session.commit()
            session.refresh(product)
        return product

    @staticmethod
    def delete(product_id: int, session: Optional[Session] = None) -> bool:
        """Delete product by ID."""
        if session is None:
            session = get_session()

        product = session.query(Product).filter(Product.id == product_id).first()
        if product:
            session.delete(product)
            session.commit()
            return True
        return False


class PriceHistoryCRUD:
    """CRUD operations for PriceHistory model."""

    @staticmethod
    def create(
        product_id: int,
        price: float,
        available: bool = True,
        notes: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> PriceHistory:
        """Create a new price history entry."""
        if session is None:
            session = get_session()

        history = PriceHistory(
            product_id=product_id,
            price=price,
            available=available,
            notes=notes,
        )
        session.add(history)
        session.commit()
        session.refresh(history)
        return history

    @staticmethod
    def get_by_product(
        product_id: int,
        limit: int = 100,
        session: Optional[Session] = None,
    ) -> List[PriceHistory]:
        """Get price history for a product."""
        if session is None:
            session = get_session()
        return (
            session.query(PriceHistory)
            .filter(PriceHistory.product_id == product_id)
            .order_by(desc(PriceHistory.checked_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_latest(
        product_id: int,
        session: Optional[Session] = None,
    ) -> Optional[PriceHistory]:
        """Get latest price history entry for a product."""
        if session is None:
            session = get_session()
        return (
            session.query(PriceHistory)
            .filter(PriceHistory.product_id == product_id)
            .order_by(desc(PriceHistory.checked_at))
            .first()
        )


class NotificationLogCRUD:
    """CRUD operations for NotificationLog model."""

    @staticmethod
    def create(
        product_id: int,
        channel: str,
        message: str,
        success: bool = True,
        error: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> NotificationLog:
        """Create a notification log entry."""
        if session is None:
            session = get_session()

        log = NotificationLog(
            product_id=product_id,
            channel=channel,
            message=message,
            success=success,
            error=error,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log

    @staticmethod
    def get_recent(
        product_id: Optional[int] = None,
        limit: int = 50,
        session: Optional[Session] = None,
    ) -> List[NotificationLog]:
        """Get recent notification logs."""
        if session is None:
            session = get_session()

        query = session.query(NotificationLog)
        if product_id:
            query = query.filter(NotificationLog.product_id == product_id)
        return query.order_by(desc(NotificationLog.sent_at)).limit(limit).all()
