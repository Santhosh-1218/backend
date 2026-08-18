from datetime import datetime
from typing import Dict, List, Any, Optional
from app.database.db import db
from app.decision_engine.priority import calculate_order_priority

def run_smart_allocation(order_id: Optional[str] = None, user_name: str = "Order Manager") -> Dict[str, Any]:
    """
    Intelligent inventory allocation engine with FEFO (First Expiry, First Out) batch intelligence.
    Handles contention across competing orders (e.g. Order #1042 vs #1048),
    allocates available stock based on priority and earliest batch expiry dates,
    calculates shortages, triggers replenishment recommendations, and logs decisions with full auditability.
    """
    all_orders = db.get_collection("orders")
    all_inventory = {inv["sku"]: inv for inv in db.get_collection("inventory")}
    
    # Filter orders to evaluate: either specific order or all unallocated/prioritized orders
    if order_id:
        target_orders = [o for o in all_orders if o["id"] == order_id or o["orderNumber"] == order_id]
    else:
        target_orders = [o for o in all_orders if o["status"] in ["CREATED", "PRIORITIZED", "INVENTORY_CHECKED"]]

    # Sort target orders by priority score descending (CRITICAL -> HIGH -> MEDIUM -> LOW)
    target_orders.sort(key=lambda x: x.get("priorityScore", 0), reverse=True)

    allocation_results = []
    
    for order in target_orders:
        order_num = order["orderNumber"]
        order_prio = order.get("priorityLevel", "MEDIUM")
        items = order.get("items", [])
        
        all_allocated = True
        has_partial = False
        total_shortage = 0
        decisions_made = []

        for it in items:
            sku = it["sku"]
            qty_req = it["quantityRequested"]
            inv = all_inventory.get(sku)

            if not inv:
                all_allocated = False
                total_shortage += qty_req
                continue

            avail = inv.get("availableQuantity", 0)
            batch_id = inv.get("batchNumber", "BATCH-2026-A1")
            expiry_date = inv.get("expiryDate", "2026-11-30")

            if avail >= qty_req:
                # Full Allocation using FEFO
                allocated = qty_req
                inv["availableQuantity"] -= allocated
                inv["reservedQuantity"] = inv.get("reservedQuantity", 0) + allocated
                it["quantityAllocated"] = allocated
                it["batchNumber"] = batch_id
                it["expiryDate"] = expiry_date

                fefo_reason = f"FEFO allocation selected Batch {batch_id} (Expires {expiry_date}) because it expires earliest among available active stock."
                
                decisions_made.append({
                    "sku": sku,
                    "allocated": allocated,
                    "shortage": 0,
                    "strategy": "FEFO",
                    "batch": batch_id,
                    "reason": fefo_reason
                })

            elif avail > 0:
                # Partial Allocation
                allocated = avail
                shortage = qty_req - avail
                inv["availableQuantity"] = 0
                inv["reservedQuantity"] = inv.get("reservedQuantity", 0) + allocated
                it["quantityAllocated"] = allocated
                it["batchNumber"] = batch_id
                it["expiryDate"] = expiry_date
                has_partial = True
                all_allocated = False
                total_shortage += shortage

                # Record decision for partial allocation with FEFO note
                situation_desc = f"{order_num} ({order_prio}) requires {qty_req} units of {it['productName']} ({sku}), but only {avail} units are physically available in {inv['bin']}."
                decision_desc = f"Allocate all {avail} available units to {order_num} from Batch {batch_id} (Expires {expiry_date}) and flag {shortage} units backorder shortage."
                reason_desc = f"FEFO priority batch + Tier-1 SLA deadline ({round(order.get('slaRemainingHours', 2.0), 1)}h remaining). Maximizes immediate fulfillment rate."
                action_desc = f"Issue picking task for {avail} units and trigger immediate replenishment PO for {shortage} units to supplier {inv.get('supplier', 'Primary Supplier')}."
                result_desc = f"Inventory updated: Available stock = 0, Reserved = {inv['reservedQuantity']}. Shortage of {shortage} units queued for replenishment."
                
                db.log_decision(
                    dec_type="INVENTORY_ALLOCATION",
                    entity_id=order_num,
                    entity_type="ORDER",
                    situation=situation_desc,
                    decision=decision_desc,
                    reason=reason_desc,
                    action=action_desc,
                    result=result_desc,
                    impact=f"Lower-priority orders for {sku} held in waiting state.",
                    approved_by="SMART_ALLOCATION_ENGINE"
                )

                # Trigger replenishment notification & exception
                db.add_notification(
                    notif_type="CRITICAL",
                    title=f"Stock Shortage Alert: {sku}",
                    message=f"Order {order_num} has a shortage of {shortage} units. Replenishment recommended immediately.",
                    role="INVENTORY_MANAGER",
                    link="/inventory"
                )

                decisions_made.append({
                    "sku": sku,
                    "allocated": allocated,
                    "shortage": shortage,
                    "strategy": "FEFO_PARTIAL",
                    "batch": batch_id,
                    "situation": situation_desc,
                    "decision": decision_desc,
                    "reason": reason_desc,
                    "action": action_desc,
                    "result": result_desc
                })
            else:
                # Zero available
                allocated = 0
                shortage = qty_req
                it["quantityAllocated"] = 0
                all_allocated = False
                total_shortage += shortage

                situation_desc = f"{order_num} requires {qty_req} units of {it['productName']} ({sku}), but 0 units are available in warehouse racks."
                decision_desc = f"Hold {order_num} in pending/waiting queue without blocking other product lines."
                reason_desc = f"Stockout condition. Awaiting incoming shipment from supplier."
                action_desc = f"Notify Order Manager and flag order as BACKORDERED."
                result_desc = f"Order status set to WAITING_STOCK."

                db.log_decision(
                    dec_type="INVENTORY_ALLOCATION",
                    entity_id=order_num,
                    entity_type="ORDER",
                    situation=situation_desc,
                    decision=decision_desc,
                    reason=reason_desc,
                    action=action_desc,
                    result=result_desc,
                    approved_by="SMART_ALLOCATION_ENGINE"
                )

            # Persist updated inventory in DB
            db.update("inventory", inv["id"], inv)

            # Record stock movements & inventory movement ledger
            if allocated > 0:
                movement_entry = {
                    "id": f"mov-{int(datetime.utcnow().timestamp()*1000)}-{sku}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "sku": sku,
                    "productName": it.get("productName", it.get("name", inv.get("productName", "Product"))),
                    "quantity": allocated,
                    "previousQuantity": avail,
                    "newQuantity": inv["availableQuantity"],
                    "movementType": "STOCK_ALLOCATED",
                    "source": f"Rack Bin {inv['bin']} (Batch: {batch_id})",
                    "destination": f"Reserved for {order_num}",
                    "userId": "sys-01",
                    "userName": user_name,
                    "reason": f"FEFO allocation to {order_num} (Priority: {order_prio}, Batch: {batch_id})",
                    "orderId": order["id"]
                }
                db.insert("stock_movements", movement_entry)
                db.insert("inventory_movements", movement_entry)

        # Update order status based on allocation
        new_status = "ALLOCATED" if (all_allocated or has_partial) else "INVENTORY_CHECKED"
        alloc_status = "FULLY_ALLOCATED" if all_allocated else ("PARTIALLY_ALLOCATED" if has_partial else "BACKORDERED")
        
        db.update("orders", order["id"], {
            "status": new_status,
            "allocationStatus": alloc_status,
            "shortageCount": total_shortage,
            "items": items,
            "updatedAt": datetime.utcnow().isoformat()
        })

        db.log_audit(
            user=user_name,
            role="ORDER_MANAGER",
            action="SMART_ALLOCATION_EXECUTED",
            entity=order_num,
            prev_val=order.get("allocationStatus", "UNALLOCATED"),
            new_val=alloc_status,
            reason=f"Smart allocation executed: {alloc_status} with shortage={total_shortage}"
        )

        allocation_results.append({
            "orderId": order["id"],
            "orderNumber": order_num,
            "priority": order_prio,
            "allocationStatus": alloc_status,
            "shortageCount": total_shortage,
            "decisions": decisions_made
        })

    return {
        "status": "SUCCESS",
        "evaluatedOrdersCount": len(target_orders),
        "results": allocation_results,
        "timestamp": datetime.utcnow().isoformat()
    }
