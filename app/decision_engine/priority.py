from datetime import datetime
from typing import Dict, Any, Tuple

def calculate_order_priority(order: Dict[str, Any], stock_availability_pct: float = 100.0) -> Tuple[int, str, str]:
    """
    Deterministic priority scoring engine.
    Returns: (priority_score: int, priority_level: str, urgency_reason: str)
    """
    score = 0
    reasons = []
    
    # 1. SLA Urgency (0 - 40 points)
    sla_hours = order.get("slaRemainingHours", 24.0)
    if sla_hours <= 2.5:
        score += 40
        reasons.append(f"SLA expires in {round(sla_hours, 1)}h (CRITICAL deadline)")
    elif sla_hours <= 8.0:
        score += 30
        reasons.append(f"SLA expires in {round(sla_hours, 1)}h (Urgent)")
    elif sla_hours <= 24.0:
        score += 15
        reasons.append(f"SLA within standard 24h window")
    else:
        score += 5
        reasons.append("Relaxed SLA window (>24h)")

    # 2. Customer Tier (0 - 35 points)
    cust_type = order.get("customerType", "LOCAL_STORE")
    if cust_type == "TIER_1_RETAILER":
        score += 35
        reasons.append("Tier-1 National Key Account (High SLA penalty)")
    elif cust_type == "SUPERMARKET_CHAIN":
        score += 25
        reasons.append("Supermarket Chain partner")
    elif cust_type == "REGIONAL_DISTRIBUTOR":
        score += 15
        reasons.append("Regional Distributor")
    elif cust_type == "E_COMMERCE":
        score += 10
        reasons.append("Direct Consumer Express")
    else:
        score += 5
        reasons.append("Local merchant / independent store")

    # 3. Order Value (0 - 15 points)
    total_amount = order.get("totalAmount", 0.0)
    if total_amount >= 1000.0:
        score += 15
        reasons.append(f"High order value (${round(total_amount, 2)})")
    elif total_amount >= 300.0:
        score += 10
        reasons.append(f"Medium order value (${round(total_amount, 2)})")
    else:
        score += 5

    # 4. Inventory Availability (0 - 10 points)
    if stock_availability_pct >= 90.0:
        score += 10
        reasons.append(f"{round(stock_availability_pct)}% inventory available in racks")
    elif stock_availability_pct >= 50.0:
        score += 5
        reasons.append(f"Partial inventory ready ({round(stock_availability_pct)}%)")
    else:
        score += 0
        reasons.append("Severe inventory constraint")

    # Final Level Mapping
    score = min(100, max(0, score))
    if score >= 85:
        level = "CRITICAL"
    elif score >= 65:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    reason_str = " • ".join(reasons)
    return score, level, reason_str
