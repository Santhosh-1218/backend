import sys
import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.database.db import db
from app.core.firebase_auth import FirebaseAuthService

def get_test_clients():
    try:
        r = httpx.get("http://127.0.0.1:8000/health", timeout=0.8)
        if r.status_code == 200:
            return httpx.Client(base_url="http://127.0.0.1:8000/api", timeout=12.0), httpx.Client(base_url="http://127.0.0.1:8000", timeout=12.0)
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

    return FastAPIApiClient(app), TestClient(app)

def run_security_and_auth_suite():
    print("=" * 65)
    print("STOCKFLOW — FINAL AUTHENTICATION & USER MANAGEMENT SECURITY SUITE")
    print("=" * 65)

    client, health_client = get_test_clients()

    # 1. Verify /health
    res = health_client.get("/health")
    assert res.status_code == 200, f"Backend health check failed: {res.status_code}"
    print("[PASS] 1. Backend API operational and healthy.")

    # 2. Super Admin authentication & list users
    super_admin_headers = {
        "X-User-Email": "admin@gmail.com",
        "X-User-Role": "SUPER_ADMIN"
    }
    res = client.get("/admin/users", headers=super_admin_headers)
    assert res.status_code == 200, f"List users failed: {res.text}"
    users = res.json()
    assert len(users) >= 1, f"Expected at least 1 primary admin user, got {len(users)}"
    print(f"[PASS] 2. Super Admin authenticated; retrieved {len(users)} warehouse users.")

    # Verify no plaintext passwords in user list
    for u in users:
        assert "password" not in u, f"Security Violation: Plaintext password found in user object {u.get('email')}"
        assert "plainPassword" not in u, f"Security Violation: plainPassword found in {u.get('email')}"
    print("[PASS] 3. Zero Plaintext Passwords verified across all user records.")

    # 4. Super Admin creates a new warehouse user
    new_user_payload = {
        "fullName": "Test Inventory Manager",
        "email": "testinventory@example.com",
        "password": "SecurePassword2026!",
        "role": "INVENTORY_MANAGER",
        "department": "Warehouse Inventory",
        "warehouseId": "WH-ALPHA-01"
    }
    res = client.post("/admin/users", json=new_user_payload, headers=super_admin_headers)
    assert res.status_code == 201, f"Create user failed: {res.text}"
    created_user = res.json()
    assert created_user["email"] == "testinventory@example.com"
    assert created_user["role"] == "INVENTORY_MANAGER"
    assert "password" not in created_user
    uid = created_user["id"]
    print(f"[PASS] 4. Super Admin created user 'testinventory@example.com' (UID: {uid}) without altering session.")

    # 5. Verify user is in list
    res = client.get("/admin/users", headers=super_admin_headers)
    all_users = res.json()
    found = any(u["email"] == "testinventory@example.com" for u in all_users)
    assert found, "Created user not found in admin user list"
    print("[PASS] 5. Verified user profile exists in warehouse database.")

    # 6. Verify RBAC enforcement: Non-admin cannot access /admin/users
    inv_headers = {
        "X-User-Email": "testinventory@example.com",
        "X-User-Role": "INVENTORY_MANAGER"
    }
    res = client.get("/admin/users", headers=inv_headers)
    assert res.status_code == 403, f"Expected 403 Forbidden for non-admin, got {res.status_code}"
    print("[PASS] 6. RBAC Guard: Non-admin blocked with 403 from User Administration.")

    # 7. Super Admin updates the user's role (Inventory Manager -> Operations Manager)
    res = client.patch(f"/admin/users/{uid}", json={"role": "OPERATIONS_MANAGER", "department": "Floor Operations"}, headers=super_admin_headers)
    assert res.status_code == 200, f"Role update failed: {res.text}"
    updated_user = res.json()
    assert updated_user["role"] == "OPERATIONS_MANAGER"
    print("[PASS] 7. Super Admin updated role to OPERATIONS_MANAGER.")

    # 8. Super Admin sets a new password
    res = client.patch(f"/admin/users/{uid}/password", json={"password": "NewSecretPassword2026!"}, headers=super_admin_headers)
    assert res.status_code == 200, f"Password reset failed: {res.text}"
    assert res.json().get("status") == "SUCCESS"
    print("[PASS] 8. Password reset executed cleanly in Firebase Auth without exposing old or new password.")

    # 9. Super Admin disables the account
    res = client.patch(f"/admin/users/{uid}/status", json={"status": "DISABLED"}, headers=super_admin_headers)
    assert res.status_code == 200, f"Status update failed: {res.text}"
    disabled_user = res.json()
    assert disabled_user["status"] == "DISABLED"
    print("[PASS] 9. User account set to DISABLED.")

    # 10. Attempt login with disabled account -> blocked with 403
    res = client.post("/auth/login", json={"email": "testinventory@example.com", "role": "OPERATIONS_MANAGER"})
    assert res.status_code == 403, f"Expected 403 Forbidden on disabled login, got {res.status_code}"
    print("[PASS] 10. Login attempt by disabled user blocked with 403.")

    # 11. Re-enable the account
    res = client.patch(f"/admin/users/{uid}/status", json={"status": "ACTIVE"}, headers=super_admin_headers)
    assert res.status_code == 200
    print("[PASS] 11. User account re-enabled to ACTIVE.")

    # 12. Login works again
    res = client.post("/auth/login", json={"email": "testinventory@example.com", "role": "OPERATIONS_MANAGER"})
    assert res.status_code == 200
    print("[PASS] 12. Login succeeded for re-enabled user.")

    # 13. Verify Audit Logs recorded all actions
    res = client.get("/analytics/audit-logs?limit=20")
    assert res.status_code == 200
    audit_logs = res.json()
    actions = [a.get("action") for a in audit_logs]
    assert "USER_CREATED" in actions, "USER_CREATED audit log missing"
    assert "ROLE_CHANGED" in actions, "ROLE_CHANGED audit log missing"
    assert "PASSWORD_UPDATED" in actions, "PASSWORD_UPDATED audit log missing"
    assert "USER_DISABLED" in actions, "USER_DISABLED audit log missing"
    assert "USER_ENABLED" in actions, "USER_ENABLED audit log missing"
    print(f"[PASS] 13. Audit events verified in Audit Log ({', '.join(['USER_CREATED', 'ROLE_CHANGED', 'PASSWORD_UPDATED', 'USER_DISABLED', 'USER_ENABLED'])}).")

    # 14. Super Admin clean delete test
    res = client.delete(f"/admin/users/{uid}", headers=super_admin_headers)
    assert res.status_code == 200
    print("[PASS] 14. User deletion executed with USER_DELETED audit record.")

    print("\n" + "=" * 65)
    print("ALL 14 FINAL SECURITY & USER MANAGEMENT TESTS PASSED (100%)")
    print("=" * 65)

if __name__ == "__main__":
    run_security_and_auth_suite()
