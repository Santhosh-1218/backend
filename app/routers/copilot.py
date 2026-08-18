from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.ai.copilot import query_copilot
from app.core.security import get_current_user

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])

@router.post("/query")
def ask_copilot(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    question = payload.get("question", "What needs my attention right now?")
    warehouse_id = payload.get("warehouseId", "ALL")
    role = current_user.get("role", "SUPER_ADMIN")
    response = query_copilot(question=question, user_role=role, warehouseId=warehouse_id)
    return response

