"""Database setup module.

This module initialises the SQLAlchemy engine and session factory. It also
provides a convenience function to create all database tables defined in
the models. SQLite is used as the backing store for simplicity; the
connection string can be adjusted to point at any supported SQLAlchemy
database backend.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Use a file-based SQLite database. When running in production you may
# substitute this URL for another engine (e.g. PostgreSQL) as needed.
DATABASE_URL = "sqlite:///./elderdocs.db"

# The connect_args flag disables thread checking for SQLite so that the same
# connection can be shared across threads in a FastAPI context.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SQLAlchemy 2.0 declarative base class.
class Base(DeclarativeBase):
    pass

# Session factory for request-scoped sessions.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Create all tables in the database.

    This function should be called once when the application starts.
    """
    from .models import Batch, Citizen  # noqa: F401
    Base.metadata.create_all(bind=engine)