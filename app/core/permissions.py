from fastapi import Depends, HTTPException, status
from typing import List
from app.core.security import get_current_user

# Role hierarchy & permissions definition
ROLE_PERMISSIONS = {
    "SUPER_ADMIN": [
        "manage_users", "manage_roles", "manage_warehouses", "manage_products",
        "manage_inventory", "manage_orders", "manage_fulfillment", "manage_exceptions",
        "view_analytics", "manage_settings", "view_finance", "run_scenarios"
    ],
    "INVENTORY_MANAGER": [
        "view_inventory", "receive_stock", "adjust_inventory", "transfer_inventory",
        "view_damaged", "manage_replenishment", "view_products", "view_analytics"
    ],
    "ORDER_MANAGER": [
        "view_orders", "create_orders", "prioritize_orders", "allocate_orders",
        "approve_decisions", "monitor_sla", "view_inventory", "view_analytics"
    ],
    "OPERATIONS_MANAGER": [
        "monitor_picking", "assign_picking", "monitor_packing", "monitor_qc",
        "monitor_dispatch", "handle_exceptions", "manage_bottlenecks", "view_analytics"
    ],
    "FINANCE_MANAGER": [
        "view_finance", "view_inventory_valuation", "view_order_value", "view_analytics"
    ],
    "PICKER": ["view_picking_tasks", "update_picking_tasks"],
    "PACKER": ["view_packing_tasks", "update_packing_tasks"],
    "QC_STAFF": ["view_qc_tasks", "update_qc_tasks"]
}

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "")
        if user_role == "SUPER_ADMIN" or user_role in allowed_roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required one of roles: {allowed_roles}, but current role is {user_role}"
        )
    return role_checker

def require_permission(required_permission: str):
    def permission_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "")
        allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
        if user_role == "SUPER_ADMIN" or required_permission in allowed_permissions:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Action requires '{required_permission}' for role '{user_role}'"
        )
    return permission_checker
