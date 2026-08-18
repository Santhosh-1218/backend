import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

# =============================================================================
# STOCKFLOW 5 AUTHORITATIVE FULFILLMENT CENTERS
# =============================================================================
STOCKFLOW_WAREHOUSES = [
    {
        "id": "HYD-01",
        "code": "HYD-01",
        "name": "StockFlow Hyderabad Central Hub",
        "fullName": "StockFlow Hyderabad Central Mega Hub",
        "location": "Shamshabad Logistics Park, Hyderabad, Telangana",
        "city": "Shamshabad, Hyderabad, Telangana",
        "state": "Telangana",
        "country": "India",
        "type": "CENTRAL_MAIN_HUB",
        "isMainHub": True,
        "floorsCount": 6,
        "totalCapacitySqFt": 750000,
        "utilizationPct": 84.6,
        "dailyThroughputOrders": 68000,
        "activeDockBays": 12,
        "activeWorkers": 320,
        "coldChainEnabled": True,
        "floors": [
            {
                "floorNumber": 1,
                "floorName": "Receiving & Yard Management (YMS)",
                "purpose": "Inbound trailer check-in, unloading, gate passes, cross-docking (Bays 01-12)",
                "zones": [
                    {"code": "Zone 1A", "name": "Inbound Unload Bays 01-06", "binsCount": 24, "status": "ACTIVE", "capacity": 92},
                    {"code": "Zone 1B", "name": "Cross-Dock Shuttles Bays 07-10", "binsCount": 16, "status": "ACTIVE", "capacity": 80},
                    {"code": "Zone 1C", "name": "Pallet Ingest QA Staging Bays 11-12", "binsCount": 20, "status": "ACTIVE", "capacity": 75}
                ]
            },
            {
                "floorNumber": 2,
                "floorName": "Inbound Storage & Bulk Put-Away",
                "purpose": "Primary bulk carton receiving, high-bay racking, pallet put-away buffer",
                "zones": [
                    {"code": "Zone 2A", "name": "Bulk FMCG & Groceries Buffer", "binsCount": 48, "status": "ACTIVE", "capacity": 88},
                    {"code": "Zone 2B", "name": "Chemical & Detergent Reserve", "binsCount": 36, "status": "ACTIVE", "capacity": 79},
                    {"code": "Zone 2C", "name": "Automotive & Hardware Staging", "binsCount": 30, "status": "ACTIVE", "capacity": 70}
                ]
            },
            {
                "floorNumber": 3,
                "floorName": "Main Inventory High-Density Storage",
                "purpose": "Pick-face replenishment, high-density shelving, cold storage chambers",
                "zones": [
                    {"code": "Zone A", "name": "Personal Care & Cosmetics", "binsCount": 60, "status": "ACTIVE", "capacity": 82},
                    {"code": "Zone B", "name": "Detergents & Surface Cleaners", "binsCount": 50, "status": "BOTTLENECK_ALERT", "capacity": 91},
                    {"code": "Zone C", "name": "Packaged Foods & Beverages", "binsCount": 72, "status": "ACTIVE", "capacity": 85},
                    {"code": "Zone D", "name": "Deep Cold Chain Reefer (-4°C to 4°C)", "binsCount": 32, "status": "ACTIVE", "capacity": 74}
                ]
            },
            {
                "floorNumber": 4,
                "floorName": "Wave Picking & Route Optimization",
                "purpose": "TSP Green Corridor pathing, multi-order tote batching, RF pick verification",
                "zones": [
                    {"code": "Zone 4A", "name": "High-Velocity Express Picking", "binsCount": 40, "status": "ACTIVE", "capacity": 89},
                    {"code": "Zone 4B", "name": "Batch Wave Consolidation Area", "binsCount": 32, "status": "ACTIVE", "capacity": 84},
                    {"code": "Zone 4C", "name": "Oversized & Heavy Item Pick Zone", "binsCount": 24, "status": "ACTIVE", "capacity": 65}
                ]
            },
            {
                "floorNumber": 5,
                "floorName": "Packing Stations & 6-Point QC Checkpoints",
                "purpose": "Barcode scan verify, digital scale gross weight checks, auto-bagging",
                "zones": [
                    {"code": "Zone 5A", "name": "Automated Packing Lines 1-12", "binsCount": 24, "status": "ACTIVE", "capacity": 88},
                    {"code": "Zone 5B", "name": "6-Point QC Inspection Stations", "binsCount": 16, "status": "ACTIVE", "capacity": 78},
                    {"code": "Zone 5C", "name": "Exception & Rework Isolation Bay", "binsCount": 12, "status": "ACTIVE", "capacity": 55}
                ]
            },
            {
                "floorNumber": 6,
                "floorName": "Outbound Dispatch & Linehaul Staging",
                "purpose": "Carrier sortation, 4x6 thermal label verification, pallet linehaul sealing",
                "zones": [
                    {"code": "Zone 6A", "name": "Tier-1 Priority Air Dispatch Staging", "binsCount": 20, "status": "ACTIVE", "capacity": 86},
                    {"code": "Zone 6B", "name": "National Linehaul Bay 05-07 Staging", "binsCount": 30, "status": "ACTIVE", "capacity": 92},
                    {"code": "Zone 6C", "name": "Control Tower & Yard Ops Dispatch Office", "binsCount": 10, "status": "ACTIVE", "capacity": 60}
                ]
            }
        ]
    },
    {
        "id": "MUM-01",
        "code": "MUM-01",
        "name": "StockFlow Mumbai Fulfillment Hub",
        "fullName": "StockFlow Mumbai City Logistics Hub",
        "location": "Bhiwandi Industrial Corridor, Mumbai, Maharashtra",
        "city": "Bhiwandi, Mumbai, Maharashtra",
        "state": "Maharashtra",
        "country": "India",
        "type": "METRO_FULFILLMENT_HUB",
        "isMainHub": False,
        "floorsCount": 2,
        "totalCapacitySqFt": 420000,
        "utilizationPct": 79.2,
        "dailyThroughputOrders": 42000,
        "activeDockBays": 8,
        "activeWorkers": 180,
        "coldChainEnabled": True,
        "floors": [
            {
                "floorNumber": 1,
                "floorName": "Receiving, Cross-Dock & Dispatch",
                "purpose": "Dock doors, high-throughput intake, same-day dispatch (Bays 01-08)",
                "zones": [
                    {"code": "Zone M1", "name": "Inbound / Outbound Dock Bays 1-8", "binsCount": 32, "status": "ACTIVE", "capacity": 80},
                    {"code": "Zone M2", "name": "Fast-Track Cross-Dock Area", "binsCount": 20, "status": "ACTIVE", "capacity": 72}
                ]
            },
            {
                "floorNumber": 2,
                "floorName": "High-Density Picking & Packing QC",
                "purpose": "Shelving, wave picking, automated packing benches",
                "zones": [
                    {"code": "Zone M3", "name": "Personal Care, Foods & Beverages", "binsCount": 48, "status": "ACTIVE", "capacity": 81},
                    {"code": "Zone M4", "name": "Electronics & Accessories Staging", "binsCount": 36, "status": "ACTIVE", "capacity": 75}
                ]
            }
        ]
    },
    {
        "id": "VJA-01",
        "code": "VJA-01",
        "name": "StockFlow Vijayawada Fulfillment Hub",
        "fullName": "StockFlow Vijayawada Andhra Distribution Hub",
        "location": "Gannavaram Logistics Node, Vijayawada, Andhra Pradesh",
        "city": "Gannavaram, Vijayawada, Andhra Pradesh",
        "state": "Andhra Pradesh",
        "country": "India",
        "type": "REGIONAL_DISTRIBUTION_HUB",
        "isMainHub": False,
        "floorsCount": 2,
        "totalCapacitySqFt": 280000,
        "utilizationPct": 71.8,
        "dailyThroughputOrders": 24000,
        "activeDockBays": 8,
        "activeWorkers": 110,
        "coldChainEnabled": True,
        "floors": [
            {
                "floorNumber": 1,
                "floorName": "Intake & Cold Storage",
                "purpose": "Fresh produce, beverages, receiving and dispatch (Bays 01-08)",
                "zones": [
                    {"code": "Zone V1", "name": "Receiving & Cold Chain Section", "binsCount": 24, "status": "ACTIVE", "capacity": 70},
                    {"code": "Zone V2", "name": "Regional Cross-Dock Staging", "binsCount": 16, "status": "ACTIVE", "capacity": 65}
                ]
            },
            {
                "floorNumber": 2,
                "floorName": "General Merchandise & Packing",
                "purpose": "Groceries, home essentials, picking and packing",
                "zones": [
                    {"code": "Zone V3", "name": "Dry Grocery & Household Shelving", "binsCount": 36, "status": "ACTIVE", "capacity": 74},
                    {"code": "Zone V4", "name": "Order Consolidation & Dispatch", "binsCount": 20, "status": "ACTIVE", "capacity": 68}
                ]
            }
        ]
    },
    {
        "id": "MAH-01",
        "code": "MAH-01",
        "name": "StockFlow Maharashtra Regional Hub",
        "fullName": "StockFlow Maharashtra Regional Logistics Center",
        "location": "Chakan Industrial Area, Pune, Maharashtra",
        "city": "Chakan, Pune, Maharashtra",
        "state": "Maharashtra",
        "country": "India",
        "type": "REGIONAL_FULFILLMENT_HUB",
        "isMainHub": False,
        "floorsCount": 2,
        "totalCapacitySqFt": 380000,
        "utilizationPct": 76.5,
        "dailyThroughputOrders": 36000,
        "activeDockBays": 8,
        "activeWorkers": 155,
        "coldChainEnabled": False,
        "floors": [
            {
                "floorNumber": 1,
                "floorName": "Heavy Freight & Bulk Automotive Intake",
                "purpose": "Spare parts, hardware, pallet storage, dock bays (Bays 01-08)",
                "zones": [
                    {"code": "Zone MH1", "name": "Heavy Equipment & Hardware Bay", "binsCount": 28, "status": "ACTIVE", "capacity": 78},
                    {"code": "Zone MH2", "name": "Automotive Spares Staging", "binsCount": 24, "status": "ACTIVE", "capacity": 72}
                ]
            },
            {
                "floorNumber": 2,
                "floorName": "Fashion, Office & Consumer Packaged Goods",
                "purpose": "Apparel, stationery, wave picking and QC",
                "zones": [
                    {"code": "Zone MH3", "name": "Apparel & Footwear Racks", "binsCount": 42, "status": "ACTIVE", "capacity": 79},
                    {"code": "Zone MH4", "name": "Packing & Carrier Dispatch", "binsCount": 26, "status": "ACTIVE", "capacity": 74}
                ]
            }
        ]
    },
    {
        "id": "CHE-01",
        "code": "CHE-01",
        "name": "StockFlow Chennai Fulfillment Hub",
        "fullName": "StockFlow Chennai Southern Corridor Hub",
        "location": "Sriperumbudur Logistics Zone, Chennai, Tamil Nadu",
        "city": "Sriperumbudur, Chennai, Tamil Nadu",
        "state": "Tamil Nadu",
        "country": "India",
        "type": "COASTAL_FULFILLMENT_HUB",
        "isMainHub": False,
        "floorsCount": 2,
        "totalCapacitySqFt": 340000,
        "utilizationPct": 74.3,
        "dailyThroughputOrders": 32000,
        "activeDockBays": 8,
        "activeWorkers": 140,
        "coldChainEnabled": True,
        "floors": [
            {
                "floorNumber": 1,
                "floorName": "Coastal Inbound & Port Transshipment",
                "purpose": "Port receiving, container staging, cold reefer (Bays 01-08)",
                "zones": [
                    {"code": "Zone CH1", "name": "Container Inbound & Dock Bays 1-8", "binsCount": 30, "status": "ACTIVE", "capacity": 75},
                    {"code": "Zone CH2", "name": "Cold Chain Seafood & Beverages", "binsCount": 20, "status": "ACTIVE", "capacity": 70}
                ]
            },
            {
                "floorNumber": 2,
                "floorName": "Electronics, Personal Care & Dispatch",
                "purpose": "Consumer electronics, personal care, automated packing",
                "zones": [
                    {"code": "Zone CH3", "name": "High-Value Electronics Vault", "binsCount": 36, "status": "ACTIVE", "capacity": 76},
                    {"code": "Zone CH4", "name": "Express Regional Dispatch Bay", "binsCount": 24, "status": "ACTIVE", "capacity": 72}
                ]
            }
        ]
    }
]

# =============================================================================
# 1,000+ REALISTIC GLOBAL PRODUCTS GENERATOR
# =============================================================================
PRODUCT_CATEGORIES_CONFIG = [
    {
        "category": "Electronics",
        "code": "ELE",
        "subcategories": [
            ("Wireless Audio", ["True Wireless Earbuds", "Noise Cancelling Headphones", "Bluetooth Party Speaker", "Waterproof Sport Earphones", "Soundbar with Subwoofer", "Gaming Headset 7.1 Surround", "Neckband Bluetooth Earphones"]),
            ("Smart Devices", ["Smartwatch Amoled Display", "Fitness Tracker Band", "Smart Home WiFi Plug", "Smart LED Bulb RGB", "Smart Security Camera 2K", "Video Doorbell WiFi"]),
            ("Computer Peripherals", ["Wireless Ergonomic Mouse", "Mechanical Gaming Keyboard", "USB-C Multiport Hub 7-in-1", "Ultra-Wide Monitor 27-inch", "Full HD Web Camera 1080p", "High-Speed NVMe SSD 1TB", "External Portable Hard Drive 2TB", "Dual-Band WiFi 6 Router"]),
            ("Power & Cables", ["65W GaN Fast Wall Charger", "20000mAh Power Bank PD", "Braided USB-C to USB-C Cable", "Lightning Fast Charging Cable", "Magnetic Wireless Charger Stand", "Surge Protector 6-Socket Strip"])
        ],
        "brands": ["Sony", "Samsung", "StockFlow Pro", "JBL", "Logitech", "Anker", "Belkin", "SanDisk", "TP-Link", "Dell", "HP", "Boat", "OnePlus", "Noise"],
        "costRange": (8.0, 120.0),
        "markup": 1.45,
        "weightRange": (0.1, 3.5),
        "dims": ["12x8x4 cm", "18x12x6 cm", "25x15x8 cm", "40x30x15 cm"]
    },
    {
        "category": "Beverages",
        "code": "BEV",
        "subcategories": [
            ("Bottled Water", ["Natural Spring Water 500ml", "Pure Drinking Water 1L Bottle", "Alkaline pH 8.5 Mineral Water", "High-Mountain Glacier Spring Water 750ml"]),
            ("Mineral Water", ["Natural Himalayan Mineral Water 500ml", "Fortified Electrolyte Mineral Water 1L", "Rich Calcium Mineral Water 750ml"]),
            ("Sparkling Water", ["Sparkling Lemon Lime Water 330ml Can", "Sparkling Berry Blast Water 330ml", "Crisp Apple Sparkling Water 500ml", "Zero-Calorie Mint Sparkling Water"]),
            ("Soft Drinks", ["Classic Cola 300ml Can", "Diet Zero-Sugar Cola 300ml", "Zesty Lemon Lime Soda 500ml", "Vintage Ginger Ale 330ml", "Refreshing Orange Fizz 500ml", "Tropical Passionfruit Soda"]),
            ("Juices", ["100% Pure Alphonso Mango Nectar 1L", "Valencia Orange Pulp Juice 1L", "Crisp Red Apple Juice 1L", "Pomegranate Antioxidant Juice 1L", "Guava Chili Infused Nectar 1L", "Mixed Tropical Berry Blend 1L"]),
            ("Energy Drinks", ["HyperCharge Energy Boost 250ml", "Volt Xtreme Caffeine Fuel 250ml", "Zero Sugar Citrus Energy 330ml", "Berry Rush Focus Energy Drink 250ml"]),
            ("Sports Drinks", ["Electrolyte Hydration Blue Raspberry 500ml", "Isotonic Lemon Lime Recovery Drink 500ml", "Electral Rapid Hydration Orange 500ml"]),
            ("Flavored Water", ["Peach Infused Natural Water 500ml", "Green Apple Vitamin Water 500ml", "Cucumber Mint Detox Water 500ml", "Tender Coconut Pure Water 200ml Tetra"])
        ],
        "brands": ["Bisleri", "Kinley", "Himalayan", "Coca-Cola", "Pepsi", "Tropicana", "Real Fruit", "Red Bull", "Monster", "Gatorade", "Raw Pressery", "StockFlow Aqua"],
        "costRange": (0.40, 3.50),
        "markup": 1.70,
        "weightRange": (0.3, 1.2),
        "dims": ["6x6x20 cm", "8x8x25 cm", "10x10x28 cm", "12x12x30 cm"]
    },
    {
        "category": "Groceries & Food",
        "code": "GRO",
        "subcategories": [
            ("Staples & Grains", ["Royal Daawat Basmati Rice 5kg", "Organic Whole Wheat Atta 5kg", "Unpolished Toor Dal 1kg", "Moong Dal Yellow Split 1kg", "Kabuli Chana Chickpeas 1kg", "Organic Rolled Oats 1kg"]),
            ("Cooking Oils & Ghee", ["Cold-Pressed Sunflower Oil 1L", "Pure Kachi Ghani Mustard Oil 1L", "Extra Virgin Olive Oil 1L", "Traditional Cow Ghee 500ml", "Refined Groundnut Oil 1L"]),
            ("Spices & Condiments", ["Himalayan Pink Rock Salt 1kg", "Organic Turmeric Powder 500g", "Kashmiri Degi Mirch Powder 500g", "Pure Garam Masala Blend 200g", "Whole Cumin Jeera Seeds 250g"]),
            ("Dry Fruits & Nuts", ["California Whole Almonds 500g", "Premium Whole Cashews W320 500g", "Chilean Walnut Kernels 250g", "Green Seedless Raisins 500g"]),
            ("Packaged Snacks", ["Classic Potato Chips Salted 180g", "Nacho Cheese Tortilla Crisps 150g", "2-Minute Masala Instant Noodles Pack of 12", "Whole Wheat Digestive Biscuits 400g", "Butter Cookies Tin 500g", "Hazelnut Chocolate Spread 350g"])
        ],
        "brands": ["Tata Sampann", "Aashirvaad", "Fortune", "Amul", "Organic Tattva", "Catch", "Nutraj", "Maggi", "Lay's", "Britannia", "Kellogg's", "Nestle"],
        "costRange": (1.20, 18.00),
        "markup": 1.40,
        "weightRange": (0.2, 5.2),
        "dims": ["15x10x5 cm", "20x15x8 cm", "30x20x10 cm", "40x25x15 cm"]
    },
    {
        "category": "Personal Care",
        "code": "PER",
        "subcategories": [
            ("Hair Care", ["Deep Moisture Hydrating Shampoo 650ml", "Anti-Dandruff Active Zinc Shampoo 400ml", "Keratin Smooth Repair Conditioner 300ml", "Moroccan Argan Hair Serum 100ml", "Organic Coconut Hair Oil 400ml"]),
            ("Bath & Body", ["Germ Protection Antibacterial Soap 4x125g", "Moisturizing Beauty Cream Bar 3x100g", "Refreshing Cool Shower Gel 500ml", "Cocoa Butter Intensive Body Lotion 400ml", "Aloe Vera Soothing Body Gel 300ml"]),
            ("Oral Care", ["Total Clean Mint Fluoride Toothpaste 150g", "Rapid Relief Sensitive Toothpaste 100g", "Activated Charcoal Whitening Toothpaste 120g", "Soft Bristle Bamboo Toothbrush 4-Pack", "Antibacterial Herbal Mouthwash 500ml"]),
            ("Skin Care", ["Gentle Hydrating Facial Cleanser 250ml", "Vitamin C Radiance Face Serum 30ml", "Broad Spectrum Sunscreen SPF 50 100ml", "Ultra-Light Oil-Free Moisturizer 100ml", "Soothing Micellar Cleansing Water 400ml"])
        ],
        "brands": ["Dove", "Head & Shoulders", "Dettol", "Lux", "Colgate", "Sensodyne", "Nivea", "Vaseline", "Cetaphil", "L'Oreal", "Old Spice", "Biotique", "Minimalist"],
        "costRange": (1.50, 14.00),
        "markup": 1.60,
        "weightRange": (0.1, 0.9),
        "dims": ["8x5x18 cm", "10x6x22 cm", "12x8x25 cm"]
    },
    {
        "category": "Cleaning Supplies",
        "code": "CLN",
        "subcategories": [
            ("Laundry Care", ["3-in-1 Ultra Oxi Laundry Pods 42ct", "Concentrated Liquid Detergent 2L", "Matic Front Load Washing Powder 2kg", "Morning Fresh Fabric Softener 1L", "In-Wash Scent Booster Beads 400g"]),
            ("Dish Care", ["Power Dishwashing Gel Lemon 750ml", "Platinum Powerwash Dish Spray 473ml", "Heavy Duty Anti-Scratch Scrub Sponges 6-Pack", "Automatic Dishwasher Detergent Tablets 30ct"]),
            ("Surface Cleaners", ["Disinfectant Surface Floor Cleaner Citrus 2L", "Streak-Free Glass and Mirror Cleaner 500ml", "Tough Stain Power Toilet Bowl Cleaner 1L", "Multipurpose Kitchen Degreaser Spray 500ml", "Biodegradable Garbage Bags Medium 60ct"])
        ],
        "brands": ["Tide", "Ariel", "Surf Excel", "Vim", "Pril", "Dawn", "Lysol", "Colin", "Harpic", "Comfort", "Scotch-Brite", "Henkel"],
        "costRange": (1.80, 15.00),
        "markup": 1.50,
        "weightRange": (0.3, 2.5),
        "dims": ["12x8x22 cm", "18x12x28 cm", "22x15x32 cm"]
    },
    {
        "category": "Automotive & Spare Parts",
        "code": "AUT",
        "subcategories": [
            ("Fluids & Lubricants", ["Fully Synthetic Engine Oil 5W-40 4L", "High Performance DOT 4 Brake Fluid 500ml", "Long-Life Radiator Coolant Pre-Mix 3L", "Windshield Washer Fluid Concentrate 1L"]),
            ("Filters & Ignition", ["Engine Air Filter High Flow", "Spin-On Oil Filter Premium", "Iridium Spark Plugs Set of 4", "Cabin AC Pollen Filter Carbon"]),
            ("Wipers & Lights", ["All-Season Frameless Wiper Blades 24-inch", "High Power LED Headlight Bulbs H7 Pair", "Fog Light Amber LED Bulbs Pair"]),
            ("Car Care & Tools", ["Ceramic Coating Wax Polish 500ml", "Microfiber Edgeless Drying Towels 3-Pack", "Digital Tire Pressure Gauge & Inflator 12V", "Heavy Duty Jumper Cables 10-Gauge", "Dashboard UV Protectant Spray 400ml"])
        ],
        "brands": ["Castrol", "Mobil 1", "Bosch", "Motul", "NGK", "Michelin", "3M Automotive", "Philips", "Turtle Wax", "StockFlow Auto"],
        "costRange": (4.00, 48.00),
        "markup": 1.55,
        "weightRange": (0.2, 4.8),
        "dims": ["15x10x8 cm", "25x15x12 cm", "35x20x15 cm"]
    },
    {
        "category": "Footwear",
        "code": "FTW",
        "subcategories": [
            ("Sports Footwear", ["Breathable Road Running Shoes", "Lightweight Mesh Training Sneakers", "Trail Running Grip Shoes", "Cushioned Walking Shoes"]),
            ("Formal & Casual", ["Classic Oxford Leather Formal Shoes", "Slip-on Suede Loafers", "Canvas Low-Top Casual Sneakers", "Waterproof Outdoor Hiking Boots"]),
            ("Sandals & Care", ["Comfort Foam Recovery Sliders", "Adjustable Strap Sports Sandals", "Memory Foam Orthopedic Insoles", "Waterproof Shoe Protector Spray 200ml"])
        ],
        "brands": ["Nike", "Adidas", "Puma", "Bata", "Woodland", "Skechers", "Reebok", "Clarks", "Red Tape", "StockFlow Footwear"],
        "costRange": (12.00, 75.00),
        "markup": 1.65,
        "weightRange": (0.6, 1.8),
        "dims": ["32x20x12 cm", "35x22x14 cm"]
    },
    {
        "category": "Clothing & Fashion",
        "code": "CLO",
        "subcategories": [
            ("Men's Apparel", ["100% Organic Cotton Crewneck T-Shirt", "Classic Pique Polo Shirt", "Slim-Fit Stretch Chino Trousers", "Selvedge Denim Regular Jeans", "Fleece Zip-Up Hoodie", "Formal Oxford Button-Down Shirt"]),
            ("Women's Apparel", ["High-Waisted Seamless Yoga Leggings", "Breathable Sports Bra Medium Support", "Relaxed Fit Cotton Tunic Top", "Stretch Denim Skinny Pants", "Lightweight Rainproof Windbreaker"]),
            ("Essentials", ["Combed Cotton Ankle Socks 6-Pack", "Thermal Base Layer Top & Bottom Set", "Microfiber Quick-Dry Gym Towel", "Water-Repellent Canvas Backpack 25L"])
        ],
        "brands": ["Levi's", "Zara", "H&M", "Allen Solly", "Van Heusen", "Under Armour", "Jockey", "Puma", "Nike", "StockFlow Apparel"],
        "costRange": (5.00, 45.00),
        "markup": 1.75,
        "weightRange": (0.15, 0.9),
        "dims": ["25x20x4 cm", "30x25x6 cm", "35x30x8 cm"]
    },
    {
        "category": "Office & Stationery",
        "code": "OFC",
        "subcategories": [
            ("Paper & Books", ["A4 Premium Copier Paper 75GSM 500 Sheets", "Hardcover Executive Notebook 200 Pages", "Spiral Grid Graph Notebook A5", "Self-Adhesive Sticky Notes Neon 5-Pack"]),
            ("Writing Instruments", ["Retractable Gel Pens 0.5mm Pack of 10", "Classic Ballpoint Pens Blue Pack of 20", "Chisel Tip Pastel Highlighters 6-Pack", "Fine Permanent Waterproof Markers 4-Pack"]),
            ("Desk Accessories", ["Heavy Duty Desk Stapler with 5000 Pins", "Mesh Metal 4-Tier Document Tray", "Adjustable Desktop Bookstand", "Precision Stainless Steel Scissors 8-inch", "Double Sided Transparent Tape 3-Pack"])
        ],
        "brands": ["Classmate", "Reynolds", "Pilot", "Camlin", "Faber-Castell", "Kangaro", "JK Copier", "3M Post-It", "Parker", "StockFlow Stationery"],
        "costRange": (0.80, 18.00),
        "markup": 1.60,
        "weightRange": (0.1, 2.5),
        "dims": ["15x10x3 cm", "22x15x5 cm", "32x24x6 cm"]
    },
    {
        "category": "Mobile & Computer Accessories",
        "code": "ACC",
        "subcategories": [
            ("Mobile Accessories", ["Tempered Glass Screen Protector 9H 2-Pack", "Shockproof TPU Air-Cushion Phone Case", "Magnetic Ring Phone Holder Stand", "In-Car Vent Phone Mount Auto-Clamp", "Fast Wireless Charging Pad 15W"]),
            ("Laptop & Desk", ["Aluminum Ergonomic Laptop Stand Riser", "Extended Gaming Desk Mouse Pad 90x40cm", "Water-Resistant Neoprene Laptop Sleeve 15.6\"", "Universal Silicon Keyboard Cover", "Velcro Cable Management Straps 20-Pack"])
        ],
        "brands": ["Spigen", "Portronics", "Amkette", "AmazonBasics", "Belkin", "Targus", "Boat", "OnePlus", "StockFlow Tech"],
        "costRange": (2.00, 28.00),
        "markup": 1.70,
        "weightRange": (0.05, 1.1),
        "dims": ["18x10x2 cm", "25x15x4 cm", "40x28x3 cm"]
    },
    {
        "category": "Home & Kitchen",
        "code": "HMK",
        "subcategories": [
            ("Cookware & Tools", ["Tri-Ply Stainless Steel Kadhai with Lid 2.5L", "Hard Anodized Non-Stick Frying Pan 24cm", "High-Carbon Stainless Steel Chef Knife 8-inch", "Antimicrobial Bamboo Cutting Board Large", "Heat Resistant Silicone Kitchen Utensils 10-Piece"]),
            ("Storage & Dining", ["Airtight Borosilicate Glass Food Containers 4-Pack", "Double Wall Vacuum Insulated Flask 1L", "Ceramic Coffee Mug Matte Finish 350ml 4-Pack", "Modular 360 Rotating Spice Rack 16 Jars", "Rustproof Stainless Steel Dish Drying Rack"])
        ],
        "brands": ["Prestige", "Hawkins", "Milton", "Borosil", "Pigeon", "Cello", "Wonderchef", "Tupperware", "StockFlow Living"],
        "costRange": (4.50, 55.00),
        "markup": 1.55,
        "weightRange": (0.4, 4.2),
        "dims": ["20x20x10 cm", "30x25x15 cm", "40x30x20 cm"]
    },
    {
        "category": "Health & Wellness",
        "code": "HLT",
        "subcategories": [
            ("Supplements", ["Daily Multivitamin with Minerals 60 Tablets", "Triple Strength Omega-3 Fish Oil 1000mg 60 Softgels", "100% Pure Whey Protein Isolate Powder 1kg", "Micronized Creatine Monohydrate 250g", "Effervescent Vitamin C 1000mg + Zinc 20 Tablets"]),
            ("Medical Devices", ["Digital Upper Arm Blood Pressure Monitor", "Fingertip Pulse Oximeter with OLED Display", "Non-Contact Infrared Forehead Thermometer", "First Aid Emergency Trauma Kit 85-Piece", "Ayurvedic Herbal Cough Lozenges 50-Pack"])
        ],
        "brands": ["Himalaya", "Optimum Nutrition", "MuscleBlaze", "HealthKart", "Dr. Morepen", "Omron", "Dabur", "Baidyanath", "StockFlow Health"],
        "costRange": (2.50, 45.00),
        "markup": 1.50,
        "weightRange": (0.1, 1.5),
        "dims": ["10x10x15 cm", "15x12x8 cm", "22x15x12 cm"]
    },
    {
        "category": "Pet Supplies",
        "code": "PET",
        "subcategories": [
            ("Dog Care", ["Adult Dog Dry Food Real Chicken & Rice 3kg", "Calcium Dental Chew Sticks 500g", "Adjustable Reflective Dog Harness & Leash Set", "Natural Oatmeal Anti-Itch Dog Shampoo 500ml", "Orthopedic Foam Pet Bed Medium"]),
            ("Cat Care", ["Tuna & Salmon Wet Cat Food Gravy Pouches 12-Pack", "Odor Control Clumping Bentonite Cat Litter 5kg", "Interactive Feather Cat Wand & Laser Toy", "Stainless Steel Anti-Skid Pet Feeding Bowls Pair"])
        ],
        "brands": ["Pedigree", "Royal Canin", "Whiskas", "Drools", "Purina", "Himalaya Pets", "StockFlow Pet"],
        "costRange": (2.00, 32.00),
        "markup": 1.45,
        "weightRange": (0.2, 5.5),
        "dims": ["18x12x6 cm", "30x20x15 cm", "45x30x20 cm"]
    },
    {
        "category": "Baby Products",
        "code": "BBY",
        "subcategories": [
            ("Diapering & Hygiene", ["Ultra Absorbent Baby Diaper Pants Size M 64ct", "Size L Breathable Baby Diaper Pants 54ct", "99% Pure Water Fragrance-Free Baby Wipes 72ct 3-Pack", "Gentle Baby Body Wash & No-Tears Shampoo 400ml", "Zinc Oxide Soothing Diaper Rash Cream 100g"]),
            ("Feeding & Care", ["Anti-Colic BPA-Free Feeding Bottle 260ml", "Soft Silicone Baby Teether & Soother Pair", "Organic Multigrain Baby Cereal with Fruit 300g", "Ultra-Soft Cotton Swaddle Blankets 3-Pack"])
        ],
        "brands": ["Pampers", "Huggies", "MamyPoko", "Johnson's Baby", "Sebamed", "Chicco", "Himalaya Baby", "Philips Avent", "StockFlow Baby"],
        "costRange": (1.80, 26.00),
        "markup": 1.40,
        "weightRange": (0.2, 2.2),
        "dims": ["15x12x10 cm", "25x20x15 cm", "35x25x20 cm"]
    },
    {
        "category": "Hardware",
        "code": "HDW",
        "subcategories": [
            ("Hand & Power Tools", ["12V Cordless Drill & Screwdriver Kit with 2 Batteries", "108-Piece Home Tool Box with Claw Hammer & Pliers", "Magnetic Torx & Precision Screwdriver Set 32-Piece", "Heavy Duty Locking Tape Measure 5m / 16ft", "Adjustable Chrome Vanadium Wrench 10-inch"]),
            ("Fasteners & Safety", ["Heavy Duty Retractable Utility Knife with 10 Blades", "LED Rechargeable Tactical Flashlight 2000 Lumens", "Cut-Resistant Level 5 Safety Work Gloves Pair", "Heavy Duty Waterproof Duct Tape 50m", "Multi-Size Wall Anchor & Screw Assortment 200-Piece"])
        ],
        "brands": ["Bosch", "Stanley", "Taparia", "Black+Decker", "DeWalt", "DTA", "StockFlow Hardware"],
        "costRange": (2.20, 65.00),
        "markup": 1.55,
        "weightRange": (0.2, 4.0),
        "dims": ["18x12x4 cm", "28x18x8 cm", "42x30x12 cm"]
    }
]

def generate_global_products() -> List[Dict[str, Any]]:
    """Generates 1,050+ authoritative, deterministic StockFlow global products."""
    products = []
    prod_counter = 1
    random.seed(42) # Deterministic generation for consistency

    for cat_cfg in PRODUCT_CATEGORIES_CONFIG:
        cat_name = cat_cfg["category"]
        cat_code = cat_cfg["code"]
        brands = cat_cfg["brands"]
        cost_min, cost_max = cat_cfg["costRange"]
        markup = cat_cfg["markup"]
        w_min, w_max = cat_cfg["weightRange"]

        for subcat_name, item_names in cat_cfg["subcategories"]:
            for item_base in item_names:
                # Generate 5 distinct SKUs / package sizes per base item
                variations = [
                    ("", 1.0, "Standard Unit"),
                    ("Plus", 1.15, "Retail Single"),
                    ("Pro", 1.30, "Commercial Pack"),
                    ("Max", 1.50, "Value Bundle"),
                    ("Ultra", 1.75, "Bulk Case Pack")
                ]
                for var_prefix, price_mult, edition_desc in variations:
                    sku = f"SKU-{cat_code}-{prod_counter:04d}"
                    brand = brands[(prod_counter + len(item_base)) % len(brands)]
                    full_name = f"{brand} {var_prefix + ' ' if var_prefix else ''}{item_base}".strip()
                    
                    cost_price = round(random.uniform(cost_min, cost_max) * price_mult, 2)
                    selling_price = round(cost_price * markup, 2)
                    weight_kg = round(random.uniform(w_min, w_max) * price_mult, 2)
                    dims = cat_cfg["dims"][(prod_counter) % len(cat_cfg["dims"])]
                    reorder_point = random.randint(20, 80)
                    safety_stock = random.randint(15, 50)
                    velocity = random.choice(["HIGH_VELOCITY", "MEDIUM_VELOCITY", "LOW_VELOCITY", "FAST_MOVING"])

                    products.append({
                        "id": f"prod-{prod_counter:04d}",
                        "productId": f"PRD-{prod_counter:04d}",
                        "sku": sku,
                        "name": full_name,
                        "category": cat_name,
                        "subcategory": subcat_name,
                        "brand": brand,
                        "barcode": f"890{prod_counter:09d}",
                        "qrCode": f"STOCKFLOW-{sku}",
                        "unit": "unit",
                        "packageSize": edition_desc,
                        "weightKg": weight_kg,
                        "dimensions": dims,
                        "costPrice": cost_price,
                        "sellingPrice": selling_price,
                        "unitPrice": selling_price,
                        "reorderPoint": reorder_point,
                        "reorderLevel": reorder_point,
                        "safetyStock": safety_stock,
                        "velocity": velocity,
                        "fastMoving": velocity in ["HIGH_VELOCITY", "FAST_MOVING"],
                        "supplier": f"{brand} Supply Logistics Pvt Ltd",
                        "active": True
                    })
                    prod_counter += 1


    return products

# =============================================================================
# PRIMARY SEED ENGINE
# =============================================================================
def generate_initial_data() -> Dict[str, Any]:
    now = datetime.utcnow()
    random.seed(1042)

    # 1. Users
    users = [
        {
            "id": "usr-admin-001",
            "uid": "o4UqOmbzqBV11AvwKahcjqF",
            "email": "admin@gmail.com",
            "name": "Super Admin",
            "fullName": "Super Admin (Network Director)",
            "role": "SUPER_ADMIN",
            "department": "Executive Network Operations",
            "warehouseId": "HYD-01",
            "assignedWarehouses": ["HYD-01", "MUM-01", "VJA-01", "MAH-01", "CHE-01"],
            "rfGunId": "HHT-9901",
            "shift": "General (24/7 Access)",
            "phone": "+91 98490 11001",
            "permissions": ["ALL"],
            "status": "ACTIVE",
            "createdAt": "2026-08-16T12:00:00Z",
            "lastActive": now.isoformat(),
            "createdBy": "System Bootstrap"
        },
        {
            "id": "usr-ooha-001",
            "uid": "YPpPh9tgrrSODwOMFO7pInF",
            "email": "ooha@gmail.com",
            "name": "Ooha",
            "fullName": "Ooha (Hyderabad Hub Director)",
            "role": "OPERATIONS_MANAGER",
            "department": "Warehouse Operations",
            "warehouseId": "HYD-01",
            "assignedWarehouses": ["HYD-01"],
            "rfGunId": "HHT-9902",
            "shift": "General Shift (08:00 - 17:00)",
            "phone": "+91 98490 22002",
            "permissions": ["ORDERS", "INVENTORY", "PICKING", "PACKING", "QC", "DISPATCH", "YMS", "RETURNS"],
            "status": "ACTIVE",
            "createdAt": "2026-08-16T12:00:00Z",
            "lastActive": now.isoformat(),
            "createdBy": "Super Admin"
        }
    ]

    # 2. Warehouses
    warehouses = STOCKFLOW_WAREHOUSES

    # 3. Global Products (1050+ items)
    products = generate_global_products()

    # 4. Branch-Specific Inventory Generator
    # Available = Current - Allocated - Damaged - Quarantined
    inventory = []
    inv_counter = 1

    # Define bins per zone for deterministic locations
    zone_bins = {
        "Zone A": ["A-01", "A-02", "A-03", "A-04", "A-05", "A-06", "A-07", "A-08"],
        "Zone B": ["B-01", "B-02", "B-03", "B-04", "B-05", "B-06", "B-07", "B-08"],
        "Zone C": ["C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08"],
        "Zone D": ["D-01", "D-02", "D-03", "D-04", "D-05", "D-06", "D-07", "D-08"]
    }

    # Map category to primary warehouse zone
    cat_zone_map = {
        "Personal Care": "Zone A",
        "Beauty & Cosmetics": "Zone A",
        "Cleaning Supplies": "Zone B",
        "Hardware": "Zone B",
        "Automotive & Spare Parts": "Zone B",
        "Groceries & Food": "Zone C",
        "Office & Stationery": "Zone C",
        "Footwear": "Zone C",
        "Clothing & Fashion": "Zone C",
        "Home & Kitchen": "Zone C",
        "Pet Supplies": "Zone C",
        "Baby Products": "Zone C",
        "Beverages": "Zone D",
        "Health & Wellness": "Zone D",
        "Electronics": "Zone D",
        "Mobile & Computer Accessories": "Zone D"
    }

    # Generate inventory for all 5 hubs
    hub_stock_multipliers = {
        "HYD-01": (1.0, 1.0),   # Hyderabad holds 100% of product catalog (large quantities)
        "MUM-01": (0.75, 0.65), # Mumbai holds 75% of catalog
        "VJA-01": (0.50, 0.40), # Vijayawada holds 50%
        "MAH-01": (0.65, 0.55), # Maharashtra holds 65%
        "CHE-01": (0.60, 0.50)  # Chennai holds 60%
    }

    for hub in STOCKFLOW_WAREHOUSES:
        hub_id = hub["id"]
        cat_coverage, qty_multiplier = hub_stock_multipliers.get(hub_id, (0.5, 0.5))

        for idx, prod in enumerate(products):
            # Deterministic inclusion for regional hubs
            if hub_id != "HYD-01" and (idx % 100) > (cat_coverage * 100):
                continue

            sku = prod["sku"]
            zone = cat_zone_map.get(prod["category"], "Zone A")
            bins_list = zone_bins.get(zone, ["A-01", "A-02"])
            bin_code = bins_list[idx % len(bins_list)]
            floor_num = 3 if hub_id == "HYD-01" else (1 if zone in ["Zone A", "Zone B"] else 2)

            # Realistic baseline stock numbers
            base_total = int(random.randint(60, 450) * qty_multiplier)
            
            # Special case: SKU-PER-0001 (Dove Deep Moisture Shampoo in HYD-01 for Order #1042)
            if hub_id == "HYD-01" and idx == 0:
                current_qty = 10
                allocated_qty = 3
                damaged_qty = 0
                quarantined_qty = 0
                available_qty = 7 # Exact available units for Order #1042 scenario!
                bin_code = "A-01"
            else:
                current_qty = base_total
                allocated_qty = int(base_total * random.uniform(0.05, 0.22))
                damaged_qty = int(base_total * random.uniform(0.0, 0.04)) if (idx % 8 == 0) else 0
                quarantined_qty = int(base_total * random.uniform(0.0, 0.03)) if (idx % 12 == 0) else 0
                available_qty = max(0, current_qty - allocated_qty - damaged_qty - quarantined_qty)

            inventory.append({
                "id": f"inv-{hub_id.lower()}-{sku.lower()}",
                "warehouseId": hub_id,
                "fulfillmentCenterId": hub_id,
                "warehouseName": hub["name"],
                "productId": prod["id"],
                "sku": sku,
                "productName": prod["name"],
                "category": prod["category"],
                "subcategory": prod["subcategory"],
                "brand": prod["brand"],
                "unit": prod["unit"],
                "costPrice": prod["costPrice"],
                "sellingPrice": prod["sellingPrice"],
                "unitPrice": prod["sellingPrice"],
                "currentQuantity": current_qty,
                "totalQuantity": current_qty,
                "allocatedQuantity": allocated_qty,
                "damagedQuantity": damaged_qty,
                "quarantinedQuantity": quarantined_qty,
                "availableQuantity": available_qty,
                "reorderPoint": prod["reorderPoint"],
                "reorderLevel": prod["reorderPoint"],
                "safetyStock": prod["safetyStock"],
                "velocity": prod["velocity"],
                "zone": zone,
                "bin": bin_code,
                "locationCode": bin_code,
                "floorNumber": floor_num,
                "updatedAt": (now - timedelta(minutes=random.randint(5, 120))).isoformat()
            })
            inv_counter += 1

    # 5. Orders (Multi-Channel StockFlow Business Lines across all 5 hubs)
    orders = []
    order_channels = ["STOCKFLOW_PRIME", "STOCKFLOW_EXPRESS", "STOCKFLOW_B2B", "STOCKFLOW_DIRECT", "STOCKFLOW_REGIONAL"]
    carriers_pool = [
        "StockFlow Linehaul Logistics (32ft Container)",
        "StockFlow Cold-Chain Reefer Express",
        "StockFlow Air Cargo Priority",
        "StockFlow Urban Shuttle Fleet",
        "StockFlow Priority Express Surface"
    ]

    order_seq = 1001

    for hub in STOCKFLOW_WAREHOUSES:
        hub_id = hub["id"]
        is_hyd = hub_id == "HYD-01"
        hub_order_count = 35 if is_hyd else 18

        for o_idx in range(hub_order_count):
            order_num = f"ORD-{order_seq}"
            order_id = f"ord-{order_seq}"
            order_channel = order_channels[o_idx % len(order_channels)]
            carrier = carriers_pool[(order_seq + o_idx) % len(carriers_pool)]

            # Special Demo Order: Order #1042 in HYD-01
            if is_hyd and order_seq == 1042:
                status = "CREATED"
                prio_level = "CRITICAL"
                prio_score = 95
                sla_rem = 1.8
                customer = "Metro Hypermarket Flagship DC"
                items = [
                    {
                        "productId": products[0]["id"],
                        "sku": products[0]["sku"],
                        "name": products[0]["name"],
                        "productName": products[0]["name"],
                        "quantityRequested": 10,
                        "quantityAllocated": 7,
                        "unitPrice": products[0]["sellingPrice"],
                        "costPrice": products[0]["costPrice"],
                        "locationCode": "A-01",
                        "zone": "Zone A",
                        "status": "ALLOCATED_PARTIAL"
                    }
                ]
                tot_amt = 79.90
            elif is_hyd and order_seq == 1048:
                status = "CREATED"
                prio_level = "LOW"
                prio_score = 28
                sla_rem = 46.5
                customer = "Sunrise Neighborhood Grocers"
                items = [
                    {
                        "productId": products[0]["id"],
                        "sku": products[0]["sku"],
                        "name": products[0]["name"],
                        "productName": products[0]["name"],
                        "quantityRequested": 5,
                        "quantityAllocated": 0,
                        "unitPrice": products[0]["sellingPrice"],
                        "costPrice": products[0]["costPrice"],
                        "locationCode": "A-01",
                        "zone": "Zone A",
                        "status": "PENDING_STOCK"
                    }
                ]
                tot_amt = 39.95
            else:
                statuses = [
                    "ALLOCATED", "PICKING", "PACKED", "PACKED", "QUALITY_CHECK",
                    "READY_TO_DISPATCH", "PACKED", "QUALITY_CHECK", "PICKED", "CREATED", "DISPATCHED"
                ]
                status = statuses[o_idx % len(statuses)]
                prio_levels = ["NORMAL", "HIGH", "CRITICAL", "LOW"]
                prio_level = prio_levels[o_idx % len(prio_levels)]
                prio_score = random.randint(30, 96) if prio_level == "CRITICAL" else random.randint(20, 75)
                sla_rem = round(random.uniform(0.8, 14.0), 1)
                customer = f"Retail Client #{random.randint(100, 999)} ({hub['city']})"

                # Sample 2-4 items from product catalog
                items = []
                tot_amt = 0.0
                item_sample_count = random.randint(1, 3)
                for it_idx in range(item_sample_count):
                    p_item = products[(order_seq * 7 + it_idx * 13) % len(products)]
                    q_req = random.randint(2, 12)
                    items.append({
                        "productId": p_item["id"],
                        "sku": p_item["sku"],
                        "name": p_item["name"],
                        "productName": p_item["name"],
                        "quantityRequested": q_req,
                        "quantityAllocated": q_req,
                        "unitPrice": p_item["sellingPrice"],
                        "costPrice": p_item["costPrice"],
                        "locationCode": "A-02",
                        "zone": "Zone A",
                        "status": "ALLOCATED"
                    })
                    tot_amt += q_req * p_item["sellingPrice"]
                tot_amt = round(tot_amt, 2)


            orders.append({
                "id": order_id,
                "orderNumber": order_num,
                "warehouseId": hub_id,
                "fulfillmentCenterId": hub_id,
                "warehouseName": hub["name"],
                "channel": order_channel,
                "customerName": customer,
                "deliveryAddress": f"Plot #{random.randint(12, 199)}, Industrial Logistics Corridor, {hub['city']}",
                "status": status,
                "priorityLevel": prio_level,
                "priorityScore": prio_score,
                "urgencyReason": "Critical Contractual SLA (< 2.0h)" if prio_level == "CRITICAL" else "Standard Scheduled Delivery",
                "slaRemainingHours": sla_rem,
                "totalAmount": tot_amt,
                "items": items,
                "carrier": carrier,
                "trackingNumber": f"SF-TRK-{order_seq}982",
                "assignedWorker": "Marcus Vance" if is_hyd else "Regional Operator",
                "createdAt": (now - timedelta(hours=random.randint(1, 8))).isoformat()
            })
            order_seq += 1

    # 6. Dock Doors & Fleet Yard Management (YMS) for all 5 hubs
    dock_doors = []
    bay_idx = 1

    for hub in STOCKFLOW_WAREHOUSES:
        hub_id = hub["id"]
        bays_count = hub["activeDockBays"]

        for b_num in range(1, bays_count + 1):
            bay_type = "INBOUND" if b_num <= (bays_count // 2) else ("CROSS_DOCK" if b_num == bays_count else "OUTBOUND")
            status = "UNLOADING" if bay_type == "INBOUND" else ("LOADING" if bay_type == "OUTBOUND" else "CROSS_DOCKING")
            progress = random.randint(30, 95)
            pallets_tot = random.randint(12, 28)
            pallets_done = int(pallets_tot * (progress / 100.0))

            dock_doors.append({
                "id": f"bay-{hub_id.lower()}-{b_num:02d}",
                "bayNumber": f"Bay {b_num:02d}",
                "warehouseId": hub_id,
                "fulfillmentCenterId": hub_id,
                "warehouseName": hub["name"],
                "type": bay_type,
                "status": status,
                "carrier": f"StockFlow Fleet Trailer #{b_num:02d}",
                "driverName": f"Driver {hub['city'].split(',')[0]} #{b_num}",
                "vehicleNumber": f"TS-09-SF-{1000 + bay_idx}",
                "gatePassId": f"GP-SF-{202600 + bay_idx}",
                "cargoDescription": "Master Cartons & Palletized Consignments",
                "assignedZone": f"Zone {chr(65 + (b_num % 4))}",
                "palletsCompleted": pallets_done,
                "palletsTotal": pallets_tot,
                "progressPct": progress,
                "etaOrDeparture": "Departing 15:30" if bay_type == "OUTBOUND" else "Unload in progress"
            })
            bay_idx += 1

    # 7. Customer Returns & Reverse Logistics (RTO Hub) for all 5 hubs
    returns = []
    ret_seq = 101

    for hub in STOCKFLOW_WAREHOUSES:
        hub_id = hub["id"]
        # Generate 2-3 returns per hub
        for r_idx in range(2):
            sku_target = products[r_idx * 5]["sku"]
            p_name = products[r_idx * 5]["name"]

            returns.append({
                "id": f"ret-{hub_id.lower()}-{r_idx+1:02d}",
                "returnNumber": f"RTO-SF-{ret_seq}",
                "orderNumber": f"ORD-{1000 + ret_seq}",
                "warehouseId": hub_id,
                "fulfillmentCenterId": hub_id,
                "warehouseName": hub["name"],
                "channel": "STOCKFLOW_D2C_EXPRESS",
                "customerName": f"Client #{ret_seq} ({hub['city']})",
                "carrier": "StockFlow Reverse Express Logistics",
                "trackingNumber": f"AWB-SF-RTO-{ret_seq}44",
                "sku": sku_target,
                "productName": p_name,
                "quantity": random.randint(2, 8),
                "returnReason": "Customer rejected parcel at doorstep (Outer box scuffed)",
                "gradingStatus": "PENDING_INSPECTION" if r_idx == 0 else "GRADED_RESTOCKED",
                "assignedGrade": None if r_idx == 0 else "GRADE_A_PRISTINE",
                "refundStatus": "PROCESSING" if r_idx == 0 else "CREDITED",
                "targetBin": "A-01",
                "timestamp": (now - timedelta(hours=random.randint(1, 12))).isoformat()
            })
            ret_seq += 1

    # 8. Cold Chain & Environmental IoT Telemetry (Zones A-D per warehouse)
    climate_sensors = []
    for hub in STOCKFLOW_WAREHOUSES:
        hub_id = hub["id"]
        climate_sensors.extend([
            {
                "zoneCode": f"{hub_id}-ZoneA",
                "zoneName": "Personal Care & Cosmetics",
                "warehouseId": hub_id,
                "fulfillmentCenterId": hub_id,
                "warehouseName": hub["name"],
                "sensorId": f"IOT-{hub_id}-A01",
                "temperatureCelsius": 21.2,
                "humidityPct": 48,
                "targetRange": "18°C - 24°C",
                "humidityTarget": "40% - 60%",
                "compressorState": "ACTIVE_ECO",
                "status": "OPTIMAL",
                "lastTelemetry": (now - timedelta(seconds=12)).isoformat()
            },
            {
                "zoneCode": f"{hub_id}-ZoneB",
                "zoneName": "Detergents & Chemical Cleaning",
                "warehouseId": hub_id,
                "fulfillmentCenterId": hub_id,
                "warehouseName": hub["name"],
                "sensorId": f"IOT-{hub_id}-B01",
                "temperatureCelsius": 22.8,
                "humidityPct": 42,
                "targetRange": "18°C - 26°C",
                "humidityTarget": "35% - 55%",
                "compressorState": "ACTIVE_VENTILATION",
                "status": "OPTIMAL",
                "lastTelemetry": (now - timedelta(seconds=18)).isoformat()
            },
            {
                "zoneCode": f"{hub_id}-ZoneC",
                "zoneName": "Packaged Foods & Dry Grocery",
                "warehouseId": hub_id,
                "fulfillmentCenterId": hub_id,
                "warehouseName": hub["name"],
                "sensorId": f"IOT-{hub_id}-C01",
                "temperatureCelsius": 19.5,
                "humidityPct": 45,
                "targetRange": "16°C - 22°C",
                "humidityTarget": "40% - 50%",
                "compressorState": "ACTIVE_STANDARD",
                "status": "OPTIMAL",
                "lastTelemetry": (now - timedelta(seconds=9)).isoformat()
            },
            {
                "zoneCode": f"{hub_id}-ZoneD",
                "zoneName": "Cold Chain & Deep Refrigeration",
                "warehouseId": hub_id,
                "fulfillmentCenterId": hub_id,
                "warehouseName": hub["name"],
                "sensorId": f"IOT-{hub_id}-D01",
                "temperatureCelsius": 3.4,
                "humidityPct": 62,
                "targetRange": "2°C - 6°C (Reefer)",
                "humidityTarget": "55% - 70%",
                "compressorState": "ACTIVE_TURBO_COOL",
                "status": "OPTIMAL",
                "lastTelemetry": (now - timedelta(seconds=5)).isoformat()
            }
        ])

    # 9. Picking Tasks, Packing Tasks, QC, Exceptions, Decisions & Audits
    pickers_pool = [
        "Marcus Vance (Senior Picker)",
        "David Miller (Fast-Track Wave)",
        "Pooja Sharma (Floor 4 Lead)",
        "Rajesh Patel (Zone Specialist)",
        "Aisha Khan (Reefer Zone)",
        "Elena Rodriguez (QC Pick)"
    ]

    picking_tasks = [
        {
            "id": "pick-001",
            "warehouseId": "HYD-01",
            "fulfillmentCenterId": "HYD-01",
            "orderId": "ord-1042",
            "orderNumber": "ORD-1042",
            "priorityLevel": "CRITICAL",
            "assignedPickerName": "Marcus Vance",
            "status": "ALLOCATED",
            "routeSequence": ["A-01", "A-04", "B-02", "C-01"],
            "items": [
                {"sku": "SKU-PER-0001", "name": products[0]["name"], "bin": "A-01", "quantity": 7, "picked": 0},
                {"sku": products[15]["sku"], "name": products[15]["name"], "bin": "A-04", "quantity": 3, "picked": 0},
                {"sku": products[30]["sku"], "name": products[30]["name"], "bin": "B-02", "quantity": 4, "picked": 0}
            ],
            "unoptimizedRouteTimeMinutes": 18.0,
            "optimizedRouteTimeMinutes": 11.0,
            "timeSavedMinutes": 7.0,
            "createdAt": (now - timedelta(minutes=15)).isoformat()
        }
    ]

    # Generate 11 additional wave picking tasks for HYD-01 and other hubs
    for p_idx in range(2, 14):
        target_ord = orders[p_idx + 2]
        w_id = target_ord.get("warehouseId", "HYD-01")
        prio = target_ord.get("priorityLevel", "HIGH")
        picker = pickers_pool[(p_idx) % len(pickers_pool)]
        bins_sample = [f"A-0{p_idx % 6 + 1}", f"B-0{p_idx % 5 + 1}", f"C-0{p_idx % 4 + 1}"]
        
        p_items = []
        for b_code in bins_sample:
            p_sample = products[(p_idx * 11 + len(b_code)) % len(products)]
            p_items.append({
                "sku": p_sample["sku"],
                "name": p_sample["name"],
                "bin": b_code,
                "quantity": random.randint(2, 8),
                "picked": 0
            })

        unopt = round(random.uniform(16.0, 24.0), 1)
        opt = round(unopt * random.uniform(0.55, 0.70), 1)
        saved = round(unopt - opt, 1)

        picking_tasks.append({
            "id": f"pick-{p_idx:03d}",
            "warehouseId": w_id,
            "fulfillmentCenterId": w_id,
            "orderId": target_ord["id"],
            "orderNumber": target_ord["orderNumber"],
            "priorityLevel": prio,
            "assignedPickerName": picker,
            "status": "ALLOCATED",
            "routeSequence": bins_sample,
            "items": p_items,
            "unoptimizedRouteTimeMinutes": unopt,
            "optimizedRouteTimeMinutes": opt,
            "timeSavedMinutes": saved,
            "createdAt": (now - timedelta(minutes=random.randint(10, 55))).isoformat()
        })

    packing_tasks = []
    quality_checks = []

    for pk_idx in range(1, 15):
        ord_ref = orders[pk_idx]
        w_id = ord_ref.get("warehouseId", "HYD-01")
        station_num = (pk_idx % 6) + 1
        gross_w = round(random.uniform(1.8, 6.5), 2)

        packing_tasks.append({
            "id": f"pack-{pk_idx:03d}",
            "warehouseId": w_id,
            "fulfillmentCenterId": w_id,
            "orderId": ord_ref["id"],
            "orderNumber": ord_ref["orderNumber"],
            "status": "READY_FOR_PACKING" if pk_idx % 2 == 0 else "PACKED",
            "packingStation": f"Station 0{station_num} (Floor 5)",
            "grossWeightKg": gross_w,
            "createdAt": (now - timedelta(minutes=random.randint(5, 40))).isoformat()
        })

        quality_checks.append({
            "id": f"qc-{pk_idx:03d}",
            "warehouseId": w_id,
            "fulfillmentCenterId": w_id,
            "orderId": ord_ref["id"],
            "orderNumber": ord_ref["orderNumber"],
            "status": "PENDING" if pk_idx <= 8 else "PASSED",
            "grossWeightVerified": True,
            "barcodeVerified": True,
            "inspectorName": "Elena Rodriguez" if pk_idx % 2 == 0 else "Kavita Rao",
            "createdAt": (now - timedelta(minutes=random.randint(3, 30))).isoformat()
        })


    exceptions = [
        {
            "id": "exc-001",
            "warehouseId": "HYD-01",
            "fulfillmentCenterId": "HYD-01",
            "type": "STOCKOUT_SHORTAGE",
            "severity": "CRITICAL",
            "title": "Inventory Shortage on SKU-PER-0001",
            "description": "Order #1042 required 10 units of Dove Shampoo; only 7 available in Bin A-01.",
            "affectedEntity": "ORD-1042 / SKU-PER-0001",
            "status": "OPEN",
            "recommendedAction": "Approve PO replenishment recommendation for 200 units to primary supplier.",
            "createdAt": (now - timedelta(minutes=20)).isoformat()
        }
    ]

    decision_logs = [
        {
            "id": "dec-001",
            "warehouseId": "HYD-01",
            "fulfillmentCenterId": "HYD-01",
            "timestamp": (now - timedelta(minutes=18)).isoformat(),
            "decisionType": "SMART_INVENTORY_ALLOCATION",
            "entityId": "ORD-1042",
            "entityType": "ORDER",
            "situation": "Contending demand: Order #1042 (10 units req) vs Order #1048 (5 units req) with 7 units in stock.",
            "decision": "Allocated 7 available units to Tier-1 SLA Order #1042; queued Order #1048.",
            "reason": "Order #1042 has contractual 2.0h SLA deadline with Tier-1 Metro Hypermarket.",
            "action": "Release wave pick for 7 units immediately and trigger expedited PO replenishment.",
            "resultExpected": "Order fulfills within 90 minutes, maintaining 99.8% on-time fulfillment compliance.",
            "impact": "Prevented SLA penalty breach of $450.",
            "approvedBy": "AUTOMATED_STOCKFLOW_PRIORITY_ENGINE",
            "status": "APPLIED"
        }
    ]

    audit_logs = [
        {
            "id": "aud-001",
            "warehouseId": "HYD-01",
            "fulfillmentCenterId": "HYD-01",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "user": "Super Admin",
            "role": "SUPER_ADMIN",
            "action": "MULTI_HUB_NETWORK_BOOTSTRAP",
            "entity": "StockFlow Enterprise 5-Hub Network",
            "previousValue": "Single Hub",
            "newValue": "5 Fulfillment Centers",
            "reason": "Enterprise network initialization across HYD-01, MUM-01, VJA-01, MAH-01, CHE-01."
        }
    ]

    stock_movements = [
        {
            "id": "mov-001",
            "warehouseId": "HYD-01",
            "fulfillmentCenterId": "HYD-01",
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "sku": products[0]["sku"],
            "productName": products[0]["name"],
            "quantity": 100,
            "previousQuantity": 10,
            "newQuantity": 110,
            "movementType": "STOCK_RECEIVED",
            "source": "Dock Bay 02 (Supplier Inbound)",
            "destination": "Bin A-01",
            "userId": "usr-admin-001",
            "userName": "Super Admin",
            "reason": "Inbound shipment received and scanned via RF Gun.",
            "orderId": None
        }
    ]

    notifications = [
        {
            "id": "notif-001",
            "warehouseId": "HYD-01",
            "fulfillmentCenterId": "HYD-01",
            "type": "CRITICAL",
            "title": "Order #1042 SLA Risk (< 2.0h)",
            "message": "Tier-1 Metro Hypermarket order requires immediate inventory allocation and wave picking.",
            "timestamp": (now - timedelta(minutes=12)).isoformat(),
            "read": False,
            "targetRole": "ALL",
            "link": "/orders"
        }
    ]

    return {
        "users": users,
        "warehouses": warehouses,
        "products": products,
        "inventory": inventory,
        "orders": orders,
        "picking_tasks": picking_tasks,
        "packing_tasks": packing_tasks,
        "quality_checks": quality_checks,
        "exceptions": exceptions,
        "decision_logs": decision_logs,
        "audit_logs": audit_logs,
        "stock_movements": stock_movements,
        "notifications": notifications,
        "dock_doors": dock_doors,
        "returns": returns,
        "climate_sensors": climate_sensors
    }
