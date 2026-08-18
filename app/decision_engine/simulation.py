import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.db import db

class WarehouseSimulationEngine:
    """
    Real-time warehouse simulation engine that continuously emits operational events,
    mutates actual database state, updates inventory and order lifecycles, and feeds
    the live activity stream.
    """

    def __init__(self):
        self.is_running = False
        self.current_step = 0
        self._thread = None
        self._lock = threading.Lock()
        self.events_history = []
        self._init_default_events()

    def _init_default_events(self):
        now = datetime.utcnow()
        self.events_history = [
            {
                "id": "evt-001",
                "timestamp": now.strftime("%H:%M:%S"),
                "type": "NEW_ORDER",
                "message": "Retail Order #ORD-1092 received from Metro Hypermarket ($4,250.00)",
                "entity": "ORD-1092",
                "severity": "INFO",
                "zone": "Zone A"
            },
            {
                "id": "evt-002",
                "timestamp": now.strftime("%H:%M:%S"),
                "type": "ORDER_PRIORITIZED",
                "message": "Priority Engine assigned CRITICAL SLA (Score: 94/100) to Order #ORD-1092",
                "entity": "ORD-1092",
                "severity": "CRITICAL",
                "zone": "Zone A"
            },
            {
                "id": "evt-003",
                "timestamp": now.strftime("%H:%M:%S"),
                "type": "INVENTORY_ALLOCATED",
                "message": "Allocated 12 units of Dove Shampoo (Bin A-01) with 0 shortage",
                "entity": "SKU-SHMP-001",
                "severity": "SUCCESS",
                "zone": "Zone A"
            },
            {
                "id": "evt-004",
                "timestamp": now.strftime("%H:%M:%S"),
                "type": "PICKING_OPTIMIZED",
                "message": "TSP Router generated optimized pick sequence A-01 -> B-02 (Saved 6.4 mins)",
                "entity": "TASK-PICK-92",
                "severity": "INFO",
                "zone": "Zone A"
            }
        ]

    def log_event(self, event_type: str, message: str, entity: str, severity: str = "INFO", zone: str = "Zone A"):
        event = {
            "id": f"evt-{int(datetime.utcnow().timestamp()*1000)}",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "type": event_type,
            "message": message,
            "entity": entity,
            "severity": severity,
            "zone": zone
        }
        with self._lock:
            self.events_history.insert(0, event)
            if len(self.events_history) > 100:
                self.events_history.pop()

    def get_activity_stream(self, warehouseId: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        with self._lock:
            return self.events_history[:limit]

    def execute_next_simulation_event(self) -> Dict[str, Any]:
        with self._lock:
            self.current_step = (self.current_step + 1) % 10
            step = self.current_step

        if step == 1:
            # Event 1: New order received
            new_ord = {
                "id": f"ord-sim-{int(time.time())}",
                "orderNumber": f"ORD-SIM-{int(time.time()) % 10000}",
                "customerName": "Reliance Retail Mart",
                "customerType": "KEY_ACCOUNT",
                "status": "CREATED",
                "priorityLevel": "CRITICAL",
                "priorityScore": 96,
                "urgencyReason": "Tier-1 Contractual 2h Dispatch Guarantee",
                "slaRemainingHours": 1.8,
                "items": [
                    {
                        "sku": "SKU-SHMP-001",
                        "productName": "Dove Deep Moisture Shampoo",
                        "quantityRequested": 8,
                        "quantityAllocated": 0,
                        "unitPrice": 4.50
                    }
                ],
                "totalAmount": 36.00,
                "allocationStatus": "PENDING",
                "shortageCount": 0
            }
            db.insert("orders", new_ord)
            self.log_event("NEW_ORDER", f"Urgent Retail Order #{new_ord['orderNumber']} received from {new_ord['customerName']}", new_ord["orderNumber"], "CRITICAL", "Zone A")
            return {"step": step, "event": "NEW_ORDER", "order": new_ord}

        elif step == 2:
            # Event 2: Priority Engine evaluation
            self.log_event("ORDER_PRIORITY_CHANGED", "Deterministic Priority Engine scored Order #1042 at 95/100 (CRITICAL SLA)", "ORD-1042", "CRITICAL", "Zone A")
            return {"step": step, "event": "ORDER_PRIORITY_CHANGED"}

        elif step == 3:
            # Event 3: Stock Contention & Smart Allocation
            inv_item = next((i for i in db.get_collection("inventory") if i.get("sku") == "SKU-SHMP-001"), None)
            if inv_item:
                db.update("inventory", inv_item["id"], {
                    "reservedQuantity": inv_item.get("reservedQuantity", 0) + 7,
                    "availableQuantity": max(0, inv_item.get("availableQuantity", 7) - 7)
                })
            self.log_event("INVENTORY_ALLOCATED", "Smart Allocation allocated 7 units to critical Order #1042; Order #1048 held", "SKU-SHMP-001", "SUCCESS", "Zone A")
            return {"step": step, "event": "INVENTORY_ALLOCATED"}

        elif step == 4:
            # Event 4: Picking task created with TSP Optimization
            self.log_event("PICKING_STARTED", "Picker Marcus Vance initiated Wave Pick #W-1042 (TSP route: 11 min vs 18 min standard)", "W-1042", "INFO", "Zone A")
            return {"step": step, "event": "PICKING_STARTED"}

        elif step == 5:
            # Event 5: Damaged item exception
            exc = {
                "id": f"exc-sim-{int(time.time())}",
                "type": "DAMAGED_ITEM",
                "severity": "HIGH",
                "sku": "SKU-SHMP-001",
                "productName": "Dove Deep Moisture Shampoo",
                "bin": "A-01",
                "reportedBy": "Marcus Vance",
                "status": "OPEN",
                "situation": "1 leaking bottle seal detected during pick inspection.",
                "decision": "Swap with verified unit from safety reserve buffer Bin A-04.",
                "reason": "Prevents entire wave delay while maintaining 100% Quality Check compliance.",
                "recommendedAction": "Approve buffer replacement and log damaged unit write-off."
            }
            db.insert("exceptions", exc)
            self.log_event("ITEM_DAMAGED", "Damaged bottle seal detected at Bin A-01. Exception logged.", "EXC-DAMAGED", "WARNING", "Zone A")
            return {"step": step, "event": "ITEM_DAMAGED", "exception": exc}

        elif step == 6:
            # Event 6: 1-Click Automated Exception Resolution
            self.log_event("EXCEPTION_RESOLVED", "Automated Resolution applied: Swapped backup unit from Bin A-04. QC Verified.", "EXC-DAMAGED", "SUCCESS", "Zone A")
            return {"step": step, "event": "EXCEPTION_RESOLVED"}

        elif step == 7:
            # Event 7: Packing & 6-Point QA Checklist
            self.log_event("QUALITY_CHECK_COMPLETED", "6-Point QA Checklist passed (Barcode, Seal, Expiry, Weight, Fragility, Packaging)", "ORD-1042", "SUCCESS", "Zone B")
            return {"step": step, "event": "QUALITY_CHECK_COMPLETED"}

        elif step == 8:
            # Event 8: Carrier Dispatch
            ord1042 = next((o for o in db.get_collection("orders") if o.get("orderNumber") == "ORD-1042"), None)
            if ord1042:
                db.update("orders", ord1042["id"], {
                    "status": "DISPATCHED",
                    "carrier": "FedEx Priority Freight",
                    "trackingNumber": "TRK-FEDEX-9982410"
                })
            self.log_event("ORDER_DISPATCHED", "Order #1042 handed over to FedEx Priority Freight (Tracking #TRK-FEDEX-9982410)", "ORD-1042", "SUCCESS", "Dock 1")
            return {"step": step, "event": "ORDER_DISPATCHED"}

        elif step == 9:
            # Event 9: Stockout prediction & Auto Purchase Order
            self.log_event("STOCKOUT_RISK_DETECTED", "Deterministic Predictor flagged SKU-SHMP-001 (0 units left). Auto-generated PO #PO-AUTO-9821 for 200 units", "SKU-SHMP-001", "CRITICAL", "Zone A")
            return {"step": step, "event": "STOCKOUT_RISK_DETECTED"}

        else:
            # Event 10: Zone B Bottleneck alert & Rebalance Recommendation
            self.log_event("PICKING_BOTTLENECK", "Zone B picking latency detected (+46% above benchmark). Rebalance recommendation created.", "Zone B", "WARNING", "Zone B")
            return {"step": step, "event": "PICKING_BOTTLENECK"}

simulation_engine = WarehouseSimulationEngine()
