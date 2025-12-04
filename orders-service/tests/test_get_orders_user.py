from app import app
def test_get_orders_for_user_empty():
    client = app.test_client()
    r = client.get("/orders/user/1")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)