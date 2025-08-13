"""PDF processing and export services.

This module contains functions responsible for parsing uploaded PDF files,
extracting citizen information, validating the extracted data and persisting
records into the database. It also implements CSV/Excel export and archival
behaviour as required by the specification.
"""

from __future__ import annotations

import csv
import datetime as dt
import logging
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:
    import pdfplumber  # type: ignore[import]
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore
import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import Citizen, FileStatus, Batch
from app.services.utils import (
    parse_thai_date,
    validate_thai_cid,
    compute_age_years,
    sanitize_filename,
)
from app.config import get_config

logger = logging.getLogger(__name__)


def extract_fields(text: str) -> Dict[str, Optional[str]]:
    """Extract citizen fields from the given text.

    The extraction logic uses simple regular expressions tuned to Thai
    administrative documents. It is intentionally conservative; if a value
    cannot be confidently extracted it will be returned as ``None``. The
    calling code should handle missing values appropriately.

    Parameters
    ----------
    text: str
        The full extracted text from a PDF.

    Returns
    -------
    dict
        A dictionary with keys corresponding to expected citizen fields.
    """
    result: Dict[str, Optional[str]] = {
        "cid": None,
        "prefix": None,
        "first_name": None,
        "last_name": None,
        "dob": None,
        "phone": None,
        "address_full": None,
        "register_date": None,
    }
    # Standardise whitespace and collapse multiple spaces
    norm_text = re.sub(r"\s+", " ", text)
    # Extract CID: first occurrence of 13 consecutive digits
    # Handle cases where the ID number might have spaces or dashes
    cid_match = re.search(r"\b\d{1,3}[-\s]?\d{1,3}[-\s]?\d{1,3}[-\s]?\d{1,3}[-\s]?\d{1,3}\b", norm_text)
    if cid_match:
        # Remove any spaces or dashes to get the clean 13-digit ID
        cid_clean = re.sub(r"[-\s]", "", cid_match.group(0))
        if len(cid_clean) == 13:
            result["cid"] = cid_clean
        else:
            # Fallback to original pattern if the cleaned version isn't 13 digits
            cid_match_original = re.search(r"\b\d{13}\b", norm_text)
            if cid_match_original:
                result["cid"] = cid_match_original.group(0)
    else:
        # Original pattern as fallback
        cid_match = re.search(r"\b\d{13}\b", norm_text)
        if cid_match:
            result["cid"] = cid_match.group(0)
    # Extract phone: Thai phone numbers usually start with 0 and have 9–10 digits
    phone_match = re.search(r"0\d{8,9}", norm_text)
    if phone_match:
        result["phone"] = phone_match.group(0)
    # Extract date strings (DOB and register date). We expect two dates in most forms.
    date_regex = re.compile(
        r"\b\d{1,2}\s(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.|มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s\d{2,4}\b"
    )
    date_matches = date_regex.findall(norm_text)
    if date_matches:
        # Assume the first date is DOB and the second date is register date if two are found
        if len(date_matches) >= 1:
            result["dob"] = date_matches[0]
        if len(date_matches) >= 2:
            result["register_date"] = date_matches[1]
    # Extract prefix, first and last names. We look for common Thai prefixes.
    prefix_regex = re.compile(
        r"(นาย|นางสาว|นาง|น\.ส\.|เด็กชาย|เด็กหญิง|ด\.ช\.|ด\.ญ\.)\s*([ก-๛A-Za-z]+)\s+([ก-๛A-Za-z]+)"
    )
    name_match = prefix_regex.search(norm_text)
    if name_match:
        result["prefix"] = name_match.group(1)
        result["first_name"] = name_match.group(2)
        result["last_name"] = name_match.group(3)
    # Extract address: look for label "ที่อยู่" and capture following text until a punctuation mark
    addr_match = re.search(r"ที่อยู่[:：]?\s*([^\n\r]+)", text)
    if addr_match:
        result["address_full"] = addr_match.group(1).strip()
    return result


def process_file(
    session: Session,
    file_path: str,
    sanitized_filename: str,
    batch: Optional[Batch] = None,
) -> Citizen:
    """Process a single PDF file and persist the extracted citizen record.

    The PDF is opened in text mode using pdfplumber. If no text can be
    extracted the record is marked for review. Once fields are extracted,
    they are normalised and validated. Error messages accumulate reasons
    why the record may need manual correction. The resulting ``Citizen``
    instance is added to the session and returned.

    Parameters
    ----------
    session: Session
        An active SQLAlchemy session.
    file_path: str
        Filesystem path to the PDF to process.
    sanitized_filename: str
        Sanitised filename corresponding to the stored PDF.
    batch: Optional[Batch], optional
        The batch to which this record belongs.

    Returns
    -------
    Citizen
        The persisted citizen record.
    """
    citizen = Citizen(
        batch=batch,
        file_path=file_path,
        sanitized_filename=sanitized_filename,
        status=FileStatus.pending,
    )
    errors: List[str] = []
    try:
        if pdfplumber is None:
            raise RuntimeError("pdfplumber library is not installed")
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as exc:
        logger.error(f"Failed to open PDF: {file_path}: {exc}")
        errors.append("ไม่สามารถอ่านไฟล์ได้")
        citizen.status = FileStatus.review
        citizen.error_reason = "; ".join(errors)
        session.add(citizen)
        session.commit()
        return citizen
    if not text.strip():
        errors.append("ไม่พบข้อความในไฟล์")
        citizen.status = FileStatus.review
        citizen.error_reason = "; ".join(errors)
        session.add(citizen)
        session.commit()
        return citizen
    fields = extract_fields(text)
    # Assign raw extracted values
    citizen.cid = fields.get("cid")
    citizen.prefix = fields.get("prefix")
    citizen.first_name = fields.get("first_name")
    citizen.last_name = fields.get("last_name")
    citizen.phone = fields.get("phone")
    citizen.address_full = fields.get("address_full")
    # Normalise and validate dates
    raw_dob = fields.get("dob")
    raw_reg_date = fields.get("register_date")
    dob_date = parse_thai_date(raw_dob) if raw_dob else None
    reg_date = parse_thai_date(raw_reg_date) if raw_reg_date else None
    citizen.dob = dob_date
    citizen.register_date = reg_date
    # Compute age
    citizen.age_years = compute_age_years(dob_date, reg_date) if dob_date and reg_date else None
    # Validate CID
    if citizen.cid:
        if not validate_thai_cid(citizen.cid):
            errors.append("เลขบัตรประชาชนไม่ถูกต้อง")
    else:
        errors.append("ไม่พบเลขบัตรประชาชน")
    # Validate phone (basic length check)
    if citizen.phone and len(citizen.phone) not in (9, 10):
        errors.append("หมายเลขโทรศัพท์ไม่ถูกต้อง")
    # Validate DOB and register date
    if raw_dob and not dob_date:
        errors.append(f"รูปแบบวันเกิดไม่ถูกต้อง: {raw_dob}")
    if raw_reg_date and not reg_date:
        errors.append(f"รูปแบบวันลงทะเบียนไม่ถูกต้อง: {raw_reg_date}")
    # Set status
    if errors:
        citizen.status = FileStatus.review
        citizen.error_reason = "; ".join(errors)
    else:
        citizen.status = FileStatus.valid
    session.add(citizen)
    session.commit()
    return citizen


def export_records(session: Session) -> Dict[str, str]:
    """Export valid or corrected records to CSV and Excel and archive their PDFs.

    Records with status ``valid`` or ``corrected`` are exported. A CSV and
    Excel (XLSX) file are written containing all the record fields. Each
    processed PDF is moved into an archive folder organised by year and month
    derived from its register date. After archiving, the record status is
    updated to ``exported``.

    Parameters
    ----------
    session: Session
        The database session used for querying and updating records.

    Returns
    -------
    dict
        A mapping containing the paths of the generated CSV and Excel files.
    """
    # Query all records eligible for export
    records = (
        session.query(Citizen)
        .filter(Citizen.status.in_([FileStatus.valid, FileStatus.corrected]))
        .all()
    )
    if not records:
        return {}
    app_config, _ = get_config()
    # Prepare data for export
    rows = []
    for rec in records:
        rows.append(
            {
                "CID": rec.cid,
                "Prefix": rec.prefix,
                "FirstName": rec.first_name,
                "LastName": rec.last_name,
                "DOB": rec.dob.isoformat() if rec.dob else None,
                "Phone": rec.phone,
                "AddressFull": rec.address_full,
                "RegisterDate": rec.register_date.isoformat() if rec.register_date else None,
                "AgeYears": rec.age_years,
                "Status": rec.status.value,
                "ErrorReason": rec.error_reason,
            }
        )
    df = pd.DataFrame(rows)
    export_dir = Path("export")
    export_dir.mkdir(exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    csv_path = export_dir / f"citizens_{timestamp}.csv"
    xlsx_path = export_dir / f"citizens_{timestamp}.xlsx"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False)
    # Archive PDFs
    archive_root = Path(app_config.get("archive_directory", "archive"))
    for rec in records:
        # Determine archive subfolder from register date or fallback to current date
        reg_date = rec.register_date or dt.date.today()
        sub_dir = archive_root / f"{reg_date.year}" / f"{reg_date.month:02d}"
        sub_dir.mkdir(parents=True, exist_ok=True)
        # Build archive filename
        cid = rec.cid or "unknown"
        first = rec.first_name or ""
        last = rec.last_name or ""
        reg_str = reg_date.strftime("%Y%m%d")
        new_name = f"{cid}_{first}{last}_{reg_str}.pdf"
        new_name = sanitize_filename(new_name)
        src_path = Path(rec.file_path)
        dest_path = sub_dir / new_name
        try:
            # Ensure the destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            # Copy the file to the archive directory and overwrite if necessary
            with open(src_path, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            # Update record
            rec.status = FileStatus.exported
            rec.file_path = str(dest_path)
        except Exception as exc:
            logger.error(f"Failed to archive {src_path}: {exc}")
    session.commit()
    return {"csv": str(csv_path), "xlsx": str(xlsx_path)}