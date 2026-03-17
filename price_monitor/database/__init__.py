"""
Database module for price monitoring.
"""

from price_monitor.database.models import (
    Base,
    NotificationLog,
    PriceHistory,
    Product,
    engine,
    get_session,
    init_db,
    SessionLocal,
)
from price_monitor.database.crud import (
    NotificationLogCRUD,
    PriceHistoryCRUD,
    ProductCRUD,
)

__all__ = [
    # Models
    "Base",
    "Product",
    "PriceHistory",
    "NotificationLog",
    # Database
    "engine",
    "SessionLocal",
    "init_db",
    "get_session",
    # CRUD
    "ProductCRUD",
    "PriceHistoryCRUD",
    "NotificationLogCRUD",
]
