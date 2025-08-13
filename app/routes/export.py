"""Export endpoint.

Provides an endpoint that triggers export of validated/corrected records
to CSV and Excel and archives their PDFs. The operation is synchronous
and may take some time depending on the number of records.
"""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.services.pdf_processor import export_records

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/export", response_model=Dict[str, str])
def export_data(db: Session = Depends(get_db)) -> Dict[str, str]:
    """Export all valid and corrected records.

    Returns a dictionary with keys ``csv`` and ``xlsx`` pointing at the
    generated files. If there are no records to export a 404 error is
    returned.
    """
    result = export_records(db)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No records to export")
    return result