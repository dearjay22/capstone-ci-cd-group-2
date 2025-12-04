from app import app
def test_create_order():
    client = app.test_client()
    r = client.post("/orders", json={"user_id":1,"product_id":2})
    assert r.status_code == 201
    data = r.get_json()
    assert data["status"] == "created"