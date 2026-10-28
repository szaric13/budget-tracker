from fastapi import APIRouter, Depends, HTTPException
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/budgets", tags=["budgets"])

_month_adapter = TypeAdapter(schemas.Month)


def _validate_month(month: str) -> None:
    try:
        _month_adapter.validate_python(month)
    except ValidationError:
        raise HTTPException(
            422,
            detail="Invalid month format, expected YYYY-MM",
        )


@router.put("/{category_id}/{month}", response_model=schemas.BudgetOut)
def upsert_budget(
    category_id: int,
    month: str,
    payload: schemas.BudgetUpdate,
    db: Session = Depends(get_db),
):
    _validate_month(month)

    if not db.get(models.Category, category_id):
        raise HTTPException(404, detail="Category not found")

    budget = (
        db.query(models.Budget)
        .filter_by(category_id=category_id, month=month)
        .first()
    )
    if budget:
        budget.amount = payload.amount
    else:
        budget = models.Budget(
            category_id=category_id, month=month, amount=payload.amount
        )
        db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("/", response_model=list[schemas.BudgetOut])
def list_budgets(month: str, db: Session = Depends(get_db)):
    _validate_month(month)
    return (
        db.query(models.Budget)
        .filter(models.Budget.month == month)
        .order_by(models.Budget.category_id)
        .all()
    )


@router.delete("/{category_id}/{month}", status_code=204)
def delete_budget(
    category_id: int, month: str, db: Session = Depends(get_db)
):
    _validate_month(month)
    budget = (
        db.query(models.Budget)
        .filter_by(category_id=category_id, month=month)
        .first()
    )
    if not budget:
        raise HTTPException(404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return None
