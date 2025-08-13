"""Files listing endpoints.

Provides an endpoint to query records filtered by status. This is useful for
finding citizens that require manual review and displaying the reason for
rejection.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models.models import Citizen, FileStatus
from app.schemas.citizen import CitizenOut

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/files", response_model=List[CitizenOut])
def list_files(
    status: Optional[FileStatus] = Query(None, description="Filter by file status"),
    db: Session = Depends(get_db),
):
    """List processed files optionally filtered by status.

    When a status is provided only records with that status are returned. If
    ``status=review`` is specified, the caller can also inspect the
    ``error_reason`` field on the returned objects.
    """
    query = db.query(Citizen)
    if status:
        query = query.filter(Citizen.status == status)
    records = query.all()
    return [CitizenOut.from_orm(r) for r in records]