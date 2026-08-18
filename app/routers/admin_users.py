from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from app.database.db import db
from app.core.security import get_current_user, require_super_admin
from app.core.firebase_auth import FirebaseAuthService

router = APIRouter(prefix="/admin/users", tags=["Admin User Management"])

class CreateUserPayload(BaseModel):
    fullName: Optional[str] = None
    name: Optional[str] = None
    email: str
    password: str
    role: str
    department: Optional[str] = "Warehouse Operations"
    warehouseId: Optional[str] = "HYD-01"
    assignedWarehouses: Optional[List[str]] = None
    rfGunId: Optional[str] = None
    shift: Optional[str] = "Morning Shift (06:00 - 14:30)"
    phone: Optional[str] = None

class UpdateUserPayload(BaseModel):
    fullName: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    warehouseId: Optional[str] = None
    assignedWarehouses: Optional[List[str]] = None
    rfGunId: Optional[str] = None
    shift: Optional[str] = None
    phone: Optional[str] = None

class UpdatePasswordPayload(BaseModel):
    password: str

class UpdateRolePayload(BaseModel):
    role: str

class UpdateStatusPayload(BaseModel):
    status: str

@router.get("", response_model=List[Dict[str, Any]])
def list_admin_users(current_user: dict = Depends(require_super_admin)):
    """
    Returns all warehouse users and their RBAC status.
    Super Admin only.
    """
    users = db.get_collection("users")
    # Clean output to ensure no sensitive credentials exist
    sanitized = []
    for u in users:
        item = dict(u)
        item.pop("password", None)
        item.pop("plainPassword", None)
        item.pop("temporaryPassword", None)
        # Ensure consistent fields
        item["name"] = item.get("name") or item.get("fullName", "")
        item["fullName"] = item.get("fullName") or item.get("name", "")
        item["status"] = item.get("status", "ACTIVE")
        item["warehouseId"] = item.get("warehouseId", "HYD-01")
        item["department"] = item.get("department", "Warehouse Operations")
        item["shift"] = item.get("shift", "General Shift")
        item["rfGunId"] = item.get("rfGunId", "")
        item["phone"] = item.get("phone", "")
        sanitized.append(item)
    return sanitized

@router.post("/sync-firebase")
def sync_firebase_users(current_user: dict = Depends(require_super_admin)):
    """
    Synchronizes known Firebase Auth registered users into active database storage.
    """
    synced = db.sync_known_firebase_users()
    sanitized = []
    for u in synced:
        item = dict(u)
        item.pop("password", None)
        item["name"] = item.get("name") or item.get("fullName", "")
        item["fullName"] = item.get("fullName") or item.get("name", "")
        item["status"] = item.get("status", "ACTIVE")
        item["warehouseId"] = item.get("warehouseId", "HYD-01")
        item["department"] = item.get("department", "Warehouse Operations")
        item["shift"] = item.get("shift", "General Shift")
        item["rfGunId"] = item.get("rfGunId", "")
        item["phone"] = item.get("phone", "")
        sanitized.append(item)
    return {
        "status": "SUCCESS",
        "message": f"Successfully synchronized {len(sanitized)} accounts.",
        "users": sanitized
    }

@router.get("/{uid}")
def get_admin_user(uid: str, current_user: dict = Depends(require_super_admin)):
    """
    Retrieves a single user profile.
    Super Admin only.
    """
    user = db.get_by_id("users", uid)
    if not user:
        # Search by UID if id differs
        for u in db.get_collection("users"):
            if u.get("uid") == uid or u.get("id") == uid:
                user = u
                break
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    item = dict(user)
    item.pop("password", None)
    return item

@router.post("", status_code=status.HTTP_201_CREATED)
def create_warehouse_user(
    payload: CreateUserPayload,
    current_user: dict = Depends(require_super_admin)
):
    """
    Creates a new warehouse user in Firebase Authentication and Firestore/DB profile.
    Does NOT alter the logged-in Super Admin session.
    Never stores plaintext password in Firestore.
    Logs USER_CREATED audit event.
    """
    email = payload.email.lower().strip()
    full_name = payload.fullName or payload.name or email.split("@")[0].title()
    role = payload.role.upper()
    department = payload.department or "Warehouse Operations"
    warehouse_id = payload.warehouseId or "HYD-01"
    assigned_warehouses = payload.assignedWarehouses or [warehouse_id]

    # 1. Check if user already exists in DB
    existing_users = db.get_collection("users")
    for u in existing_users:
        if u.get("email", "").lower() == email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An account with email {email} already exists."
            )

    # 2. Create in Firebase Authentication
    success, fb_res = FirebaseAuthService.create_user(
        email=email,
        password=payload.password,
        display_name=full_name
    )
    
    uid = fb_res.get("uid") or f"uid-{int(datetime.utcnow().timestamp()*1000)}"

    # 3. Create User Document for Firestore / DB (NO password stored)
    user_doc = {
        "id": uid,
        "uid": uid,
        "name": full_name,
        "fullName": full_name,
        "email": email,
        "role": role,
        "department": department,
        "warehouseId": warehouse_id,
        "assignedWarehouses": assigned_warehouses,
        "rfGunId": payload.rfGunId or "HHT-8850",
        "shift": payload.shift or "Morning Shift (06:00 - 14:30)",
        "phone": payload.phone or "+91 98000 00000",
        "status": "ACTIVE",
        "createdAt": datetime.utcnow().isoformat(),
        "createdBy": current_user.get("name", "Super Admin"),
        "updatedAt": datetime.utcnow().isoformat()
    }

    db.insert("users", user_doc)

    # 4. Create Audit Log
    db.log_audit(
        user=current_user.get("name", "Super Admin"),
        role=current_user.get("role", "SUPER_ADMIN"),
        action="USER_CREATED",
        entity=f"{full_name} <{email}>",
        prev_val=None,
        newValue=f"Role: {role}, Dept: {department}, Facility: {warehouse_id}",
        reason=f"Super Admin created warehouse staff profile with role {role}."
    )

    db.add_notification(
        notif_type="SUCCESS",
        title=f"User Created: {full_name}",
        message=f"{full_name} assigned role {role} for {department}.",
        role="SUPER_ADMIN",
        link="/users"
    )

    return user_doc

@router.patch("/{uid}")
def update_warehouse_user(
    uid: str,
    payload: UpdateUserPayload,
    current_user: dict = Depends(require_super_admin)
):
    """
    Updates user details (Name, Email, Role, Department, Status).
    Synchronizes with Firebase Auth and Firestore.
    Logs audit events for modifications.
    """
    user = db.get_by_id("users", uid)
    if not user:
        for u in db.get_collection("users"):
            if u.get("uid") == uid or u.get("id") == uid:
                user = u
                break
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    updates: Dict[str, Any] = {}
    prev_role = user.get("role")
    prev_email = user.get("email")
    prev_dept = user.get("department")
    prev_status = user.get("status", "ACTIVE")

    if payload.name or payload.fullName:
        name_val = payload.fullName or payload.name
        updates["name"] = name_val
        updates["fullName"] = name_val

    if payload.email:
        updates["email"] = payload.email.lower().strip()

    if payload.role:
        updates["role"] = payload.role.upper()

    if payload.department:
        updates["department"] = payload.department

    if payload.warehouseId:
        updates["warehouseId"] = payload.warehouseId

    if payload.assignedWarehouses is not None:
        updates["assignedWarehouses"] = payload.assignedWarehouses

    if payload.rfGunId is not None:
        updates["rfGunId"] = payload.rfGunId

    if payload.shift is not None:
        updates["shift"] = payload.shift

    if payload.phone is not None:
        updates["phone"] = payload.phone

    if payload.status:
        updates["status"] = payload.status.upper()

    # Sync with Firebase Auth
    FirebaseAuthService.update_user_profile(
        uid=user.get("uid", uid),
        display_name=updates.get("name"),
        email=updates.get("email"),
        disabled=(updates.get("status") == "DISABLED") if "status" in updates else None
    )

    updated_user = db.update("users", user["id"], updates)

    # Log specific audit events
    if "role" in updates and updates["role"] != prev_role:
        db.log_audit(
            user=current_user.get("name", "Super Admin"),
            role=current_user.get("role", "SUPER_ADMIN"),
            action="ROLE_CHANGED",
            entity=user.get("name", user.get("email")),
            prev_val=prev_role,
            newValue=updates["role"],
            reason=f"Role updated from {prev_role} to {updates['role']} by Super Admin"
        )

    if "status" in updates and updates["status"] != prev_status:
        action_name = "USER_DISABLED" if updates["status"] == "DISABLED" else "USER_ENABLED"
        db.log_audit(
            user=current_user.get("name", "Super Admin"),
            role=current_user.get("role", "SUPER_ADMIN"),
            action=action_name,
            entity=user.get("name", user.get("email")),
            prev_val=prev_status,
            newValue=updates["status"],
            reason=f"Account status changed to {updates['status']}"
        )

    if "email" in updates and updates["email"] != prev_email:
        db.log_audit(
            user=current_user.get("name", "Super Admin"),
            role=current_user.get("role", "SUPER_ADMIN"),
            action="EMAIL_CHANGED",
            entity=user.get("name", uid),
            prev_val=prev_email,
            newValue=updates["email"],
            reason="User email address updated in Firebase Auth and profile"
        )

    if "department" in updates and updates["department"] != prev_dept:
        db.log_audit(
            user=current_user.get("name", "Super Admin"),
            role=current_user.get("role", "SUPER_ADMIN"),
            action="DEPARTMENT_CHANGED",
            entity=user.get("name", uid),
            prev_val=prev_dept,
            newValue=updates["department"],
            reason="User department assignment updated"
        )

    db.log_audit(
        user=current_user.get("name", "Super Admin"),
        role=current_user.get("role", "SUPER_ADMIN"),
        action="USER_UPDATED",
        entity=user.get("name", uid),
        prev_val=None,
        newValue=str(list(updates.keys())),
        reason="Super Admin saved user profile changes."
    )

    return updated_user

@router.patch("/{uid}/password")
def reset_user_password(
    uid: str,
    payload: UpdatePasswordPayload,
    current_user: dict = Depends(require_super_admin)
):
    """
    Resets/Updates password in Firebase Authentication directly.
    NEVER retrieves or displays old password.
    NEVER saves password in Firestore.
    Logs PASSWORD_UPDATED audit event.
    """
    user = db.get_by_id("users", uid)
    if not user:
        for u in db.get_collection("users"):
            if u.get("uid") == uid or u.get("id") == uid:
                user = u
                break
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_pwd = payload.password
    if len(new_pwd) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    # Update in Firebase Auth
    FirebaseAuthService.update_password(
        uid=user.get("uid", uid),
        new_password=new_pwd,
        email=user.get("email")
    )

    # Log Audit
    db.log_audit(
        user=current_user.get("name", "Super Admin"),
        role=current_user.get("role", "SUPER_ADMIN"),
        action="PASSWORD_UPDATED",
        entity=f"{user.get('name', 'User')} ({user.get('email')})",
        prev_val="[HIDDEN]",
        newValue="[PASSWORD_RESET_SUCCESS]",
        reason="Super Admin set a new password via secure Firebase Auth bridge"
    )

    return {
        "status": "SUCCESS",
        "message": "Password updated successfully in Firebase Authentication."
    }

@router.patch("/{uid}/role")
def update_user_role(
    uid: str,
    payload: UpdateRolePayload,
    current_user: dict = Depends(require_super_admin)
):
    """
    Updates user role and logs ROLE_CHANGED.
    """
    return update_warehouse_user(uid, UpdateUserPayload(role=payload.role), current_user)

@router.patch("/{uid}/status")
def update_user_status(
    uid: str,
    payload: UpdateStatusPayload,
    current_user: dict = Depends(require_super_admin)
):
    """
    Updates user active/disabled status and logs USER_DISABLED / USER_ENABLED.
    """
    return update_warehouse_user(uid, UpdateUserPayload(status=payload.status), current_user)

@router.delete("/{uid}")
def delete_warehouse_user(
    uid: str,
    current_user: dict = Depends(require_super_admin)
):
    """
    Deletes user permanently from Firebase Auth and DB.
    Super Admin only with audit log.
    """
    user = db.get_by_id("users", uid)
    if not user:
        for u in db.get_collection("users"):
            if u.get("uid") == uid or u.get("id") == uid:
                user = u
                break
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    FirebaseAuthService.delete_user(user.get("uid", uid))
    db.delete("users", user["id"])

    db.log_audit(
        user=current_user.get("name", "Super Admin"),
        role=current_user.get("role", "SUPER_ADMIN"),
        action="USER_DELETED",
        entity=f"{user.get('name')} <{user.get('email')}>",
        prev_val=user.get("role"),
        newValue="DELETED",
        reason="Super Admin permanently removed warehouse user account"
    )

    return {"status": "SUCCESS", "message": "User deleted successfully."}
