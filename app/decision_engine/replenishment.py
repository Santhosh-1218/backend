from typing import List, Dict, Any
from app.database.db import db

def analyze_replenishment_needs() -> List[Dict[str, Any]]:
    """
    Evaluates inventory levels against daily demand and lead times.
    Generates actionable replenishment recommendations.
    """
    inventory_items = db.get_collection("inventory")
    products = {p["sku"]: p for p in db.get_collection("products")}
    recommendations = []

    for inv in inventory_items:
        sku = inv["sku"]
        prod = products.get(sku, {})
        
        available = inv.get("availableQuantity", 0)
        reorder_level = inv.get("reorderLevel", prod.get("reorderLevel", 50))
        reorder_qty = inv.get("reorderQuantity", prod.get("reorderQuantity", 200))
        daily_demand = prod.get("dailyDemandRate", 12.0)
        lead_time = prod.get("leadTimeDays", 3)
        
        # Lead time demand = Daily Demand * Lead Time Days
        lead_time_demand = daily_demand * lead_time
        days_of_supply = round(available / max(0.1, daily_demand), 1)

        # Risk classification
        if available <= 0:
            risk_level = "CRITICAL"
            reason = f"OUT OF STOCK (0 units available). Immediate stockout impacting active fulfillment orders."
            priority = "IMMEDIATE"
            recommended_qty = int(reorder_qty * 1.5)
        elif available < (lead_time_demand * 0.8):
            risk_level = "CRITICAL"
            reason = f"Severe stockout risk within {days_of_supply} days. Current stock ({available}) is below lead-time demand ({round(lead_time_demand, 1)} units)."
            priority = "URGENT"
            recommended_qty = reorder_qty
        elif available <= reorder_level:
            risk_level = "HIGH"
            reason = f"Stock level ({available} units) breached safety reorder threshold ({reorder_level} units). Supply covers {days_of_supply} days."
            priority = "HIGH"
            recommended_qty = reorder_qty
        elif days_of_supply < (lead_time * 2):
            risk_level = "MODERATE"
            reason = f"Stock buffer trending low. Projected depletion in {days_of_supply} days."
            priority = "STANDARD"
            recommended_qty = reorder_qty
        else:
            continue # Healthy stock

        rec = {
            "sku": sku,
            "productId": inv.get("productId"),
            "productName": inv.get("productName"),
            "category": inv.get("category"),
            "binLocation": inv.get("bin"),
            "availableQuantity": available,
            "reorderLevel": reorder_level,
            "recommendedQuantity": recommended_qty,
            "supplier": prod.get("supplier", "Standard FMCG Supplier"),
            "estimatedCost": round(recommended_qty * prod.get("costPrice", 5.0), 2),
            "leadTimeDays": lead_time,
            "daysOfSupply": days_of_supply,
            "riskLevel": risk_level,
            "suggestedPriority": priority,
            "reason": reason,
            "action": f"Issue Purchase Order for {recommended_qty} units to {prod.get('supplier', 'Supplier')}"
        }
        recommendations.append(rec)

    # Sort critical first
    risk_rank = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
    recommendations.sort(key=lambda x: risk_rank.get(x["riskLevel"], 3))
    return recommendations
