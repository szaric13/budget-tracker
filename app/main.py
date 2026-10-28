from fastapi import FastAPI

from .database import Base, engine
from .routers import budgets, categories, csv_import, summary, transactions

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Budget Tracker API",
    version="1.0.0",
    description="Personal budget tracker: categories, transactions, budgets, monthly summary.",
)

app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(summary.router)
app.include_router(csv_import.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
