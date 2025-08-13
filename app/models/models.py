"""SQLAlchemy models for the elderdocs application.

These models define the database schema used by the FastAPI service. The
schema captures metadata about uploaded PDF documents and the extracted
citizen records. Each PDF belongs to a batch and yields a single citizen
record once processed. Status flags record whether the record is valid,
requires review, has been corrected, or has been exported.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, Enum as SAEnum
from enum import Enum  # Built‑in Enum for our FileStatus class
from sqlalchemy.orm import relationship

from .database import Base


class FileStatus(str, Enum):
    """Enumeration of possible processing states for a citizen record."""

    pending = "pending"
    valid = "valid"
    review = "review"
    corrected = "corrected"
    exported = "exported"


class Batch(Base):
    """Represents a batch of uploaded PDF files.

    A batch groups together a set of PDF documents uploaded in a single request.
    """

    __tablename__ = "batches"

    # Allow unmapped attributes on SQLAlchemy 2.0. Without this flag,
    # SQLAlchemy will enforce the use of Annotated types or Mapped[] for
    # relationships and optional columns. Setting this to True allows the
    # legacy style annotations to pass without raising an error.
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    created_at: dt.datetime = Column(DateTime, default=dt.datetime.utcnow)

    citizens: list[Citizen] = relationship(
        "Citizen", back_populates="batch", cascade="all, delete-orphan"
    )


class Citizen(Base):
    """Represents a citizen record extracted from a PDF document."""

    __tablename__ = "citizens"

    # Allow unmapped attributes. See comment on Batch for details.
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    batch_id: int = Column(Integer, ForeignKey("batches.id"), nullable=True)
    cid: Optional[str] = Column(String(13), nullable=True)
    prefix: Optional[str] = Column(String(32), nullable=True)
    first_name: Optional[str] = Column(String(64), nullable=True)
    last_name: Optional[str] = Column(String(64), nullable=True)
    dob: Optional[dt.date] = Column(Date, nullable=True)
    phone: Optional[str] = Column(String(16), nullable=True)
    address_full: Optional[str] = Column(Text, nullable=True)
    register_date: Optional[dt.date] = Column(Date, nullable=True)
    age_years: Optional[int] = Column(Integer, nullable=True)
    status: FileStatus = Column(SAEnum(FileStatus), default=FileStatus.pending, nullable=False)
    error_reason: Optional[str] = Column(Text, nullable=True)
    file_path: Optional[str] = Column(String(256), nullable=True)
    sanitized_filename: Optional[str] = Column(String(128), nullable=True)
    created_at: dt.datetime = Column(DateTime, default=dt.datetime.utcnow)
    updated_at: dt.datetime = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    batch: Batch = relationship("Batch", back_populates="citizens")