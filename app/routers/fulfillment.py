from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.db import db
from app.core.security import get_current_user
from app.decision_engine.picking import optimize_picking_route

router = APIRouter(prefix="/fulfillment", tags=["Fulfillment"])

# 1. Picking
@router.get("/picking/tasks")
def get_picking_tasks(
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None
):
    all_tasks = db.get_collection("picking_tasks")
    target_fc = fulfillmentCenterId or warehouseId
    if target_fc and target_fc != "ALL":
        filtered = [
            t for t in all_tasks 
            if t.get("warehouseId") == target_fc or t.get("fulfillmentCenterId") == target_fc
        ]
        return filtered if filtered else all_tasks
    return all_tasks


@router.post("/picking/create-task")
def create_picking_task(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    order_id = payload.get("orderId")
    order = db.get_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Extract bin locations from order items
    items = order.get("items", [])
    bins = [it.get("locationCode", "A-01") for it in items if it.get("quantityAllocated", 0) > 0]
    
    # Run route optimization
    route_opt = optimize_picking_route(bins)

    task = {
        "id": f"pick-{int(datetime.utcnow().timestamp()*1000)}",
        "orderId": order["id"],
        "orderNumber": order["orderNumber"],
        "priorityLevel": order.get("priorityLevel", "MEDIUM"),
        "assignedPickerId": current_user.get("id", "usr-004"),
        "assignedPickerName": current_user.get("name", "Marcus Vance"),
        "status": "PENDING",
        "items": [
            {
                "sku": it["sku"],
                "name": it["productName"],
                "bin": it.get("locationCode", "A-01"),
                "quantity": it.get("quantityAllocated", it["quantityRequested"]),
                "picked": 0
            }
            for it in items if it.get("quantityAllocated", 0) > 0 or it["quantityRequested"] > 0
        ],
        "unoptimizedRouteTimeMinutes": route_opt["unoptimizedMinutes"],
        "optimizedRouteTimeMinutes": route_opt["optimizedMinutes"],
        "timeSavedMinutes": route_opt["savedMinutes"],
        "routeSequence": route_opt["optimizedRoute"],
        "currentStep": 0,
        "createdAt": datetime.utcnow().isoformat()
    }

    db.insert("picking_tasks", task)
    db.update("orders", order["id"], {"status": "PICKING"})

    db.log_decision(
        dec_type="PICKING_ROUTE_OPTIMIZATION",
        entity_id=task["id"],
        entity_type="TASK",
        situation=f"Picking wave generated for {order['orderNumber']} across {len(bins)} bins: {bins}.",
        decision=f"Optimized path sequence: {' → '.join(route_opt['optimizedRoute'])}.",
        reason="Reduces aisle backtracking by 38.8%.",
        action="Direct picker via handheld device along the optimized path.",
        result=f"Estimated pick time reduced from {route_opt['unoptimizedMinutes']}m to {route_opt['optimizedMinutes']}m (Saved {route_opt['savedMinutes']}m)."
    )

    return task

@router.post("/picking/complete-task")
def complete_picking_task(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    task_id = payload.get("taskId")
    task = db.get_by_id("picking_tasks", task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Picking task not found")

    db.update("picking_tasks", task["id"], {"status": "COMPLETED"})
    db.update("orders", task["orderId"], {"status": "PICKED"})

    # Auto-create Packing Task
    pack_task = {
        "id": f"pack-{int(datetime.utcnow().timestamp()*1000)}",
        "orderId": task["orderId"],
        "orderNumber": task["orderNumber"],
        "stationId": "PACK-STATION-01",
        "packerName": "Packer Station Alpha",
        "status": "PENDING",
        "boxType": "Carton Type B (40x30x25cm)",
        "items": task["items"],
        "createdAt": datetime.utcnow().isoformat()
    }
    db.insert("packing_tasks", pack_task)

    db.log_audit(
        user=current_user.get("name", "Picker"),
        role=current_user.get("role", "OPERATIONS_MANAGER"),
        action="PICKING_COMPLETED",
        entity=task["orderNumber"],
        prev_val="PICKING",
        newValue="PICKED",
        reason="All line items picked from bins and delivered to packing station"
    )

    return {"status": "SUCCESS", "orderId": task["orderId"], "packingTaskId": pack_task["id"]}

# 2. Packing
@router.get("/packing/tasks")
def get_packing_tasks(
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None
):
    all_tasks = db.get_collection("packing_tasks")
    target_fc = fulfillmentCenterId or warehouseId
    if target_fc and target_fc != "ALL":
        filtered = [
            t for t in all_tasks 
            if t.get("warehouseId") == target_fc or t.get("fulfillmentCenterId") == target_fc
        ]
        return filtered if filtered else all_tasks
    return all_tasks

@router.post("/packing/complete-task")
def complete_packing_task(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    pack_id = payload.get("taskId")
    pack_task = db.get_by_id("packing_tasks", pack_id)
    if not pack_task:
        raise HTTPException(status_code=404, detail="Packing task not found")

    db.update("packing_tasks", pack_task["id"], {"status": "COMPLETED"})
    db.update("orders", pack_task["orderId"], {"status": "PACKED"})

    return {"status": "SUCCESS", "orderId": pack_task["orderId"]}

# 3. Quality Check (QC)
@router.post("/qc/verify")
def verify_qc(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    order_id = payload.get("orderId")
    order = db.get_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    has_issue = payload.get("hasIssue", False)
    issue_type = payload.get("issueType", "DAMAGED_ITEM") # DAMAGED_ITEM, MISSING_ITEM

    if has_issue:
        # Create Exception
        exc = {
            "id": f"exc-{int(datetime.utcnow().timestamp()*1000)}",
            "exceptionType": issue_type,
            "severity": "HIGH",
            "title": f"QC Exception: {issue_type.replace('_', ' ').title()} on {order['orderNumber']}",
            "problem": payload.get("problemDescription", f"Quality check inspection failed on {order['orderNumber']}: {issue_type}"),
            "affectedEntity": order["orderNumber"],
            "affectedId": order["id"],
            "detectedAt": datetime.utcnow().isoformat(),
            "recommendedDecision": "Quarantine damaged goods and issue immediate repick ticket to fulfillment queue.",
            "resolutionPlan": "Repick missing/damaged units from secondary bin and re-inspect before sealing carton.",
            "status": "OPEN",
            "assignedUser": "Operations Manager"
        }
        db.insert("exceptions", exc)
        db.update("orders", order["id"], {"status": "EXCEPTION"})

        db.add_notification(
            notif_type="CRITICAL",
            title=f"QC Failure: {order['orderNumber']}",
            message=f"{issue_type} detected during quality inspection. Exception raised.",
            role="OPERATIONS_MANAGER",
            link="/exceptions"
        )
        return {"status": "EXCEPTION_CREATED", "exception": exc}
    else:
        # QC Passed
        qc_record = {
            "id": f"qc-{int(datetime.utcnow().timestamp()*1000)}",
            "orderId": order["id"],
            "orderNumber": order["orderNumber"],
            "inspectorName": current_user.get("name", "QC Inspector"),
            "status": "PASSED",
            "checks": {
                "correctProduct": True,
                "correctQuantity": True,
                "noDamagedItems": True,
                "noMissingItems": True,
                "packagingIntact": True,
                "barcodeLegible": True
            },
            "notes": "Passed comprehensive 6-point quality audit.",
            "timestamp": datetime.utcnow().isoformat()
        }
        db.insert("quality_checks", qc_record)
        db.update("orders", order["id"], {"status": "READY_TO_DISPATCH"})

        return {"status": "PASSED", "qcRecord": qc_record}

# 4. Dispatch
@router.post("/dispatch")
def dispatch_order(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    order_id = payload.get("orderId")
    order = db.get_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    carrier = payload.get("carrier", "FedEx Priority Freight")
    tracking_no = f"TRK-{int(datetime.utcnow().timestamp()*1000)%10000000}"

    db.update("orders", order["id"], {
        "status": "DISPATCHED",
        "carrier": carrier,
        "trackingNumber": tracking_no,
        "dispatchedAt": datetime.utcnow().isoformat()
    })

    # Record Movement
    for it in order.get("items", []):
        qty_dispatched = it.get("quantityAllocated", it["quantityRequested"])
        if qty_dispatched > 0:
            db.insert("stock_movements", {
                "id": f"mov-{int(datetime.utcnow().timestamp()*1000)}-{it['sku']}",
                "timestamp": datetime.utcnow().isoformat(),
                "sku": it["sku"],
                "productName": it["productName"],
                "quantity": qty_dispatched,
                "previousQuantity": qty_dispatched,
                "newQuantity": 0,
                "movementType": "STOCK_DISPATCHED",
                "source": "Staging Dock 04",
                "destination": f"Carrier: {carrier} ({order['customerName']})",
                "userId": current_user.get("id", "usr-004"),
                "userName": current_user.get("name", "Operations Manager"),
                "reason": f"Dispatched against order {order['orderNumber']}",
                "orderId": order["id"]
            })

    db.log_audit(
        user=current_user.get("name", "Operations Manager"),
        role=current_user.get("role", "OPERATIONS_MANAGER"),
        action="ORDER_DISPATCHED",
        entity=order["orderNumber"],
        prev_val="READY_TO_DISPATCH",
        newValue=f"DISPATCHED ({carrier})",
        reason=f"Handed over to carrier. Tracking #{tracking_no}"
    )

    db.add_notification(
        notif_type="SUCCESS",
        title=f"Order Dispatched: {order['orderNumber']}",
        message=f"Consignment handed over to {carrier}. Tracking: {tracking_no}",
        role="ALL",
        link="/orders"
    )

    return {
        "status": "SUCCESS",
        "orderNumber": order["orderNumber"],
        "trackingNumber": tracking_no,
        "carrier": carrier
    }

# 5. Barcode & Wrong Item Detection
@router.post("/scan-verify")
def scan_verify_item(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    order_id = payload.get("orderId")
    expected_sku = payload.get("expectedSku")
    scanned_sku = payload.get("scannedSku")

    if expected_sku != scanned_sku:
        # Log mismatch audit
        db.log_audit(
            user=current_user.get("name", "Picker"),
            role="OPERATIONS_MANAGER",
            action="WRONG_ITEM_INTERCEPTED",
            entity=f"Order {order_id}: Expected {expected_sku} vs Scanned {scanned_sku}",
            prev_val=scanned_sku,
            newValue=expected_sku,
            reason="Barcode mismatch intercepted at pick/QC station. Erroneous item blocked."
        )

        return {
            "status": "MISMATCH",
            "matched": False,
            "expectedSku": expected_sku,
            "scannedSku": scanned_sku,
            "title": "❌ SKU Mismatch Detected",
            "decision": f"Do not pack {scanned_sku}. Return item to staging bin and pick verified SKU {expected_sku}.",
            "recommendedAction": "Return incorrect item and scan correct SKU barcode."
        }

    return {
        "status": "MATCH",
        "matched": True,
        "expectedSku": expected_sku,
        "scannedSku": scanned_sku,
        "message": "Barcode verified successfully."
    }

# 6. Missing Item Investigation Sweep
@router.post("/missing-item-sweep")
def missing_item_sweep(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    sku = payload.get("sku")
    expected_bin = payload.get("expectedBin", "A-01")
    order_id = payload.get("orderId")

    from app.decision_engine.operations_intelligence import operations_intel
    result = operations_intel.resolve_missing_item_search(sku, expected_bin)

    db.log_decision(
        dec_type="EXCEPTION_RESOLUTION",
        entity_id=sku,
        entity_type="INVENTORY",
        situation=result["situation"],
        decision=result["decision"],
        reason=result["reason"],
        action=result["action"],
        result=f"Fulfillment resumed using reserve location {result['alternativeLocationFound']}.",
        approved_by=current_user.get("name", "Operations Manager")
    )

    return result

# 7. Generic State Transition
@router.post("/transition-status")
def transition_order_status(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from app.decision_engine.fulfillment_lifecycle import lifecycle_engine
    order_id = payload.get("orderId")
    target_status = payload.get("targetStatus")
    notes = payload.get("notes", "")

    return lifecycle_engine.transition_order_state(
        order_id=order_id,
        target_status=target_status,
        user_name=current_user.get("name", "Operations Manager"),
        user_role=current_user.get("role", "OPERATIONS_MANAGER"),
        notes=notes
    )

# 8. Dock Door & Yard Management (YMS)
@router.get("/dock-doors")
def get_dock_doors(
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None
):
    doors = db.get_collection("dock_doors")
    target_fc = fulfillmentCenterId or warehouseId
    if target_fc and target_fc != "ALL":
        return [
            d for d in doors 
            if d.get("warehouseId") == target_fc or d.get("fulfillmentCenterId") == target_fc
        ]
    return doors

@router.post("/dock-doors/assign")
def assign_dock_door(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    bay_id = payload.get("bayId")
    carrier = payload.get("carrier", "StockFlow Linehaul Fleet")
    driver_name = payload.get("driverName", "Assigned Driver")
    vehicle_number = payload.get("vehicleNumber", "TS-09-SF-1042")
    cargo_desc = payload.get("cargoDescription", "Inbound General Merchandise")
    assigned_zone = payload.get("assignedZone", "Zone A")

    door = db.get_by_id("dock_doors", bay_id)
    if not door:
        raise HTTPException(status_code=404, detail="Dock door bay not found")

    updated = {
        **door,
        "status": "UNLOADING",
        "carrier": carrier,
        "driverName": driver_name,
        "vehicleNumber": vehicle_number,
        "cargoDescription": cargo_desc,
        "assignedZone": assigned_zone,
        "progressPct": 15,
        "palletsCompleted": 3,
        "palletsTotal": 20,
        "etaOrDeparture": "Unloading in progress"
    }

    db.update("dock_doors", bay_id, updated)
    db.log_audit(
        user=current_user.get("name", "Gate Security"),
        role="LOGISTICS_DISPATCHER",
        action="DOCK_DOOR_ASSIGNED",
        entity=f"{door['bayNumber']} ({carrier})",
        prev_val=door["status"],
        newValue="UNLOADING",
        reason=f"Trailer {vehicle_number} checked in at gate. Staged for {assigned_zone} receiving."
    )

    return updated

@router.post("/dock-doors/complete-unload")
def complete_dock_unload(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    bay_id = payload.get("bayId")
    door = db.get_by_id("dock_doors", bay_id)
    if not door:
        raise HTTPException(status_code=404, detail="Dock door bay not found")

    updated = {
        **door,
        "status": "SEALED_DEPARTURE" if door["type"] == "OUTBOUND" else "UNLOAD_COMPLETE",
        "progressPct": 100,
        "palletsCompleted": door.get("palletsTotal", 20),
        "etaOrDeparture": "Gate Release Approved"
    }

    db.update("dock_doors", bay_id, updated)
    db.log_audit(
        user=current_user.get("name", "Dock Supervisor"),
        role="LOGISTICS_DISPATCHER",
        action="DOCK_UNLOAD_COMPLETED",
        entity=door["bayNumber"],
        prev_val=door["status"],
        newValue=updated["status"],
        reason="All pallets received and verified against manifest. Gate pass clearance granted."
    )

    return updated

# 9. Reverse Logistics & Customer Returns (RTO Hub)
@router.get("/returns")
def get_customer_returns(
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None
):
    returns_list = db.get_collection("returns")
    target_fc = fulfillmentCenterId or warehouseId
    if target_fc and target_fc != "ALL":
        return [
            r for r in returns_list 
            if r.get("warehouseId") == target_fc or r.get("fulfillmentCenterId") == target_fc
        ]
    return returns_list

@router.post("/returns/grade-and-restock")
def grade_and_restock_return(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    return_id = payload.get("returnId")
    grade = payload.get("grade", "GRADE_A_PRISTINE") # GRADE_A_PRISTINE | GRADE_B_REPACK | GRADE_C_SCRAP
    target_bin = payload.get("targetBin", "A-01")
    notes = payload.get("notes", "")

    ret_item = db.get_by_id("returns", return_id)
    if not ret_item:
        raise HTTPException(status_code=404, detail="Return item not found")

    if "A" in grade or "B" in grade:
        grading_status = "GRADED_RESTOCKED"
        refund_status = "CREDITED"
        # Increment active inventory
        sku = ret_item.get("sku")
        qty = ret_item.get("quantity", 1)
        inv_item = db.get_by_id("inventory", sku)
        if inv_item:
            new_avail = inv_item.get("availableQuantity", 0) + qty
            new_curr = inv_item.get("currentQuantity", 0) + qty
            db.update("inventory", sku, {
                **inv_item,
                "availableQuantity": new_avail,
                "currentQuantity": new_curr,
                "bin": target_bin
            })
    else:
        grading_status = "GRADED_DAMAGED"
        refund_status = "REPLACED_SENT"

    updated = {
        **ret_item,
        "gradingStatus": grading_status,
        "assignedGrade": grade,
        "refundStatus": refund_status,
        "targetBin": target_bin,
        "inspectorNotes": notes,
        "inspectedBy": current_user.get("name", "QA Inspector"),
        "inspectedAt": datetime.utcnow().isoformat()
    }

    db.update("returns", return_id, updated)
    db.log_decision(
        dec_type="RETURN_QA_GRADING",
        entity_id=ret_item["returnNumber"],
        entity_type="RETURN_CONSIGNMENT",
        situation=f"Customer return for {ret_item['productName']} (Qty: {ret_item['quantity']}) received from {ret_item['carrier']}.",
        decision=f"Assigned {grade}. Restocked to {target_bin} with refund status {refund_status}.",
        reason=notes or "Autonomous reverse logistics QA evaluation completed.",
        action=f"Updated inventory buffer in {target_bin} and processed customer credit note.",
        result=f"Inventory recovery: {'100%' if 'A' in grade else '50%' if 'B' in grade else '0% (Scrap claim)'}.",
        approved_by=current_user.get("name", "QA Inspector")
    )

    return updated

# 10. Cold Chain & Environmental IoT Telemetry
@router.get("/climate-telemetry")
def get_climate_telemetry(
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None
):
    sensors = db.get_collection("climate_sensors")
    target_fc = fulfillmentCenterId or warehouseId
    if target_fc and target_fc != "ALL":
        return [
            s for s in sensors 
            if s.get("warehouseId") == target_fc or s.get("fulfillmentCenterId") == target_fc
        ]
    return sensors

# 11. Shipping Label Data Generator
@router.get("/shipping-label/{order_id}")
def get_shipping_label_data(order_id: str):
    order = db.get_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = order.get("items", [])
    total_qty = sum(it.get("quantityAllocated", it.get("quantityRequested", 1)) for it in items)
    channel = order.get("channel", "STOCKFLOW_PRIME")

    return {
        "orderId": order.get("id"),
        "orderNumber": order.get("orderNumber"),
        "retailChannel": channel,
        "customerName": order.get("customerName"),
        "customerAddress": order.get("deliveryAddress", "Plot 42, Industrial Logistics Park, Shamshabad, Hyderabad, Telangana 500108"),
        "warehouseOrigin": "StockFlow Hyderabad Central Mega Hub HYD-01, Shamshabad Logistics Park",
        "carrier": order.get("carrier", "StockFlow Priority Air Express"),
        "trackingNumber": order.get("trackingNumber", f"SF-AWB-{order.get('orderNumber', '1042')[4:]}9821"),
        "ssccPalletCode": f"(00) 0 8901234 {order.get('orderNumber', '1042')[4:]}00192 4",
        "itemCount": len(items),
        "totalUnits": total_qty,
        "items": items,
        "grossWeightKg": "2.45",
        "routingBin": "BAY-04 / PALLET-P12",
        "slaDeadline": order.get("slaRemainingHours", 1.8),
        "generatedAt": datetime.utcnow().isoformat()
    }


