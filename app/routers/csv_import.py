import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/import", tags=["import"])

MAX_ROWS = 1_000_000
BATCH_SIZE = 1000
REQUIRED_COLUMNS = {"type", "amount", "date", "description", "category"}


@router.post("/transactions", response_model=schemas.ImportResult)
async def import_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, detail="File must be a .csv file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - fieldnames
    if missing:
        raise HTTPException(
            400,
            detail=f"Missing required columns: {sorted(missing)}",
        )

    categories_map = {
        c.name.lower(): c for c in db.query(models.Category).all()
    }

    imported = 0
    errors: list[schemas.ImportErrorItem] = []
    batch: list[models.Transaction] = []
    row_count = 0

    for line_no, row in enumerate(reader, start=2):
        row_count += 1
        if row_count > MAX_ROWS:
            errors.append(
                schemas.ImportErrorItem(
                    row=line_no,
                    error=f"Maximum {MAX_ROWS} rows exceeded; remaining rows skipped",
                )
            )
            break

        category_name_raw = (row.get("category") or "").strip()
        if not category_name_raw:
            errors.append(
                schemas.ImportErrorItem(row=line_no, error="Category is required")
            )
            continue

        category = categories_map.get(category_name_raw.lower())
        if not category:
            errors.append(
                schemas.ImportErrorItem(
                    row=line_no,
                    error=f"Category '{category_name_raw}' does not exist",
                )
            )
            continue

        description_raw = (row.get("description") or "").strip() or None

        try:
            payload = schemas.TransactionCreate(
                type=(row.get("type") or "").strip().lower(),
                amount=(row.get("amount") or "").strip(),
                date=(row.get("date") or "").strip(),
                description=description_raw,
                category_id=category.id,
            )
        except ValidationError as exc:
            msgs = "; ".join(
                f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()
            )
            errors.append(
                schemas.ImportErrorItem(row=line_no, error=msgs)
            )
            continue

        batch.append(models.Transaction(**payload.model_dump()))
        imported += 1

        if len(batch) >= BATCH_SIZE:
            db.add_all(batch)
            db.commit()
            batch = []

    if batch:
        db.add_all(batch)
        db.commit()

    return schemas.ImportResult(imported=imported, errors=errors)
