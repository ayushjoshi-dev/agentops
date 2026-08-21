"""
AgentOps — Database Seed Script
=================================

This script populates the database with realistic demo data:
- 20 customers
- 50 products (7 categories)
- 100 orders (all statuses)
- Order items
- 15 support tickets

Run from backend/ directory:
    python scripts/seed.py

IMPORTANT: Run AFTER alembic upgrade head
"""

import sys
import os
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.ticket import SupportTicket, TicketStatus, TicketPriority
# Import all remaining models so SQLAlchemy can resolve relationships
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document, DocumentChunk
from app.models.agent_run import AgentRun
from app.models.tool_call import ToolCall


# ── Seed Data ──────────────────────────────────────────────

USERS_DATA = [
    {"email": "arjun.sharma@gmail.com",    "full_name": "Arjun Sharma",    "password": "Demo@1234"},
    {"email": "priya.patel@gmail.com",     "full_name": "Priya Patel",     "password": "Demo@1234"},
    {"email": "rahul.verma@gmail.com",     "full_name": "Rahul Verma",     "password": "Demo@1234"},
    {"email": "sneha.gupta@gmail.com",     "full_name": "Sneha Gupta",     "password": "Demo@1234"},
    {"email": "vikram.singh@gmail.com",    "full_name": "Vikram Singh",    "password": "Demo@1234"},
    {"email": "ananya.reddy@gmail.com",    "full_name": "Ananya Reddy",    "password": "Demo@1234"},
    {"email": "rohan.mehta@gmail.com",     "full_name": "Rohan Mehta",     "password": "Demo@1234"},
    {"email": "kavya.nair@gmail.com",      "full_name": "Kavya Nair",      "password": "Demo@1234"},
    {"email": "aditya.joshi@gmail.com",    "full_name": "Aditya Joshi",    "password": "Demo@1234"},
    {"email": "divya.kumar@gmail.com",     "full_name": "Divya Kumar",     "password": "Demo@1234"},
    {"email": "karan.malhotra@gmail.com",  "full_name": "Karan Malhotra",  "password": "Demo@1234"},
    {"email": "pooja.iyer@gmail.com",      "full_name": "Pooja Iyer",      "password": "Demo@1234"},
    {"email": "siddharth.rao@gmail.com",   "full_name": "Siddharth Rao",   "password": "Demo@1234"},
    {"email": "nisha.shah@gmail.com",      "full_name": "Nisha Shah",      "password": "Demo@1234"},
    {"email": "amit.bose@gmail.com",       "full_name": "Amit Bose",       "password": "Demo@1234"},
    {"email": "riya.das@gmail.com",        "full_name": "Riya Das",        "password": "Demo@1234"},
    {"email": "suresh.pillai@gmail.com",   "full_name": "Suresh Pillai",   "password": "Demo@1234"},
    {"email": "meera.krishna@gmail.com",   "full_name": "Meera Krishna",   "password": "Demo@1234"},
    {"email": "nikhil.chopra@gmail.com",   "full_name": "Nikhil Chopra",   "password": "Demo@1234"},
    # Demo user — easy for recruiters to test
    {"email": "demo@shopease.com",         "full_name": "Demo User",       "password": "Demo@1234", "is_demo": True},
]

PRODUCTS_DATA = [
    # Laptops
    {"name": "Dell Inspiron 15 3000",       "category": "Laptop",      "price": 45999,  "brand": "Dell",       "stock": 35, "rating": 4.2, "description": "15.6-inch FHD display, Intel Core i5-12th Gen, 8GB RAM, 512GB SSD, Windows 11"},
    {"name": "HP Pavilion 14",              "category": "Laptop",      "price": 52999,  "brand": "HP",         "stock": 28, "rating": 4.3, "description": "14-inch FHD IPS, AMD Ryzen 5 5600U, 16GB RAM, 512GB SSD, backlit keyboard"},
    {"name": "Lenovo IdeaPad Slim 5",       "category": "Laptop",      "price": 57999,  "brand": "Lenovo",     "stock": 22, "rating": 4.4, "description": "14-inch 2.8K OLED, Intel Core i7, 16GB RAM, 1TB SSD, Thunderbolt 4"},
    {"name": "ASUS VivoBook 16X",           "category": "Laptop",      "price": 61999,  "brand": "ASUS",       "stock": 18, "rating": 4.1, "description": "16-inch FHD+, Intel Core i5-13th Gen, 8GB RAM, 512GB SSD, ASUS AI noise-canceling"},
    {"name": "Acer Aspire 7",               "category": "Laptop",      "price": 68999,  "brand": "Acer",       "stock": 15, "rating": 4.2, "description": "15.6-inch FHD 144Hz, AMD Ryzen 7, NVIDIA RTX 3050, 16GB RAM, 512GB SSD"},
    {"name": "MSI Modern 14",               "category": "Laptop",      "price": 74999,  "brand": "MSI",        "stock": 12, "rating": 4.5, "description": "14-inch FHD IPS, Intel Core i7-13th Gen, 16GB RAM, 512GB NVMe SSD"},
    {"name": "MacBook Air M2",              "category": "Laptop",      "price": 114900, "brand": "Apple",      "stock": 20, "rating": 4.8, "description": "13.6-inch Liquid Retina, Apple M2 chip, 8GB RAM, 256GB SSD, 18-hour battery"},
    {"name": "LG Gram 16",                  "category": "Laptop",      "price": 129999, "brand": "LG",         "stock": 8,  "rating": 4.6, "description": "16-inch WQXGA IPS, Intel i7-12th Gen, 16GB RAM, 1TB SSD, under 1.2kg"},

    # Mobiles
    {"name": "Samsung Galaxy A54 5G",       "category": "Mobile",      "price": 38999,  "brand": "Samsung",    "stock": 60, "rating": 4.3, "description": "6.4-inch Super AMOLED, Exynos 1380, 8GB RAM, 128GB, 50MP triple camera, 5000mAh"},
    {"name": "Redmi Note 13 Pro",           "category": "Mobile",      "price": 24999,  "brand": "Xiaomi",     "stock": 80, "rating": 4.4, "description": "6.67-inch AMOLED 120Hz, Snapdragon 7s Gen 2, 8GB RAM, 256GB, 200MP camera"},
    {"name": "Realme 12 Pro+",              "category": "Mobile",      "price": 27999,  "brand": "Realme",     "stock": 55, "rating": 4.2, "description": "6.7-inch AMOLED curved, Snapdragon 7s Gen 2, 12GB RAM, 256GB, 50MP periscope"},
    {"name": "OnePlus Nord CE 4",           "category": "Mobile",      "price": 24999,  "brand": "OnePlus",    "stock": 45, "rating": 4.3, "description": "6.7-inch AMOLED 120Hz, Snapdragon 7 Gen 3, 8GB RAM, 128GB, 50MP, 100W SuperVOOC"},
    {"name": "iPhone 15",                   "category": "Mobile",      "price": 79900,  "brand": "Apple",      "stock": 30, "rating": 4.7, "description": "6.1-inch Super Retina XDR, A16 Bionic, 48MP camera system, USB-C, Dynamic Island"},
    {"name": "Google Pixel 8a",             "category": "Mobile",      "price": 52999,  "brand": "Google",     "stock": 25, "rating": 4.5, "description": "6.1-inch OLED, Google Tensor G3, 8GB RAM, 128GB, 64MP camera, 7 years updates"},
    {"name": "Vivo V30 Pro",                "category": "Mobile",      "price": 35999,  "brand": "Vivo",       "stock": 40, "rating": 4.2, "description": "6.78-inch AMOLED curved, Snapdragon 7 Gen 3, 12GB RAM, 256GB, 50MP ZEISS lens"},

    # Headphones
    {"name": "Sony WH-1000XM5",            "category": "Headphones",  "price": 24990,  "brand": "Sony",       "stock": 40, "rating": 4.8, "description": "Industry-leading ANC, 30hr battery, LDAC, multipoint, speak-to-chat, foldable"},
    {"name": "Bose QuietComfort 45",        "category": "Headphones",  "price": 29900,  "brand": "Bose",       "stock": 25, "rating": 4.7, "description": "High-fidelity ANC, 24hr battery, awareness mode, comfortable fit, USB-C charging"},
    {"name": "JBL Tune 770NC",              "category": "Headphones",  "price": 9999,   "brand": "JBL",        "stock": 65, "rating": 4.2, "description": "ANC, 70hr battery, JBL Pure Bass sound, multi-point connect, voice assistant"},
    {"name": "Boat Rockerz 550",            "category": "Headphones",  "price": 1799,   "brand": "boAt",       "stock": 120, "rating": 4.0, "description": "40hr playback, 40mm drivers, super extra bass, Bluetooth 5.0, Type-C charging"},
    {"name": "Nothing Ear 2",               "category": "Headphones",  "price": 9999,   "brand": "Nothing",    "stock": 35, "rating": 4.4, "description": "Dual driver ANC, LHDC codec, 36hr total, 6 mics, transparent design"},
    {"name": "Apple AirPods Pro 2nd Gen",   "category": "Headphones",  "price": 24900,  "brand": "Apple",      "stock": 30, "rating": 4.8, "description": "H2 chip, ANC + Transparency, Personalized Spatial Audio, MagSafe charging case"},

    # TVs
    {"name": "Sony Bravia X75L 43\"",       "category": "TV",          "price": 42990,  "brand": "Sony",       "stock": 20, "rating": 4.5, "description": "43-inch 4K UHD, Google TV, HDR10, Dolby Atmos, X-Reality PRO, 60Hz, 3 HDMI"},
    {"name": "Samsung Crystal 4K 50\"",     "category": "TV",          "price": 44990,  "brand": "Samsung",    "stock": 18, "rating": 4.4, "description": "50-inch 4K UHD, Crystal Processor 4K, HDR10+, PurColor, Tizen Smart TV"},
    {"name": "Mi TV 5X 55\"",              "category": "TV",          "price": 37999,  "brand": "Xiaomi",     "stock": 30, "rating": 4.3, "description": "55-inch 4K QLED, 60Hz, Dolby Vision + Atmos, Android 11 TV, 2.5W Woofer"},
    {"name": "LG OLED C3 55\"",            "category": "TV",          "price": 129990, "brand": "LG",         "stock": 10, "rating": 4.9, "description": "55-inch 4K OLED evo, α9 Gen6 AI Processor, 120Hz VRR, G-Sync, Dolby Vision IQ"},

    # Cameras
    {"name": "Canon EOS R50",               "category": "Camera",      "price": 74995,  "brand": "Canon",      "stock": 15, "rating": 4.5, "description": "24.2MP APS-C CMOS, Dual Pixel CMOS AF II, 4K 30fps, RF-S 18-45mm kit lens"},
    {"name": "Sony Alpha ZV-E10",           "category": "Camera",      "price": 59990,  "brand": "Sony",       "stock": 12, "rating": 4.4, "description": "24.2MP APS-C Exmor CMOS, 4K video, directional mic, vlog-optimized, E-mount"},
    {"name": "Fujifilm X-T30 II",           "category": "Camera",      "price": 74999,  "brand": "Fujifilm",   "stock": 8,  "rating": 4.6, "description": "26.1MP X-Trans CMOS 4, X-Processor 4, 4K 30fps, 18 Film Simulations, IBIS"},
    {"name": "GoPro Hero 12 Black",         "category": "Camera",      "price": 44990,  "brand": "GoPro",      "stock": 25, "rating": 4.5, "description": "5.3K 60fps video, 27MP photos, HyperSmooth 6.0, waterproof to 10m, GP-Log"},

    # Tablets
    {"name": "iPad 10th Gen",               "category": "Tablet",      "price": 44900,  "brand": "Apple",      "stock": 25, "rating": 4.6, "description": "10.9-inch Liquid Retina, A14 Bionic, 64GB, 12MP front camera, USB-C, Wi-Fi 6"},
    {"name": "Samsung Galaxy Tab S9 FE",    "category": "Tablet",      "price": 37999,  "brand": "Samsung",    "stock": 20, "rating": 4.4, "description": "10.9-inch TFT LCD, Exynos 1380, 6GB RAM, 128GB, S Pen included, IP68"},
    {"name": "Lenovo Tab P12",              "category": "Tablet",      "price": 27999,  "brand": "Lenovo",     "stock": 18, "rating": 4.3, "description": "12.7-inch 3K IPS, MediaTek Dimensity 7050, 8GB RAM, 128GB, 4 JBL speakers"},
    {"name": "Redmi Pad Pro",               "category": "Tablet",      "price": 22999,  "brand": "Xiaomi",     "stock": 35, "rating": 4.2, "description": "12.1-inch 2.5K, Snapdragon 7s Gen 2, 8GB RAM, 128GB, 10,000mAh, 45W charging"},

    # Smartwatches
    {"name": "Apple Watch Series 9 41mm",   "category": "Smartwatch",  "price": 41900,  "brand": "Apple",      "stock": 30, "rating": 4.8, "description": "Always-On Retina display, S9 SiP, Double Tap, blood oxygen, ECG, crash detection"},
    {"name": "Samsung Galaxy Watch 6",      "category": "Smartwatch",  "price": 27999,  "brand": "Samsung",    "stock": 25, "rating": 4.5, "description": "1.3-inch Super AMOLED, Exynos W930, advanced sleep tracking, BIA sensor"},
    {"name": "Amazfit GTR 4",               "category": "Smartwatch",  "price": 12999,  "brand": "Amazfit",    "stock": 45, "rating": 4.3, "description": "1.43-inch AMOLED, 14-day battery, 150+ sports modes, Zepp OS 2.0, Alexa"},
    {"name": "Garmin Venu 3",               "category": "Smartwatch",  "price": 44999,  "brand": "Garmin",     "stock": 15, "rating": 4.7, "description": "AMOLED display, up to 14-day battery, nap detection, wheelchair mode, AMOLED"},
    {"name": "boAt Storm Call 2",           "category": "Smartwatch",  "price": 1499,   "brand": "boAt",       "stock": 100, "rating": 4.0, "description": "1.83-inch HD display, calling, health suite, 100+ sports, 7-day battery"},

    # Additional products to reach 50
    {"name": "Sony WF-1000XM5",            "category": "Headphones",  "price": 19990,  "brand": "Sony",       "stock": 35, "rating": 4.7, "description": "Truly wireless ANC earbuds, 8+24hr battery, LDAC, multipoint, 6 mics"},
    {"name": "OnePlus 12R 5G",              "category": "Mobile",      "price": 39999,  "brand": "OnePlus",    "stock": 40, "rating": 4.5, "description": "6.78-inch AMOLED 120Hz, Snapdragon 8 Gen 1, 8GB RAM, 128GB, 100W SUPERVOOC"},
    {"name": "Realme Narzo 60 5G",          "category": "Mobile",      "price": 13999,  "brand": "Realme",     "stock": 70, "rating": 4.1, "description": "6.74-inch FHD+ 120Hz, Dimensity 6080, 6GB RAM, 128GB, 64MP, 5000mAh"},
    {"name": "ASUS ROG Phone 8",            "category": "Mobile",      "price": 79999,  "brand": "ASUS",       "stock": 12, "rating": 4.6, "description": "6.78-inch AMOLED 165Hz, Snapdragon 8 Gen 3, 12GB RAM, 256GB, 6000mAh, AeroActive Cooler X"},
    {"name": "Dell UltraSharp 27 4K",       "category": "TV",          "price": 54999,  "brand": "Dell",       "stock": 10, "rating": 4.7, "description": "27-inch 4K IPS, USB-C 90W, HDR600, 100% sRGB, pivot tilt swivel stand"},
    {"name": "Nikon Z30",                   "category": "Camera",      "price": 69995,  "brand": "Nikon",      "stock": 10, "rating": 4.4, "description": "20.9MP APS-C BSI CMOS, 4K 30fps, 209-pt phase detect AF, no OVF, vlog ready"},
    {"name": "Honor Pad 9",                 "category": "Tablet",      "price": 24999,  "brand": "Honor",      "stock": 22, "rating": 4.2, "description": "12.1-inch 2.5K IPS, Snapdragon 6 Gen 1, 8GB RAM, 256GB, 8 speakers, 8300mAh"},
    {"name": "Fitbit Charge 6",             "category": "Smartwatch",  "price": 14999,  "brand": "Fitbit",     "stock": 30, "rating": 4.3, "description": "AMOLED display, Google Maps, Google Pay, ECG, SpO2, 7-day battery, GPS"},
    {"name": "Logitech MX Master 3S",       "category": "Laptop",      "price": 9995,   "brand": "Logitech",   "stock": 50, "rating": 4.8, "description": "Ultra-fast MagSpeed scroll, 8K DPI, ergonomic, USB-C, multi-device, quiet clicks"},
    {"name": "SanDisk Extreme 1TB SSD",     "category": "Laptop",      "price": 12999,  "brand": "SanDisk",    "stock": 60, "rating": 4.6, "description": "USB 3.2 Gen 2, 1050MB/s read, IP55 rated, 256-bit AES, 5-year warranty"},
]

ADDRESSES = [
    "42, MG Road, Bengaluru, Karnataka 560001",
    "15, Connaught Place, New Delhi 110001",
    "8, Marine Drive, Mumbai, Maharashtra 400020",
    "23, Park Street, Kolkata, West Bengal 700016",
    "7, Nungambakkam High Road, Chennai, Tamil Nadu 600034",
    "101, Banjara Hills, Hyderabad, Telangana 500034",
    "55, Civil Lines, Jaipur, Rajasthan 302006",
    "12, Koregaon Park, Pune, Maharashtra 411001",
    "88, Sector 17, Chandigarh 160017",
    "33, Gomti Nagar, Lucknow, Uttar Pradesh 226010",
]

TICKET_ISSUES = [
    ("Received damaged product", "The product I received has physical damage — the screen has a crack and the box looks like it was dropped. I did not damage it. Please initiate a replacement."),
    ("Wrong item delivered", "I ordered a Sony WH-1000XM5 headphones but received a boAt Rockerz 550 instead. This is clearly the wrong item. Please send the correct product."),
    ("Order not delivered", "My order shows as delivered 3 days ago but I have not received anything. I checked with my neighbors and building security. Please investigate."),
    ("Refund not received", "I returned my order 15 days ago. The return was picked up and status shows 'Refund Initiated' but I have not received any money. Please check."),
    ("Product stopped working", "The laptop I purchased stopped working within 10 days of delivery. It will not turn on at all. This seems like a manufacturing defect."),
    ("Missing accessories", "The camera I ordered arrived without the promised kit lens and USB cable. Only the camera body was in the box. Please send the missing accessories."),
    ("Order cancellation request", "I accidentally placed a duplicate order. Please cancel order number and refund the amount before it ships."),
    ("Billing discrepancy", "I was charged ₹2,000 more than the displayed price. My bank statement shows a different amount than what was shown at checkout."),
    ("Delivery to wrong address", "My order was delivered to the wrong address. I had updated my address but it was shipped to the old one. Please help recover the package."),
    ("Product quality issue", "The smartwatch band broke within a week of use. The stitching came apart completely. This is clearly a quality defect. Please replace."),
]


def seed_users(db) -> list[User]:
    print("Seeding users...")
    users = []
    for i, data in enumerate(USERS_DATA):
        # Check if user already exists
        existing = db.query(User).filter(User.email == data["email"]).first()
        if existing:
            users.append(existing)
            continue

        user = User(
            email=data["email"],
            full_name=data["full_name"],
            hashed_password=hash_password(data["password"]),
            is_verified=True,
            is_active=True,
            is_demo=data.get("is_demo", False),
        )
        db.add(user)
        users.append(user)

    db.flush()
    print(f"  → {len(users)} users ready")
    return users


def seed_products(db) -> list[Product]:
    print("Seeding products...")
    products = []
    for data in PRODUCTS_DATA:
        existing = db.query(Product).filter(Product.name == data["name"]).first()
        if existing:
            products.append(existing)
            continue

        product = Product(
            name=data["name"],
            category=data["category"],
            price=Decimal(str(data["price"])),
            original_price=Decimal(str(int(data["price"] * 1.1))),  # 10% higher
            stock_quantity=data["stock"],
            is_available=True,
            description=data["description"],
            brand=data["brand"],
            rating=data["rating"],
            review_count=random.randint(50, 5000),
            attributes={"warranty_years": 1, "in_box": "product, charger, manual"},
        )
        db.add(product)
        products.append(product)

    db.flush()
    print(f"  → {len(products)} products ready")
    return products


def seed_orders(db, users: list[User], products: list[Product]) -> list[Order]:
    print("Seeding orders...")
    orders = []
    statuses = list(OrderStatus)
    
    # Distribute statuses realistically
    status_weights = {
        OrderStatus.PLACED: 5,
        OrderStatus.PROCESSING: 10,
        OrderStatus.SHIPPED: 15,
        OrderStatus.OUT_FOR_DELIVERY: 10,
        OrderStatus.DELIVERED: 40,
        OrderStatus.CANCELLED: 8,
        OrderStatus.RETURN_REQUESTED: 7,
        OrderStatus.REFUNDED: 5,
    }
    weighted_statuses = []
    for status, weight in status_weights.items():
        weighted_statuses.extend([status] * weight)

    for i in range(1, 101):
        order_number = f"ORD-{1000 + i}"
        existing = db.query(Order).filter(Order.order_number == order_number).first()
        if existing:
            orders.append(existing)
            continue

        user = random.choice(users)
        status = random.choice(weighted_statuses)
        
        # Created date: between 90 days ago and today
        days_ago = random.randint(1, 90)
        created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        
        # Delivery date logic
        delivery_date = None
        if status in [OrderStatus.DELIVERED, OrderStatus.RETURN_REQUESTED, OrderStatus.REFUNDED]:
            delivery_date = created_at + timedelta(days=random.randint(3, 7))
        elif status in [OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY]:
            delivery_date = datetime.now(timezone.utc) + timedelta(days=random.randint(1, 3))
        
        # Tracking number for shipped/delivered
        tracking_number = None
        if status not in [OrderStatus.PLACED, OrderStatus.PROCESSING, OrderStatus.CANCELLED]:
            carriers = ["FEDEX", "BLUEDART", "DELHIVERY", "DTDC", "EKART"]
            carrier = random.choice(carriers)
            tracking_number = f"{carrier}{random.randint(100000000, 999999999)}"

        # Select 1-3 products for this order
        order_products = random.sample(products, random.randint(1, 3))
        total = Decimal("0")
        
        order = Order(
            order_number=order_number,
            user_id=user.id,
            status=status,
            tracking_number=tracking_number,
            shipping_address=random.choice(ADDRESSES),
            delivery_date=delivery_date,
            created_at=created_at,
            updated_at=created_at,
            total_amount=Decimal("0"),  # Will update after items
        )
        db.add(order)
        db.flush()  # Get order.id

        # Create order items
        for product in order_products:
            qty = random.randint(1, 2)
            unit_price = product.price
            subtotal = unit_price * qty
            total += subtotal

            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=qty,
                unit_price=unit_price,
                subtotal=subtotal,
                created_at=created_at,
            )
            db.add(item)

        order.total_amount = total
        orders.append(order)

    db.flush()
    print(f"  → {len(orders)} orders ready")
    return orders


def seed_tickets(db, users: list[User], orders: list[Order]) -> None:
    print("Seeding support tickets...")
    # Only delivered/problematic orders get tickets
    problematic_orders = [
        o for o in orders
        if o.status in [
            OrderStatus.DELIVERED,
            OrderStatus.RETURN_REQUESTED,
            OrderStatus.REFUNDED,
        ]
    ]

    priorities = [TicketPriority.LOW, TicketPriority.MEDIUM, TicketPriority.HIGH, TicketPriority.URGENT]
    priority_weights = [10, 50, 30, 10]
    
    statuses = [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED]
    status_weights = [40, 25, 20, 15]
    
    for i in range(1, 16):
        ticket_number = f"TKT-{1000 + i}"
        existing = db.query(SupportTicket).filter(SupportTicket.ticket_number == ticket_number).first()
        if existing:
            continue

        order = random.choice(problematic_orders) if problematic_orders else None
        user = db.query(User).filter(User.id == order.user_id).first() if order else random.choice(users)
        issue_title, issue_desc = random.choice(TICKET_ISSUES)
        priority = random.choices(priorities, weights=priority_weights)[0]
        status = random.choices(statuses, weights=status_weights)[0]

        created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
        resolved_at = None
        if status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            resolved_at = created_at + timedelta(days=random.randint(1, 7))

        ticket = SupportTicket(
            ticket_number=ticket_number,
            user_id=user.id,
            order_id=order.id if order else None,
            title=issue_title,
            description=issue_desc,
            status=status,
            priority=priority,
            resolved_at=resolved_at,
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(ticket)

    db.flush()
    print("  → 15 tickets ready")


def main():
    print("\n[SEED] AgentOps Seed Script")
    print("=" * 40)

    db = SessionLocal()
    try:
        users = seed_users(db)
        products = seed_products(db)
        orders = seed_orders(db, users, products)
        seed_tickets(db, users, orders)
        
        db.commit()
        print("\n[SUCCESS] Seed completed successfully!")
        print(f"   Users:    {len(users)}")
        print(f"   Products: {len(products)}")
        print(f"   Orders:   {len(orders)}")
        print(f"   Tickets:  15")
        print("\n[KEY] Demo login: demo@shopease.com / Demo@1234")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
