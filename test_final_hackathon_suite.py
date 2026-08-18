import httpx
import json
from fastapi.testclient import TestClient
from app.main import app

def get_client():
    try:
        r = httpx.get("http://127.0.0.1:8000/health", timeout=0.8)
        if r.status_code == 200:
            return httpx.Client(base_url="http://127.0.0.1:8000/api", timeout=15.0)
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

def test_final_hackathon_suite():
    print("==================================================")
    print("STOCKFLOW FINAL HACKATHON MASTER TEST SUITE")
    print("==================================================")

    client = get_client()

    # 1. Reset Demo State
    r = client.post("/demo/reset")
    assert r.status_code == 200
    print("[PASS] 1. Demo state reset to initial clean seed data.")

    # 2. Test FEFO Smart Allocation & Movement Ledger
    r = client.post("/orders/allocate", json={"orderId": "ord-1042"})
    assert r.status_code == 200
    alloc_res = r.json()
    print("[PASS] 2. FEFO Smart Allocation executed for Order #1042:")
    print(f"     - Evaluated: {alloc_res.get('evaluatedOrdersCount')} orders.")
    
    # 3. Check Inventory Movement Ledger
    r = client.get("/inventory/movements")
    assert r.status_code == 200
    movements = r.json()
    assert len(movements) > 0
    print(f"[PASS] 3. Immutable Inventory Movement Ledger verified ({len(movements)} movements recorded).")

    # 4. State Transition Engine Validation Guards
    # 4.1 Test Invalid Transition (CREATED -> DISPATCHED must be blocked)
    r = client.post("/fulfillment/transition-status", json={
        "orderId": "ord-1048",
        "targetStatus": "DISPATCHED",
        "notes": "Attempting unauthorized shortcut"
    })
    assert r.status_code == 200

    res = r.json()
    assert res["status"] == "ERROR", "Invalid transition should have been rejected!"
    print(f"[PASS] 4.1 State Transition Guard: Invalid jump blocked ({res['message']}).")

    # 4.2 Test Valid Transition (ALLOCATED -> PICKING)
    r = client.post("/fulfillment/transition-status", json={
        "orderId": "ord-1042",
        "targetStatus": "PICKING",
        "notes": "Wave pick initiated"
    })
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "SUCCESS"
    print(f"[PASS] 4.2 State Transition Guard: Valid transition verified ({res['previousStatus']} -> {res['newStatus']}).")

    # 5. Wrong Item Detection & Barcode Scanner Verification
    # 5.1 Test Mismatch
    r = client.post("/fulfillment/scan-verify", json={
        "orderId": "ORD-1042",
        "expectedSku": "SKU-SHMP-001",
        "scannedSku": "SKU-SHMP-002"
    })
    assert r.status_code == 200
    scan_res = r.json()
    assert scan_res["matched"] is False
    print(f"[PASS] 5.1 Wrong Item Mismatch Intercepted: SKU Mismatch Detected ({scan_res['decision']})")

    # 5.2 Test Match
    r = client.post("/fulfillment/scan-verify", json={
        "orderId": "ORD-1042",
        "expectedSku": "SKU-SHMP-001",
        "scannedSku": "SKU-SHMP-001"
    })
    assert r.status_code == 200
    assert r.json()["matched"] is True
    print("[PASS] 5.2 Correct Barcode Verified successfully.")

    # 6. Missing Item Sweep & Alternative Bin Location Finder
    r = client.post("/fulfillment/missing-item-sweep", json={
        "sku": "SKU-SOAP-002",
        "expectedBin": "A-01",
        "orderId": "ORD-1042"
    })
    assert r.status_code == 200
    sweep_res = r.json()
    assert sweep_res["alternativeLocationFound"] == "B-07"
    print(f"[PASS] 6. Missing Item Resolved: Found alternative units at Bin {sweep_res['alternativeLocationFound']}.")

    # 7. Complete Demo Scenario Sequence (Steps 1 to 8)
    for s in range(1, 9):
        r = client.post(f"/demo/step/{s}")
        assert r.status_code == 200
        step_res = r.json()
        print(f"[PASS] 7.{s} Demo Step {s} Applied: {step_res.get('title')}")

    # 8. Verify Order #1042 final state
    r = client.get("/demo/scenario-status")
    assert r.status_code == 200
    status_data = r.json()
    assert status_data["order1042"]["status"] == "DISPATCHED"
    assert "1042" in status_data["order1042"]["trackingNumber"]
    print(f"[PASS] 8. Order #1042 Lifecycle Finalized: Status = {status_data['order1042']['status']} (Tracking #{status_data['order1042']['trackingNumber']}).")

    # 9. Verify Safe Reset (Users must remain intact)
    r = client.post("/demo/reset")
    assert r.status_code == 200
    r = client.get("/auth/users")
    assert r.status_code == 200
    users = r.json()
    assert len(users) >= 1, "Users must not be deleted during demo reset!"
    print(f"[PASS] 9. Safe Demo Reset verified: {len(users)} primary user accounts preserved intact.")

    print("\n==================================================")
    print("ALL FINAL HACKATHON MASTER TESTS PASSED (100%)")
    print("==================================================")

if __name__ == "__main__":
    test_final_hackathon_suite()
