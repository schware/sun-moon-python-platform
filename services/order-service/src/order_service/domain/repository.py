from __future__ import annotations

from netframework_core.ddd.repository import Repository
from order_service.domain.entities import Order


class OrderRepository(Repository[Order, str]):
    """Domain-facing port; see infrastructure/repository_impl.py for the
    SQLAlchemy adapter."""
