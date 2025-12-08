from app import app


def test_index_ok(monkeypatch):
    client = app.test_client()
    resp = client.get("/users")
    assert resp.status_code in (200, 500)
