from decimal import Decimal


def _cat(client, name="Food"):
    return client.post(
        "/categories/", json={"name": name, "color": "#FF0000"}
    ).json()


def test_amount_must_be_positive(client):
    cat = _cat(client)
    r = client.post(
        "/transactions/",
        json={
            "type": "expense",
            "amount": "0",
            "date": "2026-10-01",
            "category_id": cat["id"],
        },
    )
    assert r.status_code == 422


def test_amount_max_two_decimals(client):
    cat = _cat(client)
    r = client.post(
        "/transactions/",
        json={
            "type": "expense",
            "amount": "10.123",
            "date": "2026-10-01",
            "category_id": cat["id"],
        },
    )
    assert r.status_code == 422


def test_amount_max_limit(client):
    cat = _cat(client)
    r = client.post(
        "/transactions/",
        json={
            "type": "expense",
            "amount": "1000000.01",
            "date": "2026-10-01",
            "category_id": cat["id"],
        },
    )
    assert r.status_code == 422


def test_invalid_type(client):
    cat = _cat(client)
    r = client.post(
        "/transactions/",
        json={
            "type": "gift",
            "amount": "10.00",
            "date": "2026-10-01",
            "category_id": cat["id"],
        },
    )
    assert r.status_code == 422


def test_ordering_newest_first_and_last_added_wins(client):
    cat = _cat(client)
    for d, amt in [("2026-10-01", "1.00"), ("2026-10-02", "2.00"), ("2026-10-02", "3.00")]:
        client.post(
            "/transactions/",
            json={
                "type": "expense",
                "amount": amt,
                "date": d,
                "category_id": cat["id"],
            },
        )
    r = client.get("/transactions/")
    amounts = [Decimal(t["amount"]) for t in r.json()]
    assert amounts == [Decimal("3.00"), Decimal("2.00"), Decimal("1.00")]


def test_filters_combined(client):
    cat_a = _cat(client, "Food")
    cat_b = _cat(client, "Transport")
    client.post(
        "/transactions/",
        json={
            "type": "expense",
            "amount": "10.00",
            "date": "2026-10-05",
            "description": "Lunch with Bob",
            "category_id": cat_a["id"],
        },
    )
    client.post(
        "/transactions/",
        json={
            "type": "expense",
            "amount": "20.00",
            "date": "2026-10-06",
            "description": "Bus ticket",
            "category_id": cat_b["id"],
        },
    )
    r = client.get(
        "/transactions/?category_id=%d&description=lunch" % cat_a["id"]
    )
    data = r.json()
    assert len(data) == 1
    assert data[0]["description"] == "Lunch with Bob"
