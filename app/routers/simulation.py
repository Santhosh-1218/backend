from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, Optional
from app.decision_engine.simulation import simulation_engine
from app.decision_engine.inventory_intelligence import inventory_intel
from app.decision_engine.operations_intelligence import operations_intel
from app.core.security import get_current_user
from app.database.db import db

router = APIRouter(prefix="/simulation", tags=["Simulation & Real-Time Intelligence"])

@router.post("/step")
def trigger_simulation_step():
    """Executes a real simulation event and updates database state."""
    return simulation_engine.execute_next_simulation_event()

@router.get("/activity-stream")
def get_live_activity_stream(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None,
    limit: int = 25
):
    """Returns the live stream of timestamped warehouse operational events."""
    target_fc = fulfillmentCenterId or warehouseId
    return simulation_engine.get_activity_stream(warehouseId=target_fc, limit=limit)

@router.get("/intelligence/attention-needed")
def get_attention_needed(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None
):
    """Aggregates critical operational anomalies for 'WHAT NEEDS MY ATTENTION RIGHT NOW?'"""
    target_fc = fulfillmentCenterId or warehouseId
    stockouts = inventory_intel.detect_stockout_risks(warehouseId=target_fc)[:2]
    sla_risks = operations_intel.detect_packing_and_sla_risks(warehouseId=target_fc)[:2]
    mismatches = inventory_intel.detect_inventory_mismatches(warehouseId=target_fc)[:1]
    capacity = operations_intel.detect_zone_capacity_risks(warehouseId=target_fc)[:1]
    workloads = operations_intel.get_worker_workloads(warehouseId=target_fc)["recommendations"][:1]

    items = []
    for s in stockouts:
        items.append({
            "id": s["id"],
            "type": "STOCKOUT_RISK",
            "severity": "CRITICAL",
            "title": f"{s['sku']} — Stockout Predicted in ~{s['daysOfSupply']} days",
            "subtitle": f"{s['productName']} has {s['availableQuantity']} units left. Pending demand: {s['pendingDemand']}.",
            "actionLabel": "Replenish PO",
            "actionType": "REPLENISH",
            "targetId": s["sku"]
        })

    for r in sla_risks:
        items.append({
            "id": r["id"],
            "type": "SLA_RISK",
            "severity": "CRITICAL",
            "title": f"Order #{r['orderNumber']} — SLA Risk in {r['slaRemainingHours']}h",
            "subtitle": f"{r['customerName']} order in {r['currentStatus']} requires expedited dispatch before 18:00 cutoff.",
            "actionLabel": "Expedite Lane",
            "actionType": "EXPEDITE_SLA",
            "targetId": r["orderId"]
        })

    for m in mismatches:
        items.append({
            "id": m["id"],
            "type": "INVENTORY_MISMATCH",
            "severity": "HIGH",
            "title": f"{m['sku']} — Inventory Discrepancy ({m['difference']} units)",
            "subtitle": f"System: {m['systemQuantity']} vs Physical: {m['physicalQuantity']} in Bin {m['bin']}.",
            "actionLabel": "Investigate & Adjust",
            "actionType": "ADJUST_COUNT",
            "targetId": m["id"]
        })

    for w in workloads:
        items.append({
            "id": w["id"],
            "type": "WORKER_OVERLOAD",
            "severity": "HIGH",
            "title": f"Worker Overload — {w['overloadedWorker']} ({w['currentTasks']} tasks)",
            "subtitle": f"Exceeds max task threshold. Recommend transferring {w['tasksToMove']} waves to {w['targetWorker']}.",
            "actionLabel": "Rebalance Shift",
            "actionType": "REBALANCE_WORKLOAD",
            "targetId": w["id"]
        })

    return items

@router.get("/intelligence/stockouts")
def get_stockouts(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None
):
    target_fc = fulfillmentCenterId or warehouseId
    return inventory_intel.detect_stockout_risks(warehouseId=target_fc)

@router.get("/intelligence/expiries")
def get_expiries(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None
):
    target_fc = fulfillmentCenterId or warehouseId
    return inventory_intel.detect_expiry_risks(warehouseId=target_fc)

@router.get("/intelligence/mismatches")
def get_mismatches(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None
):
    target_fc = fulfillmentCenterId or warehouseId
    return inventory_intel.detect_inventory_mismatches(warehouseId=target_fc)

@router.post("/intelligence/resolve-mismatch")
def resolve_mismatch(
    payload: Dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)
):
    exception_id = payload.get("exceptionId")
    physical_quantity = int(payload.get("physicalQuantity", 92))
    reason = payload.get("reason", "Physical cycle count discrepancy confirmed and adjusted.")
    return inventory_intel.resolve_inventory_mismatch(exception_id, physical_quantity, user.get("name", "Manager"), reason)

@router.get("/intelligence/workloads")
def get_workloads(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None
):
    target_fc = fulfillmentCenterId or warehouseId
    return operations_intel.get_worker_workloads(warehouseId=target_fc)

@router.post("/intelligence/rebalance-workload")
def rebalance_workload(
    payload: Dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)
):
    overloaded = payload.get("overloadedWorkerId", "wrk-01")
    target = payload.get("targetWorkerId", "wrk-03")
    tasks = int(payload.get("tasksCount", 8))
    return operations_intel.rebalance_worker_tasks(overloaded, target, tasks, user.get("name", "Operations Manager"))

@router.get("/intelligence/sla-risks")
def get_sla_risks(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None
):
    target_fc = fulfillmentCenterId or warehouseId
    return operations_intel.detect_packing_and_sla_risks(warehouseId=target_fc)

@router.get("/intelligence/capacity-risks")
def get_capacity_risks(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None
):
    target_fc = fulfillmentCenterId or warehouseId
    return operations_intel.detect_zone_capacity_risks(warehouseId=target_fc)

@router.get("/intelligence/multi-warehouse")
def get_multi_warehouse():
    return inventory_intel.detect_multi_warehouse_imbalance()

@router.get("/intelligence/slow-moving")
def get_slow_moving(
    warehouseId: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None
):
    target_fc = fulfillmentCenterId or warehouseId
    return inventory_intel.detect_slow_moving_stock(warehouseId=target_fc)
