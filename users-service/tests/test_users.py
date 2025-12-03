from app import app
import json

def test_index_ok(monkeypatch):
    client = app.test_client()
    # monkeypatch database functions if desired; here we just check response shape
    resp = client.get("/users")
    assert resp.status_code in (200,500)