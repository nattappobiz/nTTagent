"""Pydantic schemas for the Citizen resource.

These schemas define the request and response models used by the API
endpoints dealing with citizen records. Pydantic models handle validation
and serialisation of field types such as dates and enumerations.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field

from app.models.models import FileStatus


class CitizenBase(BaseModel):
    cid: Optional[str] = Field(None, min_length=13, max_length=13)
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[dt.date] = None
    phone: Optional[str] = None
    address_full: Optional[str] = None
    register_date: Optional[dt.date] = None
    age_years: Optional[int] = None

    class Config:
        # Use from_attributes in Pydantic v2 to allow ORM object conversion
        from_attributes = True


class CitizenCreate(CitizenBase):
    pass


class CitizenUpdate(CitizenBase):
    """Model for updating citizen details via PUT.

    All fields are optional; only provided fields will be updated. Upon
    update the record will be revalidated by the service to adjust its status.
    """

    pass


class CitizenOut(CitizenBase):
    id: int
    status: FileStatus
    error_reason: Optional[str] = None
    sanitized_filename: Optional[str] = None

    class Config(CitizenBase.Config):
        pass