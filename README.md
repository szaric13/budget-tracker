# Budget Tracker API

A REST API for a personal budget tracker. One user can record income and expenses, organise transactions into categories, set monthly budgets per category, and view a summary for each month. All amounts are in **euros (EUR)**.

Built with **Python 3.12**, **FastAPI**, **SQLAlchemy 2.0**, **SQLite**, **Pydantic v2**, and **pytest**.

## Table of contents

- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Installation and running](#installation-and-running)
- [Running tests](#running-tests)
- [Data and database](#data-and-database)
- [API documentation](#api-documentation)
  - [Categories](#categories)
  - [Transactions](#transactions)
  - [Budgets](#budgets)
  - [Monthly summary](#monthly-summary)
  - [CSV import](#csv-import)
  - [Health check](#health-check)
- [CSV import format](#csv-import-format)
- [Design decisions](#design-decisions)
- [Error handling](#error-handling)
- [License](#license)

## Tech stack

| Layer | Technology | Why |
| --- | --- | --- |
| Language | Python 3.12 | Stable release with prebuilt dependency wheels |
| Web framework | FastAPI 0.115 | Automatic OpenAPI docs and Pydantic integration |
| ORM | SQLAlchemy 2.0 | Models, relationships, and cross-database compatibility |
| Database | SQLite | Zero configuration, persistent single-file database |
| Validation | Pydantic v2 | Declarative rules and clear error messages |
| Testing | pytest + httpx | Isolated API tests using an in-memory database |

## Project structure

```text
budget-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app and router registration
│   ├── database.py             # Engine, session factory, get_db dependency
│   ├── models.py               # SQLAlchemy models: Category, Transaction, Budget
│   ├── schemas.py              # Pydantic validation schemas
│   ├── utils.py                # month_bounds and to_money helpers
│   └── routers/
│       ├── __init__.py
│       ├── categories.py       # /categories endpoints
│       ├── transactions.py     # /transactions endpoints
│       ├── budgets.py          # /budgets endpoints
│       ├── summary.py          # /summary endpoint
│       └── csv_import.py       # /import/transactions endpoint
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures: in-memory DB and client
│   ├── test_categories.py
│   ├── test_transactions.py
│   ├── test_summary.py
│   └── test_csv_import.py
├── sample.csv                  # Example import file
├── pytest.ini
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and running

### Prerequisites

- Python 3.12 or newer
- Git

### 1. Clone the repository

```bash
git clone https://github.com/szaric13/budget-tracker.git
cd budget-tracker
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

Once running, open:

| Resource | URL |
| --- | --- |
| Base URL | http://127.0.0.1:8000 |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| OpenAPI JSON | http://127.0.0.1:8000/openapi.json |

## Running tests

```bash
pytest -v
```

The supplied project description specifies **22 passing tests**. Tests use an in-memory SQLite database with `StaticPool`, so they do not modify `budget.db` and remain isolated from one another.

Test coverage includes:

- **Validation:** amount limits and decimal places, hex colours, name length, transaction types.
- **Monthly summary:** totals, balance, category breakdown, ordering, empty months.
- **CSV import:** successful imports, case-insensitive category matching, row-level errors, missing columns.
- **Business rules:** duplicate categories, restrictions on category deletion, cascade deletion of budgets.

## Data and database

The persistent database is stored in `budget.db` in the project root. It is created automatically when the application first starts.

### Persistence across restarts

Because `budget.db` is a file on disk, data remains available after restarting the application. Tables are created using `CREATE TABLE IF NOT EXISTS`; existing tables and records are not dropped on startup.

### Inspect data

```bash
python -c "import sqlite3; c = sqlite3.connect('budget.db'); [print(r) for r in c.execute('SELECT * FROM categories')]"
```

You can also open `budget.db` with **DB Browser for SQLite**.

### Reset the database

Stop the application, delete the database file, then restart it.

**Windows (PowerShell):**

```powershell
Remove-Item budget.db
```

**Linux / macOS:**

```bash
rm budget.db
```

> **Warning:** Resetting the database permanently deletes all locally stored categories, transactions, and budgets.

## API documentation

Interactive endpoint documentation is available through [Swagger UI](http://127.0.0.1:8000/docs) and [ReDoc](http://127.0.0.1:8000/redoc) while the API is running.

### Categories

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/categories/` | Create a category |
| `GET` | `/categories/` | List all categories, sorted by name |
| `GET` | `/categories/{id}` | Get a category by ID |
| `PATCH` | `/categories/{id}` | Update the name and/or colour |
| `DELETE` | `/categories/{id}` | Delete a category |

**Create category — `POST /categories/`**

Request:

```json
{
  "name": "Food",
  "color": "#FF0000"
}
```

Response (`201 Created`):

```json
{
  "id": 1,
  "name": "Food",
  "color": "#FF0000"
}
```

Rules:

- `name`: 1–30 characters after trimming leading and trailing spaces; case-insensitively unique.
- `color`: hexadecimal colour in `#RRGGBB` format.
- Categories referenced by transactions cannot be deleted (`400 Bad Request`).
- Deleting a category also deletes its associated budgets.

### Transactions

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/transactions/` | Create a transaction |
| `GET` | `/transactions/` | List transactions with filters and pagination |
| `GET` | `/transactions/{id}` | Get a transaction by ID |
| `PATCH` | `/transactions/{id}` | Update a transaction |
| `DELETE` | `/transactions/{id}` | Delete a transaction |

**Create transaction — `POST /transactions/`**

Request:

```json
{
  "type": "expense",
  "amount": "12.50",
  "date": "2026-10-08",
  "description": "Lunch",
  "category_id": 1
}
```

Response (`201 Created`):

```json
{
  "id": 1,
  "type": "expense",
  "amount": "12.50",
  "date": "2026-10-08",
  "description": "Lunch",
  "category_id": 1,
  "category_name": "Food"
}
```

**Query parameters for `GET /transactions/`:**

| Parameter | Type | Description |
| --- | --- | --- |
| `skip` | Integer ≥ 0 | Pagination offset; default `0` |
| `limit` | Integer, 1–1000 | Page size; default `50` |
| `date_from` | Date | Inclusive start date |
| `date_to` | Date | Inclusive end date |
| `category_id` | Integer | Filter by category |
| `type` | `income` or `expense` | Filter by transaction type |
| `description` | String | Case-insensitive substring search |

All filters can be combined. Transactions are sorted from newest to oldest; transactions on the same date are sorted with the most recently added first.

Example:

```http
GET /transactions/?type=expense&date_from=2026-10-01&date_to=2026-10-31&limit=50&skip=0
```

Rules:

- `type` must be `income` or `expense`.
- `amount` must be greater than `0`, at most `1,000,000.00`, with at most two decimal places.
- `date` must use ISO format `YYYY-MM-DD`.
- `description` is optional, with a maximum length of 200 characters.
- `category_id` must reference an existing category.

### Budgets

| Method | Endpoint | Description |
| --- | --- | --- |
| `PUT` | `/budgets/{category_id}/{month}` | Create or update a monthly category budget |
| `GET` | `/budgets/?month=YYYY-MM` | List budgets for a month |
| `DELETE` | `/budgets/{category_id}/{month}` | Remove a monthly category budget |

**Set a budget — `PUT /budgets/1/2026-10`**

Request:

```json
{
  "amount": "150.00"
}
```

Response (`200 OK`):

```json
{
  "id": 1,
  "month": "2026-10",
  "category_id": 1,
  "amount": "150.00"
}
```

`PUT` is **idempotent**: repeating the request updates the existing budget rather than creating a duplicate.

### Monthly summary

**`GET /summary/?month=YYYY-MM`**

Example response:

```json
{
  "total_income": "300.00",
  "total_expense": "47.50",
  "balance": "252.50",
  "categories": [
    {
      "category_name": "Food",
      "spent": "32.50",
      "budget": "150.00",
      "remaining": "117.50"
    },
    {
      "category_name": "Transport",
      "spent": "15.00",
      "budget": "0.00",
      "remaining": "-15.00"
    }
  ]
}
```

Summary rules:

- `balance = total_income - total_expense`; a negative balance is permitted.
- `categories` contains every category with an expense or a budget during the requested month.
- `remaining = budget - spent`; a negative result indicates overspending.
- Categories are sorted by `spent` descending, then `category_name` ascending.
- A month with no transactions and no budgets returns zero totals and an empty `categories` list.

### CSV import

**`POST /import/transactions`** accepts a multipart form upload with a file field.

Example CSV:

```csv
type,amount,date,description,category
expense,12.50,2026-10-08,Lunch,Eating out
income,300.00,2026-10-09,,Other
```

Example response:

```json
{
  "imported": 2,
  "errors": [
    {
      "row": 4,
      "error": "Category 'Doesnotexist' does not exist"
    }
  ]
}
```

Import rules:

- Each row follows the same validation rules as a regular transaction.
- Every referenced category must already exist; names are matched case-insensitively.
- An empty `description` becomes `null`.
- `imported` counts successful rows; `errors` contains failed rows with CSV line numbers (header = line 1).
- The maximum supported import size is **1,000,000 rows**.

### Health check

**`GET /health`**

Response:

```json
{
  "status": "ok"
}
```

## CSV import format

CSV files must use UTF-8 encoding. A UTF-8 BOM is accepted (`utf-8-sig`).

| Column | Required | Notes |
| --- | --- | --- |
| `type` | Yes | `income` or `expense` |
| `amount` | Yes | Decimal greater than 0; maximum two decimal places |
| `date` | Yes | ISO date `YYYY-MM-DD` |
| `description` | Yes, may be empty | Empty value is converted to `null` |
| `category` | Yes | Must match an existing category (case-insensitive) |

A ready-to-use example is provided in [`sample.csv`](sample.csv).

## Design decisions

### Decimal instead of float for money

Floating-point arithmetic introduces precision issues (for example, `0.1 + 0.2` is not exactly `0.3`). Monetary amounts use `Decimal` in Python and `Numeric(10, 2)` in SQLAlchemy. Values are converted through `str()` before quantisation:

```python
Decimal(str(value)).quantize(Decimal("0.01"))
```

### Case-insensitive category uniqueness

Using `String(30, collation="NOCASE")` with a unique constraint at the SQLite database level prevents both `Food` and `food` from being stored as distinct categories.

### Database-level deletion rules

- `Transaction.category_id` uses **`ON DELETE RESTRICT`**: categories with transactions cannot be deleted.
- `Budget.category_id` uses **`ON DELETE CASCADE`**: deleting a category removes its associated budgets.

The `delete_category` endpoint also checks for related transactions to return a friendlier error response.

### Python Decimal aggregation for summaries

The supplied design uses Python `Decimal` aggregation rather than relying on SQLite `SUM()` for monetary values, avoiding potential floating-point rounding errors. This is practical for monthly datasets of thousands of records; a database with native decimal aggregation, such as PostgreSQL, would be worth considering at much larger scales.

### Indexed date-range filtering

The `month_bounds` helper creates a start and end date. Filtering with indexed date comparisons:

```sql
WHERE date >= :first_date AND date <= :last_date
```

is preferable to wrapping the date column in a function such as `strftime('%Y-%m', date)`, which can prevent efficient use of an ordinary date index.

### Batched CSV inserts

CSV rows are accumulated into batches of **1,000** using `add_all`, reducing database overhead compared with committing every row separately.

### Shared validation between JSON and CSV

Both JSON requests and CSV imports use `schemas.TransactionCreate`, keeping validation rules in one place and avoiding inconsistent behaviour.

## Error handling

| Status | Meaning | Example |
| --- | --- | --- |
| `200 OK` | Successful request | GET, PUT, PATCH |
| `201 Created` | Resource created | POST |
| `204 No Content` | Resource deleted | DELETE |
| `400 Bad Request` | Invalid business operation | Unknown category; category with transactions |
| `404 Not Found` | Resource does not exist | Unknown resource ID |
| `409 Conflict` | Unique constraint conflict | Duplicate category name |
| `422 Unprocessable Entity` | Request validation failed | Invalid format, amount range, or enum |
| `500 Internal Server Error` | Unexpected server error | Unhandled failure |

Error responses use FastAPI's conventional `detail` field. Example:

```json
{
  "detail": "Category 'food' already exists"
}
```

## License

This project was built as a technical assignment for an internship application. **No license has been specified.**
