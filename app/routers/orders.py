from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.database.db import db
from app.core.security import get_current_user
from app.decision_engine.priority import calculate_order_priority
from app.decision_engine.allocation import run_smart_allocation
from app.models.schemas import Order

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("")
def get_orders(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None,
    limit: int = 100
):
    orders = db.get_collection("orders")
    target_fc = fulfillmentCenterId or warehouseId
    
    if target_fc and target_fc != "ALL":
        orders = [
            o for o in orders 
            if o.get("fulfillmentCenterId") == target_fc or o.get("warehouseId") == target_fc
        ]
        
    if status and status != "ALL":
        orders = [o for o in orders if o.get("status", "").upper() == status.upper()]
    if priority and priority != "ALL":
        orders = [o for o in orders if o.get("priorityLevel", "").upper() == priority.upper()]
    if search:
        s = search.lower()
        orders = [o for o in orders if s in o.get("orderNumber", "").lower() or s in o.get("customerName", "").lower()]
        
    return orders[:limit]

@router.get("/{order_id}")
def get_order_details(order_id: str):
    order = db.get_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("")
def create_order(order: Order, current_user: dict = Depends(get_current_user)):
    order_data = order.model_dump()
    
    # Calculate initial priority
    score, level, reason = calculate_order_priority(order_data)
    order_data["priorityScore"] = score
    order_data["priorityLevel"] = level
    order_data["urgencyReason"] = reason
    order_data["status"] = "PRIORITIZED"

    created = db.insert("orders", order_data)

    db.log_decision(
        dec_type="PRIORITY_ASSIGNMENT",
        entity_id=order_data["orderNumber"],
        entity_type="ORDER",
        situation=f"New order {order_data['orderNumber']} created for {order_data['customerName']}.",
        decision=f"Assigned {level} Priority (Score {score}/100)",
        reason=reason,
        action="Queued for automated inventory checking and wave allocation.",
        result="Order prioritized in fulfillment stream."
    )

    db.log_audit(
        user=current_user.get("name", "Order Manager"),
        role=current_user.get("role", "ORDER_MANAGER"),
        action="ORDER_CREATED",
        entity=order_data["orderNumber"],
        prev_val=None,
        newValue=f"{level} (${order_data['totalAmount']})",
        reason="Order received from retailer EDI"
    )

    return created

@router.post("/prioritize-all")
def prioritize_all_orders(current_user: dict = Depends(get_current_user)):
    orders = db.get_collection("orders")
    updated_count = 0

    for o in orders:
        if o.get("status") in ["CREATED", "PRIORITIZED"]:
            score, level, reason = calculate_order_priority(o)
            db.update("orders", o["id"], {
                "priorityScore": score,
                "priorityLevel": level,
                "urgencyReason": reason,
                "status": "PRIORITIZED"
            })
            updated_count += 1

    return {
        "status": "SUCCESS",
        "prioritizedOrdersCount": updated_count,
        "message": f"Successfully evaluated and scored {updated_count} active orders."
    }

@router.post("/allocate")
def trigger_smart_allocation(payload: Optional[Dict[str, Any]] = None, current_user: dict = Depends(get_current_user)):
    order_id = payload.get("orderId") if payload else None
    user_name = current_user.get("name", "Order Manager")
    
    result = run_smart_allocation(order_id=order_id, user_name=user_name)
    return result
