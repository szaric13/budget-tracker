from sqlalchemy import (
    Column, Integer, String, Date, Numeric, ForeignKey,
    UniqueConstraint, CheckConstraint, Index,
)
from sqlalchemy.orm import relationship
from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30, collation="NOCASE"), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=False)

    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship(
        "Budget", back_populates="category", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(10), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    description = Column(String(200), nullable=True)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )

    category = relationship("Category", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("type IN ('income', 'expense')", name="ck_transaction_type"),
        Index("ix_transactions_date_id", "date", "id"),
    )

    @property
    def category_name(self) -> str:
        return self.category.name if self.category else None


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String(7), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    category = relationship("Category", back_populates="budgets")

    __table_args__ = (
        UniqueConstraint("month", "category_id", name="uq_budget_month_category"),
        CheckConstraint("length(month) = 7", name="ck_budget_month_format"),
    )
