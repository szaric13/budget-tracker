from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..utils import month_bounds, to_money

router = APIRouter(prefix="/summary", tags=["summary"])

_month_adapter = TypeAdapter(schemas.Month)


def _validate_month(month: str) -> None:
    try:
        _month_adapter.validate_python(month)
    except ValidationError:
        raise HTTPException(
            422,
            detail="Invalid month format, expected YYYY-MM",
        )


@router.get("/", response_model=schemas.SummaryOut)
def monthly_summary(month: str, db: Session = Depends(get_db)):
    _validate_month(month)

    first, last = month_bounds(month)

    transactions = (
        db.query(models.Transaction)
        .options(joinedload(models.Transaction.category))
        .filter(
            models.Transaction.date >= first,
            models.Transaction.date <= last,
        )
        .all()
    )

    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")
    spent_by_category: dict[str, Decimal] = {}

    for tx in transactions:
        amount = to_money(tx.amount)
        if tx.type == "income":
            total_income += amount
        else:
            total_expense += amount
            name = tx.category.name
            spent_by_category[name] = (
                spent_by_category.get(name, Decimal("0.00")) + amount
            )

    budgets = (
        db.query(models.Budget)
        .options(joinedload(models.Budget.category))
        .filter(models.Budget.month == month)
        .all()
    )
    budget_by_category: dict[str, Decimal] = {
        b.category.name: to_money(b.amount) for b in budgets
    }

    all_names = set(spent_by_category) | set(budget_by_category)

    category_rows: list[schemas.CategorySummary] = []
    for name in all_names:
        spent = spent_by_category.get(name, Decimal("0.00"))
        budget = budget_by_category.get(name, Decimal("0.00"))
        category_rows.append(
            schemas.CategorySummary(
                category_name=name,
                spent=spent,
                budget=budget,
                remaining=budget - spent,
            )
        )

    category_rows.sort(key=lambda c: (-c.spent, c.category_name.lower()))

    return schemas.SummaryOut(
        total_income=total_income,
        total_expense=total_expense,
        balance=total_income - total_expense,
        categories=category_rows,
    )
