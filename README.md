# Budget Tracker API

A simple REST API for tracking personal income, expenses, and monthly budgets. Transactions can be grouped by category, filtered, or imported from a CSV file. All amounts are in euros.

Built with Python 3.12, FastAPI, SQLAlchemy, SQLite, and Pydantic.

## Getting started

```bash
git clone https://github.com/szaric13/budget-tracker.git
cd budget-tracker
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install the dependencies and start the server:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Features

- Create, update, and delete categories and transactions
- Filter transactions by date, category, type, or description
- Set monthly budgets for each category
- View monthly income, expenses, balance, and remaining budgets
- Import transactions from CSV

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/categories/` | Create a category |
| GET | `/categories/` | List categories |
| GET | `/categories/{id}` | Get a category |
| PATCH | `/categories/{id}` | Update a category |
| DELETE | `/categories/{id}` | Delete a category |
| POST | `/transactions/` | Add a transaction |
| GET | `/transactions/` | List and filter transactions |
| GET | `/transactions/{id}` | Get a transaction |
| PATCH | `/transactions/{id}` | Update a transaction |
| DELETE | `/transactions/{id}` | Delete a transaction |
| PUT | `/budgets/{category_id}/{month}` | Set a monthly budget |
| GET | `/budgets/?month=YYYY-MM` | List monthly budgets |
| DELETE | `/budgets/{category_id}/{month}` | Delete a budget |
| GET | `/summary/?month=YYYY-MM` | Get a monthly summary |
| POST | `/import/transactions` | Import a CSV file |

For request and response schemas, see the Swagger documentation at `/docs`.

### Example transaction

`POST /transactions/`

```json
{
  "type": "expense",
  "amount": "12.50",
  "date": "2026-10-08",
  "description": "Lunch",
  "category_id": 1
}
```

The category must already exist. Amounts must be positive and have no more than two decimal places.

### CSV import

Upload a UTF-8 CSV file to `POST /import/transactions` using the `file` form field. Example:

```csv
type,amount,date,description,category
expense,12.50,2026-10-08,Lunch,Food
income,300.00,2026-10-09,,Other
```

Categories must exist before importing. The response includes the number of imported rows and any row-level errors. A `sample.csv` file is included.

## Tests

```bash
pytest -v
```

Tests use an in-memory SQLite database, so they don't modify the application's data.

## Database

SQLite data is stored in `budget.db`, which is created automatically and persists between restarts. To reset it, stop the server and delete the file.

Money values use `Decimal` to avoid floating-point rounding issues.
