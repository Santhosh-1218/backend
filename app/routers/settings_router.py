from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.database.db import db
from app.core.security import get_current_user, require_super_admin

router = APIRouter(prefix="/settings", tags=["System Settings"])

class UpdateSettingsPayload(BaseModel):
    criticalSlaWindowHours: Optional[float] = Field(None, ge=0.5, le=24.0)
    highSlaWindowHours: Optional[float] = Field(None, ge=1.0, le=48.0)
    standardSlaWindowHours: Optional[float] = Field(None, ge=2.0, le=72.0)
    smartWaveAllocationEnabled: Optional[bool] = None
    tspRouteOptimizationEnabled: Optional[bool] = None
    autoReplenishmentThreshold: Optional[int] = Field(None, ge=1, le=500)
    maxWaveBatchSize: Optional[int] = Field(None, ge=5, le=100)
    dynamicSlottingEnabled: Optional[bool] = None
    fefoExpiryControlEnabled: Optional[bool] = None
    coldChainTempThreshold: Optional[float] = Field(None, ge=0.5, le=10.0)
    defaultWarehouseId: Optional[str] = None
    crossDockMaxHours: Optional[float] = Field(None, ge=1.0, le=48.0)
    qcWeightTolerancePercent: Optional[float] = Field(None, ge=0.1, le=10.0)
    hhtBarcodeStrictVerification: Optional[bool] = None
    autoQuarantineDamaged: Optional[bool] = None
    sessionTimeoutMinutes: Optional[int] = Field(None, ge=5, le=480)
    currencyCode: Optional[str] = "INR"
    currencySymbol: Optional[str] = "₹"
    alertNotificationsEnabled: Optional[bool] = None
    soundAlertsEnabled: Optional[bool] = None
    autoManifestCourierDispatch: Optional[bool] = None

@router.get("", response_model=Dict[str, Any])
def get_system_settings(current_user: dict = Depends(get_current_user)):
    """
    Returns persistent warehouse system settings.
    """
    settings_list = db.get_collection("settings")
    if settings_list:
        return settings_list[0]
    
    default_settings = {
        "id": "global",
        "criticalSlaWindowHours": 2.0,
        "highSlaWindowHours": 6.0,
        "standardSlaWindowHours": 12.0,
        "smartWaveAllocationEnabled": True,
        "tspRouteOptimizationEnabled": True,
        "autoReplenishmentThreshold": 20,
        "maxWaveBatchSize": 25,
        "dynamicSlottingEnabled": True,
        "fefoExpiryControlEnabled": True,
        "coldChainTempThreshold": 1.5,
        "defaultWarehouseId": "HYD-01",
        "crossDockMaxHours": 4.0,
        "qcWeightTolerancePercent": 1.5,
        "hhtBarcodeStrictVerification": True,
        "autoQuarantineDamaged": True,
        "sessionTimeoutMinutes": 60,
        "currencyCode": "INR",
        "currencySymbol": "₹",
        "alertNotificationsEnabled": True,
        "soundAlertsEnabled": True,
        "autoManifestCourierDispatch": True,
        "updatedAt": datetime.utcnow().isoformat(),
        "updatedBy": "System Default"
    }
    db.insert("settings", default_settings)
    return default_settings

@router.post("", response_model=Dict[str, Any])
def update_system_settings(
    payload: UpdateSettingsPayload,
    current_user: dict = Depends(require_super_admin)
):
    """
    Updates persistent warehouse configuration in Firestore settings/global.
    Super Admin only with audit trail.
    """
    settings_list = db.get_collection("settings")
    current_settings = settings_list[0] if settings_list else {
        "id": "global",
        "criticalSlaWindowHours": 2.0,
        "highSlaWindowHours": 6.0,
        "standardSlaWindowHours": 12.0,
        "smartWaveAllocationEnabled": True,
        "tspRouteOptimizationEnabled": True,
        "autoReplenishmentThreshold": 20,
        "maxWaveBatchSize": 25,
        "dynamicSlottingEnabled": True,
        "fefoExpiryControlEnabled": True,
        "coldChainTempThreshold": 1.5,
        "defaultWarehouseId": "HYD-01",
        "crossDockMaxHours": 4.0,
        "qcWeightTolerancePercent": 1.5,
        "hhtBarcodeStrictVerification": True,
        "autoQuarantineDamaged": True,
        "sessionTimeoutMinutes": 60,
        "currencyCode": "INR",
        "currencySymbol": "₹",
        "alertNotificationsEnabled": True,
        "soundAlertsEnabled": True,
        "autoManifestCourierDispatch": True
    }

    updates = {k: v for k, v in payload.dict().items() if v is not None}
    updates["updatedAt"] = datetime.utcnow().isoformat()
    updates["updatedBy"] = current_user.get("name", "Super Admin")

    if settings_list:
        updated = db.update("settings", current_settings["id"], updates)
    else:
        current_settings.update(updates)
        updated = db.insert("settings", current_settings)

    # Log immutable audit event
    db.log_audit(
        user=current_user.get("name", "Super Admin"),
        role=current_user.get("role", "SUPER_ADMIN"),
        action="SETTINGS_UPDATED",
        entity="settings/global",
        prev_val=str({k: current_settings.get(k) for k in updates if k != "updatedAt" and k != "updatedBy"}),
        newValue=str({k: updates[k] for k in updates if k != "updatedAt" and k != "updatedBy"}),
        reason="Super Admin updated persistent warehouse operations configuration",
        user_id=current_user.get("uid") or current_user.get("id")
    )

    db.add_notification(
        notif_type="SUCCESS",
        title="Settings Updated",
        message=f"Warehouse operations parameters updated by {current_user.get('name', 'Super Admin')}.",
        role="SUPER_ADMIN",
        link="/settings"
    )

    return updated
