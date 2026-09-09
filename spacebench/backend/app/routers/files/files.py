import io
import os
import uuid
import zipfile

from app.validators.upload import Sp3Validator, RnxValidator, ClkValidator, FileDescriptor
from app.validators.upload.base import FileValidationError, FileValidator
from app.validators.upload.py import PythonValidator
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse as FileDownloadResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.settings import settings
from app.models.pod import UploadedFile, FileType
from app.schemas.pod import FileResponse

from pathlib import Path

from starlette.responses import StreamingResponse
from app.core.settings import settings

# ════════════ DEBUG MODE ══════════════════════════════════════════════════════════════════════════════════════════════

DEBUG_MODE = settings.DEBUG_MODE


router = APIRouter(prefix="/api/files", tags=["Files"])

# Modifiability
ALL_VALIDATORS: list[FileValidator] = [
    Sp3Validator(),
    RnxValidator(),
    ClkValidator(),
    PythonValidator()
]

ALLOWED_EXTENSIONS: dict[str, FileType] = {}
for validator in ALL_VALIDATORS:
    ALLOWED_EXTENSIONS[validator.ext] = validator.file_type

VALIDATORS: dict[str, FileValidator] = {}
for validator in ALL_VALIDATORS:
    VALIDATORS[validator.ext] = validator


@router.post("/upload", response_model=FileResponse, status_code=201)
async def upload_file(
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_session),
):


    # Validate EXTENSION
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        accepted_extensions = ", ".join(ALLOWED_EXTENSIONS.keys())
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Accepted: {accepted_extensions}")

    if DEBUG_MODE: print(f"Ext : {ext}")

    # If the upload files does not exists, creates it.
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_id = str(uuid.uuid4())

    # If the mission folder does not exists, creates it.

    dest_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    validation_metadata = None

    # Validate CONTENT
    validator = VALIDATORS.get(ext)
    if validator:
        descriptor = FileDescriptor(
            id=file_id,
            path=Path(dest_path),
            file_type=ALLOWED_EXTENSIONS[ext].value,
            original_name=file.filename,
        )

        if DEBUG_MODE: print(f"Descriptor : {descriptor}")

        result = validator.validate(descriptor)

        if DEBUG_MODE: print(f"Result : {result}")

        if not result.valid:
            os.remove(dest_path) # Delete the file
            if DEBUG_MODE: print("This file is not valid !")
            raise HTTPException(status_code=422, detail=f"File not valid : {result.issues}")


        if result.metadata:
            if DEBUG_MODE: print(f"Resultats metadata : {result.metadata}")
            validation_metadata = result.metadata

    record = UploadedFile(
        id=file_id,
        original_name=file.filename,
        stored_path=dest_path,
        file_type=ALLOWED_EXTENSIONS[ext],
        validation_metadata=validation_metadata
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    
    return record


@router.get("/{file_id}/download")
async def download_file(file_id: str, session: AsyncSession = Depends(get_session)):
    record = await session.get(UploadedFile, file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(record.stored_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileDownloadResponse(record.stored_path, filename=record.original_name)


@router.post("/bulk/download")
async def download_files_bulk(file_ids: list[str], session: AsyncSession = Depends(get_session)):

    if not file_ids:
        raise HTTPException(status_code=400, detail="No files ID provided")

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_id in file_ids:

            record = await session.get(UploadedFile, file_id)

            if not record:
                raise HTTPException(status_code=404, detail="File not found")

            if not os.path.exists(record.stored_path):
                raise HTTPException(status_code=404, detail="File not found on disk")

            zip_file.write(record.stored_path, record.original_name)

    zip_buffer.seek(0)

    return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=spacebench_export.zip"})