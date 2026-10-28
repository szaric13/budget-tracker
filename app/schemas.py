from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, condecimal, constr


CategoryName = constr(strip_whitespace=True, min_length=1, max_length=30)
HexColor = constr(pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryCreate(BaseModel):
    name: CategoryName
    color: HexColor


class CategoryUpdate(BaseModel):
    name: Optional[CategoryName] = None
    color: Optional[HexColor] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    color: str

    model_config = {"from_attributes": True}


Amount = condecimal(
    gt=0,
    le=Decimal("1000000.00"),
    max_digits=10,
    decimal_places=2,
)


class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    amount: Amount
    date: date
    description: Optional[constr(max_length=200)] = None
    category_id: int


class TransactionUpdate(BaseModel):
    type: Optional[Literal["income", "expense"]] = None
    amount: Optional[Amount] = None
    date: Optional[date] = None
    description: Optional[constr(max_length=200)] = None
    category_id: Optional[int] = None


class TransactionOut(BaseModel):
    id: int
    type: str
    amount: Decimal
    date: date
    description: Optional[str] = None
    category_id: int
    category_name: str

    model_config = {"from_attributes": True}


Month = constr(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class BudgetCreate(BaseModel):
    month: Month
    category_id: int
    amount: Amount


class BudgetUpdate(BaseModel):
    amount: Amount


class BudgetOut(BaseModel):
    id: int
    month: str
    category_id: int
    amount: Decimal

    model_config = {"from_attributes": True}


class CategorySummary(BaseModel):
    category_name: str
    spent: Decimal
    budget: Decimal
    remaining: Decimal


class SummaryOut(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    categories: list[CategorySummary]


class ImportErrorItem(BaseModel):
    row: int
    error: str


class ImportResult(BaseModel):
    imported: int
    errors: list[ImportErrorItem]
