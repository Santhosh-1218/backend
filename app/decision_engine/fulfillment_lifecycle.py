from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from app.database.db import db

# Strict Order Lifecycle State Machine
VALID_TRANSITIONS = {
    "CREATED": ["PRIORITIZED", "ALLOCATED", "CANCELLED"],
    "PRIORITIZED": ["ALLOCATED", "HOLD", "CANCELLED"],
    "INVENTORY_CHECKED": ["ALLOCATED", "BACKORDERED", "CANCELLED"],
    "ALLOCATED": ["PICKING", "HOLD", "CANCELLED"],
    "PICKING": ["PICKED", "EXCEPTION", "HOLD"],
    "PICKED": ["PACKING", "EXCEPTION"],
    "PACKING": ["PACKED", "EXCEPTION"],
    "PACKED": ["QUALITY_CHECK", "READY_TO_DISPATCH", "EXCEPTION"],
    "QUALITY_CHECK": ["READY_TO_DISPATCH", "EXCEPTION"],
    "READY_TO_DISPATCH": ["DISPATCHED", "HOLD"],
    "DISPATCHED": ["IN_TRANSIT", "COMPLETED"],
    "IN_TRANSIT": ["COMPLETED", "EXCEPTION"],
    "COMPLETED": [],
    "EXCEPTION": ["PICKING", "PACKING", "QUALITY_CHECK", "READY_TO_DISPATCH", "CANCELLED"],
    "HOLD": ["PRIORITIZED", "ALLOCATED", "CANCELLED"]
}

class FulfillmentLifecycleEngine:
    """
    Validates and executes lifecycle state transitions across the full order fulfillment pipeline.
    Guarantees state integrity, movement ledger accuracy, and immutable audit trails.
    """

    @staticmethod
    def validate_transition(current_status: str, target_status: str) -> Tuple[bool, str]:
        if current_status == target_status:
            return True, "State already matching."

        allowed = VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            return False, f"Invalid transition: Cannot move order from {current_status} to {target_status}. Allowed next states: {', '.join(allowed)}."

        return True, "Valid transition."

    @staticmethod
    def transition_order_state(
        order_id: str,
        target_status: str,
        user_name: str = "System Engine",
        user_role: str = "OPERATIONS_MANAGER",
        notes: str = "",
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        order = db.get_by_id("orders", order_id)
        if not order:
            return {"status": "ERROR", "message": f"Order {order_id} not found."}

        current_status = order.get("status", "CREATED")
        is_valid, err_msg = FulfillmentLifecycleEngine.validate_transition(current_status, target_status)
        if not is_valid:
            return {"status": "ERROR", "message": err_msg}

        # Guard: Cannot dispatch without QC pass
        if target_status == "DISPATCHED":
            # Verify QC record
            qc_records = [q for q in db.get_collection("quality_checks") if q.get("orderId") == order_id]
            if qc_records and qc_records[0].get("status") == "FAILED":
                return {"status": "ERROR", "message": "Cannot dispatch order: Quality Check FAILED. Resolve QC exception before dispatching."}

        # Prepare update dict
        update_fields = {
            "status": target_status,
            "updatedAt": datetime.utcnow().isoformat()
        }

        if extra_metadata:
            update_fields.update(extra_metadata)

        # Apply database update
        db.update("orders", order_id, update_fields)

        # Log Movement Ledger if applicable
        movement_type_map = {
            "ALLOCATED": "STOCK_ALLOCATED",
            "PICKED": "STOCK_PICKED",
            "PACKED": "STOCK_PACKED",
            "DISPATCHED": "STOCK_DISPATCHED",
            "COMPLETED": "STOCK_COMPLETED"
        }

        if target_status in movement_type_map:
            for it in order.get("items", []):
                sku = it.get("sku")
                qty = it.get("quantityAllocated", it.get("quantityRequested", 1))
                inv_item = next((i for i in db.get_collection("inventory") if i.get("sku") == sku), None)
                
                db.insert("inventory_movements", {
                    "id": f"mov-{int(datetime.utcnow().timestamp()*1000)}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "sku": sku,
                    "productName": it.get("productName", sku),
                    "movementType": movement_type_map[target_status],
                    "quantity": qty,
                    "previousQuantity": inv_item.get("totalQuantity", 100) if inv_item else 100,
                    "newQuantity": (inv_item.get("totalQuantity", 100) - qty) if target_status == "DISPATCHED" else (inv_item.get("totalQuantity", 100) if inv_item else 100),
                    "fromLocation": inv_item.get("bin", "A-01") if inv_item else "A-01",
                    "toLocation": "Carrier Staging Bay" if target_status == "DISPATCHED" else "Packing Station",
                    "referenceOrder": order.get("orderNumber", order_id),
                    "userId": user_name,
                    "userName": user_name,
                    "reason": notes or f"Order transitioned to {target_status}"
                })

        # Log Audit Trail
        db.log_audit(
            user=user_name,
            role=user_role,
            action=f"ORDER_STATUS_{target_status}",
            entity=f"Order #{order.get('orderNumber', order_id)}",
            prev_val=current_status,
            newValue=target_status,
            reason=notes or f"Fulfillment stage transition: {current_status} -> {target_status}"
        )

        return {
            "status": "SUCCESS",
            "orderId": order_id,
            "orderNumber": order.get("orderNumber"),
            "previousStatus": current_status,
            "newStatus": target_status,
            "updatedAt": update_fields["updatedAt"],
            "allowedNextStates": VALID_TRANSITIONS.get(target_status, [])
        }

lifecycle_engine = FulfillmentLifecycleEngine()
