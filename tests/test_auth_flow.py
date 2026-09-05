import os
os.environ["DATABASE_URL"] = "sqlite:///./test_fenix.db"
os.environ["JWT_SECRET"] = "test-secret-please-change"
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_register_login():
    username = "tester_auth_flow"
    r = client.post("/api/auth/register", json={"username": username, "display_name": "Tester", "password": "test123456"})
    assert r.status_code in (201, 409)
    if r.status_code == 409:
        r = client.post("/api/auth/login", json={"username": username, "password": "test123456"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == username
