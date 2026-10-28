def test_create_category_strips_whitespace(client):
    r = client.post("/categories/", json={"name": "  Food  ", "color": "#FF0000"})
    assert r.status_code == 201
    assert r.json()["name"] == "Food"


def test_create_category_duplicate_case_insensitive(client):
    client.post("/categories/", json={"name": "Food", "color": "#FF0000"})
    r = client.post("/categories/", json={"name": "food", "color": "#00FF00"})
    assert r.status_code == 409


def test_create_category_invalid_color(client):
    r = client.post("/categories/", json={"name": "Food", "color": "red"})
    assert r.status_code == 422


def test_create_category_name_too_long(client):
    r = client.post(
        "/categories/", json={"name": "x" * 31, "color": "#FF0000"}
    )
    assert r.status_code == 422


def test_list_categories_sorted_by_name(client):
    for n in ["Zebra", "Apple", "Mango"]:
        client.post("/categories/", json={"name": n, "color": "#000000"})
    r = client.get("/categories/")
    names = [c["name"] for c in r.json()]
    assert names == ["Apple", "Mango", "Zebra"]


def test_delete_category_with_transactions_fails(client):
    cat = client.post(
        "/categories/", json={"name": "Food", "color": "#FF0000"}
    ).json()
    client.post(
        "/transactions/",
        json={
            "type": "expense",
            "amount": "10.00",
            "date": "2026-10-01",
            "description": None,
            "category_id": cat["id"],
        },
    )
    r = client.delete(f"/categories/{cat['id']}")
    assert r.status_code == 400


def test_delete_category_removes_budgets(client):
    cat = client.post(
        "/categories/", json={"name": "Food", "color": "#FF0000"}
    ).json()
    client.put(f"/budgets/{cat['id']}/2026-10", json={"amount": "100.00"})
    r = client.delete(f"/categories/{cat['id']}")
    assert r.status_code == 204
    r = client.get("/budgets/?month=2026-10")
    assert r.json() == []
