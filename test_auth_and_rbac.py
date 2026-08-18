import httpx
import json
from fastapi.testclient import TestClient
from app.main import app

def get_client():
    try:
        r = httpx.get("http://127.0.0.1:8000/health", timeout=0.8)
        if r.status_code == 200:
            return httpx.Client(base_url="http://127.0.0.1:8000/api", timeout=12.0)
    except Exception:
        pass

    class FastAPIApiClient:
        def __init__(self, app_instance):
            self.tc = TestClient(app_instance)
        def get(self, url, **kwargs):
            full_url = "/api" + url if not url.startswith("/api") else url
            return self.tc.get(full_url, **kwargs)
        def post(self, url, **kwargs):
            full_url = "/api" + url if not url.startswith("/api") else url
            return self.tc.post(full_url, **kwargs)
        def patch(self, url, **kwargs):
            full_url = "/api" + url if not url.startswith("/api") else url
            return self.tc.patch(full_url, **kwargs)
        def put(self, url, **kwargs):
            full_url = "/api" + url if not url.startswith("/api") else url
            return self.tc.put(full_url, **kwargs)
        def delete(self, url, **kwargs):
            full_url = "/api" + url if not url.startswith("/api") else url
            return self.tc.delete(full_url, **kwargs)

    return FastAPIApiClient(app)

def test_auth_and_rbac():
    print("==================================================")
    print("STOCKFLOW AUTHENTICATION & RBAC SECURITY TEST SUITE")
    print("==================================================")

    client = get_client()
    # 1. Reset db
    r = client.post("/demo/reset")
    assert r.status_code == 200
    print("[PASS] 1. Reset database to clean initial state.")

    # 2. Test Super Admin Login
    r = client.post("/auth/login", json={"email": "admin@stockflow.io", "role": "SUPER_ADMIN"})
    assert r.status_code == 200
    admin_data = r.json()
    assert admin_data["user"]["role"] == "SUPER_ADMIN"
    print(f"[PASS] 2. Super Admin Login Verified ({admin_data['user']['email']})")

    # 3. Test Inventory Manager Login
    r = client.post("/auth/login", json={"email": "inventory@stockflow.io", "role": "INVENTORY_MANAGER"})
    assert r.status_code == 200
    inv_data = r.json()
    assert inv_data["user"]["role"] == "INVENTORY_MANAGER"
    print(f"[PASS] 3. Inventory Manager Login Verified ({inv_data['user']['email']})")

    # 4. Test Super Admin User Creation
    admin_headers = {"X-User-Role": "SUPER_ADMIN", "X-User-Email": "admin@stockflow.io"}
    new_user_payload = {
        "id": "usr-test-099",
        "name": "Alex Taylor",
        "email": "alex.test@stockflow.io",
        "role": "OPERATIONS_MANAGER",
        "department": "Fulfillment Bay 4",
        "status": "ACTIVE",
        "warehouseId": "HYD-01"
    }
    r = client.post("/auth/users", json=new_user_payload, headers=admin_headers)
    assert r.status_code == 200, f"User creation failed: {r.text}"
    print(f"[PASS] 4. Super Admin created user: {new_user_payload['email']}")

    # 5. Test Non-Admin blocked from creating user (RBAC 403)
    inv_headers = {"X-User-Role": "INVENTORY_MANAGER", "X-User-Email": "inventory@stockflow.io"}
    r = client.post("/auth/users", json={"name": "Hacker", "email": "hacker@test.com", "role": "SUPER_ADMIN"}, headers=inv_headers)
    assert r.status_code == 403
    print("[PASS] 5. Unauthorized user creation blocked (403 Forbidden verified).")

    # 6. Test Disable User
    r = client.put("/auth/users/usr-test-099", json={"status": "DISABLED"}, headers=admin_headers)
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["status"] == "DISABLED"
    print("[PASS] 6. User account status disabled (status: DISABLED).")

    # 7. Check Audit Trail for Auth Events
    r = client.get("/analytics/audit-logs?limit=10")
    assert r.status_code == 200
    audits = r.json()
    actions = [a["action"] for a in audits]
    assert "USER_CREATED" in actions or "USER_DISABLED" in actions
    print(f"[PASS] 7. Auth Audit Events logged: {actions[:3]}")

    # 8. Test Hackathon Demo Scenario run
    for step in range(1, 9):
        r = client.post(f"/demo/step/{step}")
        assert r.status_code == 200
    print("[PASS] 8. Live Demo Scenario Step 1-8 executed seamlessly with database sync.")

    print("\n==================================================")
    print("ALL AUTH & RBAC SECURITY TESTS PASSED WITH 100% SUCCESS")
    print("==================================================")

if __name__ == "__main__":
    test_auth_and_rbac()
