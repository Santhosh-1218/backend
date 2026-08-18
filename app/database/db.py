import json
import os
import threading
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from app.database.seed_data import generate_initial_data
from app.database.firestore_repo import firestore_repo

logger = logging.getLogger(__name__)

# Known Firebase registered accounts for zero-data-loss synchronization
KNOWN_FIREBASE_USERS = [
    {
        "id": "usr-admin-001",
        "uid": "o4UqOmbzqBV11AvwKahcjqF",
        "email": "admin@gmail.com",
        "name": "Super Admin",
        "fullName": "Super Admin (Network Director)",
        "role": "SUPER_ADMIN",
        "department": "Executive Network Operations",
        "warehouseId": "HYD-01",
        "assignedWarehouses": ["HYD-01", "MUM-01", "VJA-01", "MAH-01", "CHE-01"],
        "rfGunId": "HHT-9901",
        "shift": "General (24/7 Access)",
        "phone": "+91 98490 11001",
        "permissions": ["ALL"],
        "status": "ACTIVE",
        "createdAt": "2026-08-16T12:00:00Z",
        "createdBy": "Firebase Auth"
    },
    {
        "id": "usr-ooha-001",
        "uid": "YPpPh9tgrrSODwOMFO7pInF",
        "email": "ooha@gmail.com",
        "name": "Ooha",
        "fullName": "Ooha (Hyderabad Hub Director)",
        "role": "OPERATIONS_MANAGER",
        "department": "Warehouse Operations",
        "warehouseId": "HYD-01",
        "assignedWarehouses": ["HYD-01"],
        "rfGunId": "HHT-9902",
        "shift": "General Shift (08:00 - 17:00)",
        "phone": "+91 98490 22002",
        "permissions": ["ORDERS", "INVENTORY", "PICKING", "PACKING", "QC", "DISPATCH", "YMS", "RETURNS"],
        "status": "ACTIVE",
        "createdAt": "2026-08-16T12:00:00Z",
        "createdBy": "Firebase Auth"
    }
]

DUMMY_EMAILS_TO_REMOVE = set()

class DatabaseManager:
    """
    Authoritative Warehouse Database & Cloud Persistence Manager.
    Delegates to local persistent storage + Firestore Repository with thread-safe synchronized caching.
    Ensures users and operations data persist across server reloads and reboots.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def _init_db(self):
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        self.repo = firestore_repo
        
        # Persistent storage path (with fallback for serverless environments)
        try:
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(backend_dir, "data")
            os.makedirs(self.data_dir, exist_ok=True)
            self.db_file_path = os.path.join(self.data_dir, "stockflow_db.json")
        except Exception:
            # Fallback to /tmp on serverless environments like AWS Lambda / Vercel
            self.data_dir = os.path.join("/tmp", "stockflow_data")
            try:
                os.makedirs(self.data_dir, exist_ok=True)
            except Exception:
                pass
            self.db_file_path = os.path.join(self.data_dir, "stockflow_db.json")

        loaded = self._load_from_disk()
        if not loaded:
            self.reset_to_seed()
        else:
            self.ensure_integrity()

    def _save_to_disk(self):
        """Thread-safe disk persistence for state preservation."""
        try:
            temp_path = f"{self.db_file_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, default=str)
            if os.path.exists(self.db_file_path):
                os.replace(temp_path, self.db_file_path)
            else:
                os.rename(temp_path, self.db_file_path)
        except Exception as e:
            logger.debug(f"Persistence note (non-fatal in ephemeral environments): {e}")

    def _load_from_disk(self) -> bool:
        """Loads persisted state from disk if available."""
        if os.path.exists(self.db_file_path):
            try:
                with open(self.db_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "users" in data:
                        self.data = data
                        logger.info("Successfully loaded database from persistent disk storage.")
                        return True
            except Exception as e:
                logger.error(f"Error loading database from disk: {e}")
        return False

    def ensure_integrity(self):
        """Ensures only valid Firebase users exist and removes dummy accounts."""
        with self._lock:
            if "users" not in self.data:
                self.data["users"] = []
            
            # Filter out all dummy users
            self.data["users"] = [
                u for u in self.data["users"]
                if u.get("email", "").lower() not in DUMMY_EMAILS_TO_REMOVE
            ]
            
            existing_emails = {u.get("email", "").lower(): u for u in self.data["users"]}
            
            for k_user in KNOWN_FIREBASE_USERS:
                email_lower = k_user["email"].lower()
                if email_lower not in existing_emails:
                    new_user = dict(k_user)
                    new_user["createdAt"] = datetime.utcnow().isoformat()
                    new_user["createdBy"] = "Firebase Sync"
                    new_user["updatedAt"] = datetime.utcnow().isoformat()
                    self.data["users"].append(new_user)
                    existing_emails[email_lower] = new_user
                    logger.info(f"Restored Firebase user: {email_lower}")
                else:
                    # Update metadata
                    existing_emails[email_lower].update(k_user)

            # Ensure 5 StockFlow warehouses & 1000+ products
            seed = generate_initial_data()
            if "warehouses" not in self.data or len(self.data["warehouses"]) < 5:
                self.data["warehouses"] = seed.get("warehouses", [])
            if "products" not in self.data or len(self.data["products"]) < 500:
                self.data["products"] = seed.get("products", [])
            if "products" not in self.data or len(self.data["products"]) < 500:
                self.data["products"] = seed.get("products", [])
            if "inventory" not in self.data or len(self.data["inventory"]) < 500:
                self.data["inventory"] = seed.get("inventory", [])
            if "orders" not in self.data or len(self.data["orders"]) < 50:
                self.data["orders"] = seed.get("orders", [])

            # Ensure new enterprise collections exist
            if "dock_doors" not in self.data or not self.data["dock_doors"]:
                self.data["dock_doors"] = seed.get("dock_doors", [])
            if "returns" not in self.data or not self.data["returns"]:
                self.data["returns"] = seed.get("returns", [])
            if "climate_sensors" not in self.data or not self.data["climate_sensors"]:
                self.data["climate_sensors"] = seed.get("climate_sensors", [])

            self._save_to_disk()


    def sync_known_firebase_users(self) -> List[Dict[str, Any]]:
        """Explicit sync of Firebase users into active database."""
        with self._lock:
            self.ensure_integrity()
            return self.get_collection("users")

    def reset_to_seed(self):
        with self._lock:
            seed = generate_initial_data()
            
            default_settings = [
                {
                    "id": "global",
                    "criticalSlaWindowHours": 2.0,
                    "highSlaWindowHours": 6.0,
                    "smartWaveAllocationEnabled": True,
                    "tspRouteOptimizationEnabled": True,
                    "autoReplenishmentThreshold": 20,
                    "defaultWarehouseId": "WH-ALPHA-01",
                    "updatedAt": datetime.utcnow().isoformat(),
                    "updatedBy": "System Bootstrap"
                }
            ]

            self.data = {
                "users": seed["users"],
                "warehouses": seed["warehouses"],
                "products": seed["products"],
                "inventory": seed["inventory"],
                "orders": seed["orders"],
                "picking_tasks": seed["picking_tasks"],
                "packing_tasks": seed["packing_tasks"],
                "quality_checks": seed["quality_checks"],
                "exceptions": seed["exceptions"],
                "decision_logs": seed["decision_logs"],
                "audit_logs": seed["audit_logs"],
                "stock_movements": seed["stock_movements"],
                "notifications": seed["notifications"],
                "dock_doors": seed.get("dock_doors", []),
                "returns": seed.get("returns", []),
                "climate_sensors": seed.get("climate_sensors", []),
                "settings": default_settings
            }

            self.ensure_integrity()
            self._save_to_disk()


            # Sync baseline seed into Firestore repository
            for col_name, items in self.data.items():
                for it in items:
                    doc_id = it.get("id") or it.get("sku") or it.get("orderNumber") or f"{col_name[:4]}-{int(datetime.utcnow().timestamp()*1000)}"
                    self.repo.create_document(col_name, doc_id, it)

    # Generic CRUD methods
    def get_collection(self, name: str) -> List[Dict[str, Any]]:
        with self._lock:
            if name == "users":
                self.ensure_integrity()
            return [dict(x) for x in self.data.get(name, [])]

    def get_by_id(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            items = self.data.get(collection, [])
            item_id_str = str(item_id).strip()
            item_id_lower = item_id_str.lower()
            
            # Exact match first
            for it in items:
                if (
                    str(it.get("id", "")).lower() == item_id_lower
                    or str(it.get("orderNumber", "")).lower() == item_id_lower
                    or str(it.get("sku", "")).lower() == item_id_lower
                    or str(it.get("uid", "")).lower() == item_id_lower
                ):
                    return dict(it)

            # Suffix/prefix loose match (e.g. "ord-1042" -> "ORD-1042" or "inv-sku-shmp-001" -> first shampoo item)
            for it in items:
                if (
                    item_id_lower in str(it.get("id", "")).lower()
                    or item_id_lower in str(it.get("orderNumber", "")).lower()
                    or (it.get("sku") and str(it.get("sku", "")).lower() in item_id_lower)
                ):
                    return dict(it)
            return None

    def insert(self, collection: str, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if collection not in self.data:
                self.data[collection] = []
            
            doc_item = dict(item)
            if "id" not in doc_item:
                doc_item["id"] = f"{collection[:4]}-{int(datetime.utcnow().timestamp()*1000)}"
            if "createdAt" not in doc_item:
                doc_item["createdAt"] = datetime.utcnow().isoformat()
            if "updatedAt" not in doc_item:
                doc_item["updatedAt"] = datetime.utcnow().isoformat()

            self.data[collection].insert(0, doc_item)
            doc_id = doc_item["id"]
            self.repo.create_document(collection, doc_id, doc_item)
            self._save_to_disk()
            return dict(doc_item)

    def update(self, collection: str, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            items = self.data.get(collection, [])
            for it in items:
                if (
                    it.get("id") == item_id
                    or it.get("orderNumber") == item_id
                    or it.get("sku") == item_id
                    or it.get("uid") == item_id
                ):
                    it.update(updates)
                    it["updatedAt"] = datetime.utcnow().isoformat()
                    doc_id = it.get("id") or item_id
                    self.repo.update_document(collection, doc_id, it)
                    self._save_to_disk()
                    return dict(it)
            return None

    def delete(self, collection: str, item_id: str) -> bool:
        with self._lock:
            items = self.data.get(collection, [])
            for i, it in enumerate(items):
                if (
                    it.get("id") == item_id
                    or it.get("orderNumber") == item_id
                    or it.get("sku") == item_id
                    or it.get("uid") == item_id
                ):
                    self.data[collection].pop(i)
                    self.repo.delete_document(collection, item_id)
                    self._save_to_disk()
                    return True
            return False

    # Atomic Inventory Operations
    def allocate_inventory_atomic(
        self,
        sku: str,
        quantity_needed: int,
        order_number: str
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Atomically allocates inventory for a SKU.
        Guarantees availableQuantity never drops below 0.
        Returns (is_full_allocation, allocated_quantity, error_or_shortage_msg)
        """
        with self._lock:
            inv = self.get_by_id("inventory", sku)
            if not inv:
                return False, 0, f"SKU {sku} does not exist in warehouse inventory."

            avail = inv.get("availableQuantity", 0)
            if avail <= 0:
                return False, 0, f"Stockout: 0 units available for {sku}."

            if avail >= quantity_needed:
                allocated = quantity_needed
                new_avail = avail - allocated
                new_res = inv.get("reservedQuantity", 0) + allocated
                self.update("inventory", sku, {
                    "availableQuantity": new_avail,
                    "reservedQuantity": new_res
                })
                return True, allocated, None
            else:
                # Partial allocation
                allocated = avail
                shortage = quantity_needed - avail
                new_res = inv.get("reservedQuantity", 0) + allocated
                self.update("inventory", sku, {
                    "availableQuantity": 0,
                    "reservedQuantity": new_res
                })
                return False, allocated, f"Partial allocation: {allocated}/{quantity_needed} allocated. Shortage: {shortage} units."

    # Auditing helper
    def log_audit(
        self,
        user: str,
        role: str,
        action: str,
        entity: str,
        prev_val: Optional[str] = None,
        new_val: Optional[str] = None,
        reason: str = "",
        newValue: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        final_new_val = newValue if newValue is not None else new_val
        audit_entry = {
            "id": f"aud-{int(datetime.utcnow().timestamp()*1000)}",
            "timestamp": datetime.utcnow().isoformat(),
            "user": user,
            "userName": user,
            "userId": user_id or f"uid-{user.lower().replace(' ', '-')}",
            "role": role,
            "action": action,
            "entity": entity,
            "previousValue": prev_val,
            "newValue": final_new_val,
            "reason": reason,
            "metadata": metadata or {}
        }
        self.insert("audit_logs", audit_entry)

    # Decision log helper
    def log_decision(
        self,
        dec_type: str,
        entity_id: str,
        entity_type: str,
        situation: str,
        decision: str,
        reason: str,
        action: str,
        result: str,
        impact: str = "",
        approved_by: str = "SYSTEM_ENGINE",
        author_role: str = "SUPER_ADMIN"
    ):
        dec_entry = {
            "id": f"dec-{int(datetime.utcnow().timestamp()*1000)}",
            "timestamp": datetime.utcnow().isoformat(),
            "decisionType": dec_type,
            "entityId": entity_id,
            "entityType": entity_type,
            "situation": situation,
            "decision": decision,
            "reason": reason,
            "actionRequired": action,
            "resultExpected": result,
            "impact": impact,
            "approvedBy": approved_by,
            "author": approved_by,
            "role": author_role,
            "status": "APPLIED"
        }
        self.insert("decision_logs", dec_entry)

    # Notification helper
    def add_notification(
        self,
        notif_type: str,
        title: str,
        message: str,
        role: str = "ALL",
        link: Optional[str] = None
    ):
        notif = {
            "id": f"notif-{int(datetime.utcnow().timestamp()*1000)}",
            "type": notif_type,
            "title": title,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "read": False,
            "role": role,
            "targetRole": role,
            "link": link
        }
        self.insert("notifications", notif)

db = DatabaseManager()
