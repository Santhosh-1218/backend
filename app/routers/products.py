from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from app.database.db import db
from app.core.security import get_current_user
from app.models.schemas import Product

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("")
def get_products(category: Optional[str] = None, search: Optional[str] = None):
    products = db.get_collection("products")
    if category and category != "ALL":
        products = [p for p in products if p.get("category", "").lower() == category.lower()]
    if search:
        s = search.lower()
        products = [p for p in products if s in p.get("name", "").lower() or s in p.get("sku", "").lower() or s in p.get("brand", "").lower()]
    return products

@router.get("/categories")
def get_categories():
    products = db.get_collection("products")
    cats = set(p.get("category") for p in products if p.get("category"))
    return sorted(list(cats))

@router.get("/{product_id}")
def get_product(product_id: str):
    p = db.get_by_id("products", product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p

@router.post("")
def create_product(product: Product, current_user: dict = Depends(get_current_user)):
    prod_data = product.model_dump()
    created = db.insert("products", prod_data)
    
    # Also initialize corresponding inventory record
    inv_data = {
        "id": f"inv-{product.sku.lower()}",
        "productId": created["id"],
        "sku": product.sku,
        "productName": product.name,
        "category": product.category,
        "warehouseId": "WH-ALPHA-01",
        "zone": f"Zone {product.locationCode[0]}",
        "rack": f"R-{product.locationCode[2:]}" if len(product.locationCode) > 2 else "R-01",
        "bin": product.locationCode,
        "batchNumber": f"BAT-{product.sku[-3:]}-2026",
        "totalQuantity": product.reorderQuantity,
        "reservedQuantity": 0,
        "damagedQuantity": 0,
        "availableQuantity": product.reorderQuantity,
        "reorderLevel": product.reorderLevel,
        "reorderQuantity": product.reorderQuantity,
    }
    db.insert("inventory", inv_data)

    db.log_audit(
        user=current_user.get("name", "Admin"),
        role=current_user.get("role", "SUPER_ADMIN"),
        action="PRODUCT_CREATED",
        entity=product.sku,
        prev_val=None,
        newValue=f"{product.name} ({product.category})",
        reason="Added new SKU to FMCG catalogue"
    )
    return created
