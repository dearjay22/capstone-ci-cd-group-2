from app import app


def test_create_user_bad_payload():
    client = app.test_client()
    r = client.post("/users", json={})
    assert r.status_code == 400
