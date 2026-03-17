"""
SQLAlchemy database models for price monitoring.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker

from price_monitor.config import settings

Base = declarative_base()


class Product(Base):
    """
    Product model representing a monitored product.

    Stores product information including URL, target price for notifications,
    and scheduling preferences.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=True)
    site: Mapped[str] = mapped_column(String(50), nullable=True)

    # Pricing
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="Rp")

    # Scheduling
    check_interval: Mapped[int] = mapped_column(
        Integer, default=360
    )  # minutes (default: 6 hours)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_notified: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    price_history: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Product(id={self.id}, name='{self.name}', "
            f"current={self.current_price}, target={self.target_price})>"
        )

    @property
    def status(self) -> str:
        """Get product monitoring status."""
        if not self.is_active:
            return "paused"
        if self.current_price is None:
            return "pending"
        if self.current_price <= self.target_price:
            return "below_target"
        return "above_target"

    @property
    def price_difference(self) -> Optional[float]:
        """Calculate difference between current and target price."""
        if self.current_price is None:
            return None
        return self.current_price - self.target_price

    @property
    def savings_percentage(self) -> Optional[float]:
        """Calculate savings percentage if below target."""
        if self.current_price is None or self.current_price > self.target_price:
            return None
        if self.target_price == 0:
            return None
        return ((self.target_price - self.current_price) / self.target_price) * 100


class PriceHistory(Base):
    """
    Price history model for tracking price changes over time.

    Records each price check result for trend analysis.
    """

    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="Rp")
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Additional data
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="price_history")

    def __repr__(self) -> str:
        return f"<PriceHistory(id={self.id}, price={self.price}, checked_at={self.checked_at})>"


class NotificationLog(Base):
    """
    Notification log model for tracking sent notifications.
    """

    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # telegram, email
    message: Mapped[str] = mapped_column(Text, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<NotificationLog(id={self.id}, channel={self.channel}, success={self.success})>"


# Database engine and session
engine = None
SessionLocal = None


def init_db(database_url: Optional[str] = None) -> None:
    """
    Initialize database connection and create tables.

    Args:
        database_url: Database connection URL (defaults to settings.DATABASE_URL)
    """
    global engine, SessionLocal

    db_url = database_url or settings.database_url
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get database session."""
    if SessionLocal is None:
        init_db()
    return SessionLocal()
