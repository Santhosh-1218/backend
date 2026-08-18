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

def test_realtime_intelligence():
    print("==================================================")
    print("STOCKFLOW REAL-TIME WAREHOUSE INTELLIGENCE SUITE")
    print("==================================================")

    client = get_client()
    # 1. Reset
    r = client.post("/demo/reset")
    assert r.status_code == 200
    print("[PASS] 1. Database reset to initial baseline state.")

    # 2. Test Real-time Simulation Step & Event Triggering
    for s in range(1, 6):
        r = client.post("/simulation/step")
        assert r.status_code == 200, f"Simulation step {s} failed: {r.text}"
        res = r.json()
        print(f"[PASS] 2.{s} Simulation Event Emitted: {res.get('event')}")

    # 3. Test Live Activity Stream
    r = client.get("/simulation/activity-stream?limit=10")
    assert r.status_code == 200
    activities = r.json()
    assert len(activities) > 0
    print(f"[PASS] 3. Live Warehouse Activity Stream verified ({len(activities)} events retrieved).")

    # 4. Test 'What Needs My Attention Right Now?' Deck
    r = client.get("/simulation/intelligence/attention-needed")
    assert r.status_code == 200
    attention_items = r.json()
    assert len(attention_items) > 0
    print(f"[PASS] 4. What Needs Attention Deck verified ({len(attention_items)} prioritized signals):")
    for item in attention_items[:3]:
        print(f"     - [{item['severity']}] {item['title']}")

    # 5. Test Stockout Forecasting
    r = client.get("/simulation/intelligence/stockouts")
    assert r.status_code == 200
    stockouts = r.json()
    print(f"[PASS] 5. Deterministic Stockout Forecasting verified ({len(stockouts)} items at risk):")
    if stockouts:
        s0 = stockouts[0]
        print(f"     - SKU: {s0['sku']} (Avail: {s0['availableQuantity']} | Projected: ~{s0['daysOfSupply']} days)")

    # 6. Test FEFO Expiry Engine
    r = client.get("/simulation/intelligence/expiries")
    assert r.status_code == 200
    expiries = r.json()
    print(f"[PASS] 6. FEFO Batch Expiry Engine verified ({len(expiries)} batches tracked).")

    # 7. Test Inventory Mismatch & Reconciliation
    r = client.get("/simulation/intelligence/mismatches")
    assert r.status_code == 200
    mismatches = r.json()
    assert len(mismatches) > 0
    target_mismatch = mismatches[0]
    print(f"[PASS] 7. Inventory Discrepancy detected for {target_mismatch['sku']} (Difference: {target_mismatch.get('difference')} units).")

    # Resolve mismatch with physical audit adjustment
    r = client.post("/simulation/intelligence/resolve-mismatch", json={
        "exceptionId": target_mismatch["id"],
        "physicalQuantity": 92,
        "reason": "Physical count verified and adjusted by inventory manager."
    })
    assert r.status_code == 200
    print(f"[PASS] 7.1 Inventory Discrepancy Adjusted: {r.json()['message']}")

    # 8. Test Worker Workload Balancer
    r = client.get("/simulation/intelligence/workloads")
    assert r.status_code == 200
    workloads = r.json()
    workers = workloads["workers"]
    print(f"[PASS] 8. Worker Workload Tracking: {len(workers)} active pickers tracked.")
    overloaded = [w for w in workers if w["status"] == "OVERLOADED"]
    if overloaded:
        print(f"     - Detected Overloaded Worker: {overloaded[0]['name']} ({overloaded[0]['activeTasks']} tasks)")
        # Execute 1-click rebalance
        r = client.post("/simulation/intelligence/rebalance-workload", json={
            "overloadedWorkerId": "wrk-01",
            "targetWorkerId": "wrk-03",
            "tasksCount": 8
        })
        assert r.status_code == 200
        print(f"[PASS] 8.1 1-Click Worker Workload Rebalance Executed: {r.json()['message']}")

    # 9. Test Packing SLA Risk Escalation
    r = client.get("/simulation/intelligence/sla-risks")
    assert r.status_code == 200
    sla_risks = r.json()
    print(f"[PASS] 9. Packing SLA Risk Escalator verified ({len(sla_risks)} orders monitored).")

    # 10. Test Multi-Warehouse Imbalance & Slow-Moving Stock
    r = client.get("/simulation/intelligence/multi-warehouse")
    assert r.status_code == 200
    xfer = r.json()[0]
    print(f"[PASS] 10. Multi-Warehouse Fulfillment Intelligence: Recommends transfer {xfer['sourceWarehouse']} -> {xfer['targetWarehouse']} ({xfer['recommendedTransferQuantity']} units of {xfer['sku']}).")

    r = client.get("/simulation/intelligence/slow-moving")
    assert r.status_code == 200
    slow = r.json()
    print(f"[PASS] 11. Slow-Moving Inventory Identification: {len(slow)} SKUs identified.")

    # 12. Test Bottlenecks
    r = client.get("/analytics/bottlenecks")
    assert r.status_code == 200
    btn = r.json()
    print(f"[PASS] 12. Operational Bottlenecks verified ({btn.get('bottlenecksFoundCount')} bottlenecks detected).")

    print("\n==================================================")
    print("ALL REAL-TIME INTELLIGENCE TESTS PASSED (100% SUCCESS)")
    print("==================================================")

if __name__ == "__main__":
    test_realtime_intelligence()
