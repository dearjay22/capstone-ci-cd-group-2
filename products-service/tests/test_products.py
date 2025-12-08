from app import app


def test_get_all_products(monkeypatch):
    client = app.test_client()

    def mock_fetch_products():
        return [{"id": 1, "name": "Laptop"}]

    monkeypatch.setattr("app.fetch_products", mock_fetch_products)

    resp = client.get("/products")
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    assert resp.json[0]["name"] == "Laptop"


def test_get_product_by_id(monkeypatch):
    client = app.test_client()

    def mock_fetch_product(product_id):
        return {"id": product_id, "name": "Phone"}

    monkeypatch.setattr("app.fetch_product", mock_fetch_product)

    resp = client.get("/products/1")
    assert resp.status_code == 200
    assert resp.json["name"] == "Phone"


def test_get_product_not_found(monkeypatch):
    client = app.test_client()

    def mock_fetch_product(product_id):
        return None

    monkeypatch.setattr("app.fetch_product", mock_fetch_product)

    resp = client.get("/products/999")
    assert resp.status_code == 404


def test_create_product(monkeypatch):
    client = app.test_client()

    def mock_create_product(data):
        return {"id": 10, "name": data["name"]}

    monkeypatch.setattr("app.create_product", mock_create_product)

    resp = client.post("/products", json={"name": "TV"})
    assert resp.status_code == 201
    assert resp.json["name"] == "TV"


def test_create_product_bad_payload():
    client = app.test_client()
    resp = client.post("/products", json={})
    assert resp.status_code == 400
