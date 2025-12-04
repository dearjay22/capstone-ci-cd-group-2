from app import app
def test_add_product():
    client = app.test_client()
    r = client.post("/products", json={"name":"Thing","price":3.5})
    assert r.status_code == 201
    data = r.get_json()
    assert data["name"] == "Thing"