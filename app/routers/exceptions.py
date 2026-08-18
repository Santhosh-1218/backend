from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.db import db
from app.core.security import get_current_user
from app.decision_engine.exceptions import resolve_exception

router = APIRouter(prefix="/exceptions", tags=["Exceptions"])

@router.get("")
def get_exceptions(
    status: Optional[str] = None, 
    severity: Optional[str] = None,
    fulfillmentCenterId: Optional[str] = None,
    warehouseId: Optional[str] = None
):
    exceptions = db.get_collection("exceptions")
    target_fc = fulfillmentCenterId or warehouseId
    
    if target_fc and target_fc != "ALL":
        exceptions = [
            e for e in exceptions 
            if e.get("fulfillmentCenterId") == target_fc or e.get("warehouseId") == target_fc
        ]
        
    if status and status != "ALL":
        exceptions = [e for e in exceptions if e.get("status", "").upper() == status.upper()]
    if severity and severity != "ALL":
        exceptions = [e for e in exceptions if e.get("severity", "").upper() == severity.upper()]
    return exceptions

@router.post("/resolve")
def resolve_exception_endpoint(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    exception_id = payload.get("exceptionId")
    resolution_type = payload.get("resolutionType", "STANDARD_APPROVAL")
    notes = payload.get("notes")
    user_name = current_user.get("name", "Operations Manager")

    result = resolve_exception(
        exception_id=exception_id,
        resolution_type=resolution_type,
        user_name=user_name,
        notes=notes
    )
    if result.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result

@router.post("")
def create_manual_exception(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    exc_data = {
        "id": f"exc-{int(datetime.utcnow().timestamp()*1000)}",
        "exceptionType": payload.get("exceptionType", "OPERATIONAL_ANOMALY"),
        "severity": payload.get("severity", "MEDIUM"),
        "title": payload.get("title", "Manual Exception Raised"),
        "problem": payload.get("problem", "Reported operational issue"),
        "affectedEntity": payload.get("affectedEntity", "Warehouse Floor"),
        "affectedId": payload.get("affectedId", "WH-ALPHA-01"),
        "detectedAt": datetime.utcnow().isoformat(),
        "recommendedDecision": payload.get("recommendedDecision", "Review and assign task to floor supervisor."),
        "resolutionPlan": payload.get("resolutionPlan", "Floor supervisor investigation required."),
        "status": "OPEN",
        "assignedUser": current_user.get("name", "Operations Manager")
    }
    db.insert("exceptions", exc_data)
    return exc_data
