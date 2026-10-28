def _post_cat(client, name):
    return client.post(
        "/categories/", json={"name": name, "color": "#FF0000"}
    ).json()


def _upload(client, content: str):
    return client.post(
        "/import/transactions",
        files={"file": ("data.csv", content.encode("utf-8"), "text/csv")},
    )


def test_csv_import_happy_path(client):
    _post_cat(client, "Eating out")
    _post_cat(client, "Other")
    csv_content = (
        "type,amount,date,description,category\n"
        "expense,12.50,2026-10-08,Lunch,Eating out\n"
        "income,300.00,2026-10-09,,Other\n"
    )
    r = _upload(client, csv_content)
    assert r.status_code == 200
    data = r.json()
    assert data["imported"] == 2
    assert data["errors"] == []

    txs = client.get("/transactions/").json()
    assert len(txs) == 2


def test_csv_import_case_insensitive_category(client):
    _post_cat(client, "Food")
    csv_content = (
        "type,amount,date,description,category\n"
        "expense,5.00,2026-10-01,x,fOOd\n"
    )
    r = _upload(client, csv_content)
    assert r.status_code == 200
    assert r.json()["imported"] == 1


def test_csv_import_reports_missing_category(client):
    csv_content = (
        "type,amount,date,description,category\n"
        "expense,5.00,2026-10-01,x,Doesnotexist\n"
    )
    r = _upload(client, csv_content)
    data = r.json()
    assert data["imported"] == 0
    assert len(data["errors"]) == 1
    assert data["errors"][0]["row"] == 2
    assert "does not exist" in data["errors"][0]["error"]


def test_csv_import_invalid_amount(client):
    _post_cat(client, "Food")
    csv_content = (
        "type,amount,date,description,category\n"
        "expense,-5.00,2026-10-01,x,Food\n"
        "expense,5.00,not-a-date,x,Food\n"
        "expense,5.00,2026-10-01,x,Food\n"
    )
    r = _upload(client, csv_content)
    data = r.json()
    assert data["imported"] == 1
    rows_with_errors = {e["row"] for e in data["errors"]}
    assert rows_with_errors == {2, 3}


def test_csv_import_missing_columns(client):
    csv_content = "type,amount\nfoo,1\n"
    r = _upload(client, csv_content)
    assert r.status_code == 400
