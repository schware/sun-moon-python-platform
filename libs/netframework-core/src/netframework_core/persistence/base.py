from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base. Each service's ORM models
    (infrastructure/models.py) inherit from this so `create_all` picks up
    every table that service defines — there's no cross-service sharing
    here despite the common import, since each service runs as its own
    process with its own copy of this class's metadata."""
