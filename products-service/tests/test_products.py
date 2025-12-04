from app import app
def test_products_list():
    client = app.test_client()
    r = client.get("/products")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)