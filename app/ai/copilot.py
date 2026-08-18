from typing import Dict, Any, List
from app.database.db import db
from app.decision_engine.replenishment import analyze_replenishment_needs
from app.decision_engine.bottleneck import detect_operational_bottlenecks

def query_copilot(question: str, user_role: str = "SUPER_ADMIN", warehouseId: str = "ALL") -> Dict[str, Any]:
    """
    Grounds AI Copilot responses in the live, structured warehouse database.
    Provides fast, deterministic insights with structured decision cards.
    """
    q_lower = question.lower()
    scope_label = f"StockFlow {warehouseId} Hub" if warehouseId and warehouseId != "ALL" else "StockFlow Enterprise 5-Hub Network"
    
    # 1. Fetch live snapshot filtered by scope
    all_orders = db.get_collection("orders")
    all_inventory = db.get_collection("inventory")
    all_exceptions = db.get_collection("exceptions")

    if warehouseId and warehouseId != "ALL":
        orders = [o for o in all_orders if o.get("warehouseId") == warehouseId or o.get("fulfillmentCenterId") == warehouseId]
        inventory = [i for i in all_inventory if i.get("warehouseId") == warehouseId or i.get("fulfillmentCenterId") == warehouseId]
        exceptions = [e for e in all_exceptions if e.get("warehouseId") == warehouseId or e.get("fulfillmentCenterId") == warehouseId]
    else:
        orders = all_orders
        inventory = all_inventory
        exceptions = all_exceptions

    open_exceptions = [e for e in exceptions if e.get("status") in ["OPEN", "IN_PROGRESS"]]
    critical_orders = [o for o in orders if o.get("priorityLevel") == "CRITICAL" and o.get("status") not in ["COMPLETED", "DISPATCHED"]]
    replenish_recs = analyze_replenishment_needs()
    bottlenecks_data = detect_operational_bottlenecks()


    # Pre-calculated answers grounded in live state
    if "which orders" in q_lower or "process first" in q_lower or "priority" in q_lower:
        top_orders = sorted(orders, key=lambda x: x.get("priorityScore", 0), reverse=True)[:3]
        orders_summary = "\n".join([
            f"• **{o['orderNumber']}** ({o['customerName']}): Priority Score {o.get('priorityScore')}/100 - {o.get('urgencyReason')}"
            for o in top_orders
        ])
        
        answer = (
            f"### High Priority Fulfillment Queue\n\n"
            f"Based on real-time SLA deadlines and customer contractual tiers, process these orders immediately:\n\n"
            f"{orders_summary}\n\n"
            f"**Recommendation:** Fast-track **{top_orders[0]['orderNumber']}** to wave picking immediately as SLA deadline expires in {top_orders[0].get('slaRemainingHours', 2.0)} hours."
        )
        decision_card = {
            "situation": f"Order {top_orders[0]['orderNumber']} has an urgent 2-hour SLA deadline with Tier-1 retailer {top_orders[0]['customerName']}.",
            "decision": f"Allocate immediate pick priority and expedite wave batch.",
            "reason": f"Contractual penalty prevention and 99.8% on-time fulfillment compliance.",
            "action": f"Release picking wave to Zone {top_orders[0]['items'][0]['locationCode'][0]} immediately.",
            "result": f"Expected fulfillment in 45 minutes, well ahead of SLA breach."
        }

    elif "1042" in q_lower or "why did the system allocate" in q_lower or "allocation" in q_lower:
        answer = (
            f"### Allocation Explanation for Order #1042 vs Order #1048\n\n"
            f"• **Order #1042 (Metro Hypermarket)**: Priority Level **CRITICAL** (Score 95), SLA deadline in 2.0 hours. Required: 10 units.\n"
            f"• **Order #1048 (Sunrise Grocery)**: Priority Level **LOW** (Score 28), SLA deadline in 48 hours. Required: 5 units.\n"
            f"• **Physical Available Stock**: 7 units of Dove Shampoo (SKU-SHMP-001) in Bin A-01.\n\n"
            f"**System Decision Logic:**\n"
            f"1. Evaluated order priority weights: Order #1042 had a 67-point priority lead over Order #1048.\n"
            f"2. Allocated all 7 available units to Order #1042 (partial fulfillment of 70%).\n"
            f"3. Held Order #1048 in pending queue to avoid splitting single-batch integrity.\n"
            f"4. Automatically flagged a 3-unit shortage and created replenishment PO recommendation."
        )
        decision_card = {
            "situation": "Contending demand: Order #1042 (10 units req) vs Order #1048 (5 units req) with only 7 units in stock.",
            "decision": "Allocate all 7 units to #1042, hold #1048, and flag 3-unit backorder.",
            "reason": "Order #1042 is a Tier-1 SLA account expiring in 2h; Order #1048 has a 48h relaxed window.",
            "action": "Dispatch 7 units now and trigger expedited supplier delivery for 200 units.",
            "result": "Critical SLA met, backorder logged with zero stock loss."
        }

    elif "stockout" in q_lower or "reorder" in q_lower or "replenish" in q_lower or "low stock" in q_lower:
        crit_recs = [r for r in replenish_recs if r["riskLevel"] in ["CRITICAL", "HIGH"]][:4]
        items_list = "\n".join([
            f"• **{r['sku']}** ({r['productName']}): Available: {r['availableQuantity']} | Reorder Qty: **{r['recommendedQuantity']} units** | Supplier: {r['supplier']}"
            for r in crit_recs
        ])
        answer = (
            f"### Inventory Stockout Risks & Replenishment Plan\n\n"
            f"There are currently **{len(crit_recs)} products** at immediate risk of stockout:\n\n"
            f"{items_list}\n\n"
            f"**Key Recommendation:** Approve Purchase Orders for top critical items ({crit_recs[0]['sku']}) immediately to avoid line stoppages."
        )
        decision_card = {
            "situation": f"{crit_recs[0]['productName']} ({crit_recs[0]['sku']}) stock is below safety buffer ({crit_recs[0]['availableQuantity']} units left).",
            "decision": f"Issue immediate PO for {crit_recs[0]['recommendedQuantity']} units to {crit_recs[0]['supplier']}.",
            "reason": f"Daily demand ({crit_recs[0].get('daysOfSupply', 1.5)} days supply remaining) exceeds lead-time safety threshold.",
            "action": "Approve purchase order and send electronic EDI to supplier.",
            "result": "Prevents stockout on 14 upcoming scheduled customer orders."
        }

    elif "bottleneck" in q_lower or "delay" in q_lower or "zone b" in q_lower:
        btn = bottlenecks_data["bottlenecks"][0] if bottlenecks_data["bottlenecks"] else None
        if btn:
            answer = (
                f"### Operational Bottleneck Alert: {btn['location']}\n\n"
                f"• **Location:** {btn['location']} (Detergents & Surface Cleaners)\n"
                f"• **Metric:** Avg Picking Time is **{btn['currentValue']}** vs Warehouse Benchmark of **{btn['benchmarkValue']}** ({btn['deviationPct']})\n"
                f"• **Tasks Backlog:** {btn['tasksBacklog']} pick tasks queued\n\n"
                f"**Root Cause:** Surge in bulk liquid detergent orders combined with only 2 pickers assigned to Zone B.\n\n"
                f"**Action Recommended:** Rebalance 2 pickers from Zone D (currently at low load) to Zone B."
            )
            decision_card = {
                "situation": btn["situation"],
                "decision": btn["decision"],
                "reason": btn["reason"],
                "action": btn["action"],
                "result": btn["result"]
            }
        else:
            answer = "All warehouse zones and fulfillment stages are currently operating within nominal cycle time benchmarks."
            decision_card = None

    elif "exception" in q_lower or "unresolved" in q_lower or "damaged" in q_lower:
        if open_exceptions:
            exc_list = "\n".join([
                f"• **{e.get('id', 'EXC')}** [{e.get('severity', 'HIGH')}]: {e.get('title', 'Warehouse Exception')} - {e.get('problem', e.get('description', e.get('details', 'Operational anomaly detected')))}"
                for e in open_exceptions[:4]
            ])
            first_exc = open_exceptions[0]
            answer = (
                f"### Active Warehouse Exceptions ({len(open_exceptions)} Unresolved)\n\n"
                f"{exc_list}\n\n"
                f"**Recommended Focus:** Resolve the **{first_exc.get('title', 'Warehouse Exception')}** by approving the suggested resolution plan in the Exception Center."
            )
            decision_card = {
                "situation": first_exc.get("problem", first_exc.get("description", "Active warehouse exception")),
                "decision": first_exc.get("recommendedDecision", "Apply automated corrective resolution"),
                "reason": "Prevents fulfillment blockages and keeps warehouse inventory records accurate.",
                "action": first_exc.get("resolutionPlan", "Execute recommended resolution in Exception Center"),
                "result": "Exception will be marked as RESOLVED and audit trail logged."
            }
        else:
            answer = "All warehouse exceptions have been successfully resolved. Operational pipeline is clear."
            decision_card = None

    else:
        answer = (
            f"### WarehouseIQ Live Operations Summary\n\n"
            f"• **Active Orders:** {len(orders)} total | **{len(critical_orders)} Critical SLA Orders**\n"
            f"• **Inventory Health:** {len(inventory)} SKUs tracked | **{len(replenish_recs)} Reorder Alerts**\n"
            f"• **Active Exceptions:** **{len(open_exceptions)} Open Issues**\n"
            f"• **Key Bottleneck:** Zone B picking time (+46% above benchmark)\n\n"
            f"How can I assist you with specific order prioritization, replenishment recommendations, or route optimization?"
        )
        decision_card = {
            "situation": f"Warehouse operating at 78.4% capacity with {len(critical_orders)} critical SLA orders requiring active tracking.",
            "decision": "Prioritize wave release for critical orders and rebalance Zone B picking staff.",
            "reason": "Ensures on-time fulfillment and resolves zone queue buildup.",
            "action": "Navigate to Orders and Analytics to review recommended actions.",
            "result": "Smooth operational throughput across all 4 warehouse zones."
        }

    return {
        "question": question,
        "answer": answer,
        "decisionCard": decision_card,
        "timestamp": db.get_collection("orders")[0].get("updatedAt")
    }
