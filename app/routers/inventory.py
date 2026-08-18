from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.db import db
from app.core.security import get_current_user
from app.decision_engine.replenishment import analyze_replenishment_needs

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("")
def get_inventory(
    zone: Optional[str] = None, 
    search: Optional[str] = None, 
    low_stock_only: bool = False,
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None
):
    items = db.get_collection("inventory")
    target_fc = fulfillmentCenterId or warehouseId
    
    if target_fc and target_fc != "ALL":
        items = [
            it for it in items 
            if it.get("fulfillmentCenterId") == target_fc or it.get("warehouseId") == target_fc
        ]
        
    if zone and zone != "ALL":
        items = [it for it in items if it.get("zone", "").lower() == zone.lower()]
    if search:
        s = search.lower()
        items = [it for it in items if s in it.get("productName", "").lower() or s in it.get("sku", "").lower() or s in it.get("bin", "").lower()]
    if low_stock_only:
        items = [it for it in items if it.get("availableQuantity", 0) <= it.get("reorderLevel", 50)]
        
    return items

@router.get("/replenishment")
def get_replenishment_recommendations(
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None
):
    target_fc = fulfillmentCenterId or warehouseId
    return analyze_replenishment_needs(fulfillmentCenterId=target_fc)

@router.get("/movements")
def get_stock_movements(
    sku: Optional[str] = None, 
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None,
    limit: int = 50
):
    movements = db.get_collection("stock_movements")
    target_fc = fulfillmentCenterId or warehouseId
    
    if target_fc and target_fc != "ALL":
        movements = [
            m for m in movements 
            if m.get("fulfillmentCenterId") == target_fc or m.get("warehouseId") == target_fc
        ]
    if sku:
        movements = [m for m in movements if m.get("sku") == sku]
    return movements[:limit]

@router.post("/receive")
def receive_stock(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    sku = payload.get("sku")
    quantity = int(payload.get("quantity", 0))
    supplier = payload.get("supplier", "Inbound Supplier")
    target_bin = payload.get("bin")
    
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    inv = db.get_by_id("inventory", f"inv-{sku.lower()}") or db.get_by_id("inventory", sku)
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory SKU record not found")

    prev_qty = inv.get("totalQuantity", 0)
    prev_avail = inv.get("availableQuantity", 0)
    
    new_total = prev_qty + quantity
    new_avail = prev_avail + quantity

    updates = {
        "totalQuantity": new_total,
        "availableQuantity": new_avail
    }
    if target_bin:
        updates["bin"] = target_bin
        updates["zone"] = f"Zone {target_bin[0]}"

    db.update("inventory", inv["id"], updates)

    # Record Movement
    db.insert("stock_movements", {
        "id": f"mov-{int(datetime.utcnow().timestamp()*1000)}",
        "timestamp": datetime.utcnow().isoformat(),
        "sku": sku,
        "productName": inv.get("productName"),
        "quantity": quantity,
        "previousQuantity": prev_avail,
        "newQuantity": new_avail,
        "movementType": "STOCK_RECEIVED",
        "source": f"Inbound Dock ({supplier})",
        "destination": f"Bin {updates.get('bin', inv['bin'])}",
        "userId": current_user.get("id", "usr-002"),
        "userName": current_user.get("name", "David Chen"),
        "reason": f"Received inbound shipment PO from {supplier}",
        "orderId": None
    })

    # Log Audit
    db.log_audit(
        user=current_user.get("name", "Inventory Manager"),
        role=current_user.get("role", "INVENTORY_MANAGER"),
        action="STOCK_RECEIVED",
        entity=sku,
        prev_val=f"Available: {prev_avail}",
        newValue=f"Available: {new_avail}",
        reason=f"Received {quantity} units from {supplier}"
    )

    db.add_notification(
        notif_type="SUCCESS",
        title=f"Stock Inbounded: {sku}",
        message=f"+{quantity} units of {inv.get('productName')} added to Bin {updates.get('bin', inv['bin'])}.",
        role="INVENTORY_MANAGER",
        link="/inventory"
    )

    return {
        "status": "SUCCESS",
        "sku": sku,
        "receivedQuantity": quantity,
        "newAvailableQuantity": new_avail,
        "bin": updates.get("bin", inv["bin"])
    }

@router.post("/adjust")
def adjust_stock(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    sku = payload.get("sku")
    adjustment_type = payload.get("type", "DAMAGED") # DAMAGED, CYCLE_COUNT, TRANSFER
    quantity = int(payload.get("quantity", 0))
    reason = payload.get("reason", "Manual adjustment")

    inv = db.get_by_id("inventory", f"inv-{sku.lower()}") or db.get_by_id("inventory", sku)
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    prev_avail = inv.get("availableQuantity", 0)
    
    if adjustment_type == "DAMAGED":
        new_damaged = inv.get("damagedQuantity", 0) + quantity
        new_avail = max(0, prev_avail - quantity)
        db.update("inventory", inv["id"], {
            "damagedQuantity": new_damaged,
            "availableQuantity": new_avail
        })
        mov_type = "STOCK_DAMAGED"
    elif adjustment_type == "TRANSFER":
        target_bin = payload.get("targetBin", "A-01")
        db.update("inventory", inv["id"], {
            "bin": target_bin,
            "zone": f"Zone {target_bin[0]}"
        })
        mov_type = "STOCK_TRANSFERRED"
        new_avail = prev_avail
    else:
        new_avail = max(0, prev_avail + quantity)
        new_total = max(0, inv.get("totalQuantity", 0) + quantity)
        db.update("inventory", inv["id"], {
            "availableQuantity": new_avail,
            "totalQuantity": new_total
        })
        mov_type = "STOCK_ADJUSTED"

    db.insert("stock_movements", {
        "id": f"mov-{int(datetime.utcnow().timestamp()*1000)}",
        "timestamp": datetime.utcnow().isoformat(),
        "sku": sku,
        "productName": inv.get("productName"),
        "quantity": quantity,
        "previousQuantity": prev_avail,
        "newQuantity": new_avail,
        "movementType": mov_type,
        "source": f"Bin {inv['bin']}",
        "destination": payload.get("targetBin", "Adjustment Area"),
        "userId": current_user.get("id", "usr-002"),
        "userName": current_user.get("name", "Inventory Manager"),
        "reason": reason,
        "orderId": None
    })

    db.log_audit(
        user=current_user.get("name", "Inventory Manager"),
        role=current_user.get("role", "INVENTORY_MANAGER"),
        action=f"STOCK_{adjustment_type}",
        entity=sku,
        prev_val=str(prev_avail),
        newValue=str(new_avail),
        reason=reason
    )

    return {"status": "SUCCESS", "sku": sku, "newAvailableQuantity": new_avail}
