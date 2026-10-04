import hashlib
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Statement
from app.schemas.schemas import StatementResponse

router = APIRouter(prefix="/statements", tags=["Statements"])

ALLOWED_EXTENSIONS = {".pdf", ".csv"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.get("", response_model=List[StatementResponse])
async def list_statements(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(Statement).order_by(Statement.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/upload", response_model=StatementResponse, status_code=status.HTTP_201_CREATED)
async def upload_statement(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename or "unknown"
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. FinLens AI supports PDF and CSV statements.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 20MB limit.",
        )

    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate file
    existing_stmt = await db.execute(select(Statement).where(Statement.file_hash == file_hash))
    if existing_stmt.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This exact statement has already been uploaded.",
        )

    statement = Statement(
        filename=filename,
        file_hash=file_hash,
        file_format="pdf" if ext == ".pdf" else "csv",
        status="pending",
    )
    db.add(statement)
    await db.commit()
    await db.refresh(statement)
    return statement


@router.get("/{statement_id}", response_model=StatementResponse)
async def get_statement(
    statement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Statement).where(Statement.id == statement_id))
    statement = result.scalar_one_or_none()
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found.")
    return statement


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_statement(
    statement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Statement).where(Statement.id == statement_id))
    statement = result.scalar_one_or_none()
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found.")

    await db.delete(statement)  # Triggers cascade deletion of transactions & jobs
    await db.commit()
    return None
