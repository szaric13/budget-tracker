from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _get_category_or_404(db: Session, category_id: int) -> models.Category:
    cat = db.get(models.Category, category_id)
    if not cat:
        raise HTTPException(400, detail=f"Category {category_id} does not exist")
    return cat


@router.post("/", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(
    payload: schemas.TransactionCreate, db: Session = Depends(get_db)
):
    _get_category_or_404(db, payload.category_id)
    tx = models.Transaction(**payload.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/", response_model=list[schemas.TransactionOut])
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category_id: Optional[int] = None,
    type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction).options(
        joinedload(models.Transaction.category)
    )

    if date_from is not None:
        query = query.filter(models.Transaction.date >= date_from)
    if date_to is not None:
        query = query.filter(models.Transaction.date <= date_to)
    if category_id is not None:
        query = query.filter(models.Transaction.category_id == category_id)
    if type is not None:
        query = query.filter(models.Transaction.type == type)
    if description:
        query = query.filter(
            func.lower(models.Transaction.description).like(f"%{description.lower()}%")
        )

    query = query.order_by(
        models.Transaction.date.desc(), models.Transaction.id.desc()
    )
    return query.offset(skip).limit(limit).all()


@router.get("/{transaction_id}", response_model=schemas.TransactionOut)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.get(models.Transaction, transaction_id)
    if not tx:
        raise HTTPException(404, detail="Transaction not found")
    return tx


@router.patch("/{transaction_id}", response_model=schemas.TransactionOut)
def update_transaction(
    transaction_id: int,
    payload: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
):
    tx = db.get(models.Transaction, transaction_id)
    if not tx:
        raise HTTPException(404, detail="Transaction not found")
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data:
        _get_category_or_404(db, data["category_id"])
    for key, value in data.items():
        setattr(tx, key, value)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.get(models.Transaction, transaction_id)
    if not tx:
        raise HTTPException(404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
    return None
