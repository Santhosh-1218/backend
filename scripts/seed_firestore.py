import sys
import os

# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.seed_data import generate_initial_data
from app.database.firestore_repo import firestore_repo
from app.core.firebase_auth import FirebaseAuthService

def seed_firestore_idempotent():
    print("=" * 65)
    print("STOCKFLOW -- CLOUD FIRESTORE IDEMPOTENT SEEDING & IMPORT SCRIPT")
    print("=" * 65)

    # 1. Bootstrap primary Super Admin in Firebase Authentication
    print("[1/3] Ensuring Primary Super Admin in Firebase Auth...")
    FirebaseAuthService.bootstrap_super_admin()

    # 2. Generate Seed Data Dictionary
    print("[2/3] Generating baseline warehouse dataset...")
    seed = generate_initial_data()
    
    # 3. Seed into Cloud Firestore Repository
    print("[3/3] Importing collections idempotently into Cloud Firestore...")
    
    total_records = 0

    # A. Warehouses
    for w in seed["warehouses"]:
        firestore_repo.create_document("warehouses", w["id"], w)
        total_records += 1
    print(f"  [OK] Seeded {len(seed['warehouses'])} warehouses (WH-ALPHA-01)")

    # B. Products
    for p in seed["products"]:
        firestore_repo.create_document("products", p["sku"], p)
        total_records += 1
    print(f"  [OK] Seeded {len(seed['products'])} products")

    # C. Inventory Bins
    for inv in seed["inventory"]:
        firestore_repo.create_document("inventory", inv["sku"], inv)
        total_records += 1
    print(f"  [OK] Seeded {len(seed['inventory'])} inventory bin records")

    # D. Orders
    for ord_doc in seed["orders"]:
        firestore_repo.create_document("orders", ord_doc["orderNumber"], ord_doc)
        total_records += 1
    print(f"  [OK] Seeded {len(seed['orders'])} orders (including ORD-1042, ORD-1048)")

    # E. Fulfillment Tasks
    for p in seed["picking_tasks"]:
        firestore_repo.create_document("picking_tasks", p["id"], p)
        total_records += 1
    for pk in seed["packing_tasks"]:
        firestore_repo.create_document("packing_tasks", pk["id"], pk)
        total_records += 1
    for qc in seed["quality_checks"]:
        firestore_repo.create_document("quality_checks", qc["id"], qc)
        total_records += 1
    print("  [OK] Seeded picking, packing, and quality check tasks")

    # F. Exceptions
    for exc in seed["exceptions"]:
        firestore_repo.create_document("exceptions", exc["id"], exc)
        total_records += 1
    print(f"  [OK] Seeded {len(seed['exceptions'])} active exception scenarios")

    # G. Decision Logs & Audit Logs
    for d in seed["decision_logs"]:
        firestore_repo.create_document("decision_logs", d["id"], d)
        total_records += 1
    for aud in seed["audit_logs"]:
        firestore_repo.create_document("audit_logs", aud["id"], aud)
        total_records += 1
    print(f"  [OK] Seeded {len(seed['decision_logs'])} decision logs & {len(seed['audit_logs'])} audit trail records")

    # H. Stock Movements & Notifications
    for sm in seed["stock_movements"]:
        firestore_repo.create_document("stock_movements", sm["id"], sm)
        total_records += 1
    for n in seed["notifications"]:
        firestore_repo.create_document("notifications", n["id"], n)
        total_records += 1
    print(f"  [OK] Seeded stock movements & operational alerts")

    # I. Global Settings
    settings_doc = {
        "id": "global",
        "criticalSlaWindowHours": 2.0,
        "highSlaWindowHours": 6.0,
        "smartWaveAllocationEnabled": True,
        "tspRouteOptimizationEnabled": True,
        "autoReplenishmentThreshold": 20,
        "defaultWarehouseId": "WH-ALPHA-01"
    }
    firestore_repo.create_document("settings", "global", settings_doc)
    total_records += 1
    print("  [OK] Seeded global warehouse configuration (settings/global)")

    # J. Users
    for u in seed["users"]:
        firestore_repo.create_document("users", u.get("uid") or u.get("id"), u)
        total_records += 1
    print(f"  [OK] Seeded {len(seed['users'])} primary Super Admin profile (users/uid-admin-001)")

    print("=" * 65)
    print(f"SUCCESS: Idempotent seeding complete ({total_records} records synchronized).")
    print("=" * 65)

if __name__ == "__main__":
    seed_firestore_idempotent()
