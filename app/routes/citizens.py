"""Citizen record endpoints.

This router exposes an endpoint for updating individual citizen records. Upon
update, the record is revalidated and its status adjusted accordingly.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models.models import Citizen, FileStatus
from app.schemas.citizen import CitizenUpdate, CitizenOut
from app.services.utils import (
    validate_thai_cid,
    parse_thai_date,
    compute_age_years,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.put("/citizens/{citizen_id}", response_model=CitizenOut)
def update_citizen(
    citizen_id: int = Path(..., description="ID of the citizen record to update"),
    payload: CitizenUpdate = ...,  # Pydantic will parse JSON body
    db: Session = Depends(get_db),
):
    """Update a citizen record and revalidate it.

    Any provided fields will overwrite the existing values. After update the
    record is revalidated: the citizen ID checksum is checked, dates are
    parsed and age is recalculated. If validation passes the status becomes
    ``corrected``; otherwise it remains ``review``.
    """
    citizen = db.query(Citizen).get(citizen_id)
    if not citizen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citizen not found")
    # Update provided fields
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(citizen, field, value)
    # Revalidate
    errors = []
    # Validate cid
    if citizen.cid:
        if not validate_thai_cid(citizen.cid):
            errors.append("เลขบัตรประชาชนไม่ถูกต้อง")
    else:
        errors.append("ไม่พบเลขบัตรประชาชน")
    # Parse dates if they are strings
    dob = citizen.dob
    reg_date = citizen.register_date
    if isinstance(dob, str):
        parsed = parse_thai_date(dob)
        if parsed:
            citizen.dob = parsed
            dob = parsed
        else:
            errors.append(f"รูปแบบวันเกิดไม่ถูกต้อง: {dob}")
            citizen.dob = None
    if isinstance(reg_date, str):
        parsed = parse_thai_date(reg_date)
        if parsed:
            citizen.register_date = parsed
            reg_date = parsed
        else:
            errors.append(f"รูปแบบวันลงทะเบียนไม่ถูกต้อง: {reg_date}")
            citizen.register_date = None
    # Recompute age
    if citizen.dob and citizen.register_date:
        citizen.age_years = compute_age_years(citizen.dob, citizen.register_date)
    else:
        citizen.age_years = None
    # Basic phone length check
    if citizen.phone and len(citizen.phone) not in (9, 10):
        errors.append("หมายเลขโทรศัพท์ไม่ถูกต้อง")
    if errors:
        citizen.status = FileStatus.review
        citizen.error_reason = "; ".join(errors)
    else:
        citizen.status = FileStatus.corrected if citizen.status != FileStatus.valid else FileStatus.valid
        citizen.error_reason = None
    db.add(citizen)
    db.commit()
    db.refresh(citizen)
    return CitizenOut.from_orm(citizen)