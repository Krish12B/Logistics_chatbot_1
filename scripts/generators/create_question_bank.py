"""Script to generate the comprehensive 160-question test dataset for FleetHarbor Logistics Chatbot.
Generates 12 category JSON files in tests/question_bank/ with strict grounding in real database records
and official knowledge base documents.
"""
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "raw" / "shipments.db"
QB_DIR = ROOT / "tests" / "question_bank"
QB_DIR.mkdir(parents=True, exist_ok=True)

# Fetch sample shipments from SQLite to ground tracking questions in real records
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def get_shipment(sid):
    cur.execute("SELECT * FROM shipments WHERE shipment_id = ?", (sid,))
    row = cur.fetchone()
    return dict(row) if row else {}

def get_employee(eid):
    cur.execute("SELECT * FROM employees WHERE employee_id = ?", (eid,))
    row = cur.fetchone()
    return dict(row) if row else {}

# -------------------------------------------------------------
# 1. GENERAL LOGISTICS QUESTIONS (15)
# -------------------------------------------------------------
cat1_general = [
    {
        "test_id": "GEN_001",
        "category": "general_logistics",
        "question": "What is logistics in modern supply chain management?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain the coordination of movement, storage, inventory, and packaging of goods from origin to consumption.",
        "evaluation_criteria": {
            "required_concepts": ["movement", "storage", "supply chain", "origin", "destination"],
            "must_not_contain": ["hallucination"]
        },
        "priority": "P1"
    },
    {
        "test_id": "GEN_002",
        "category": "general_logistics",
        "question": "What are the core functions of a logistics carrier like FleetHarbor?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail freight forwarding, ocean/air cargo transportation, warehousing, customs clearance, and last-mile delivery.",
        "evaluation_criteria": {
            "required_concepts": ["freight", "warehousing", "transportation", "customs", "delivery"],
            "must_not_contain": []
        },
        "priority": "P1"
    },
    {
        "test_id": "GEN_003",
        "category": "general_logistics",
        "question": "What is the difference between logistics and supply chain management?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Clarify that logistics is a specialized subset focusing on movement/storage, while supply chain encompasses procurement, manufacturing, sourcing, and distribution.",
        "evaluation_criteria": {
            "required_concepts": ["subset", "procurement", "movement", "storage", "supply chain"],
            "must_not_contain": []
        },
        "priority": "P2"
    },
    {
        "test_id": "GEN_004",
        "category": "general_logistics",
        "question": "What is the difference between logistics and transportation?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain that transportation is the physical movement of freight, whereas logistics encompasses transportation plus warehousing, inventory, documentation, and customs compliance.",
        "evaluation_criteria": {
            "required_concepts": ["physical movement", "warehousing", "inventory", "documentation"],
            "must_not_contain": []
        },
        "priority": "P2"
    },
    {
        "test_id": "GEN_005",
        "category": "general_logistics",
        "question": "What is a Bill of Lading (BOL) and why is it legally important?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Define Bill of Lading as a legal title document, contract of carriage, and receipt for goods issued by carrier to shipper.",
        "evaluation_criteria": {
            "required_concepts": ["contract of carriage", "receipt of goods", "document of title", "consignee"],
            "must_not_contain": []
        },
        "priority": "P0"
    },
    {
        "test_id": "GEN_006",
        "category": "general_logistics",
        "question": "Explain the difference between FOB and CIF Incoterms.",
        "expected_intent": "direct_definition",
        "expected_source": "knowledge_base",
        "expected_behavior": "Provide structured comparison of Free On Board (buyer pays marine freight and insurance from origin port) vs Cost Insurance Freight (seller pays carriage and marine insurance to destination port).",
        "evaluation_criteria": {
            "required_concepts": ["FOB", "CIF", "Free On Board", "Cost, Insurance, and Freight", "risk transfer"],
            "must_not_contain": []
        },
        "priority": "P0"
    },
    {
        "test_id": "GEN_007",
        "category": "general_logistics",
        "question": "What is demurrage and how does it differ from detention?",
        "expected_intent": "direct_definition",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain that demurrage applies inside the port terminal beyond free days, whereas detention applies outside the terminal when containers are held past allowed return time.",
        "evaluation_criteria": {
            "required_concepts": ["demurrage", "detention", "terminal", "free days", "container"],
            "must_not_contain": []
        },
        "priority": "P1"
    },
    {
        "test_id": "GEN_008",
        "category": "general_logistics",
        "question": "What is cross-docking in modern freight distribution?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Describe unloading inbound cargo from incoming trucks/rail directly into outbound vehicles with zero or minimal intermediate warehouse storage.",
        "evaluation_criteria": {
            "required_concepts": ["cross-docking", "inbound", "outbound", "storage", "hub"],
            "must_not_contain": []
        },
        "priority": "P2"
    },
    {
        "test_id": "GEN_009",
        "category": "general_logistics",
        "question": "What does LCL and FCL stand for in container shipping?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain Less than Container Load (consolidated shipments from multiple shippers) vs Full Container Load (dedicated exclusive container for a single shipper).",
        "evaluation_criteria": {
            "required_concepts": ["Less than Container Load", "Full Container Load", "consolidation", "container"],
            "must_not_contain": []
        },
        "priority": "P1"
    },
    {
        "test_id": "GEN_010",
        "category": "general_logistics",
        "question": "What is an Air Waybill (AWB)?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Define AWB as the non-negotiable transport document issued by an air carrier covering carriage of goods on scheduled flights.",
        "evaluation_criteria": {
            "required_concepts": ["Air Waybill", "air carrier", "tracking", "non-negotiable", "consignee"],
            "must_not_contain": []
        },
        "priority": "P1"
    },
    {
        "test_id": "GEN_011",
        "category": "general_logistics",
        "question": "What is intermodal freight transport?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain moving freight in a standardized container or vehicle using multiple modes of transportation (rail, ship, truck) without handling cargo itself during mode transfers.",
        "evaluation_criteria": {
            "required_concepts": ["intermodal", "rail", "ship", "truck", "container", "transfer"],
            "must_not_contain": []
        },
        "priority": "P2"
    },
    {
        "test_id": "GEN_012",
        "category": "general_logistics",
        "question": "What are standard ISO container dimensions for 20ft and 40ft containers?",
        "expected_intent": "direct_definition",
        "expected_source": "knowledge_base",
        "expected_behavior": "List standard dimensions: 20ft (approx 5.9m x 2.35m x 2.39m, ~33 CBM) and 40ft (12.03m x 2.35m x 2.39m, ~67.7 CBM).",
        "evaluation_criteria": {
            "required_concepts": ["20ft", "40ft", "payload", "capacity", "dimensions"],
            "must_not_contain": []
        },
        "priority": "P1"
    },
    {
        "test_id": "GEN_013",
        "category": "general_logistics",
        "question": "What is volumetric weight and how is air freight dimensional weight calculated?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "State the IATA standard volumetric ratio: (L x W x H in cm) / 6000 = volumetric weight in kg (or 1 CBM = 167 kg).",
        "evaluation_criteria": {
            "required_concepts": ["volumetric weight", "IATA", "6000", "dimensional weight"],
            "must_not_contain": []
        },
        "priority": "P1"
    },
    {
        "test_id": "GEN_014",
        "category": "general_logistics",
        "question": "What is cold-chain logistics in pharmaceutical transport?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain temperature-controlled supply chain maintaining prescribed temperature ranges (2-8°C, -20°C, -70°C) from manufacturer to patient under GDP standards.",
        "evaluation_criteria": {
            "required_concepts": ["temperature-controlled", "cold-chain", "pharma", "GDP", "2°C to 8°C"],
            "must_not_contain": []
        },
        "priority": "P0"
    },
    {
        "test_id": "GEN_015",
        "category": "general_logistics",
        "question": "What are the six stages of a complete shipment lifecycle?",
        "expected_intent": "direct_definition",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail the 6 stages: Booking & Order Creation, Inbound Pickup & Consolidation, Export Customs, Linehaul Transit, Import Customs, Out for Delivery & POD.",
        "evaluation_criteria": {
            "required_concepts": ["Booking", "Pickup", "Export Customs", "Linehaul", "Import Customs", "Proof of Delivery"],
            "must_not_contain": []
        },
        "priority": "P0"
    }
]

# -------------------------------------------------------------
# 2. SHIPMENT TRACKING (20)
# -------------------------------------------------------------
cat2_tracking = []
sample_ids = [
    "SHP-10001", "SHP-10002", "SHP-10003", "SHP-10004", "SHP-10005",
    "SHP-10006", "SHP-10007", "SHP-10008", "SHP-10009", "SHP-10010",
    "SHP-10011", "SHP-10012", "SHP-10013", "SHP-10014", "SHP-10015",
    "SHP-10016", "SHP-10017", "SHP-10018", "SHP-10019", "SHP-10020"
]

for idx, sid in enumerate(sample_ids, start=1):
    rec = get_shipment(sid)
    cat2_tracking.append({
        "test_id": f"TRACK_{idx:03d}",
        "category": "shipment_tracking",
        "question": f"What is the status and location of shipment {sid}?",
        "required_shipment_id": sid,
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Return structured shipment tracking report with verified database fields.",
        "expected_fields": ["shipment_id", "status", "current_location", "origin", "destination", "estimated_delivery"],
        "ground_truth": {
            "status": rec.get("status"),
            "current_location": rec.get("current_location"),
            "origin": rec.get("origin"),
            "destination": rec.get("destination"),
            "delay_reason": rec.get("delay_reason", "")
        },
        "priority": "P0"
    })

# Customize some question variants in tracking
cat2_tracking[0]["question"] = "Track shipment SHP-10001"
cat2_tracking[1]["question"] = "Where is shipment SHP-10002 located right now?"
cat2_tracking[2]["question"] = "Show me the tracking status for SHP-10003"
cat2_tracking[3]["question"] = "Has shipment SHP-10004 been delivered?"
cat2_tracking[4]["question"] = "Is SHP-10005 out for delivery today?"
cat2_tracking[5]["question"] = "What is the expected delivery date for SHP-10006?"
cat2_tracking[6]["question"] = "Why is shipment SHP-10007 delayed?"
cat2_tracking[7]["question"] = "Get full transit route details for SHP-10008"
cat2_tracking[8]["question"] = "Check delivery confirmation of SHP-10009"
cat2_tracking[9]["question"] = "What is holding up shipment SHP-10010 at customs?"

# -------------------------------------------------------------
# 3. DELIVERY MANAGEMENT (15)
# -------------------------------------------------------------
cat3_delivery = [
    {
        "test_id": "DELIV_001",
        "category": "delivery_management",
        "question": "What does 'Out for Delivery' status mean?",
        "expected_intent": "direct_definition",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain cargo has departed local delivery hub on courier vehicle for physical delivery today.",
        "priority": "P0"
    },
    {
        "test_id": "DELIV_002",
        "category": "delivery_management",
        "question": "What happens when a delivery attempt fails because consignee is unavailable?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain delivery re-attempt protocol, driver notice card, and 7-day depot holding window.",
        "priority": "P1"
    },
    {
        "test_id": "DELIV_003",
        "category": "delivery_management",
        "question": "What is Proof of Delivery (POD) and what details are recorded?",
        "expected_intent": "direct_definition",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail electronic POD capturing recipient signature, GPS coordinates, timestamp, and package piece count.",
        "priority": "P0"
    },
    {
        "test_id": "DELIV_004",
        "category": "delivery_management",
        "question": "How are delivery time windows scheduled for Enterprise tier accounts?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite customer rules SLA providing guaranteed 2-hour delivery booking slots for Enterprise customers.",
        "priority": "P1"
    },
    {
        "test_id": "DELIV_005",
        "category": "delivery_management",
        "question": "What procedure is followed when cargo is delivered to a destination hub?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail unloading scan, LPN verification, physical container seal check, and sorting to linehaul bay.",
        "priority": "P1"
    },
    {
        "test_id": "DELIV_006",
        "category": "delivery_management",
        "question": "What is the maximum allowed holding time at destination hub before return haulage?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain standard holding period is 7 to 10 days before Return to Shipper (RTS) procedures initiate.",
        "priority": "P2"
    },
    {
        "test_id": "DELIV_007",
        "category": "delivery_management",
        "question": "How does FleetHarbor handle address correction requests during transit?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain rerouting request process through dispatch before final-mile dispatch, including re-consignment fee if applicable.",
        "priority": "P2"
    },
    {
        "test_id": "DELIV_008",
        "category": "delivery_management",
        "question": "What is the delivery cutoff time for same-day priority air shipments?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail airport tender cutoff times (typically 12:00 or 14:00 local airport time).",
        "priority": "P2"
    },
    {
        "test_id": "DELIV_009",
        "category": "delivery_management",
        "question": "Can a consignee inspect packages before signing the Proof of Delivery?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain outer carton visual condition signoff and policy for noting damaged boxes directly on POD.",
        "priority": "P1"
    },
    {
        "test_id": "DELIV_010",
        "category": "delivery_management",
        "question": "What delivery confirmation options are available for high-value cargo?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail adult signature required (DSR), photo POD, and dual security escort for sensitive consignments.",
        "priority": "P1"
    },
    {
        "test_id": "DELIV_011",
        "category": "delivery_management",
        "question": "What is the estimated delivery time for SHP-10005?",
        "required_shipment_id": "SHP-10005",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Retrieve estimated delivery date 2026-11-16 and out for delivery status from database.",
        "priority": "P0"
    },
    {
        "test_id": "DELIV_012",
        "category": "delivery_management",
        "question": "What is last-mile logistics routing optimization?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain dynamic courier route sequencing based on traffic telemetry, delivery windows, and fuel efficiency.",
        "priority": "P2"
    },
    {
        "test_id": "DELIV_013",
        "category": "delivery_management",
        "question": "What happens if a recipient refuses to accept a delivery?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Document delivery rejection status 'Refused by Consignee', return to local depot, and notification to shipper.",
        "priority": "P1"
    },
    {
        "test_id": "DELIV_014",
        "category": "delivery_management",
        "question": "How are delivery time windows calculated across international time zones?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain UTC standardized timestamps with automatic destination local time conversion for delivery estimates.",
        "priority": "P2"
    },
    {
        "test_id": "DELIV_015",
        "category": "delivery_management",
        "question": "What is the procedure for contactless delivery during high-security consignments?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain OTP or one-time delivery verification code paired with geo-tagged delivery photograph.",
        "priority": "P2"
    }
]

# -------------------------------------------------------------
# 4. SHIPMENT DELAYS AND EXCEPTIONS (15)
# -------------------------------------------------------------
cat4_delays = [
    {
        "test_id": "DELAY_001",
        "category": "shipment_delays",
        "question": "What happens when a shipment is delayed due to weather?",
        "expected_intent": "direct_definition",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain exception trigger, status change to Delayed, automated ETA recalculation, and notification dispatch.",
        "priority": "P0"
    },
    {
        "test_id": "DELAY_002",
        "category": "shipment_delays",
        "question": "Why is shipment SHP-10002 delayed?",
        "required_shipment_id": "SHP-10002",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Identify delay reason from database: 'Port congestion at Jebel Ali'.",
        "priority": "P0"
    },
    {
        "test_id": "DELAY_003",
        "category": "shipment_delays",
        "question": "What is the reason for delay on shipment SHP-10007?",
        "required_shipment_id": "SHP-10007",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Identify delay reason from database: 'Weather disruption at Mumbai airport'.",
        "priority": "P0"
    },
    {
        "test_id": "DELAY_004",
        "category": "shipment_delays",
        "question": "What is the company policy for escalating shipments delayed more than 48 hours?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite escalation protocol: Level 2 operations supervisor alert, route rerouting review, and direct client call.",
        "priority": "P1"
    },
    {
        "test_id": "DELAY_005",
        "category": "shipment_delays",
        "question": "How are customs holds categorized and resolved?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail HOLD-DOC (documentation missing), HOLD-VAL (customs valuation dispute), and HOLD-PHYS (physical inspection lane).",
        "priority": "P0"
    },
    {
        "test_id": "DELAY_006",
        "category": "shipment_delays",
        "question": "Why is shipment SHP-10003 on customs hold?",
        "required_shipment_id": "SHP-10003",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Explain customs status: 'Held - awaiting commercial invoice' at JFK Airport, USA.",
        "priority": "P0"
    },
    {
        "test_id": "DELAY_007",
        "category": "shipment_delays",
        "question": "What is the root cause of delay for SHP-10010?",
        "required_shipment_id": "SHP-10010",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Identify customs status: 'Held - missing packing list' at LAX Airport, USA.",
        "priority": "P0"
    },
    {
        "test_id": "DELAY_008",
        "category": "shipment_delays",
        "question": "What compensation is available if a guaranteed delivery SLA is breached?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite customer terms: freight credit or refund per account tier SLA guidelines.",
        "priority": "P1"
    },
    {
        "test_id": "DELAY_009",
        "category": "shipment_delays",
        "question": "What happens if a cold-chain pharma shipment experiences a temperature excursion?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite policy CC-POL-9921: immediate isolation in secondary reefer, 24-hr QA deviation root-cause investigation, and cold-chain stability assessment.",
        "priority": "P0"
    },
    {
        "test_id": "DELAY_010",
        "category": "shipment_delays",
        "question": "How should an employee handle cargo damaged in transit during linehaul?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Quarantine cargo, photograph packaging, log exception in WMS/ERP, file damaged freight report within 12 hours.",
        "priority": "P1"
    },
    {
        "test_id": "DELAY_011",
        "category": "shipment_delays",
        "question": "What is the procedure if a cargo container seal is found broken or mismatched?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Stop unloading immediately, alert security supervisor, notify customs liaison, take high-resolution photos, and verify seal bolt serial number against manifest.",
        "priority": "P0"
    },
    {
        "test_id": "DELAY_012",
        "category": "shipment_delays",
        "question": "How long does a customer have to file a formal cargo loss claim?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite claims timeline: outer damage within 3 days, concealed damage within 14 days, total loss within 30 days of estimated delivery.",
        "priority": "P1"
    },
    {
        "test_id": "DELAY_013",
        "category": "shipment_delays",
        "question": "What happens when a shipment is marked as 'Cancelled'?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain order voiding, return-to-sender or cancellation of dispatch, and assessment of cancellation haulage fee if cargo was already collected.",
        "priority": "P2"
    },
    {
        "test_id": "DELAY_014",
        "category": "shipment_delays",
        "question": "What is the demurrage charge rate if a container exceeds free time at port?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite customer terms: $85/day for dry containers, $220/day for reefers/hazmat containers after standard 4-7 free days.",
        "priority": "P1"
    },
    {
        "test_id": "DELAY_015",
        "category": "shipment_delays",
        "question": "How does FleetHarbor notify consignees about in-transit delays?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain automated EDI/email exception notifications triggered dynamically upon status update.",
        "priority": "P2"
    }
]

# -------------------------------------------------------------
# 5. COMPANY POLICIES AND PROCEDURES (15)
# -------------------------------------------------------------
cat5_policies = [
    {
        "test_id": "POL_001",
        "category": "company_policies",
        "question": "What is FleetHarbor's temperature control policy CC-POL-9921 for pharma cargo?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain CC-POL-9921 4 temperature regimes: Cryogenic (-70°C), Frozen (-20°C), Refrigerated (2°C-8°C), and Controlled Room Temp (15°C-25°C).",
        "priority": "P0"
    },
    {
        "test_id": "POL_002",
        "category": "company_policies",
        "question": "Where are FleetHarbor dual corporate headquarters located?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "State dual headquarters in Singapore (Marina Bay) and Rotterdam (Wilhelminakade, Netherlands).",
        "priority": "P1"
    },
    {
        "test_id": "POL_003",
        "category": "company_policies",
        "question": "What are FleetHarbor's company commitments regarding Net-Zero sustainability?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite FleetHarbor Net-Zero 2040 commitment, bio-fueled maritime vessels, and electric last-mile delivery fleet.",
        "priority": "P2"
    },
    {
        "test_id": "POL_004",
        "category": "company_policies",
        "question": "What are the speed limits and safety rules for forklifts in FleetHarbor warehouses?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite warehouse SOP: 8 km/h speed limit in pedestrian shared bays, mandatory horn at intersections, high-visibility vest and steel-toe boots.",
        "priority": "P1"
    },
    {
        "test_id": "POL_005",
        "category": "company_policies",
        "question": "What is the mandatory segregation distance for hazardous materials in sorting hubs?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite hazmat SOP: minimum 6-meter physical segregation or certified firewall between incompatible chemical classes.",
        "priority": "P0"
    },
    {
        "test_id": "POL_006",
        "category": "company_policies",
        "question": "What are the rules for shipping standalone lithium-ion batteries by air?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite IATA regulations UN3480 Section IA/IB: max 30% State of Charge (SoC), Cargo Aircraft Only (CAO) label, and UN 38.3 test certificate.",
        "priority": "P0"
    },
    {
        "test_id": "POL_007",
        "category": "company_policies",
        "question": "What customer account tiers does FleetHarbor provide and what are their SLAs?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain Enterprise (99.5% SLA, 15-min emergency dispatch, 30-day net payment), Healthcare, and Standard tiers.",
        "priority": "P1"
    },
    {
        "test_id": "POL_008",
        "category": "company_policies",
        "question": "What is the cancellation haulage fee policy when an order is cancelled after dispatch?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite customer rules: $150 cancellation charge for standard road haulage, $450 for specialized heavy/reefer transport.",
        "priority": "P2"
    },
    {
        "test_id": "POL_009",
        "category": "company_policies",
        "question": "What is the target settlement timeframe for customer cargo damage claims?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite claims SOP: 21 business days SLA for claims review and financial compensation settlement.",
        "priority": "P1"
    },
    {
        "test_id": "POL_010",
        "category": "company_policies",
        "question": "What are the dry ice packaging standards for deep-frozen pharmaceutical transport?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail Class 9 UN1845 labelling, vented packaging to prevent pressure buildup, net weight declared on air waybill.",
        "priority": "P0"
    },
    {
        "test_id": "POL_011",
        "category": "company_policies",
        "question": "What are the company warehouse stacking height limits for standard Euro pallets?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "State standard warehouse maximum pallet stack height of 1.8 meters (or 2 tiers of shrink-wrapped pallets max).",
        "priority": "P1"
    },
    {
        "test_id": "POL_012",
        "category": "company_policies",
        "question": "What certifications are required for cold-chain handlers at FleetHarbor?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Cite IATA CEIV Pharma certification and WHO Good Distribution Practice (GDP) annual qualification.",
        "priority": "P1"
    },
    {
        "test_id": "POL_013",
        "category": "company_policies",
        "question": "What are the rules regarding hazardous materials Class 1 and Class 7 transport?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain that Class 1 (Explosives) and Class 7 (Radioactive) are strictly prohibited on commercial flights and require dedicated military/charter permits.",
        "priority": "P0"
    },
    {
        "test_id": "POL_014",
        "category": "company_policies",
        "question": "What is the policy for reporting warehouse workplace safety incidents?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Immediate halt of operations in affected zone, notification of safety officer, and submission of incident log within 2 hours.",
        "priority": "P1"
    },
    {
        "test_id": "POL_015",
        "category": "company_policies",
        "question": "What are the free time allowances before demurrage applies at international ports?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Standard ocean carriage allows 4 to 7 calendar days free time for container discharge and collection.",
        "priority": "P1"
    }
]

# -------------------------------------------------------------
# 6. EMPLOYEE ASSISTANCE (15)
# -------------------------------------------------------------
cat6_employee = [
    {
        "test_id": "EMP_001",
        "category": "employee_assistance",
        "question": "Look up employee EMP-20001 details",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Retrieve employee profile for Stella Davis (Airfreight Capacity Planner, Tokyo Narita hub).",
        "priority": "P0"
    },
    {
        "test_id": "EMP_002",
        "category": "employee_assistance",
        "question": "Who is employee EMP-20004 and what is their role?",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Retrieve profile for Wei Russo (Cargo Claims Resolution Manager, Amsterdam Schiphol).",
        "priority": "P0"
    },
    {
        "test_id": "EMP_003",
        "category": "employee_assistance",
        "question": "What is the phone extension and email for EMP-20003?",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Retrieve Siddharth Jackson, extension x4003, siddharth.jackson@fleetharbor.com.",
        "priority": "P0"
    },
    {
        "test_id": "EMP_004",
        "category": "employee_assistance",
        "question": "How do I register an operational exception for a stuck container?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain logging into WMS, tagging shipment with exception reason code, and forwarding to hub dispatch supervisor.",
        "priority": "P1"
    },
    {
        "test_id": "EMP_005",
        "category": "employee_assistance",
        "question": "What information is mandatory when booking a new international shipment?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "List Shipper/Consignee tax IDs, HS Tariff Codes, Cargo Gross/Net weights, Dimensions, Declared Commercial Value.",
        "priority": "P1"
    },
    {
        "test_id": "EMP_006",
        "category": "employee_assistance",
        "question": "How should an employee handle shift handover at a sort hub?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail shift handover checklist: high-priority hot orders, unresolved exception holds, equipment inspections, and pending linehauls.",
        "priority": "P2"
    },
    {
        "test_id": "EMP_007",
        "category": "employee_assistance",
        "question": "Look up employee record for EMP-20010",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Return employee profile from employees directory.",
        "priority": "P1"
    },
    {
        "test_id": "EMP_008",
        "category": "employee_assistance",
        "question": "What is the procedure if a package barcode is smudged or unreadable?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Reprint LPN label via system lookup using airway bill or waybill tracking number.",
        "priority": "P2"
    },
    {
        "test_id": "EMP_009",
        "category": "employee_assistance",
        "question": "Who do I contact in case of an emergency hazmat spill in the warehouse?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Evacuate upwind, activate warehouse emergency alarm, contact environmental safety response desk.",
        "priority": "P0"
    },
    {
        "test_id": "EMP_010",
        "category": "employee_assistance",
        "question": "How do employees file an overtime claim for night shifts?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Submit bi-weekly timesheet approved by shift operations manager to HR payroll portal.",
        "priority": "P2"
    },
    {
        "test_id": "EMP_011",
        "category": "employee_assistance",
        "question": "Look up employee EMP-20005",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Retrieve Lily Hoffmann (Air Cargo Loadmaster, London Heathrow).",
        "priority": "P0"
    },
    {
        "test_id": "EMP_012",
        "category": "employee_assistance",
        "question": "What is the standard procedure for pallet wrapping and strapping?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Minimum 5 layers of high-tensile stretch film with cross-corner banding for linehaul stability.",
        "priority": "P2"
    },
    {
        "test_id": "EMP_013",
        "category": "employee_assistance",
        "question": "What are the weight distribution limits when loading a 53ft dry van?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Steer axle ≤ 12,000 lbs, Drive tandem ≤ 34,000 lbs, Trailer tandem ≤ 34,000 lbs, Gross ≤ 80,000 lbs.",
        "priority": "P1"
    },
    {
        "test_id": "EMP_014",
        "category": "employee_assistance",
        "question": "How do dispatchers confirm driver rest hours under Hours of Service (HOS) rules?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Verify Electronic Logging Device (ELD) telematics ensuring 10 consecutive hours off-duty.",
        "priority": "P2"
    },
    {
        "test_id": "EMP_015",
        "category": "employee_assistance",
        "question": "Look up employee EMP-20020",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Return employee record from database.",
        "priority": "P1"
    }
]

# -------------------------------------------------------------
# 7. DOCUMENTATION AND KNOWLEDGE RETRIEVAL (10)
# -------------------------------------------------------------
cat7_docs = [
    {
        "test_id": "DOC_001",
        "category": "documentation_retrieval",
        "question": "Summarize the required international customs documents described in the compliance manual.",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Summarize Commercial Invoice, Packing List, Original Bill of Lading / AWB, Certificate of Origin, and Import Declarations.",
        "priority": "P0"
    },
    {
        "test_id": "DOC_002",
        "category": "documentation_retrieval",
        "question": "What does the company manual say about resolving customs HOLD-DOC exceptions?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Identify required submission of missing invoices or packing lists electronically through customs broker within 48 hours.",
        "priority": "P0"
    },
    {
        "test_id": "DOC_003",
        "category": "documentation_retrieval",
        "question": "Explain the four international customs inspection lanes described in trade documents.",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail Green channel (immediate electronic clearance), Yellow (document review), Orange/Blue (scanning), Red channel (mandatory physical inspection).",
        "priority": "P1"
    },
    {
        "test_id": "DOC_004",
        "category": "documentation_retrieval",
        "question": "Summarize the Dangerous Goods Declaration (DGD) requirements in company documents.",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail shipper declaration with UN number, proper shipping name, class, packing group, 24/7 emergency response contact number.",
        "priority": "P0"
    },
    {
        "test_id": "DOC_005",
        "category": "documentation_retrieval",
        "question": "What is the procedure for calibration of temperature sensors under GDP manual?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Annual three-point NIST-traceable calibration with digital certificate retention for 5 years.",
        "priority": "P1"
    },
    {
        "test_id": "DOC_006",
        "category": "documentation_retrieval",
        "question": "Explain what the customer carriage document says regarding limits of carrier liability.",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain standard carrier liability limits under Montreal Convention (air) and Hague-Visby rules (ocean), advising declared value cargo insurance.",
        "priority": "P1"
    },
    {
        "test_id": "DOC_007",
        "category": "documentation_retrieval",
        "question": "What does the warehouse manual specify about battery charging station safety?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail explosive hydrogen gas ventilation, eyewash stations within 10 meters, and acid-resistant PPE.",
        "priority": "P2"
    },
    {
        "test_id": "DOC_008",
        "category": "documentation_retrieval",
        "question": "Explain the documentation required for European Union Import Control System 2 (ICS2).",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain Entry Summary Declaration (ENS) with 6-digit HS codes required prior to aircraft loading.",
        "priority": "P1"
    },
    {
        "test_id": "DOC_009",
        "category": "documentation_retrieval",
        "question": "What are the rules regarding UN 4G fiberboard box packaging in the dangerous goods manual?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail drop-tested fiberboard specifications, dangerous goods orientation arrows, and UN certification marks.",
        "priority": "P2"
    },
    {
        "test_id": "DOC_010",
        "category": "documentation_retrieval",
        "question": "Summarize the customer shipping contract rules regarding booking cancellations.",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail cancellation cut-offs (24 hours prior to pickup without fee; late cancellation incur $150 haulage fee).",
        "priority": "P1"
    }
]

# -------------------------------------------------------------
# 8. DATABASE AND DATA VALIDATION (15)
# -------------------------------------------------------------
cat8_validation = [
    {
        "test_id": "VAL_001",
        "category": "database_validation",
        "question": "Show shipment details for SHP-10001",
        "required_shipment_id": "SHP-10001",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Validate that returned record has non-null shipment_id, status, origin, destination, and valid date formats.",
        "priority": "P0"
    },
    {
        "test_id": "VAL_002",
        "category": "database_validation",
        "question": "Verify if shipment SHP-10002 has a recorded delay reason.",
        "required_shipment_id": "SHP-10002",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Confirm that delay_reason is populated ('Port congestion at Jebel Ali').",
        "priority": "P0"
    },
    {
        "test_id": "VAL_003",
        "category": "database_validation",
        "question": "Does shipment SHP-10004 have a valid delivered status and completed transit?",
        "required_shipment_id": "SHP-10004",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Verify that status is Delivered and current_location matches destination.",
        "priority": "P0"
    },
    {
        "test_id": "VAL_004",
        "category": "database_validation",
        "question": "Check the customs status field for shipment SHP-10003",
        "required_shipment_id": "SHP-10003",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Verify customs_status contains 'Held - awaiting commercial invoice'.",
        "priority": "P0"
    },
    {
        "test_id": "VAL_005",
        "category": "database_validation",
        "question": "What is the origin and destination of shipment SHP-10006?",
        "required_shipment_id": "SHP-10006",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Verify origin is 'Kolkata, India' and destination is 'Tokyo, Japan'.",
        "priority": "P0"
    },
    {
        "test_id": "VAL_006",
        "category": "database_validation",
        "question": "Verify whether employee EMP-20002 has an active status and valid certification.",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Verify Marco Chowdhury certification 'IATA Dangerous Goods Regulations (DGR Cat 6)' and Active status.",
        "priority": "P1"
    },
    {
        "test_id": "VAL_007",
        "category": "database_validation",
        "question": "Is the estimated delivery date formatted properly for SHP-10008?",
        "required_shipment_id": "SHP-10008",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Verify date '2026-11-24' formats into clean readable date string.",
        "priority": "P1"
    },
    {
        "test_id": "VAL_008",
        "category": "database_validation",
        "question": "Check if shipment SHP-10009 has last_updated timestamp populated.",
        "required_shipment_id": "SHP-10009",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Confirm timestamp '2026-11-12 11:30' is returned.",
        "priority": "P1"
    },
    {
        "test_id": "VAL_009",
        "category": "database_validation",
        "question": "Verify route continuity for shipment SHP-10001",
        "required_shipment_id": "SHP-10001",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Verify route shows 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub'.",
        "priority": "P0"
    },
    {
        "test_id": "VAL_010",
        "category": "database_validation",
        "question": "Does shipment SHP-10010 contain valid customs clearance information?",
        "required_shipment_id": "SHP-10010",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Confirm customs_status reports 'Held - missing packing list'.",
        "priority": "P0"
    },
    {
        "test_id": "VAL_011",
        "category": "database_validation",
        "question": "Validate the data fields of shipment SHP-10011",
        "required_shipment_id": "SHP-10011",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Confirm all mandatory relational attributes are present.",
        "priority": "P1"
    },
    {
        "test_id": "VAL_012",
        "category": "database_validation",
        "question": "Check shipment record SHP-10012 for date inconsistencies.",
        "required_shipment_id": "SHP-10012",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Confirm estimated delivery and last updated dates are valid ISO strings.",
        "priority": "P1"
    },
    {
        "test_id": "VAL_013",
        "category": "database_validation",
        "question": "Verify that shipment SHP-10013 has an assigned origin and destination.",
        "required_shipment_id": "SHP-10013",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Validate non-empty origin and destination strings.",
        "priority": "P1"
    },
    {
        "test_id": "VAL_014",
        "category": "database_validation",
        "question": "Verify employee profile EMP-20003 assigned hub details.",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Confirm Siddharth Jackson assigned to 'Mumbai Air Cargo & JNPT Terminal (India)'.",
        "priority": "P1"
    },
    {
        "test_id": "VAL_015",
        "category": "database_validation",
        "question": "Validate data fields for shipment SHP-10015",
        "required_shipment_id": "SHP-10015",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Ensure status is one of the supported 5 status types.",
        "priority": "P1"
    }
]

# -------------------------------------------------------------
# 9. MULTI-TURN CONVERSATIONS (10 scenarios)
# -------------------------------------------------------------
cat9_multiturn = [
    {
        "test_id": "CONV_001",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "Show me shipment SHP-10001",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Return tracking details for SHP-10001."
            },
            {
                "turn": 2,
                "question": "Where is it right now?",
                "expected_intent": "shipment_location",
                "expected_behavior": "Resolve pronoun 'it' to SHP-10001 and return Dubai Hub, UAE."
            },
            {
                "turn": 3,
                "question": "When will it arrive at destination?",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Resolve 'it' to SHP-10001 and return estimated delivery 2026-11-20."
            }
        ],
        "priority": "P0"
    },
    {
        "test_id": "CONV_002",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "Check status of package SHP-10002",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Return status Delayed."
            },
            {
                "turn": 2,
                "question": "Why is it delayed?",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Resolve pronoun to SHP-10002 and return delay reason: Port congestion at Jebel Ali."
            },
            {
                "turn": 3,
                "question": "What is its destination?",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Return Dubai, UAE."
            }
        ],
        "priority": "P0"
    },
    {
        "test_id": "CONV_003",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "Look up shipment SHP-10003",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Return status On Hold - Customs."
            },
            {
                "turn": 2,
                "question": "What documents are required to clear this hold?",
                "expected_intent": "general_knowledge",
                "expected_behavior": "Identify that commercial invoice is missing and provide submission instructions."
            }
        ],
        "priority": "P0"
    },
    {
        "test_id": "CONV_004",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "Tell me about shipment SHP-10004",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Return status Delivered."
            },
            {
                "turn": 2,
                "question": "Has it been signed for?",
                "expected_intent": "general_knowledge",
                "expected_behavior": "Confirm delivery status and explain Proof of Delivery is recorded upon final delivery."
            }
        ],
        "priority": "P1"
    },
    {
        "test_id": "CONV_005",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "Where is SHP-10005 heading?",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Return destination Sydney, Australia."
            },
            {
                "turn": 2,
                "question": "Is it out for delivery?",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Confirm status is Out for Delivery."
            }
        ],
        "priority": "P1"
    },
    {
        "test_id": "CONV_006",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "Track order SHP-10007",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Return status Delayed."
            },
            {
                "turn": 2,
                "question": "Where is it stuck?",
                "expected_intent": "shipment_location",
                "expected_behavior": "Return current location Mumbai Hub, India."
            },
            {
                "turn": 3,
                "question": "Now check SHP-10008 instead",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Switch reference to SHP-10008 and return status In Transit."
            },
            {
                "turn": 4,
                "question": "Where is this one?",
                "expected_intent": "shipment_location",
                "expected_behavior": "Return current location London Heathrow Hub, UK for SHP-10008."
            }
        ],
        "priority": "P0"
    },
    {
        "test_id": "CONV_007",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "Hello, how can you help me?",
                "expected_intent": "general_conversation",
                "expected_behavior": "Return greeting and list logistics capabilities."
            },
            {
                "turn": 2,
                "question": "Can you track SHP-10009?",
                "expected_intent": "shipment_tracking",
                "expected_behavior": "Return details for SHP-10009."
            }
        ],
        "priority": "P1"
    },
    {
        "test_id": "CONV_008",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "What is the policy for cold-chain pharmaceutical shipments?",
                "expected_intent": "general_knowledge",
                "expected_behavior": "Explain CC-POL-9921 guidelines."
            },
            {
                "turn": 2,
                "question": "What happens if temperatures rise above 8 degrees?",
                "expected_intent": "general_knowledge",
                "expected_behavior": "Explain excursion protocol and quarantine."
            }
        ],
        "priority": "P1"
    },
    {
        "test_id": "CONV_009",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "Look up employee EMP-20001",
                "expected_intent": "employee_lookup",
                "expected_behavior": "Return Stella Davis profile."
            },
            {
                "turn": 2,
                "question": "What shift does she work?",
                "expected_intent": "employee_lookup",
                "expected_behavior": "Return Swing Shift (14:00 - 22:30)."
            }
        ],
        "priority": "P1"
    },
    {
        "test_id": "CONV_010",
        "category": "multi_turn_conversations",
        "turns": [
            {
                "turn": 1,
                "question": "What are your cargo weight limits?",
                "expected_intent": "direct_definition",
                "expected_behavior": "Return ISO container specifications."
            },
            {
                "turn": 2,
                "question": "And what is demurrage?",
                "expected_intent": "direct_definition",
                "expected_behavior": "Explain port container terminal fee without context collision."
            }
        ],
        "priority": "P1"
    }
]

# -------------------------------------------------------------
# 10. COMPLEX AND LOGICAL QUESTIONS (10)
# -------------------------------------------------------------
cat10_logical = [
    {
        "test_id": "LOGIC_001",
        "category": "complex_logical",
        "question": "Compare the status, location, and destination of shipment SHP-10001 and SHP-10002.",
        "expected_intent": "complex_comparison",
        "expected_source": "shipment_database",
        "expected_behavior": "Compare SHP-10001 (In Transit, Dubai Hub, destined for London) with SHP-10002 (Delayed, Jebel Ali Port, destined for Dubai).",
        "priority": "P1"
    },
    {
        "test_id": "LOGIC_002",
        "category": "complex_logical",
        "question": "Based on the tracking history of SHP-10003, what specific action must the shipper take to resume transit?",
        "required_shipment_id": "SHP-10003",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Reason that customs hold is due to missing commercial invoice and advise submitting invoice to JFK customs broker.",
        "priority": "P0"
    },
    {
        "test_id": "LOGIC_003",
        "category": "complex_logical",
        "question": "Explain why air freight would be preferred over ocean freight for pharmaceutical vaccines under policy CC-POL-9921.",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Reason about transit speed (1-5 days vs 20-40 days), strict temperature stability, active telemetry, and reduced excursion risk.",
        "priority": "P1"
    },
    {
        "test_id": "LOGIC_004",
        "category": "complex_logical",
        "question": "What is the relationship between customs status and shipment status when a consignment is held at gateway?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain that regulatory hold prevents departure scan, causing shipment status to transition into 'On Hold - Customs'.",
        "priority": "P1"
    },
    {
        "test_id": "LOGIC_005",
        "category": "complex_logical",
        "question": "If a shipment route is Mumbai -> Dubai -> London, and current location is Dubai Hub, what milestones are completed and pending?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Deduce: Mumbai departure completed, Dubai transit in progress, London arrival and final delivery pending.",
        "priority": "P0"
    },
    {
        "test_id": "LOGIC_006",
        "category": "complex_logical",
        "question": "Compare the cost and risk transfer points of FOB vs CIF for an ocean shipment departing Singapore.",
        "expected_intent": "direct_definition",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain that both transfer risk once cargo passes ship's rail at Singapore, but CIF requires seller to pay maritime freight and insurance.",
        "priority": "P1"
    },
    {
        "test_id": "LOGIC_007",
        "category": "complex_logical",
        "question": "Analyze why shipment SHP-10007 has an estimated delivery later than SHP-10001 despite similar booking dates.",
        "expected_intent": "complex_comparison",
        "expected_source": "shipment_database",
        "expected_behavior": "Explain that SHP-10007 experienced weather disruption at Mumbai airport extending transit time to 2026-11-28.",
        "priority": "P1"
    },
    {
        "test_id": "LOGIC_008",
        "category": "complex_logical",
        "question": "What happens if a consignee requests delivery to a different country while cargo is in transit?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain cross-border re-manifesting requires cancelling original export customs declaration, re-filing import duties, and rerouting linehaul.",
        "priority": "P2"
    },
    {
        "test_id": "LOGIC_009",
        "category": "complex_logical",
        "question": "How do weight and dimensional volume interact to determine whether actual or volumetric weight is billed?",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Explain chargeable weight is always the greater of actual gross mass vs volumetric (dimensional) mass.",
        "priority": "P1"
    },
    {
        "test_id": "LOGIC_010",
        "category": "complex_logical",
        "question": "Explain the operational dependencies between LPN barcode generation, dock receiving, and sortation bay assignment.",
        "expected_intent": "general_knowledge",
        "expected_source": "knowledge_base",
        "expected_behavior": "Detail that LPN uniquely tracks pallet load, allowing automated sorters to scan and route pallets directly to scheduled outbound trailer bays.",
        "priority": "P2"
    }
]

# -------------------------------------------------------------
# 11. AMBIGUOUS AND INCOMPLETE QUESTIONS (10)
# -------------------------------------------------------------
cat11_ambiguous = [
    {
        "test_id": "AMB_001",
        "category": "ambiguous_questions",
        "question": "Where is my shipment?",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Politely ask the user to provide their 5-digit Shipment ID (e.g., SHP-10001) instead of inventing a status.",
        "priority": "P0"
    },
    {
        "test_id": "AMB_002",
        "category": "ambiguous_questions",
        "question": "When will it arrive?",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Request tracking number or shipment ID to check estimated delivery.",
        "priority": "P0"
    },
    {
        "test_id": "AMB_003",
        "category": "ambiguous_questions",
        "question": "Track order",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Prompt user for shipment reference number.",
        "priority": "P0"
    },
    {
        "test_id": "AMB_004",
        "category": "ambiguous_questions",
        "question": "Why is it late?",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Ask which shipment ID the user is referring to.",
        "priority": "P1"
    },
    {
        "test_id": "AMB_005",
        "category": "ambiguous_questions",
        "question": "Status check",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Prompt user to provide their shipment ID.",
        "priority": "P1"
    },
    {
        "test_id": "AMB_006",
        "category": "ambiguous_questions",
        "question": "Can you check my employee profile?",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Request employee ID (e.g., EMP-20001).",
        "priority": "P1"
    },
    {
        "test_id": "AMB_007",
        "category": "ambiguous_questions",
        "question": "What is the fee?",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Ask whether user refers to demurrage, detention, freight cancellation, or re-delivery fees.",
        "priority": "P2"
    },
    {
        "test_id": "AMB_008",
        "category": "ambiguous_questions",
        "question": "Is it cleared?",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Ask for the shipment number to verify customs clearance status.",
        "priority": "P1"
    },
    {
        "test_id": "AMB_009",
        "category": "ambiguous_questions",
        "question": "Where is the hub located?",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Ask which gateway hub (Singapore, Dubai, Rotterdam, Frankfurt, etc.) the user is inquiring about.",
        "priority": "P2"
    },
    {
        "test_id": "AMB_010",
        "category": "ambiguous_questions",
        "question": "Tell me about delivery",
        "expected_intent": "clarification_request",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Provide overview of delivery operations and offer to track a specific shipment or explain delivery policies.",
        "priority": "P2"
    }
]

# -------------------------------------------------------------
# 12. NEGATIVE AND EDGE-CASE QUESTIONS (10)
# -------------------------------------------------------------
cat12_edge_cases = [
    {
        "test_id": "EDGE_001",
        "category": "negative_edge_cases",
        "question": "Track shipment SHP-99999",
        "required_shipment_id": "SHP-99999",
        "expected_intent": "shipment_tracking",
        "expected_source": "shipment_database",
        "expected_behavior": "Return user-friendly 'Shipment Not Found' notice advising user to verify the ID.",
        "priority": "P0"
    },
    {
        "test_id": "EDGE_002",
        "category": "negative_edge_cases",
        "question": "Track shipment INVALID-ID-XYZ",
        "expected_intent": "shipment_tracking",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Inform user that shipment IDs follow the pattern SHP-10001 (SHP with 5 digits).",
        "priority": "P0"
    },
    {
        "test_id": "EDGE_003",
        "category": "negative_edge_cases",
        "question": "   ",
        "expected_intent": "error_handling",
        "expected_source": "api_validation",
        "expected_behavior": "Reject empty/whitespace query with 400 Bad Request or validation message.",
        "priority": "P0"
    },
    {
        "test_id": "EDGE_004",
        "category": "negative_edge_cases",
        "question": "What is the weather on Mars tomorrow?",
        "expected_intent": "unsupported_offtopic",
        "expected_source": "classifier",
        "expected_behavior": "Politely decline off-topic query and restate logistics support capabilities.",
        "priority": "P1"
    },
    {
        "test_id": "EDGE_005",
        "category": "negative_edge_cases",
        "question": "Look up employee EMP-99999",
        "expected_intent": "employee_lookup",
        "expected_source": "employee_database",
        "expected_behavior": "Return polite notice that employee EMP-99999 is not found in personnel directory.",
        "priority": "P0"
    },
    {
        "test_id": "EDGE_006",
        "category": "negative_edge_cases",
        "question": "Can you write a poem about quantum computers baking cookies?",
        "expected_intent": "unsupported_offtopic",
        "expected_source": "classifier",
        "expected_behavior": "Decline off-topic request and refocus on logistics operations.",
        "priority": "P1"
    },
    {
        "test_id": "EDGE_007",
        "category": "negative_edge_cases",
        "question": "DROP TABLE shipments; SELECT * FROM users;",
        "expected_intent": "security_sanitization",
        "expected_source": "classifier",
        "expected_behavior": "Safely sanitize SQL injection attempt and treat as invalid query or standard lookup without error.",
        "priority": "P0"
    },
    {
        "test_id": "EDGE_008",
        "category": "negative_edge_cases",
        "question": "<script>alert('xss vulnerability')</script> Track SHP-10001",
        "expected_intent": "security_sanitization",
        "expected_source": "chatbot_logic",
        "expected_behavior": "Properly HTML/script escape input and safely answer shipment tracking for SHP-10001.",
        "priority": "P0"
    },
    {
        "test_id": "EDGE_009",
        "category": "negative_edge_cases",
        "question": "A" * 3000,
        "expected_intent": "error_handling",
        "expected_source": "api_validation",
        "expected_behavior": "Reject oversized query exceeding 2000 character limit with HTTP 413 or QueryTooLongError.",
        "priority": "P1"
    },
    {
        "test_id": "EDGE_010",
        "category": "negative_edge_cases",
        "question": "What is the status of SHP-10001? Also tell me about EMP-20001 and FOB vs CIF shipping terms.",
        "expected_intent": "complex_query",
        "expected_source": "orchestrator",
        "expected_behavior": "Handle compound multi-part query by prioritizing shipment tracking and providing comprehensive answers.",
        "priority": "P1"
    }
]

# Write out each category to tests/question_bank/
files_map = {
    "general_logistics.json": cat1_general,
    "shipment_tracking.json": cat2_tracking,
    "delivery_management.json": cat3_delivery,
    "shipment_delays.json": cat4_delays,
    "company_policies.json": cat5_policies,
    "employee_assistance.json": cat6_employee,
    "documentation.json": cat7_docs,
    "data_validation.json": cat8_validation,
    "multi_turn_conversations.json": cat9_multiturn,
    "logical_questions.json": cat10_logical,
    "ambiguous_questions.json": cat11_ambiguous,
    "edge_cases.json": cat12_edge_cases,
}

total_q = 0
for fname, data in files_map.items():
    p = QB_DIR / fname
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    # Count questions
    count = len(data)
    if fname == "multi_turn_conversations.json":
        turn_count = sum(len(d.get("turns", [])) for d in data)
        print(f"Created {fname:32s} -> {count} scenarios ({turn_count} turns)")
        total_q += turn_count
    else:
        print(f"Created {fname:32s} -> {count} questions")
        total_q += count

print("=" * 60)
print(f"TOTAL TEST QUESTIONS IN QUESTION BANK: {total_q}")
print(f"Question bank generated at: {QB_DIR}")
conn.close()
