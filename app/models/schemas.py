from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# User & Auth
class UserBase(BaseModel):
    id: str
    email: str
    name: str
    role: str # SUPER_ADMIN, INVENTORY_MANAGER, ORDER_MANAGER, OPERATIONS_MANAGER, FINANCE_MANAGER, PICKER, PACKER, QC_STAFF
    avatar: Optional[str] = None
    warehouseId: Optional[str] = "WH-ALPHA-01"

class UserLoginRequest(BaseModel):
    email: str
    password: Optional[str] = "password123"
    role: Optional[str] = None

# Product Schema
class Product(BaseModel):
    id: str
    sku: str
    name: str
    brand: str
    category: str # Personal Care, Detergents & Cleaning, Packaged Foods & Snacks, Beverages, Household Goods
    unit: str # bottle, pack, box, tube
    size: str # 340ml, 500g, 1L, etc.
    reorderLevel: int = 50
    reorderQuantity: int = 200
    supplier: str
    costPrice: float
    sellingPrice: float
    active: bool = True
    locationCode: str = "A-01" # Default primary rack/bin
    leadTimeDays: int = 3
    dailyDemandRate: float = 12.0
    imageUrl: Optional[str] = None

# Inventory & Bin Schema
class InventoryItem(BaseModel):
    id: str
    productId: str
    sku: str
    productName: str
    category: str
    warehouseId: str = "WH-ALPHA-01"
    zone: str # Zone A, Zone B, Zone C, Zone D
    rack: str # R-01 to R-06
    bin: str # A-01, B-02, etc.
    batchNumber: str
    expiryDate: Optional[str] = None
    totalQuantity: int
    reservedQuantity: int = 0
    damagedQuantity: int = 0
    availableQuantity: int = 0 # calculated: total - reserved - damaged
    reorderLevel: int = 50
    reorderQuantity: int = 200
    lastUpdated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class StockMovement(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    sku: str
    productName: str
    quantity: int
    previousQuantity: int
    newQuantity: int
    movementType: str # STOCK_RECEIVED, STOCK_ALLOCATED, STOCK_PICKED, STOCK_PACKED, STOCK_DISPATCHED, STOCK_DAMAGED, STOCK_ADJUSTED, STOCK_TRANSFERRED
    source: str
    destination: str
    userId: str
    userName: str
    reason: str
    orderId: Optional[str] = None

# Order & Item Schema
class OrderItem(BaseModel):
    productId: str
    sku: str
    productName: str
    category: str
    quantityRequested: int
    quantityAllocated: int = 0
    quantityPicked: int = 0
    quantityPacked: int = 0
    unitPrice: float
    locationCode: str = "A-01"

class Order(BaseModel):
    id: str
    orderNumber: str
    customerName: str
    customerType: str # TIER_1_RETAILER, SUPERMARKET_CHAIN, REGIONAL_DISTRIBUTOR, LOCAL_STORE, E_COMMERCE
    items: List[OrderItem]
    totalAmount: float
    status: str # CREATED, PRIORITIZED, INVENTORY_CHECKED, ALLOCATED, PICKING, PICKED, PACKING, PACKED, QUALITY_CHECK, READY_TO_DISPATCH, DISPATCHED, COMPLETED, EXCEPTION
    priorityScore: int = 50
    priorityLevel: str = "MEDIUM" # CRITICAL, HIGH, MEDIUM, LOW
    urgencyReason: str = "Standard processing window"
    slaDeadline: str
    slaRemainingHours: float = 24.0
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    warehouseId: str = "WH-ALPHA-01"
    allocationStatus: str = "UNALLOCATED" # UNALLOCATED, FULLY_ALLOCATED, PARTIALLY_ALLOCATED, BACKORDERED
    shortageCount: int = 0
    assignedPicker: Optional[str] = None
    trackingNumber: Optional[str] = None
    carrier: Optional[str] = None

# Decision Log Schema
class DecisionLog(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    decisionType: str # PRIORITY_ASSIGNMENT, INVENTORY_ALLOCATION, REPLENISHMENT_RECOMMENDATION, PICKING_ROUTE_OPTIMIZATION, EXCEPTION_RESOLUTION, BOTTLENECK_ALERT
    entityId: str
    entityType: str # ORDER, INVENTORY, TASK, EXCEPTION, WAREHOUSE
    situation: str
    decision: str
    reason: str
    actionRequired: str
    resultExpected: str
    impact: Optional[str] = None
    approvedBy: Optional[str] = "SYSTEM_ENGINE"
    status: str = "APPLIED" # APPLIED, PENDING_APPROVAL, REJECTED

# Picking, Packing & QC Task Schemas
class PickingTask(BaseModel):
    id: str
    orderId: str
    orderNumber: str
    priorityLevel: str
    assignedPickerId: Optional[str] = None
    assignedPickerName: Optional[str] = "Warehouse Staff"
    status: str = "PENDING" # PENDING, IN_PROGRESS, COMPLETED, BLOCKED
    items: List[Dict[str, Any]]
    unoptimizedRouteTimeMinutes: float = 18.0
    optimizedRouteTimeMinutes: float = 11.0
    timeSavedMinutes: float = 7.0
    routeSequence: List[str] # ["A-01", "A-03", "B-02", "C-01"]
    currentStep: int = 0
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class PackingTask(BaseModel):
    id: str
    orderId: str
    orderNumber: str
    stationId: str = "PACK-STATION-01"
    packerName: str = "Packer Staff"
    status: str = "PENDING" # PENDING, IN_PROGRESS, COMPLETED
    boxType: str = "Standard Heavy-Duty Carton"
    items: List[Dict[str, Any]]
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class QualityCheck(BaseModel):
    id: str
    orderId: str
    orderNumber: str
    inspectorName: str = "QC Inspector"
    status: str = "PASSED" # PASSED, FAILED, UNDER_REVIEW
    checks: Dict[str, bool] = {
        "correctProduct": True,
        "correctQuantity": True,
        "noDamagedItems": True,
        "noMissingItems": True,
        "packagingIntact": True,
        "barcodeLegible": True
    }
    notes: Optional[str] = "All QC verification checks passed perfectly."
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Exception Schema
class WarehouseException(BaseModel):
    id: str
    exceptionType: str # LOW_STOCK, OUT_OF_STOCK, DAMAGED_ITEM, MISSING_ITEM, WRONG_ITEM, INVENTORY_MISMATCH, SLA_RISK, PICKING_DELAY, PACKING_DELAY, QUALITY_FAILURE
    severity: str # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    problem: str
    affectedEntity: str # Order #1042 or SKU-SHMP-001
    affectedId: str
    detectedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    recommendedDecision: str
    resolutionPlan: str
    status: str = "OPEN" # OPEN, IN_PROGRESS, RESOLVED, ESCALATED
    assignedUser: str = "Operations Manager"
    resolvedAt: Optional[str] = None
    resolutionNotes: Optional[str] = None

# Notification Schema
class Notification(BaseModel):
    id: str
    type: str # CRITICAL, WARNING, INFO, SUCCESS
    title: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    read: bool = False
    targetRole: Optional[str] = "ALL"
    link: Optional[str] = None

# Audit Log Schema
class AuditLog(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    user: str
    role: str
    action: str
    entity: str
    previousValue: Optional[str] = None
    newValue: Optional[str] = None
    reason: str
