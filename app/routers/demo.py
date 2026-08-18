from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime
from app.database.db import db
from app.decision_engine.allocation import run_smart_allocation
from app.decision_engine.picking import optimize_picking_route
from app.decision_engine.exceptions import resolve_exception

router = APIRouter(prefix="/demo", tags=["Hackathon Demo Scenario"])

@router.post("/reset")
def reset_demo_state():
    """Resets database back to clean seed data for fresh demo presentation."""
    db.reset_to_seed()
    return {"status": "SUCCESS", "message": "Demo state reset to initial seed data successfully."}

@router.get("/scenario-status")
def get_scenario_status():
    """Returns current state of Order #1042, Order #1048, and primary inventory item."""
    ord_1042 = db.get_by_id("orders", "ord-1042")
    ord_1048 = db.get_by_id("orders", "ord-1048")
    sku_1042 = ord_1042["items"][0]["sku"] if ord_1042 and ord_1042.get("items") else "SKU-ELE-0001"
    
    inv_item = (
        db.get_by_id("inventory", f"inv-hyd-01-{sku_1042.lower()}")
        or db.get_by_id("inventory", sku_1042)
        or db.get_by_id("inventory", "inv-sku-shmp-001")
        or (db.get_collection("inventory")[0] if db.get_collection("inventory") else {"bin": "A-01", "availableQuantity": 7})
    )
    
    exceptions = [e for e in db.get_collection("exceptions") if "1042" in str(e.get("affectedEntity", "")) or "SHMP" in str(e.get("affectedEntity", ""))]
    decisions = [d for d in db.get_collection("decision_logs") if "1042" in str(d.get("entityId", ""))]

    return {
        "order1042": ord_1042,
        "order1048": ord_1048,
        "inventory": inv_item,
        "relatedExceptions": exceptions,
        "relatedDecisions": decisions,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/step/{step_number}")
def execute_demo_step(step_number: int):
    """Executes a specific step of the 16-step Hackathon Live Demo scenario."""
    now_iso = datetime.utcnow().isoformat()
    
    if step_number == 1:
        # Conflict Detection
        return {
            "step": 1,
            "title": "Stock Contention Detected",
            "details": "Order #1042 requires 10 units. Order #1048 requires 5 units. Available stock = 7 units.",
            "status": "DETECTED"
        }
        
    elif step_number == 2:
        # Priority Engine Evaluation
        db.update("orders", "ord-1042", {"priorityScore": 95, "priorityLevel": "CRITICAL"})
        db.update("orders", "ord-1048", {"priorityScore": 28, "priorityLevel": "LOW"})
        return {
            "step": 2,
            "title": "Priority Scoring Evaluated",
            "details": "Order #1042 scored 95/100 (CRITICAL SLA). Order #1048 scored 28/100 (LOW).",
            "status": "SCORED"
        }

    elif step_number == 3:
        # Smart Allocation Execution
        alloc_res = run_smart_allocation(order_id="ord-1042", user_name="Sarah Jenkins (Super Admin)")
        return {
            "step": 3,
            "title": "Smart Inventory Allocation Applied",
            "details": "Allocated 7/10 units to Order #1042. Order #1048 held in waiting queue.",
            "allocationResult": alloc_res,
            "status": "ALLOCATED"
        }

    elif step_number == 4:
        # Shortage & Replenishment Trigger
        db.add_notification(
            notif_type="CRITICAL",
            title="PO Generated: SKU-SHMP-001",
            message="Shortage of 3 units on Order #1042. Recommended PO of 200 units dispatched to Unilever Logistics.",
            role="INVENTORY_MANAGER",
            link="/inventory"
        )
        return {
            "step": 4,
            "title": "Shortage Calculated & Replenishment Recommended",
            "details": "3 units shortage calculated. Auto-generated Purchase Order recommendation for 200 units.",
            "status": "REPLENISHMENT_TRIGGERED"
        }

    elif step_number == 5:
        # Route Optimization & Picking Task
        route_opt = optimize_picking_route(["A-01", "A-04", "B-02", "C-01"])
        pick_task = {
            "id": "pick-demo-1042",
            "orderId": "ord-1042",
            "orderNumber": "ORD-1042",
            "priorityLevel": "CRITICAL",
            "assignedPickerName": "Marcus Vance",
            "status": "IN_PROGRESS",
            "items": [{"sku": "SKU-SHMP-001", "name": "Dove Deep Moisture Shampoo", "bin": "A-01", "quantity": 7, "picked": 7}],
            "unoptimizedRouteTimeMinutes": 18.0,
            "optimizedRouteTimeMinutes": 11.0,
            "timeSavedMinutes": 7.0,
            "routeSequence": ["A-01", "B-02", "C-01"],
            "currentStep": 3,
            "createdAt": now_iso
        }
        db.insert("picking_tasks", pick_task)
        db.update("orders", "ord-1042", {"status": "PICKING"})
        return {
            "step": 5,
            "title": "Picking Route Optimized",
            "details": "Route time reduced from 18 min to 11 min (Saved 7 minutes, +38.8% efficiency).",
            "task": pick_task,
            "status": "PICKING"
        }

    elif step_number == 6:
        # Simulated Damaged Item Exception during Packing/QC
        db.update("orders", "ord-1042", {"status": "EXCEPTION"})
        exc = {
            "id": "exc-demo-1042",
            "exceptionType": "DAMAGED_ITEM",
            "severity": "HIGH",
            "title": "Damaged Cap Seal on Order #1042",
            "problem": "1 unit of Dove Shampoo found with leaking cap seal at Packing Station 01.",
            "affectedEntity": "ORD-1042",
            "affectedId": "ord-1042",
            "detectedAt": now_iso,
            "recommendedDecision": "Quarantine damaged bottle, swap with inspected backup buffer unit from Bin A-01.",
            "resolutionPlan": "Replace leaking unit from reserve buffer, re-seal carton, and complete QC.",
            "status": "OPEN",
            "assignedUser": "Marcus Vance"
        }
        db.insert("exceptions", exc)
        return {
            "step": 6,
            "title": "Simulated Exception Created",
            "details": "1 damaged bottle detected during inspection. Exception logged in Exception Center.",
            "exception": exc,
            "status": "EXCEPTION_RAISED"
        }

    elif step_number == 7:
        # Resolve Exception & Complete QC
        resolve_res = resolve_exception("exc-demo-1042", "BUFFER_REPLACEMENT", "Marcus Vance", "Backup unit verified and replaced")
        db.update("orders", "ord-1042", {"status": "READY_TO_DISPATCH"})
        return {
            "step": 7,
            "title": "Exception Resolved & QC Passed",
            "details": "1-click automated resolution applied. Backup bottle swapped, QC passed, marked Ready to Dispatch.",
            "resolution": resolve_res,
            "status": "READY_TO_DISPATCH"
        }

    elif step_number == 8:
        # Final Dispatch
        trk_num = "SF-AWB-1042-998241"
        db.update("orders", "ord-1042", {
            "status": "DISPATCHED",
            "carrier": "StockFlow Priority Air Express",
            "trackingNumber": trk_num,
            "dispatchedAt": now_iso
        })
        db.log_audit(
            user="Marcus Vance",
            role="OPERATIONS_MANAGER",
            action="ORDER_DISPATCHED",
            entity="ORD-1042",
            prev_val="READY_TO_DISPATCH",
            newValue="DISPATCHED",
            reason="Handed over to StockFlow Priority Air Express"
        )
        return {
            "step": 8,
            "title": "Order #1042 Dispatched",
            "details": f"Fulfillment complete. Consignment in transit with StockFlow Priority Air Express (Tracking #{trk_num}). Full audit trail logged.",
            "status": "COMPLETED"
        }

    return {"status": "UNKNOWN_STEP"}
