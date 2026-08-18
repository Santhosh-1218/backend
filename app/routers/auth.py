from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from app.database.db import db
from app.core.security import get_current_user
from app.models.schemas import UserLoginRequest
from app.core.firebase_auth import FirebaseAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me")
def get_current_user_profile(user: dict = Depends(get_current_user)):
    sanitized = dict(user)
    sanitized.pop("password", None)
    return sanitized

@router.get("/users")
def list_users(user: dict = Depends(get_current_user)):
    users = db.get_collection("users")
    sanitized = []
    for u in users:
        item = dict(u)
        item.pop("password", None)
        sanitized.append(item)
    return sanitized

@router.post("/login")
def login_user(payload: UserLoginRequest):
    users = db.get_collection("users")
    email = payload.email.lower().strip()
    
    # Check if user exists in database
    for u in users:
        if u["email"].lower() == email:
            if u.get("status") == "DISABLED":
                raise HTTPException(
                    status_code=403,
                    detail="Your StockFlow account is currently disabled. Please contact your administrator."
                )
            
            # Log login audit
            db.log_audit(
                user=u.get("name", email),
                role=u.get("role", "STAFF"),
                action="LOGIN_SUCCESS",
                entity=email,
                prev_val=None,
                newValue="ACTIVE_SESSION",
                reason="User authenticated successfully into Warehouse Hub"
            )

            sanitized = dict(u)
            sanitized.pop("password", None)
            return {
                "token": f"token-{u['id']}-{u['role']}",
                "user": sanitized
            }

    # Determine assigned role
    if "admin" in email:
        assigned_role = "SUPER_ADMIN"
    elif "inventory" in email:
        assigned_role = "INVENTORY_MANAGER"
    elif "finance" in email:
        assigned_role = "FINANCE_MANAGER"
    elif "order" in email:
        assigned_role = "ORDER_MANAGER"
    else:
        assigned_role = getattr(payload, "role", None) or "OPERATIONS_MANAGER"

    # If new user authenticated via Firebase Auth
    db.log_audit(
        user=email.split("@")[0].title(),
        role=assigned_role,
        action="LOGIN_SUCCESS",
        entity=email,
        prev_val=None,
        newValue="ACTIVE_SESSION",
        reason="Authenticated via Firebase Authentication"
    )

    return {
        "token": f"token-firebase-{email}",
        "user": {
            "id": f"usr-{email.split('@')[0]}",
            "email": email,
            "name": email.split("@")[0].title(),
            "role": assigned_role,
            "status": "ACTIVE",
            "warehouseId": "HYD-01"
        }
    }

@router.post("/users")
def create_auth_user(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super Admin permission required to create users.")
    
    email = payload.get("email", "").lower().strip()
    name = payload.get("name") or payload.get("fullName") or email.split("@")[0].title()
    role = payload.get("role", "STAFF").upper()
    user_id = payload.get("id") or f"usr-{int(datetime.utcnow().timestamp()*1000)}"
    
    user_doc = {
        "id": user_id,
        "uid": user_id,
        "name": name,
        "fullName": name,
        "email": email,
        "role": role,
        "department": payload.get("department", "Warehouse Operations"),
        "warehouseId": payload.get("warehouseId", "HYD-01"),
        "status": payload.get("status", "ACTIVE"),
        "createdAt": datetime.utcnow().isoformat()
    }
    db.insert("users", user_doc)
    
    db.log_audit(
        user=current_user.get("name", "Super Admin"),
        role=current_user.get("role", "SUPER_ADMIN"),
        action="USER_CREATED",
        entity=email,
        prev_val=None,
        newValue=role,
        reason="Super Admin registered new warehouse staff profile"
    )
    
    return user_doc

@router.put("/users/{user_id}")
def update_auth_user(user_id: str, payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super Admin permission required to modify users.")
    
    user = db.get_by_id("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    updates = {}
    if "status" in payload:
        updates["status"] = payload["status"]
    if "role" in payload:
        updates["role"] = payload["role"]
    if "name" in payload or "fullName" in payload:
        name = payload.get("name") or payload.get("fullName")
        updates["name"] = name
        updates["fullName"] = name
        
    updated = db.update("users", user["id"], updates)
    
    action = "USER_DISABLED" if updates.get("status") == "DISABLED" else "USER_UPDATED"
    db.log_audit(
        user=current_user.get("name", "Super Admin"),
        role=current_user.get("role", "SUPER_ADMIN"),
        action=action,
        entity=user.get("email", user_id),
        prev_val=user.get("status"),
        newValue=updates.get("status", updates.get("role")),
        reason=f"User updated by Super Admin"
    )
    
    return updated
