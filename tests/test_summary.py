from decimal import Decimal


def _post_cat(client, name, color="#FF0000"):
    return client.post(
        "/categories/", json={"name": name, "color": color}
    ).json()


def _post_tx(client, cat_id, type_, amount, date, desc=None):
    return client.post(
        "/transactions/",
        json={
            "type": type_,
            "amount": amount,
            "date": date,
            "description": desc,
            "category_id": cat_id,
        },
    )


def test_summary_empty_month(client):
    r = client.get("/summary/?month=2026-10")
    assert r.status_code == 200
    data = r.json()
    assert Decimal(data["total_income"]) == Decimal("0.00")
    assert Decimal(data["total_expense"]) == Decimal("0.00")
    assert Decimal(data["balance"]) == Decimal("0.00")
    assert data["categories"] == []


def test_summary_totals_and_balance(client):
    cat = _post_cat(client, "Food")
    _post_tx(client, cat["id"], "income", "300.00", "2026-10-01")
    _post_tx(client, cat["id"], "expense", "50.00", "2026-10-15")
    _post_tx(client, cat["id"], "expense", "25.00", "2026-10-20")
    _post_tx(client, cat["id"], "expense", "999.00", "2026-09-30")

    data = client.get("/summary/?month=2026-10").json()
    assert Decimal(data["total_income"]) == Decimal("300.00")
    assert Decimal(data["total_expense"]) == Decimal("75.00")
    assert Decimal(data["balance"]) == Decimal("225.00")


def test_summary_per_category_and_sorting(client):
    food = _post_cat(client, "Food")
    transport = _post_cat(client, "Transport")
    rent = _post_cat(client, "Rent")

    _post_tx(client, food["id"], "expense", "200.00", "2026-10-01")
    _post_tx(client, transport["id"], "expense", "50.00", "2026-10-02")
    _post_tx(client, rent["id"], "expense", "700.00", "2026-10-03")

    utilities = _post_cat(client, "Utilities")
    client.put(f"/budgets/{food['id']}/2026-10", json={"amount": "250.00"})
    client.put(f"/budgets/{utilities['id']}/2026-10", json={"amount": "100.00"})

    data = client.get("/summary/?month=2026-10").json()
    cats = data["categories"]
    names = [c["category_name"] for c in cats]
    assert names == ["Rent", "Food", "Transport", "Utilities"]

    rent_row = cats[0]
    assert Decimal(rent_row["spent"]) == Decimal("700.00")
    assert Decimal(rent_row["budget"]) == Decimal("0.00")
    assert Decimal(rent_row["remaining"]) == Decimal("-700.00")

    food_row = next(c for c in cats if c["category_name"] == "Food")
    assert Decimal(food_row["spent"]) == Decimal("200.00")
    assert Decimal(food_row["budget"]) == Decimal("250.00")
    assert Decimal(food_row["remaining"]) == Decimal("50.00")

    util_row = next(c for c in cats if c["category_name"] == "Utilities")
    assert Decimal(util_row["spent"]) == Decimal("0.00")
    assert Decimal(util_row["budget"]) == Decimal("100.00")
    assert Decimal(util_row["remaining"]) == Decimal("100.00")


def test_summary_tie_sorted_by_name(client):
    a = _post_cat(client, "Zebra")
    b = _post_cat(client, "Apple")
    _post_tx(client, a["id"], "expense", "10.00", "2026-10-01")
    _post_tx(client, b["id"], "expense", "10.00", "2026-10-02")
    data = client.get("/summary/?month=2026-10").json()
    names = [c["category_name"] for c in data["categories"]]
    assert names == ["Apple", "Zebra"]
