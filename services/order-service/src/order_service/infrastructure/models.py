from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from netframework_core.persistence.base import Base


class OrderModel(Base):
    """ORM shape, private to infrastructure/ — go through OrderRepository."""

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20))
    lines: Mapped[list[dict]] = mapped_column(JSON)
