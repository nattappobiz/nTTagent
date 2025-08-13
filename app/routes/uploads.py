"""Upload endpoints for handling PDF submissions.

This router exposes an endpoint to accept multiple PDF files. Uploaded files
are stored to the configured input directory and processed immediately. A
batch record groups all uploads for ease of tracking.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_config
from app.models.database import SessionLocal
from app.models.models import Batch
from app.schemas.citizen import CitizenOut
from app.services.pdf_processor import process_file
from app.services.utils import sanitize_filename

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/uploads", response_model=List[CitizenOut])
async def upload_pdfs(
    files: List[UploadFile] = File(..., description="One or more PDF files"),
    db: Session = Depends(get_db),
):
    """Receive one or more PDF files, save them to disk and process them.

    Each upload request creates a new batch. Files are sanitised and saved
    under the configured input directory. After saving, the PDFs are parsed
    to extract citizen information.
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")
    app_config, _ = get_config()
    input_dir = Path(app_config.get("input_directory", "input"))
    input_dir.mkdir(exist_ok=True)
    # Create batch
    batch = Batch()
    db.add(batch)
    db.commit()
    db.refresh(batch)
    results: List[CitizenOut] = []
    for upload in files:
        # Verify PDF content type
        if upload.content_type != "application/pdf":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File {upload.filename} is not a PDF")
        original_name = upload.filename or "unnamed.pdf"
        safe_name = sanitize_filename(original_name)
        file_path = input_dir / safe_name
        # Ensure unique file name by appending numeric suffix if file exists
        counter = 1
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        while file_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            file_path = input_dir / new_name
            counter += 1
        # Save file to disk
        with open(file_path, "wb") as out_file:
            content = await upload.read()
            out_file.write(content)
        # Close the UploadFile explicitly
        await upload.close()
        # Process PDF
        citizen = process_file(db, str(file_path), file_path.name, batch=batch)
        results.append(CitizenOut.from_orm(citizen))
    return results