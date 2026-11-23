"""Production scale data generator:
Generates:
  1. 10,000 realistic shipment records in:
     - data/processed/shipments.csv
     - data/raw/shipments.csv
     - data/raw/shipments.db (SQLite with PRIMARY KEY index)
     - data/sql/supabase_10k_seed.sql (Batched PostgreSQL multi-row inserts)
  2. 500 employee records in:
     - data/generated/employees_roster.csv
"""
from __future__ import annotations

import csv
import os
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_DATA_DIR = _ROOT / "data"
_GENERATED_DIR = _DATA_DIR / "generated"
_PROCESSED_DIR = _DATA_DIR / "processed"
_RAW_DIR = _DATA_DIR / "raw"
_SQL_DIR = _DATA_DIR / "sql"

for d in [_GENERATED_DIR, _PROCESSED_DIR, _RAW_DIR, _SQL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 1. GENERATE 500 EMPLOYEES ROSTER
# ==============================================================================

DEPARTMENTS_ROLES = {
    "Terminal & Warehouse Operations": [
        "Warehouse Operations Supervisor",
        "Inbound Dock Receiving Lead",
        "Outbound Dispatch Coordinator",
        "Lead Forklift Equipment Operator",
        "Cross-Docking Specialist",
        "Container Yard Marshall",
        "Inventory Control Auditor",
    ],
    "Customs & Trade Compliance": [
        "Senior Licensed Customs Broker",
        "Trade Compliance Auditor",
        "Tariff & HS Classification Specialist",
        "Cross-Border Regulatory Officer",
        "Export Control Specialist",
        "Customs Clearance Liaison",
    ],
    "Cold-Chain Quality & Life Sciences": [
        "GDP Compliance Manager",
        "Healthcare QA Specialist",
        "Cryogenic Storage Technician",
        "IoT Sensor Calibration Lead",
        "Temperature Excursion Investigator",
    ],
    "Flight Operations & Airfreight": [
        "Air Cargo Loadmaster",
        "Aviation Ramp Controller",
        "Airfreight Capacity Planner",
        "Charter Flight Operations Lead",
    ],
    "Marine Logistics & Ocean Freight": [
        "Container Vessel Stowage Coordinator",
        "Port Terminal Liaison Officer",
        "Reefer Technical Inspector",
        "Intermodal Rail Transfer Planner",
    ],
    "Dangerous Goods & Hazmat Safety": [
        "Certified Dangerous Goods Safety Advisor (DGSA)",
        "IATA DGR Compliance Inspector",
        "Hazmat Chemical Containment Specialist",
        "Industrial Packaging Verification Officer",
    ],
    "Fleet Engineering & Maintenance": [
        "Commercial Fleet Maintenance Supervisor",
        "Heavy Vehicle Telematics Technician",
        "Automated Guided Vehicle (AGV) Systems Engineer",
    ],
    "Customer Success & Accounts": [
        "Enterprise Strategic Account Director",
        "Tracking Escalation & Incident Lead",
        "Cargo Claims Resolution Manager",
        "Priority Customer Support Specialist",
    ],
    "Last-Mile Express Courier Network": [
        "Last-Mile Courier Dispatch Manager",
        "Route Optimization Controller",
        "Urban Fleet Delivery Supervisor",
    ],
}

FIRST_NAMES = [
    "James", "Emma", "Liam", "Sophia", "Michael", "Olivia", "Ethan", "Ava", "William", "Isabella",
    "Alexander", "Mia", "Daniel", "Charlotte", "David", "Amelia", "Joseph", "Harper", "Andrew", "Evelyn",
    "Siddharth", "Priya", "Arjun", "Ananya", "Rohan", "Meera", "Vikram", "Deepa", "Rahul", "Pooja",
    "Wei", "Ling", "Jian", "Mei", "Chen", "Yuki", "Kenji", "Hana", "Lukas", "Elena", "Mateo", "Camila",
    "Gabriel", "Chloe", "Lucas", "Aria", "Henry", "Grace", "Oliver", "Zoe", "Noah", "Hannah", "Benjamin",
    "Nora", "Samuel", "Lily", "Sebastian", "Ellie", "Jack", "Stella", "Logan", "Maya", "Jackson", "Leah",
    "Kavita", "Amit", "Naveen", "Sunita", "Harish", "Neha", "Aditya", "Suresh", "Lakshmi", "Rajesh",
    "Hiroshi", "Aoi", "Daiki", "Sakura", "Min-jun", "Ji-woo", "Seo-jun", "Ha-eun", "Carlos", "Sofia",
    "Alejandro", "Valentina", "Diego", "Lucia", "Marco", "Giulia", "Antoine", "Camille", "Stefan", "Katja"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Anderson",
    "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark",
    "Patel", "Sharma", "Verma", "Iyer", "Mukherjee", "Kulkarni", "Deshmukh", "Chowdhury", "Bose", "Nair",
    "Zhang", "Li", "Wang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou",
    "Tanaka", "Sato", "Suzuki", "Takahashi", "Watanabe", "Ito", "Yamamoto", "Nakamura", "Kobayashi", "Kato",
    "Mueller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
    "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy", "Roux", "David", "Bertrand",
    "Santos", "Ferreira", "Silva", "Oliveira", "Souza", "Rodrigues", "Almeida", "Costa", "Carvalho", "Gomes",
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Greco"
]

HUBS_LIST = [
    "Dubai Logistics City Gateway (UAE)",
    "Singapore Changi Mega Cargo Hub (Singapore)",
    "Rotterdam Maasvlakte Terminal (Netherlands)",
    "Frankfurt CargoCity South Hub (Germany)",
    "London Heathrow World Cargo Centre (UK)",
    "Los Angeles Long Beach Intermodal (USA)",
    "Shanghai Pudong Logistics Park (China)",
    "Mumbai Air Cargo & JNPT Terminal (India)",
    "Sydney Mascot International Cargo (Australia)",
    "Chicago O'Hare Northeast Cargo Terminal (USA)",
    "Tokyo Narita Air Cargo Center (Japan)",
    "Hong Kong SuperTerminal 1 (Hong Kong)",
    "Amsterdam Schiphol Logistics Hub (Netherlands)",
    "Antwerp Port Container Terminal (Belgium)",
    "Busan New Port Container Terminal (South Korea)",
]

SHIFTS = [
    "Day Shift (06:00 - 14:30)",
    "Swing Shift (14:00 - 22:30)",
    "Night / Overnight Shift (22:00 - 06:30)",
    "24/7 Operations On-Call Rotation",
]

CERTIFICATIONS = [
    "Licensed Customs Broker (LCB)",
    "IATA Dangerous Goods Regulations (DGR Cat 6)",
    "GDP Life Sciences & Pharma Certified (CC-POL-9921)",
    "Certified Supply Chain Professional (CSCP)",
    "Six Sigma Green Belt (Logistics Quality)",
    "Certified Forklift & MHE Safety Trainer",
    "ISO 9001 / ISO 14001 Quality Auditor",
    "TAPA Security Class-A Certified",
    "Standard Operations Certified",
]

random.seed(101)

employee_rows = []
used_emails = set()

for idx in range(1, 501):
    emp_id = f"EMP-{20000 + idx}"
    dept = random.choice(list(DEPARTMENTS_ROLES.keys()))
    role = random.choice(DEPARTMENTS_ROLES[dept])
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    full_name = f"{fn} {ln}"
    
    clean_fn = fn.lower().replace("-", "")
    clean_ln = ln.lower().replace("-", "")
    base_email = f"{clean_fn}.{clean_ln}@fleetharbor.com"
    email = base_email
    counter = 1
    while email in used_emails:
        email = f"{clean_fn}.{clean_ln}{counter}@fleetharbor.com"
        counter += 1
    used_emails.add(email)

    hub = random.choice(HUBS_LIST)
    shift = random.choice(SHIFTS)
    cert = random.choice(CERTIFICATIONS)
    phone_ext = f"x{4000 + idx}"

    employee_rows.append({
        "employee_id": emp_id,
        "full_name": full_name,
        "department": dept,
        "job_title": role,
        "assigned_hub": hub,
        "shift": shift,
        "certification": cert,
        "email": email,
        "phone_extension": phone_ext,
        "status": "Active"
    })

emp_csv = _GENERATED_DIR / "employees_roster.csv"
with open(emp_csv, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(employee_rows[0].keys()))
    writer.writeheader()
    writer.writerows(employee_rows)
print(f"Generated Employees Roster CSV: {emp_csv} ({len(employee_rows)} records)")


# ==============================================================================
# 2. GENERATE 10,000 REAL-TIME SHIPMENTS
# ==============================================================================

TRADE_LANES = [
    ("Mumbai, India", "London, UK", "Mumbai Hub -> Dubai Hub -> London Heathrow Hub"),
    ("Chennai, India", "Dubai, UAE", "Chennai Port -> Jebel Ali Port"),
    ("Delhi, India", "New York, USA", "Delhi Hub -> Frankfurt Hub -> JFK Airport"),
    ("Ahmedabad, India", "Singapore", "Ahmedabad Hub -> Singapore Hub"),
    ("Pune, India", "Sydney, Australia", "Pune Hub -> Singapore Hub -> Sydney Hub"),
    ("Kolkata, India", "Tokyo, Japan", "Kolkata Hub -> Singapore Hub -> Tokyo Hub"),
    ("Bangalore, India", "Berlin, Germany", "Bangalore Hub -> Mumbai Hub -> Frankfurt Hub -> Berlin Depot"),
    ("Hyderabad, India", "Toronto, Canada", "Hyderabad Hub -> Dubai Hub -> London Hub -> Toronto Pearson Hub"),
    ("Jaipur, India", "Dubai, UAE", "Jaipur Hub -> Mumbai Hub -> Dubai Hub"),
    ("Surat, India", "Los Angeles, USA", "Surat Hub -> Singapore Hub -> LAX Airport"),
    ("Shanghai, China", "Los Angeles, USA", "Shanghai Port -> Long Beach Port -> LA Intermodal Depot"),
    ("Frankfurt, Germany", "Tokyo, Japan", "Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub"),
    ("Rotterdam, Netherlands", "Sydney, Australia", "Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot"),
    ("Dubai, UAE", "New York, USA", "Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center"),
    ("Singapore", "Amsterdam, Netherlands", "Changi Cargo -> Doha Hub -> Amsterdam Schiphol"),
    ("Antwerp, Belgium", "Toronto, Canada", "Antwerp Port -> Halifax Port -> Toronto Logistics Terminal"),
    ("Shenzhen, China", "Paris, France", "Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub"),
    ("Busan, South Korea", "Vancouver, Canada", "Busan Port -> Pacific Route -> Vancouver Port"),
    ("Hong Kong", "Frankfurt, Germany", "Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity"),
    ("Bangalore, India", "San Francisco, USA", "Bangalore Air Cargo -> Singapore -> SFO Air Freight"),
    ("Melbourne, Australia", "Auckland, New Zealand", "Melbourne Port -> Tasman Sea Route -> Auckland Wharf"),
    ("Doha, Qatar", "Madrid, Spain", "Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub"),
    ("Sao Paulo, Brazil", "Miami, USA", "Santos Port -> Caribbean Route -> Port of Miami"),
    ("Johannesburg, South Africa", "London, UK", "O.R. Tambo Airport -> Nairobi Hub -> London Heathrow"),
    ("Taipei, Taiwan", "Munich, Germany", "Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal"),
    ("Zurich, Switzerland", "Boston, USA", "Zurich Airport -> Dublin Hub -> Boston Logan Freight"),
    ("Chicago, USA", "Rotterdam, Netherlands", "Chicago Rail -> Port of New York -> Rotterdam Port"),
    ("Milan, Italy", "Dubai, UAE", "Milan Malpensa -> Istanbul Transit -> Dubai Hub"),
    ("Seoul, South Korea", "Frankfurt, Germany", "Incheon Airport -> Almaty Transit -> Frankfurt Hub"),
    ("Seattle, USA", "Tokyo, Japan", "Seattle Port -> North Pacific Route -> Tokyo Port"),
    ("Santos, Brazil", "Rotterdam, Netherlands", "Santos Port -> Atlantic Route -> Rotterdam Port"),
    ("Kuala Lumpur, Malaysia", "Melbourne, Australia", "KLIA Cargo -> Darwin -> Melbourne Airport"),
    ("Bangkok, Thailand", "Los Angeles, USA", "Suvarnabhumi Airport -> Taipei Hub -> LAX Cargo"),
    ("Ho Chi Minh City, Vietnam", "Hamburg, Germany", "Cat Lai Port -> Singapore -> Suez Canal -> Hamburg Port"),
    ("Warsaw, Poland", "Chicago, USA", "Warsaw Chopin -> Frankfurt Hub -> Chicago O'Hare"),
    ("Dublin, Ireland", "New York, USA", "Dublin Airport -> Shannon Hub -> JFK Airport"),
    ("Istanbul, Turkey", "Singapore", "Istanbul Airport -> Doha Hub -> Changi Cargo"),
    ("Houston, USA", "Dhahran, Saudi Arabia", "Houston Port -> Atlantic Route -> Dammam Port"),
    ("Manila, Philippines", "San Francisco, USA", "Manila Airport -> Honolulu Transit -> SFO Air Cargo"),
    ("Copenhagen, Denmark", "Shanghai, China", "Copenhagen Airport -> Helsinki Hub -> Shanghai Pudong"),
]

STATUS_WEIGHTS = [
    ("In Transit", 42),
    ("Delivered", 30),
    ("Delayed", 13),
    ("On Hold - Customs", 8),
    ("Out for Delivery", 7),
]

DELAY_REASONS = [
    "Port congestion and vessel berthing backlog",
    "Severe weather and typhoon diversion in Pacific corridor",
    "Partner airline mechanical inspection delay",
    "Highway transit disruption and road transport detour",
    "Customs secondary inspection and valuation audit",
    "Peak holiday cargo sorting backlog at gateway facility",
    "Rail corridor track maintenance delay",
    "Air traffic control radar delay at international gateway",
    "Maritime canal convoy queuing congestion",
]

CUSTOMS_STATUSES = [
    "Cleared",
    "Not yet required",
    "Under review - Documentation pending",
    "Inspection required - Physical examination scheduled",
    "Duty payment processing",
    "Export clearance completed",
    "Held - awaiting commercial invoice",
    "Held - missing packing list",
]

random.seed(2026)
now = datetime(2026, 11, 20, 18, 0)

shipments_rows = []

# Canonical 10 core shipments
canonical_10 = [
    {
        "shipment_id": "SHP-10001",
        "origin": "Mumbai, India",
        "destination": "London, UK",
        "status": "In Transit",
        "current_location": "Dubai Hub, UAE",
        "route": "Mumbai Hub -> Dubai Hub -> London Heathrow Hub",
        "estimated_delivery": "2026-11-20",
        "delay_reason": "",
        "customs_status": "Not yet required",
        "last_updated": "2026-11-15 18:30",
    },
    {
        "shipment_id": "SHP-10002",
        "origin": "Chennai, India",
        "destination": "Dubai, UAE",
        "status": "Delayed",
        "current_location": "Jebel Ali Port, UAE",
        "route": "Chennai Port -> Jebel Ali Port",
        "estimated_delivery": "2026-11-19",
        "delay_reason": "Port congestion at Jebel Ali",
        "customs_status": "Cleared",
        "last_updated": "2026-11-16 08:00",
    },
    {
        "shipment_id": "SHP-10003",
        "origin": "Delhi, India",
        "destination": "New York, USA",
        "status": "On Hold - Customs",
        "current_location": "JFK Airport, USA",
        "route": "Delhi Hub -> Frankfurt Hub -> JFK Airport",
        "estimated_delivery": "2026-11-22",
        "delay_reason": "Customs hold",
        "customs_status": "Held - awaiting commercial invoice",
        "last_updated": "2026-11-15 12:10",
    },
    {
        "shipment_id": "SHP-10004",
        "origin": "Ahmedabad, India",
        "destination": "Singapore",
        "status": "Delivered",
        "current_location": "Singapore",
        "route": "Ahmedabad Hub -> Singapore Hub",
        "estimated_delivery": "2026-11-10",
        "delay_reason": "",
        "customs_status": "Cleared",
        "last_updated": "2026-11-10 14:45",
    },
    {
        "shipment_id": "SHP-10005",
        "origin": "Pune, India",
        "destination": "Sydney, Australia",
        "status": "Out for Delivery",
        "current_location": "Sydney Local Depot",
        "route": "Pune Hub -> Singapore Hub -> Sydney Hub",
        "estimated_delivery": "2026-11-16",
        "delay_reason": "",
        "customs_status": "Cleared",
        "last_updated": "2026-11-16 07:20",
    },
    {
        "shipment_id": "SHP-10006",
        "origin": "Kolkata, India",
        "destination": "Tokyo, Japan",
        "status": "In Transit",
        "current_location": "Singapore Hub",
        "route": "Kolkata Hub -> Singapore Hub -> Tokyo Hub",
        "estimated_delivery": "2026-11-25",
        "delay_reason": "",
        "customs_status": "Pending",
        "last_updated": "2026-11-17 09:15",
    },
    {
        "shipment_id": "SHP-10007",
        "origin": "Bangalore, India",
        "destination": "Berlin, Germany",
        "status": "Delayed",
        "current_location": "Mumbai Hub, India",
        "route": "Bangalore Hub -> Mumbai Hub -> Frankfurt Hub -> Berlin Depot",
        "estimated_delivery": "2026-11-28",
        "delay_reason": "Weather disruption at Mumbai airport",
        "customs_status": "Not yet required",
        "last_updated": "2026-11-17 06:00",
    },
    {
        "shipment_id": "SHP-10008",
        "origin": "Hyderabad, India",
        "destination": "Toronto, Canada",
        "status": "In Transit",
        "current_location": "London Heathrow Hub, UK",
        "route": "Hyderabad Hub -> Dubai Hub -> London Hub -> Toronto Pearson Hub",
        "estimated_delivery": "2026-11-24",
        "delay_reason": "",
        "customs_status": "Cleared",
        "last_updated": "2026-11-16 22:45",
    },
    {
        "shipment_id": "SHP-10009",
        "origin": "Jaipur, India",
        "destination": "Dubai, UAE",
        "status": "Delivered",
        "current_location": "Dubai, UAE",
        "route": "Jaipur Hub -> Mumbai Hub -> Dubai Hub",
        "estimated_delivery": "2026-11-12",
        "delay_reason": "",
        "customs_status": "Cleared",
        "last_updated": "2026-11-12 11:30",
    },
    {
        "shipment_id": "SHP-10010",
        "origin": "Surat, India",
        "destination": "Los Angeles, USA",
        "status": "On Hold - Customs",
        "current_location": "LAX Airport, USA",
        "route": "Surat Hub -> Singapore Hub -> LAX Airport",
        "estimated_delivery": "2026-11-26",
        "delay_reason": "Customs hold",
        "customs_status": "Held - missing packing list",
        "last_updated": "2026-11-17 03:50",
    },
]

shipments_rows.extend(canonical_10)

status_choices = [s[0] for s in STATUS_WEIGHTS]
status_weights = [s[1] for s in STATUS_WEIGHTS]

print("Generating 9,990 additional shipment records (Total: 10,000)...")

for idx in range(11, 10001):
    sid = f"SHP-{10000 + idx}"
    origin, dest, route = random.choice(TRADE_LANES)
    status = random.choices(status_choices, weights=status_weights, k=1)[0]
    
    # Real-time realistic dates and timestamps
    if status == "Delivered":
        deliv_date = now - timedelta(days=random.randint(1, 10), hours=random.randint(1, 12))
        eta = deliv_date.strftime("%Y-%m-%d")
        updated = deliv_date.strftime("%Y-%m-%d %H:%M")
        curr_loc = f"{dest} Consignee Facility"
        delay = ""
        customs = "Cleared"
    elif status == "Out for Delivery":
        eta = now.strftime("%Y-%m-%d")
        updated = (now - timedelta(hours=random.randint(1, 8), minutes=random.randint(0, 50))).strftime("%Y-%m-%d %H:%M")
        curr_loc = f"{dest} Local Courier Delivery Center"
        delay = ""
        customs = "Cleared"
    elif status == "Delayed":
        eta = (now + timedelta(days=random.randint(3, 14))).strftime("%Y-%m-%d")
        updated = (now - timedelta(hours=random.randint(2, 36))).strftime("%Y-%m-%d %H:%M")
        delay = random.choice(DELAY_REASONS)
        customs = random.choice(["Cleared", "Not yet required", "Under review - Documentation pending", "Duty payment processing"])
        curr_loc = f"Transit Facility near {origin.split(',')[0]}"
    elif status == "On Hold - Customs":
        eta = (now + timedelta(days=random.randint(2, 8))).strftime("%Y-%m-%d")
        updated = (now - timedelta(hours=random.randint(1, 24))).strftime("%Y-%m-%d %H:%M")
        delay = "Customs documentation audit in progress"
        customs = random.choice([
            "Under review - Documentation pending",
            "Held - awaiting commercial invoice",
            "Held - missing packing list",
            "Inspection required - Physical examination scheduled",
            "Duty payment processing"
        ])
        curr_loc = f"{dest.split(',')[0]} International Customs Exam Station"
    else:  # In Transit
        eta = (now + timedelta(days=random.randint(1, 9))).strftime("%Y-%m-%d")
        updated = (now - timedelta(hours=random.randint(1, 20))).strftime("%Y-%m-%d %H:%M")
        delay = ""
        customs = random.choice(["Not yet required", "Export clearance completed", "Cleared", "Duty payment processing"])
        mid_hop = route.split(" -> ")[1] if " -> " in route else origin
        curr_loc = f"In Transit ({mid_hop})"

    shipments_rows.append({
        "shipment_id": sid,
        "origin": origin,
        "destination": dest,
        "status": status,
        "current_location": curr_loc,
        "route": route,
        "estimated_delivery": eta,
        "delay_reason": delay,
        "customs_status": customs,
        "last_updated": updated,
    })

fieldnames = [
    "shipment_id", "origin", "destination", "status", "current_location",
    "route", "estimated_delivery", "delay_reason", "customs_status", "last_updated"
]

# Write CSV files
for out_path in [_PROCESSED_DIR / "shipments.csv", _RAW_DIR / "shipments.csv"]:
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(shipments_rows)
    print(f"Wrote Shipments CSV: {out_path} ({len(shipments_rows)} records, {out_path.stat().st_size:,} bytes)")


# Write to SQLite Database
db_path = _RAW_DIR / "shipments.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Shipments Table
cur.execute("DROP TABLE IF EXISTS shipments;")
cur.execute("""
CREATE TABLE shipments (
    shipment_id TEXT PRIMARY KEY,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    status TEXT NOT NULL,
    current_location TEXT,
    route TEXT,
    estimated_delivery TEXT,
    delay_reason TEXT,
    customs_status TEXT,
    last_updated TEXT
);
""")
cur.execute("CREATE INDEX idx_shipments_id ON shipments(shipment_id);")
cur.execute("CREATE INDEX idx_shipments_status ON shipments(status);")

sqlite_tuples = [
    (
        r["shipment_id"], r["origin"], r["destination"], r["status"],
        r["current_location"], r["route"], r["estimated_delivery"],
        r["delay_reason"], r["customs_status"], r["last_updated"]
    )
    for r in shipments_rows
]

cur.executemany("""
INSERT INTO shipments (
    shipment_id, origin, destination, status, current_location,
    route, estimated_delivery, delay_reason, customs_status, last_updated
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", sqlite_tuples)

# 2. Employees Table
cur.execute("DROP TABLE IF EXISTS employees;")
cur.execute("""
CREATE TABLE employees (
    employee_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    department TEXT NOT NULL,
    job_title TEXT NOT NULL,
    assigned_hub TEXT NOT NULL,
    shift TEXT NOT NULL,
    certification TEXT,
    email TEXT UNIQUE NOT NULL,
    phone_extension TEXT,
    status TEXT NOT NULL DEFAULT 'Active'
);
""")
cur.execute("CREATE INDEX idx_emp_dept ON employees(department);")
cur.execute("CREATE INDEX idx_emp_hub ON employees(assigned_hub);")

emp_tuples = [
    (
        e["employee_id"], e["full_name"], e["department"], e["job_title"],
        e["assigned_hub"], e["shift"], e["certification"], e["email"],
        e["phone_extension"], e["status"]
    )
    for e in employee_rows
]

cur.executemany("""
INSERT INTO employees (
    employee_id, full_name, department, job_title, assigned_hub,
    shift, certification, email, phone_extension, status
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", emp_tuples)

# 3. Customer Accounts Table (if customer_accounts.csv exists)
cust_csv = _GENERATED_DIR / "customer_accounts.csv"
customer_rows = []
if cust_csv.exists():
    with open(cust_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        customer_rows = list(reader)
    cur.execute("DROP TABLE IF EXISTS customers;")
    cur.execute("""
    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        tier TEXT NOT NULL,
        on_time_sla_target TEXT,
        specialty_requirements TEXT,
        payment_terms TEXT,
        credit_limit TEXT,
        dedicated_account_rep TEXT,
        contract_status TEXT
    );
    """)
    cur.executemany("""
    INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, [tuple(c.values()) for c in customer_rows])

# 4. Global Hubs Table (if global_hubs.csv exists)
hubs_csv = _GENERATED_DIR / "global_hubs.csv"
hubs_rows = []
if hubs_csv.exists():
    with open(hubs_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        hubs_rows = list(reader)
    cur.execute("DROP TABLE IF EXISTS hubs;")
    cur.execute("""
    CREATE TABLE hubs (
        facility_name TEXT NOT NULL,
        hub_code TEXT PRIMARY KEY,
        city_country TEXT NOT NULL,
        primary_transport_mode TEXT,
        storage_capacity_sqft TEXT,
        certifications TEXT,
        operations_desk_phone TEXT,
        status TEXT
    );
    """)
    cur.executemany("""
    INSERT INTO hubs VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, [tuple(h.values()) for h in hubs_rows])

conn.commit()
cur.execute("SELECT COUNT(*) FROM shipments;")
ship_cnt = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM employees;")
emp_cnt = cur.fetchone()[0]
conn.close()
print(f"Synchronized SQLite Database: {db_path} (Shipments: {ship_cnt:,}, Employees: {emp_cnt:,})")


# ==============================================================================
# 3. WRITE BATCHED POSTGRESQL / SUPABASE SEED SQL
# ==============================================================================

sql_path = _SQL_DIR / "supabase_10k_seed.sql"
print(f"Generating optimized multi-row SQL seed script for Supabase: {sql_path}...")

with open(sql_path, "w", encoding="utf-8") as f:
    f.write("-- FleetHarbor Production Scale 10,000 Shipments & 500 Employees Seed for PostgreSQL / Supabase\n")
    f.write("-- Generated: 20 November 2026\n\n")

    # 1. Shipments Table DDL
    f.write("CREATE TABLE IF NOT EXISTS public.shipments (\n")
    f.write("    shipment_id VARCHAR(32) PRIMARY KEY,\n")
    f.write("    origin VARCHAR(128) NOT NULL,\n")
    f.write("    destination VARCHAR(128) NOT NULL,\n")
    f.write("    status VARCHAR(64) NOT NULL,\n")
    f.write("    current_location VARCHAR(128),\n")
    f.write("    route TEXT,\n")
    f.write("    estimated_delivery DATE,\n")
    f.write("    delay_reason TEXT,\n")
    f.write("    customs_status VARCHAR(128),\n")
    f.write("    last_updated TIMESTAMP\n")
    f.write(");\n\n")
    f.write("CREATE INDEX IF NOT EXISTS idx_shipments_status ON public.shipments(status);\n")
    f.write("CREATE INDEX IF NOT EXISTS idx_shipments_origin ON public.shipments(origin);\n")
    f.write("CREATE INDEX IF NOT EXISTS idx_shipments_destination ON public.shipments(destination);\n\n")

    batch_size = 200
    for i in range(0, len(shipments_rows), batch_size):
        batch = shipments_rows[i:i + batch_size]
        f.write("INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated) VALUES\n")
        values_list = []
        for s in batch:
            orig = s["origin"].replace("'", "''")
            dest = s["destination"].replace("'", "''")
            stat = s["status"].replace("'", "''")
            loc = (s["current_location"] or "").replace("'", "''")
            rte = (s["route"] or "").replace("'", "''")
            eta = f"'{s['estimated_delivery']}'" if s["estimated_delivery"] else "NULL"
            delay_val = s['delay_reason'].replace("'", "''") if s["delay_reason"] else None
            cust_val = s['customs_status'].replace("'", "''") if s["customs_status"] else None
            delay = f"'{delay_val}'" if delay_val else "NULL"
            cust = f"'{cust_val}'" if cust_val else "NULL"
            upd = f"'{s['last_updated']}'" if s["last_updated"] else "NULL"
            values_list.append(f"  ('{s['shipment_id']}', '{orig}', '{dest}', '{stat}', '{loc}', '{rte}', {eta}, {delay}, {cust}, {upd})")
        f.write(",\n".join(values_list))
        f.write("\nON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;\n\n")

    # 2. Employees Table DDL and Data
    f.write("-- Employees Roster Table\n")
    f.write("CREATE TABLE IF NOT EXISTS public.employees (\n")
    f.write("    employee_id VARCHAR(32) PRIMARY KEY,\n")
    f.write("    full_name VARCHAR(128) NOT NULL,\n")
    f.write("    department VARCHAR(128) NOT NULL,\n")
    f.write("    job_title VARCHAR(128) NOT NULL,\n")
    f.write("    assigned_hub VARCHAR(128) NOT NULL,\n")
    f.write("    shift VARCHAR(64) NOT NULL,\n")
    f.write("    certification VARCHAR(128),\n")
    f.write("    email VARCHAR(128) UNIQUE NOT NULL,\n")
    f.write("    phone_extension VARCHAR(32),\n")
    f.write("    status VARCHAR(32) DEFAULT 'Active'\n")
    f.write(");\n\n")
    f.write("CREATE INDEX IF NOT EXISTS idx_employees_dept ON public.employees(department);\n")
    f.write("CREATE INDEX IF NOT EXISTS idx_employees_hub ON public.employees(assigned_hub);\n\n")

    for i in range(0, len(employee_rows), batch_size):
        batch = employee_rows[i:i + batch_size]
        f.write("INSERT INTO public.employees (employee_id, full_name, department, job_title, assigned_hub, shift, certification, email, phone_extension, status) VALUES\n")
        values_list = []
        for e in batch:
            fn = e["full_name"].replace("'", "''")
            dept = e["department"].replace("'", "''")
            title = e["job_title"].replace("'", "''")
            hub = e["assigned_hub"].replace("'", "''")
            shift = e["shift"].replace("'", "''")
            cert = (e["certification"] or "").replace("'", "''")
            email = e["email"].replace("'", "''")
            ext = e["phone_extension"].replace("'", "''")
            values_list.append(f"  ('{e['employee_id']}', '{fn}', '{dept}', '{title}', '{hub}', '{shift}', '{cert}', '{email}', '{ext}', 'Active')")
        f.write(",\n".join(values_list))
        f.write("\nON CONFLICT (employee_id) DO UPDATE SET department = EXCLUDED.department, job_title = EXCLUDED.job_title, assigned_hub = EXCLUDED.assigned_hub, email = EXCLUDED.email;\n\n")

    # 3. Customer Accounts Table DDL and Data
    if customer_rows:
        f.write("-- Customer Accounts Table\n")
        f.write("CREATE TABLE IF NOT EXISTS public.customer_accounts (\n")
        f.write("    customer_id VARCHAR(32) PRIMARY KEY,\n")
        f.write("    company_name VARCHAR(128) NOT NULL,\n")
        f.write("    tier VARCHAR(32) NOT NULL,\n")
        f.write("    on_time_sla_target VARCHAR(32),\n")
        f.write("    specialty_requirements TEXT,\n")
        f.write("    payment_terms VARCHAR(32),\n")
        f.write("    credit_limit VARCHAR(32),\n")
        f.write("    dedicated_account_rep VARCHAR(128),\n")
        f.write("    contract_status VARCHAR(32)\n")
        f.write(");\n\n")
        f.write("INSERT INTO public.customer_accounts VALUES\n")
        cust_vals = []
        for c in customer_rows:
            vals = []
            for v in c.values():
                clean_v = str(v).replace("'", "''")
                vals.append(f"'{clean_v}'")
            cust_vals.append(f"  ({', '.join(vals)})")
        f.write(",\n".join(cust_vals))
        f.write("\nON CONFLICT (customer_id) DO NOTHING;\n\n")

print(f"Generated Supabase 10K SQL Seed: {sql_path} ({sql_path.stat().st_size:,} bytes)")


# ==============================================================================
# 4. GENERATE EMPLOYEE ROSTER KNOWLEDGE BASE TEXT MANUAL
# ==============================================================================

kb_dir = _ROOT / "knowledge_base"
kb_emp_path = kb_dir / "employee_roster_and_department_directory.txt"
print(f"Generating comprehensive Knowledge Base Manual: {kb_emp_path}...")

dept_summary = {}
for e in employee_rows:
    dept = e["department"]
    dept_summary.setdefault(dept, []).append(e)

with open(kb_emp_path, "w", encoding="utf-8") as f:
    f.write("# FLEETHARBOR GLOBAL LOGISTICS – EMPLOYEE ROSTER & DEPARTMENT DIRECTORY\n")
    f.write("Document ID: SOP-EMP-500\n")
    f.write("Effective Date: November 2026\n")
    f.write("Classification: Internal Operations Manual & Staffing Directory\n\n")
    
    f.write("## 1. Executive Summary & Workforce Architecture\n")
    f.write("FleetHarbor Logistics operates an international workforce of 500 certified logistics professionals deployed across 15 global mega-hubs and regional gateways. Operations span 24/7/365 across three primary shift rotations: Day Shift (06:00 - 14:30), Swing Shift (14:00 - 22:30), and Overnight Shift (22:00 - 06:30), supported by an On-Call Escalation rotation.\n\n")
    
    f.write("## 2. Departmental Breakdown & Key Roles\n")
    for dept_name, emps in sorted(dept_summary.items()):
        f.write(f"### Department: {dept_name} (Total Staff: {len(emps)})\n")
        f.write(f"- Primary Operational Mandate: End-to-end execution, oversight, and quality control for {dept_name.lower()} operations.\n")
        f.write(f"- Key Active Specialists & Certified Personnel:\n")
        # List sample specialists
        for sample in emps[:10]:
            f.write(f"  * {sample['employee_id']}: {sample['full_name']} | Title: {sample['job_title']} | Hub: {sample['assigned_hub']} | Shift: {sample['shift']} | Cert: {sample['certification']} | Contact: {sample['email']} (Ext: {sample['phone_extension']})\n")
        f.write("\n")

    f.write("## 3. Global Hub Staffing Directory\n")
    f.write("Every global gateway maintains a dedicated operations desk reachable via VoIP extension and dispatch channel:\n")
    for hub in HUBS_LIST:
        f.write(f"- {hub}: Staffed 24/7 across Inbound, Outbound, Customs, and Cold-Chain desks.\n")
    f.write("\n")

    f.write("## 4. Certification Standards\n")
    f.write("FleetHarbor personnel maintain rigorous international certifications:\n")
    f.write("- Licensed Customs Broker (LCB): Mandatory for export/import declaration validation.\n")
    f.write("- IATA Dangerous Goods Regulations (DGR Cat 6): Mandatory for hazmat cargo handling and lithium battery packaging.\n")
    f.write("- GDP Life Sciences & Pharma (CC-POL-9921): Mandatory for temperature-controlled active container reefer maintenance.\n")
    f.write("- Six Sigma Green Belt: Continuous improvement and freight claims mitigation.\n")
    f.write("- TAPA Security Class-A: High-value asset handling and container seal inspection.\n\n")

    f.write("## 5. Escalation & Contact Protocol\n")
    f.write("For urgent shipment tracking, customs holds, or temperature excursion investigations, staff and customers can reach the command center at dispatch@fleetharbor.com or internal extensions x4001 through x4500.\n")

print(f"Generated Employee Knowledge Base: {kb_emp_path} ({kb_emp_path.stat().st_size:,} bytes)")
print("Real-time production generation completed successfully!")


print(f"Generated Supabase 10K SQL Seed: {sql_path} ({sql_path.stat().st_size:,} bytes)")
print("Real-time production generation completed successfully!")
