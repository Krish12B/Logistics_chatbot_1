"""Generator script for FleetHarbor Logistics large dataset, knowledge base, SQLite, and Supabase seed.
Generates:
  1. 6 authoritative knowledge base guides in knowledge_base/*.txt
  2. 250+ shipment records in data/processed/shipments.csv, data/raw/shipments.csv, and data/raw/shipments.db
  3. Additional CSVs in data/generated/:
     - company_profile.csv
     - customer_accounts.csv
     - employees_roster.csv
     - global_hubs.csv
     - policies_rules.csv
  4. Augments data/knowledge_base/kb_long.csv with new structured rows
  5. Generates data/sql/supabase_full_seed.sql
"""
from __future__ import annotations

import csv
import json
import os
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_KB_DIR = _ROOT / "knowledge_base"
_DATA_DIR = _ROOT / "data"
_GENERATED_DIR = _DATA_DIR / "generated"
_PROCESSED_DIR = _DATA_DIR / "processed"
_RAW_DIR = _DATA_DIR / "raw"
_SQL_DIR = _DATA_DIR / "sql"
_DATA_KB_DIR = _DATA_DIR / "knowledge_base"

for d in [_KB_DIR, _GENERATED_DIR, _PROCESSED_DIR, _RAW_DIR, _SQL_DIR, _DATA_KB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 1. WRITE DETAILED KNOWLEDGE BASE TEXT DOCUMENTS
# ==============================================================================

DOC_COMPANY = """# FleetHarbor Logistics • Comprehensive Company Profile & Global Services Manual
Document Reference: DOC-FLEET-CO-2026
Classification: Public / Customer & Employee Reference
Last Revised: 20 November 2026

## 1. Executive Summary & Company History
FleetHarbor AI Logistics (operating globally as FleetHarbor Maritime & Freight Inc.) is a premier multi-modal third-party logistics (3PL) and supply chain technology carrier founded in 2011. Operating dual corporate headquarters in Singapore (Asia-Pacific Operations) and Rotterdam (European & Transatlantic Operations), FleetHarbor connects over 140 nations through 280 strategic logistics facilities, 45 automated regional sorting hubs, and a unified digital freight platform.

Our corporate mission is to deliver zero-defect logistics intelligence, connecting shippers, carriers, customs authorities, and end-consignees with complete end-to-end transparency, audited temperature control, and automated clearance workflows.

## 2. Core Service Offerings & Transport Modes
FleetHarbor provides six core logistics service channels:

### A. Ocean Freight Services (FCL & LCL)
- Full Container Load (FCL): Direct maritime shipping using standard 20ft, 40ft, 40ft High Cube, flat rack, and open-top containers across major carrier alliances.
- Less than Container Load (LCL): Consolidated weekly groupage sailings between major global trade lanes with guaranteed container stripping at destination container freight stations (CFS).
- Reefer Maritime Transport: Active temperature-controlled container transport for agricultural and pharmaceutical consignments with 24/7 telematics monitoring.

### B. Global Air Freight & Express Cargo
- FleetHarbor Air Priority (24-48 Hours): Guaranteed space on scheduled widebody flights with priority apron transfer and express customs processing.
- Standard Air Freight (3-5 Business Days): Cost-effective consolidated air cargo for high-density, general industrial freight.
- Air Charter Services: Dedicated full-charter Boeing 777F and 747-8F freighters for oversized project cargo, humanitarian emergencies, and urgent automotive factory-line disruptions.

### C. Road Linehaul & Intermodal Rail
- Domestic & Cross-Border Linehaul: Modern fleet of Euro-6 and Tier-4 compliant semi-trucks, double-drop trailers, and insulated box-trailers.
- Intermodal Rail Corridors: High-efficiency rail transport connecting inland container depots (ICDs) directly to deep-water maritime ports in North America, Europe, and India.
- Last-Mile Express: Dedicated courier fleet for business delivery with photographic Proof of Delivery (POD) and electronic signature capture.

### D. Cold-Chain Life Sciences & Healthcare Logistics
- GDP-certified pharmaceutical storage and transport operating under policy code CC-POL-9921.
- Validated temperature regimes: Cryogenic/Dry Ice (-70°C), Deep Frozen (-20°C), Refrigerated (2°C to 8°C), and Controlled Room Temperature (15°C to 25°C).
- Real-time IoT continuous data logging with cellular, satellite, and GPS position telemetry.

### E. Customs Brokerage & Trade Compliance Advisory
- Dedicated licensed in-house customs brokers operating across 60+ global customs jurisdictions.
- Direct automated data interchange with US CBP (ACE), EU Customs (ICS2), UK HMRC (CDS), and Indian Customs (ICEGATE).
- Tariff classification (HS codes), binding tariff rulings, and trade compliance audits.

### F. Warehousing, 3PL Fulfillment & Value-Added Services
- Over 12 million square feet of Class-A warehousing across North America, Europe, Asia, and the Middle East.
- Capabilities include bonded warehousing, pick-and-pack fulfillment, kitting, cross-docking, and return logistics (reverse supply chain).

## 3. Global Infrastructure & Primary Gateway Hubs
FleetHarbor operates primary gateway facilities at:
- Dubai Logistics City Hub (UAE): Transshipment crossroads connecting Europe, Africa, and East Asia.
- Singapore Changi Airfreight Centre (Singapore): Southeast Asian pharma and high-tech electronics hub.
- Rotterdam Maasvlakte Gateway (Netherlands): Deep-water maritime port and European intermodal rail terminal.
- Frankfurt CargoCity South (Germany): Central European air freight consolidation and cold-storage center.
- London Heathrow Cargo Centre (UK): Air cargo gateway for transatlantic and Asian freight.
- Los Angeles Long Beach Intermodal Terminal (USA): Transpacific maritime gateway to North American rail networks.
- Shanghai Pudong Logistics Park (China): East Asian manufacturing export consolidation center.
- Mumbai Air Cargo Complex & JNPT Port (India): South Asian industrial and pharmaceutical export hub.
- Sydney Mascot Cargo Depot (Australia): Australasian distribution center.

## 4. Sustainability & Green Logistics Commitment
FleetHarbor is pledged to achieve net-zero carbon operations by 2040:
- Sustainable Aviation Fuel (SAF) partnership covering 15% of annual air freight routes.
- Electric and hydrogen fuel cell last-mile delivery fleet deployed in 30 major urban centers.
- Carbon offset tracking and verified emissions reporting provided free of charge on all commercial invoices.

## 5. Contact & Support Escalation Directory
- Global Customer Service: support@fleetharbor.com (24/7/365 coverage)
- Operations Escalation Hotline: +1 (800) 555-HARBOR / +44 20 7946 0991
- Customs Emergency Desk: customs-clearing@fleetharbor.com
- Pharma & Cold-Chain Operations: pharma-care@fleetharbor.com
- Corporate Headquarters Singapore: 12 Marina Boulevard, Marina Bay Financial Centre, Singapore 018982
- European Headquarters Rotterdam: Wilhelminakade 179, 3072 AP Rotterdam, Netherlands
"""

DOC_CUSTOMER = """# FleetHarbor Logistics • Customer Shipping Rules, Service Level Agreements & Terms of Carriage
Document Reference: DOC-FLEET-CUST-2026
Classification: Public / Customer Reference
Last Revised: 20 November 2026

## 1. General Carriage Terms & Scope
These Terms of Carriage apply to all transport, warehousing, customs brokerage, and logistics services arranged by FleetHarbor Logistics. By booking a consignment or tendering cargo, the customer (shipper, consignee, or agent) agrees to these terms.

## 2. Customer Account Tiers & Service Level Agreements (SLAs)
FleetHarbor operates three account tiers:
1. Enterprise Corporate:
   - Dedicated Account Manager and 24/7 logistics desk.
   - Guaranteed space allocation on core maritime and air lanes.
   - Customized API integration for continuous tracking webhook feeds.
   - Standard credit terms: Net 30 or Net 60 days.
2. Healthcare & Pharma Priority:
   - Mandatory GDP compliance under policy CC-POL-9921.
   - Pre-conditioned reefer containers and continuous temperature alerts.
   - Immediate 2-hour escalation on any sensor excursion.
3. Standard Commercial:
   - Access to FleetHarbor web portal and automated REST API.
   - Standard transit schedules.
   - Credit terms: Net 15 days or prepayment.

## 3. Booking, Cancellation & Amendment Procedures
- Booking Cut-Off Times:
  - Air Freight: Minimum 8 hours prior to scheduled flight departure.
  - Ocean FCL: Minimum 48 hours prior to vessel container port cut-off.
  - Ocean LCL: Minimum 24 hours prior to CFS cargo delivery deadline.
  - Road Linehaul: Minimum 4 hours prior to scheduled dock pickup.
- Booking Cancellations:
  - Cancellations received before cargo dispatch: No cancellation penalty.
  - Cancellations received after container placement or vehicle dispatch: Subject to empty haulage charges ($150 - $450 depending on zone).
- In-Transit Rerouting:
  - Shippers may request in-transit destination diversion via the portal or API prior to cargo arrival at the final delivery hub.
  - Rerouting administration fee: $75 plus difference in linehaul freight rates.

## 4. Demurrage, Detention & Free Time Allowances
To maintain equipment velocity and prevent port terminal congestion, strict free time rules apply:
- Ocean Import FCL Free Time: 5 calendar days from vessel discharge.
- Ocean Export FCL Free Time: 7 calendar days prior to vessel departure.
- Demurrage Daily Rates (after free time expiry):
  - Standard Dry Container (20ft / 40ft): $85 per day for Days 1-5; $150 per day thereafter.
  - Reefer Temperature-Controlled Container: $180 per day for Days 1-3; $320 per day thereafter.
- Air Cargo Free Time: 48 hours from airline airway bill availability notice. Free time excludes national customs gazetted holidays.

## 5. Freight Loss, Damage & Claims Resolution
- Notification Windows:
  - Obvious External Damage: Must be noted on the Proof of Delivery (POD) at the time of delivery. Written notice within 3 calendar days.
  - Concealed Damage (internal): Written claim notice within 14 calendar days of delivery.
  - Non-Delivery / Loss: Written notice within 30 calendar days from the scheduled estimated delivery date.
- Required Claim Documents:
  - Formal claim statement specifying claimed amount.
  - Copy of signed Waybill / Bill of Lading with delivery exception notation.
  - Original commercial supplier invoice proving cargo cost value.
  - Photographic evidence of outer packaging, inner packaging, and damaged merchandise.
  - Certified salvage assessment or destruction certificate.
- Settlement SLA: Complete claims evaluated and settled within 21 business days of file completion.

## 6. Liability Limits & Marine Cargo Insurance
- Standard Carrier Liability:
  - Air Freight: 22 SDR (Special Drawing Rights) per kilogram pursuant to the Montreal Convention.
  - Ocean Freight: 666.67 SDR per package or 2 SDR per kilogram under the Hague-Visby Rules.
  - Domestic Road: $2.00 per pound unless higher declared value is contracted.
- All-Risk Cargo Insurance: Shippers are strongly advised to purchase FleetHarbor All-Risk Marine Insurance, covering 110% of CIF invoice value against accidental physical loss or damage from external causes.
"""

DOC_EMPLOYEE = """# FleetHarbor Logistics • Internal Employee Operations Handbook & Warehouse SOP
Document Reference: DOC-FLEET-EMP-2026
Classification: Internal Operations Manual / Staff Reference
Last Revised: 20 November 2026

## 1. Safety Protocols & Personal Protective Equipment (PPE)
All FleetHarbor operations personnel, dock workers, and forklift operators must strictly adhere to Zero-Harm Safety Standards:
- Mandatory PPE in all warehouse, dock, and container yard areas:
  - Steel-toe certified safety shoes (EN ISO 20345 / ASTM F2413).
  - High-visibility class 2 or class 3 fluorescent vest.
  - Protective hard hats when operating under overhead racking or container cranes.
  - Protective gloves and safety glasses during hazmat handling or pallet strapping.
- Forklift & Material Handling Equipment (MHE):
  - Maximum warehouse aisle speed: 8 km/h (5 mph).
  - Daily pre-shift equipment checklist mandatory before turning on any forklift or reach truck.
  - Pedestrian walkway separation: Maintain a minimum 3-meter safety bubble from moving machinery.

## 2. Inbound Dock Receiving & Verification Workflow
Step 1: Driver Check-In & Security Inspection
- Confirm driver identity against dispatch manifest and verify carrier seal numbers on trailer doors before breaking seals.
- If seal is broken or does not match manifest, DO NOT open doors. Immediately notify the Dock Supervisor and Security Desk.

Step 2: Unloading & Barcode Scanning
- Scan master Bill of Lading / Air Waybill barcode into FleetHarbor WMS.
- Inspect outer pallets for transit damage, tilting, crushing, or water ingress.
- Generate and affix internal FleetHarbor License Plate Number (LPN) tracking barcodes to every received pallet.

Step 3: Staging & Temperature Verification
- Ambient Cargo: Move to designated staging lane within 45 minutes of receipt.
- Cold-Chain Cargo: Move into temperature-controlled pre-cool dock within 15 minutes. Check internal data logger display and log temperature into WMS.

## 3. Hazmat & Dangerous Goods Handling SOP
- Segregation: Incompatible chemicals (e.g., Class 3 Flammables and Class 5.1 Oxidizers) must never be stored in adjacent rack bays. Maintain minimum 6-meter segregation distance or fire-rated barrier wall.
- Spill Kit Deployment: Every dock station is equipped with a universal chemical spill kit. In the event of a leak > 5 liters, activate facility emergency response and evacuate downwind personnel.

## 4. Dispatch, Linehaul Loading & Weight Distribution
- Axle Weight Compliance: Forklift operators must distribute heavy pallets evenly along trailer bed to ensure steering and drive axle weight limits are never breached.
- Pallet Bracing: Use certified load bars, ratchet straps (minimum 2,500 kg rating), and inflatable dunnage bags in trailer gaps to prevent cargo movement during transit.
- Driver Sign-Out: Driver receives printed paper manifest, signed equipment interchange receipt (EIR), and digital dispatch confirmation on mobile terminal.

## 5. Shift Handover & Escalation Protocols
- Shift Handover Log: Operations supervisors must conduct a 15-minute face-to-face handover at shift change (06:00, 14:00, 22:00), reviewing:
  - Unresolved tracking exceptions or customs holds.
  - Reefer units undergoing active temperature observation.
  - High-value cargo stored in high-security cage.
- Escalation Matrix:
  - Level 1 (Immediate): Warehouse Supervisor (resolves dock delays, damaged pallet repackaging).
  - Level 2 (Within 2 Hours): Terminal Operations Manager (resolves equipment failure, driver shortages).
  - Level 3 (Within 4 Hours): Regional Operations Director & VP Quality (handles catastrophic incidents, structural loss).
"""

DOC_CUSTOMS = """# FleetHarbor Logistics • International Customs Clearance, Tariffs & Cross-Border Compliance Guide
Document Reference: DOC-FLEET-CUSTM-2026
Classification: Public / Compliance Advisory
Last Revised: 20 November 2026

## 1. Statutory International Clearance Documentation
Every cross-border commercial shipment processed by FleetHarbor Customs Brokerage must be accompanied by accurate documentation:
1. Commercial Invoice:
   - Full legal names and addresses of Seller (Exporter) and Buyer (Importer).
   - Detailed product description (generic names like "parts" or "samples" are legally rejected).
   - 6-digit to 10-digit Harmonized System (HS) Tariff Code.
   - Declared unit value, total invoice value, and commercial trade currency (USD, EUR, GBP, etc.).
   - Applicable Incoterms 2020 rules (e.g. FOB Mumbai, CIF Rotterdam, DDP London).
   - True Country of Origin for each line item.
2. Packing List:
   - Exact itemization of packages, box dimensions, gross weight, net weight, and packaging type.
   - Identification of package marks, numbers, and container seal IDs.
3. Transport Document:
   - Original Ocean Bill of Lading (OBL), Express Sea Waybill, or Master Air Waybill (MAWB).
4. Preferential Certificate of Origin:
   - When claiming duty reduction under bilateral or multilateral Free Trade Agreements (e.g. USMCA, EU-UK TCA, ASEAN FTA).

## 2. Global Customs Inspection Lanes & Procedures
Customs authorities across the globe categorize consignments into three processing channels:
- Green Channel (Immediate Clearance): Automated electronic manifest assessment with no physical inspection. Release issued within 1-4 hours of vessel/flight arrival.
- Yellow Channel (Documentary Audit): Customs officer audits valuation, HS classification, licenses, or origin certificates. Clearance turnaround: 12-24 hours.
- Red Channel (Physical & X-Ray Examination): Container or cargo is transferred to customs exam station for container destuffing, non-intrusive imaging, and physical commodity sampling. Clearance turnaround: 48-72 hours.

## 3. Resolving Customs Holds & Exception Management
When a shipment is marked "On Hold - Customs", FleetHarbor's Automated Customs Interface flags the specific hold code:
- HOLD-DOC: Documentation Discrepancy. Resolution: Customer must provide amended commercial invoice or packing list within 24 hours.
- HOLD-VAL: Valuation Review. Resolution: Importer must provide commercial purchase order, manufacturer payment proof, or catalog price verification.
- HOLD-PGA: Partner Government Agency Review (e.g. US FDA, EU Health Authority, UK DEFRA, Indian FSSAI). Resolution: Specialized product registration filings, laboratory batch certificates, or import permit validation.
- HOLD-PHYS: Physical Customs Inspection. Resolution: FleetHarbor customs runner attends examination station to oversee cargo unpacking and repacking.

## 4. Key Regional Customs Frameworks
- United States (US CBP): ACE automated portal, ISF (10+2) filing required 24 hours prior to ocean loading, Section 321 de minimis limit ($800).
- European Union: UCC framework, Import Control System 2 (ICS2) safety and security filing, IOSS for e-commerce imports < €150.
- United Kingdom (HMRC): Customs Declaration Service (CDS), GVMS (Goods Vehicle Movement Service) for cross-Channel roll-on/roll-off freight.
- India (CBIC / ICEGATE): Mandatory Bill of Entry filing, IGST valuation, faceless assessment processing.
"""

DOC_COLD_CHAIN = """# FleetHarbor Logistics • Cold-Chain Pharmaceutical & GDP Temperature-Controlled Operations Manual
Document Reference: DOC-FLEET-COLD-2026
Classification: Healthcare Compliance Reference
Last Revised: 20 November 2026

## 1. Compliance Mandates & Policy CC-POL-9921
All temperature-sensitive pharmaceutical, biological, vaccine, and clinical trial shipments managed by FleetHarbor Life Sciences are governed by Policy Code CC-POL-9921. This policy mandates full compliance with:
- World Health Organization (WHO) Good Distribution Practices (GDP) Technical Report Series No. 957.
- European Commission Guidelines on GDP of Medicinal Products (2013/C 343/01).
- United States Pharmacopeia (USP) <1079> Good Storage and Shipping Practices.

## 2. Defined Temperature Operating Regimes
FleetHarbor provides certified temperature control across four defined operating ranges:
1. Deep Cryogenic & Dry Ice (-70°C to -80°C):
   - Used for mRNA vaccines, cell therapies, and genetic materials.
   - Packaged in certified VIP (Vacuum Insulated Panel) dry ice shippers with monitored sublimation rates (standard hold time: 120-168 hours).
2. Frozen Regime (-20°C to -10°C):
   - Used for specialized plasma, viral vectors, and frozen active pharmaceutical ingredients (APIs).
3. Refrigerated Cold-Chain (+2°C to +8°C):
   - Primary biopharmaceutical standard for monoclonal antibodies, insulin, and injectable biologics.
   - Strictly prohibited from freezing; requires calibrated phase-change material (PCM) coolants.
4. Controlled Room Temperature / Ambient (+15°C to +25°C):
   - Required for finished pharmaceutical tablets, medical devices, and diagnostics vulnerable to extreme hot or cold climate swings.

## 3. Real-Time Telematics, Calibration & Data Logging
- Active Telemetry Trackers: Every cold-chain shipment carries a calibrated NIST-traceable cellular/satellite tracker reporting:
  - Internal cargo temperature (±0.1°C precision).
  - Ambient outside temperature.
  - Real-time GPS location and geofence triggers.
  - Shock, tilt, and box lid opening (ambient light sensor).
- Data Sampling Rate: Standard logging interval is every 10 minutes during transit and every 2 minutes when temperature deviates within 1.0°C of critical limits.

## 4. Temperature Excursion Management Protocol
An excursion is defined as any verified temperature reading outside the validated specification. When an excursion occurs:
- Immediate Quarantine: The shipment is tagged as "Under Investigation" in the tracking portal. Warehouse staff move goods into emergency backup cold rooms (+4°C or -20°C).
- Quality Assurance Notification: FleetHarbor Healthcare QA team and the shipper are notified via automated emergency webhook and phone dispatch within 30 minutes.
- Investigation & Root-Cause Analysis (RCA): FleetHarbor compiles an Excursion RCA dossier within 24 hours, evaluating Mean Kinetic Temperature (MKT), duration of deviation, and sensor calibration certificates for pharmaceutical QA release.
"""

DOC_HAZMAT = """# FleetHarbor Logistics • Dangerous Goods, Hazardous Materials & Industrial Packaging Standards
Document Reference: DOC-FLEET-HAZ-2026
Classification: Dangerous Goods Compliance Reference
Last Revised: 20 November 2026

## 1. Regulatory Authority & Dangerous Goods Classes
Transport of dangerous goods is conducted under strict adherence to IATA Dangerous Goods Regulations (DGR) for air transport, the International Maritime Dangerous Goods (IMDG) Code for ocean freight, and ADR regulations for European road transit.

FleetHarbor accepts and handles Dangerous Goods in Classes 2 through 9:
- Class 2: Gases (Flammable, Non-Flammable, Toxic - e.g. compressed nitrogen, argon, propane).
- Class 3: Flammable Liquids (e.g. paints, solvents, adhesives, ethanol solutions).
- Class 4: Flammable Solids, Spontaneously Combustible & Dangerous When Wet substances.
- Class 5: Oxidizing Substances (Class 5.1) and Organic Peroxides (Class 5.2).
- Class 6: Toxic Substances (Class 6.1) and Infectious Substances (Class 6.2 - UN2814/UN2900).
- Class 8: Corrosive Substances (Acids and Alkalis - UN1789, UN1824).
- Class 9: Miscellaneous Dangerous Goods (including lithium batteries UN3480, UN3481, UN3090, UN3091, environmentally hazardous substances, dry ice UN1845).
Note: Class 1 Explosives and Class 7 Radioactive Materials are subject to specialized government permitting and restricted commercial charter.

## 2. Lithium Battery Transport Requirements
Lithium-ion and lithium-metal batteries represent the highest-volume regulated commodity in modern supply chains:
- State of Charge (SoC) Limit: Lithium-ion batteries (UN3480) shipped as standalone cargo via air must be tendered at a State of Charge not exceeding 30% of rated capacity.
- Cargo Aircraft Only (CAO): Standalone lithium batteries (UN3480 / UN3090) are strictly forbidden on passenger aircraft and must carry the CAO orange diamond label.
- UN Testing Requirements: All battery types must have successfully completed UN Manual of Tests and Criteria Part III, Subsection 38.3 (UN 38.3 test summary report required prior to booking).

## 3. UN-Certified Packaging & Marking Requirements
- Packaging Performance Standards: Dangerous goods must be packed in UN-certified packaging displaying official UN specification codes (e.g. `UN 4G/Y145/S/26/USA/...`).
- Outer Markings:
  - Applicable Hazard Diamond Warning Labels (minimum 100mm x 100mm).
  - Proper Shipping Name (PSN) in English.
  - UN Identification Number (e.g. "UN 1263 PAINT").
  - Shipper and Consignee contact details.
  - Two Package Orientation "This Way Up" red arrows on opposite vertical faces.
- Shipper's Declaration for Dangerous Goods (DGD): Must be completed and signed by an IATA/IMDG certified dangerous goods specialist.
"""

txt_files = {
    "company_profile_and_fleet_services.txt": DOC_COMPANY,
    "customer_rules_and_shipping_terms.txt": DOC_CUSTOMER,
    "employee_operations_and_warehouse_sop.txt": DOC_EMPLOYEE,
    "customs_trade_compliance_and_crossborder_rules.txt": DOC_CUSTOMS,
    "pharma_cold_chain_and_gdp_manual.txt": DOC_COLD_CHAIN,
    "dangerous_goods_hazmat_and_packaging_rules.txt": DOC_HAZMAT,
}

for fname, text in txt_files.items():
    p = _KB_DIR / fname
    with open(p, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    print(f"Wrote knowledge base text guide: {p} ({len(text)} bytes)")


# ==============================================================================
# 2. GENERATE 250+ REALISTIC SHIPMENTS DATASET
# ==============================================================================

HUBS = [
    ("Mumbai, India", "London, UK", "Mumbai Hub -> Dubai Hub -> London Heathrow Hub"),
    ("Chennai, India", "Singapore", "Chennai Port -> Port of Singapore -> Jurong Logistics Hub"),
    ("Shanghai, China", "Los Angeles, USA", "Shanghai Port -> Long Beach Port -> LA Intermodal Depot"),
    ("Frankfurt, Germany", "Tokyo, Japan", "Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub"),
    ("Rotterdam, Netherlands", "Sydney, Australia", "Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot"),
    ("Dubai, UAE", "New York, USA", "Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center"),
    ("Delhi, India", "Chicago, USA", "Delhi Air Cargo -> London Heathrow -> Chicago O'Hare Hub"),
    ("Hamburg, Germany", "Mumbai, India", "Hamburg Port -> Suez Transit -> JNPT Mumbai"),
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
]

STATUSES = [
    "In Transit",
    "Delivered",
    "Delayed",
    "On Hold - Customs",
    "Out for Delivery",
]

DELAY_REASONS = [
    None,
    "Port congestion and vessel berthing backlog",
    "Severe weather and typhoon diversion in Pacific corridor",
    "Partner airline mechanical inspection delay",
    "Documentation discrepancy on commercial invoice",
    "Highway transit disruption and road transport detour",
    "Customs secondary inspection and valuation audit",
    "Peak holiday cargo sorting backlog at gateway facility",
]

CUSTOMS_STATUSES = [
    "Cleared",
    "Not yet required",
    "Under review - Documentation pending",
    "Inspection required - Physical examination scheduled",
    "Duty payment processing",
    "Export clearance completed",
]

CARGO_TYPES = [
    "High-Tech Consumer Electronics",
    "Pharmaceutical Vaccines (CC-POL-9921 2°C-8°C)",
    "Automotive Powertrain Components",
    "Industrial Machinery Spare Parts",
    "Organic Agricultural Produce (Reefer)",
    "Apparel & Fashion Textiles",
    "Medical Diagnostic Equipment",
    "Chemical Polymers (Class 9 Hazmat)",
    "Solar PV Inverters & Battery Modules",
    "Precision Aerospace Hardware",
]

random.seed(42)
base_date = datetime(2026, 11, 15)

shipments_rows = []
for i in range(1, 261):
    sid = f"SHP-{10000 + i}"
    origin, dest, route_tmpl = random.choice(HUBS)
    status = random.choices(
        STATUSES,
        weights=[40, 25, 15, 10, 10],
        k=1
    )[0]

    # Grounded known shipments from existing tests (SHP-10001 to SHP-10010)
    if sid == "SHP-10001":
        origin = "Mumbai, India"
        dest = "London, UK"
        status = "In Transit"
        curr_loc = "Dubai Hub, UAE"
        route = "Mumbai Hub -> Dubai Hub -> London Heathrow Hub"
        delay = None
        customs = "Not yet required"
        eta = "2026-11-20"
        updated = "2026-11-15 18:30"
    elif sid == "SHP-10002":
        origin = "Chennai, India"
        dest = "Dubai, UAE"
        status = "Delayed"
        curr_loc = "Jebel Ali Port, UAE"
        route = "Chennai Port -> Jebel Ali Port"
        delay = "Port congestion at Jebel Ali"
        customs = "Cleared"
        eta = "2026-11-19"
        updated = "2026-11-16 08:00"
    elif sid == "SHP-10003":
        origin = "Delhi, India"
        dest = "New York, USA"
        status = "On Hold - Customs"
        curr_loc = "JFK Airport, USA"
        route = "Delhi Hub -> Frankfurt Hub -> JFK Airport"
        delay = "Customs hold"
        customs = "Held - awaiting commercial invoice"
        eta = "2026-11-22"
        updated = "2026-11-15 12:10"
    elif sid == "SHP-10004":
        origin = "Ahmedabad, India"
        dest = "Singapore"
        status = "Delivered"
        curr_loc = "Singapore"
        route = "Ahmedabad Hub -> Singapore Hub"
        delay = None
        customs = "Cleared"
        eta = "2026-11-10"
        updated = "2026-11-10 14:45"
    elif sid == "SHP-10005":
        origin = "Pune, India"
        dest = "Sydney, Australia"
        status = "Out for Delivery"
        curr_loc = "Sydney Local Depot"
        route = "Pune Hub -> Singapore Hub -> Sydney Hub"
        delay = None
        customs = "Cleared"
        eta = "2026-11-16"
        updated = "2026-11-16 07:20"
    elif sid == "SHP-10006":
        origin = "Kolkata, India"
        dest = "Tokyo, Japan"
        status = "In Transit"
        curr_loc = "Singapore Hub"
        route = "Kolkata Hub -> Singapore Hub -> Tokyo Hub"
        delay = None
        customs = "Pending"
        eta = "2026-11-25"
        updated = "2026-11-17 09:15"
    elif sid == "SHP-10007":
        origin = "Bangalore, India"
        dest = "Berlin, Germany"
        status = "Delayed"
        curr_loc = "Mumbai Hub, India"
        route = "Bangalore Hub -> Mumbai Hub -> Frankfurt Hub -> Berlin Depot"
        delay = "Weather disruption at Mumbai airport"
        customs = "Not yet required"
        eta = "2026-11-28"
        updated = "2026-11-17 06:00"
    elif sid == "SHP-10008":
        origin = "Hyderabad, India"
        dest = "Toronto, Canada"
        status = "In Transit"
        curr_loc = "London Heathrow Hub, UK"
        route = "Hyderabad Hub -> Dubai Hub -> London Hub -> Toronto Pearson Hub"
        delay = None
        customs = "Cleared"
        eta = "2026-11-24"
        updated = "2026-11-16 22:45"
    elif sid == "SHP-10009":
        origin = "Jaipur, India"
        dest = "Dubai, UAE"
        status = "Delivered"
        curr_loc = "Dubai, UAE"
        route = "Jaipur Hub -> Mumbai Hub -> Dubai Hub"
        delay = None
        customs = "Cleared"
        eta = "2026-11-12"
        updated = "2026-11-12 11:30"
    elif sid == "SHP-10010":
        origin = "Surat, India"
        dest = "Los Angeles, USA"
        status = "On Hold - Customs"
        curr_loc = "LAX Airport, USA"
        route = "Surat Hub -> Singapore Hub -> LAX Airport"
        delay = "Customs hold"
        customs = "Held - missing packing list"
        eta = "2026-11-26"
        updated = "2026-11-17 03:50"
    else:
        # Generate realistic values
        route = route_tmpl
        if status == "Delivered":
            curr_loc = f"{dest} Consignee Facility"
            delay = None
            customs = "Cleared"
            eta = (base_date - timedelta(days=random.randint(1, 4))).strftime("%Y-%m-%d")
            updated = (base_date - timedelta(days=random.randint(1, 2), hours=random.randint(1, 10))).strftime("%Y-%m-%d %H:%M")
        elif status == "Out for Delivery":
            curr_loc = f"{dest} Local Delivery Center"
            delay = None
            customs = "Cleared"
            eta = base_date.strftime("%Y-%m-%d")
            updated = (base_date - timedelta(hours=random.randint(1, 6))).strftime("%Y-%m-%d %H:%M")
        elif status == "Delayed":
            curr_loc = f"Transit Hub near {origin.split(',')[0]}"
            delay = random.choice([r for r in DELAY_REASONS if r is not None])
            customs = random.choice(CUSTOMS_STATUSES)
            eta = (base_date + timedelta(days=random.randint(4, 12))).strftime("%Y-%m-%d")
            updated = (base_date - timedelta(hours=random.randint(2, 24))).strftime("%Y-%m-%d %H:%M")
        elif status == "On Hold - Customs":
            curr_loc = f"{dest.split(',')[0]} International Customs Exam Station"
            delay = "Customs documentation audit in progress"
            customs = "Under review - Documentation pending"
            eta = (base_date + timedelta(days=random.randint(2, 7))).strftime("%Y-%m-%d")
            updated = (base_date - timedelta(hours=random.randint(2, 18))).strftime("%Y-%m-%d %H:%M")
        else: # In Transit
            curr_loc = f"In Transit ({route.split(' -> ')[1] if ' -> ' in route else origin})"
            delay = None
            customs = random.choice(["Not yet required", "Export clearance completed", "Duty payment processing"])
            eta = (base_date + timedelta(days=random.randint(1, 8))).strftime("%Y-%m-%d")
            updated = (base_date - timedelta(hours=random.randint(1, 14))).strftime("%Y-%m-%d %H:%M")

    shipments_rows.append({
        "shipment_id": sid,
        "origin": origin,
        "destination": dest,
        "status": status,
        "current_location": curr_loc,
        "route": route,
        "estimated_delivery": eta,
        "delay_reason": delay or "",
        "customs_status": customs,
        "last_updated": updated,
    })

# Save to data/processed/shipments.csv and data/raw/shipments.csv
fieldnames = [
    "shipment_id", "origin", "destination", "status", "current_location",
    "route", "estimated_delivery", "delay_reason", "customs_status", "last_updated"
]

for out_path in [_PROCESSED_DIR / "shipments.csv", _RAW_DIR / "shipments.csv"]:
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(shipments_rows)
    print(f"Wrote shipments CSV: {out_path} ({len(shipments_rows)} records)")

# Update SQLite database
db_path = _RAW_DIR / "shipments.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS shipments (
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
for r in shipments_rows:
    cur.execute("""
    INSERT INTO shipments (
        shipment_id, origin, destination, status, current_location,
        route, estimated_delivery, delay_reason, customs_status, last_updated
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(shipment_id) DO UPDATE SET
        origin=excluded.origin,
        destination=excluded.destination,
        status=excluded.status,
        current_location=excluded.current_location,
        route=excluded.route,
        estimated_delivery=excluded.estimated_delivery,
        delay_reason=excluded.delay_reason,
        customs_status=excluded.customs_status,
        last_updated=excluded.last_updated;
    """, (
        r["shipment_id"], r["origin"], r["destination"], r["status"],
        r["current_location"], r["route"], r["estimated_delivery"],
        r["delay_reason"], r["customs_status"], r["last_updated"]
    ))
conn.commit()
cur.execute("SELECT COUNT(*) FROM shipments;")
print(f"Updated SQLite database: {db_path} (Total count: {cur.fetchone()[0]})")
conn.close()


# ==============================================================================
# 3. GENERATE COMPANY, CUSTOMER, EMPLOYEE, HUB, AND POLICY CSVS
# ==============================================================================

# A. Employees Roster
departments = ["Terminal Operations", "Customs Brokerage", "Cold-Chain Quality", "Flight Dispatch", "Marine Logistics", "Customer Success"]
roles = {
    "Terminal Operations": ["Warehouse Operations Supervisor", "Inbound Dock Lead", "Forklift Team Lead", "Inventory Cross-Dock Specialist"],
    "Customs Brokerage": ["Senior Licensed Customs Broker", "Trade Compliance Auditor", "Tariff Classification Specialist", "Cross-Border Documentation Lead"],
    "Cold-Chain Quality": ["Healthcare QA Specialist", "GDP Compliance Auditor", "Cryogenic Packaging Technician", "Sensor Calibration Lead"],
    "Flight Dispatch": ["Air Cargo Load Planner", "Aviation Ramp Controller", "Charter Flight Operations Manager"],
    "Marine Logistics": ["Container Vessel Stowage Coordinator", "Port Terminal Liaison", "Reefer Operations Specialist"],
    "Customer Success": ["Enterprise Account Manager", "Tracking Escalation Specialist", "Claims Resolution Manager"]
}

first_names = ["James", "Emma", "Liam", "Sophia", "Michael", "Olivia", "Ethan", "Ava", "William", "Isabella", "Alexander", "Mia", "Daniel", "Charlotte", "David", "Amelia", "Joseph", "Harper", "Andrew", "Evelyn", "Siddharth", "Priya", "Arjun", "Ananya", "Rohan", "Meera", "Vikram", "Deepa", "Rahul", "Pooja", "Wei", "Ling", "Jian", "Mei", "Chen", "Yuki", "Kenji", "Hana", "Lukas", "Elena", "Mateo", "Camila"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Anderson", "Patel", "Sharma", "Verma", "Iyer", "Mukherjee", "Zhang", "Li", "Wang", "Tanaka", "Sato", "Mueller", "Schmidt", "Dubois", "Moreau", "Santos", "Fischer", "Rossi"]

employee_rows = []
for idx in range(1, 101):
    dept = random.choice(departments)
    role = random.choice(roles[dept])
    fn = random.choice(first_names)
    ln = random.choice(last_names)
    emp_id = f"EMP-{20000 + idx}"
    email = f"{fn.lower()}.{ln.lower()}{random.randint(1, 99)}@fleetharbor.com"
    hub_loc = random.choice([h[0] for h in HUBS])
    shift = random.choice(["Day Shift (06:00 - 14:30)", "Swing Shift (14:00 - 22:30)", "Night / Overnight Shift (22:00 - 06:30)"])
    cert = random.choice(["IATA DGR Certified", "GDP Pharma Certified", "Licensed Customs Broker", "Certified Forklift Trainer", "Six Sigma Green Belt", "Standard Ops"])
    
    employee_rows.append({
        "employee_id": emp_id,
        "full_name": f"{fn} {ln}",
        "department": dept,
        "job_title": role,
        "assigned_hub": hub_loc,
        "shift": shift,
        "certification": cert,
        "email": email,
        "phone_extension": f"x{4000 + idx}",
        "status": "Active"
    })

emp_csv_path = _GENERATED_DIR / "employees_roster.csv"
with open(emp_csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(employee_rows[0].keys()))
    writer.writeheader()
    writer.writerows(employee_rows)
print(f"Wrote Employees Roster CSV: {emp_csv_path} ({len(employee_rows)} records)")


# B. Customer Accounts & SLA Tiers
client_industries = [
    ("BioPharma Global Inc.", "Healthcare Priority", 99.8, "CC-POL-9921 Cold Chain", "Net 45"),
    ("AeroDynamics Propulsion Ltd.", "Enterprise Corporate", 99.5, "Charter & AOG Urgent", "Net 30"),
    ("OmniRetail Direct E-Commerce", "E-Commerce Premier", 98.9, "Daily Cross-Docking", "Net 15"),
    ("Quantum Silicon Microdevices", "Enterprise Corporate", 99.7, "Temperature & Shock Monitored", "Net 30"),
    ("Nordic Marine Harvest Co.", "Perishable Reefer Priority", 99.2, "Reefer Maritime & Cold Storage", "Net 30"),
    ("Apex Automotive Tier-1", "Enterprise Corporate", 99.4, "Just-In-Time Assembly Feed", "Net 45"),
    ("Horizon Renewable Solar Systems", "Standard Commercial", 98.0, "Oversized Flat Rack Cargo", "Net 30"),
    ("GeneVax Vaccines International", "Healthcare Priority", 99.9, "Cryogenic Dry Ice (-70°C)", "Net 60"),
    ("TerraChemical Industrial Solutions", "Enterprise Corporate", 99.1, "Class 3/8 Hazmat Certified", "Net 30"),
    ("Alpine Precision Watches & Optics", "High-Value Secured", 99.9, "Armored Escort & Tamper Seal", "Net 15"),
]

customer_rows = []
for idx in range(1, 101):
    template = client_industries[(idx - 1) % len(client_industries)]
    c_id = f"CUST-{50000 + idx}"
    comp_name = f"{template[0]} {idx if idx > 10 else ''}".strip()
    tier = template[1]
    sla_ontime = template[2]
    specialty = template[3]
    payment_terms = template[4]
    credit_limit = f"${random.randint(50, 800) * 1000:,}"
    account_rep = random.choice(employee_rows)["full_name"]

    customer_rows.append({
        "customer_id": c_id,
        "company_name": comp_name,
        "tier": tier,
        "on_time_sla_target": f"{sla_ontime}%",
        "specialty_requirements": specialty,
        "payment_terms": payment_terms,
        "credit_limit": credit_limit,
        "dedicated_account_rep": account_rep,
        "contract_status": "Active / Verified"
    })

cust_csv_path = _GENERATED_DIR / "customer_accounts.csv"
with open(cust_csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(customer_rows[0].keys()))
    writer.writeheader()
    writer.writerows(customer_rows)
print(f"Wrote Customer Accounts CSV: {cust_csv_path} ({len(customer_rows)} records)")


# C. Global Hubs & Facilities
hub_specs = [
    ("Dubai Logistics City Gateway", "DXB-HUB-01", "Dubai, UAE", "Air & Ocean Transshipment", 450000, "GDP Pharma, IATA CEIV, Free Trade Zone", "+971 4 800 4272"),
    ("Singapore Changi Mega Cargo Hub", "SIN-HUB-02", "Singapore", "Air Cargo & Life Sciences", 380000, "GDP Pharma Certified, Halal Logistics, TAPA Class A", "+65 6542 8899"),
    ("Rotterdam Maasvlakte Terminal", "RTM-HUB-03", "Rotterdam, Netherlands", "Maritime Container & Intermodal Rail", 850000, "Automated Guided Vehicles, Authorized Economic Operator (AEO)", "+31 10 252 0000"),
    ("Frankfurt CargoCity South Hub", "FRA-HUB-04", "Frankfurt, Germany", "Airfreight & European Distribution", 520000, "IATA CEIV Pharma, Temperature Controlled -20°C to +25°C", "+49 69 690 0"),
    ("London Heathrow World Cargo Centre", "LHR-HUB-05", "London, UK", "Air Cargo & Transatlantic Linehaul", 290000, "AEO Certified, Bonded Customs Warehouse, Courier Express", "+44 20 8759 7700"),
    ("Los Angeles Long Beach Intermodal", "LAX-HUB-06", "Los Angeles, USA", "Transpacific Ocean & BNSF Rail", 920000, "C-TPAT Tier 3, Container Freight Station, Heavy-Lift Crane", "+1 310 555 0199"),
    ("Shanghai Pudong Logistics Park", "PVG-HUB-07", "Shanghai, China", "Air & Ocean Export Consolidation", 680000, "China Customs Class AA, High-Tech Electronics Cleanroom", "+86 21 6834 0000"),
    ("Mumbai Air Cargo & JNPT Terminal", "BOM-HUB-08", "Mumbai, India", "Air Cargo & Port Transshipment", 410000, "Pharma Cold Chain, ICEGATE EDI, Bonded Zone", "+91 22 2682 9000"),
    ("Sydney Mascot International Cargo", "SYD-HUB-09", "Sydney, Australia", "Air Cargo & Domestic Express Linehaul", 260000, "DAFF Biosecurity Certified, Dangerous Goods Storage", "+61 2 9667 9111"),
    ("Chicago O'Hare Northeast Cargo Terminal", "ORD-HUB-10", "Chicago, USA", "Midwest Intermodal Rail & Air Cargo", 490000, "Foreign Trade Zone #22, Cold Chain Vaccine Hub", "+1 773 686 2200")
]

hub_rows = []
for h in hub_specs:
    hub_rows.append({
        "facility_name": h[0],
        "hub_code": h[1],
        "city_country": h[2],
        "primary_transport_mode": h[3],
        "storage_capacity_sqft": h[4],
        "certifications": h[5],
        "operations_desk_phone": h[6],
        "status": "Operational 24/7"
    })

hub_csv_path = _GENERATED_DIR / "global_hubs.csv"
with open(hub_csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(hub_rows[0].keys()))
    writer.writeheader()
    writer.writerows(hub_rows)
print(f"Wrote Global Hubs CSV: {hub_csv_path} ({len(hub_rows)} records)")


# ==============================================================================
# 4. AUGMENT data/knowledge_base/kb_long.csv WITH EXPANDED CATEGORIES
# ==============================================================================

kb_csv_path = _DATA_KB_DIR / "kb_long.csv"
existing_kb = []
if kb_csv_path.exists():
    with open(kb_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        existing_kb = list(reader)

new_kb_entries = [
    {
        "doc_id": "CO-FLEET-OVERVIEW",
        "category": "company_overview",
        "section_title": "FleetHarbor AI Global Network and Executive Overview",
        "content": "FleetHarbor AI Logistics is an international multi-modal third-party logistics (3PL) carrier with dual headquarters in Singapore and Rotterdam. Operating across 140 countries with 280 strategic facilities, FleetHarbor provides Ocean Freight (FCL/LCL), Global Air Cargo, Intermodal Road and Rail linehaul, Temperature-controlled Life Sciences cold-chain under policy CC-POL-9921, and licensed customs brokerage at over 60 global gateways.",
        "tags": "company;overview;fleetharbor;services;network;headquarters;singapore;rotterdam",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "CUST-TERMS-BILLING",
        "category": "policies",
        "section_title": "Customer Terms of Carriage, Billing SLAs and Payment Schedules",
        "content": "FleetHarbor customer accounts operate under three credit tiers: Enterprise Corporate (Net 30/60 days with dedicated account rep), Healthcare Priority (GDP mandatory compliance, Net 45), and Standard Commercial (Net 15 days or pre-paid). Booking cancellations made before container placement incur zero fees; dispatch cancellations are subject to $150-$450 empty haulage fees.",
        "tags": "customer;billing;terms;credit;sla;cancellation;fees",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "CUST-DEMURRAGE-STORAGE",
        "category": "policies",
        "section_title": "Ocean and Air Cargo Free Time and Demurrage Fee Schedule",
        "content": "Ocean Import FCL containers receive 5 calendar days of free time following vessel discharge. Ocean Export FCL containers receive 7 calendar days before departure. Demurrage rates after free time are $85/day for Days 1-5 and $150/day thereafter for dry containers. Reefer containers incur $180/day for Days 1-3 and $320/day thereafter. Air cargo free time is 48 hours from airline arrival notice.",
        "tags": "demurrage;detention;free time;storage fees;ocean container;air freight",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "CUST-CLAIMS-DAMAGE",
        "category": "claims_guidance",
        "section_title": "Freight Loss and Cargo Damage Claims Submission and Settlement SOP",
        "content": "To file a cargo claim: obvious external damage must be noted on the Proof of Delivery (POD) at delivery with formal written notice within 3 days. Concealed damage must be filed within 14 calendar days. Total loss claims must be submitted within 30 days of estimated delivery date. Submissions require the signed Waybill/BOL, original supplier invoice, damage photos, and salvage estimate. FleetHarbor resolves completed claims within 21 business days.",
        "tags": "claims;damage;loss;cargo claims;compensation;proof of delivery;settlement",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "EMP-WAREHOUSE-SAFETY",
        "category": "warehouse_operations",
        "section_title": "Warehouse Safety Protocols, Zero-Harm PPE and Material Handling Rules",
        "content": "All warehouse employees and forklift operators must wear certified steel-toe shoes (ASTM F2413 / EN ISO 20345), high-visibility class 2/3 vests, and hard hats under overhead racks. Forklift speed is strictly governed to a maximum of 8 km/h (5 mph). Daily pre-shift MHE checklists are mandatory. Maintain a 3-meter safety perimeter from moving equipment at all times.",
        "tags": "employee;safety;warehouse;ppe;forklift;rules;sop",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "EMP-DOCK-RECEIVING",
        "category": "warehouse_operations",
        "section_title": "Inbound Truck Check-in, Container Seal Verification and Put-Away SOP",
        "content": "Inbound receiving SOP: Dock supervisors must match carrier container seal numbers with shipping manifests prior to cutting seals. If a seal is broken or mismatched, doors remain closed and Security is alerted. Received cargo is scanned via master barcode, inspected for transit damage, tagged with internal License Plate Number (LPN) barcodes, and moved to storage within 45 minutes (15 minutes for cold-chain items).",
        "tags": "inbound;dock;receiving;seals;lpn;warehouse;sop;barcode",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "CUSTM-CLEARANCE-DOCS",
        "category": "document_guide",
        "section_title": "Mandatory International Customs Clearance Documentation Guidelines",
        "content": "International cross-border customs clearance requires: 1) Commercial Invoice stating buyer/seller names, full product description, 6-10 digit HS code, commercial currency, Incoterms 2020 rules, and country of origin; 2) Packing List detailing itemization, dimensions, gross and net weights; 3) Transport Bill of Lading or Air Waybill; 4) Certificate of Origin when claiming preferential tariff treatment. Incomplete documents trigger customs red-channel holds.",
        "tags": "customs;documentation;commercial invoice;packing list;bill of lading;hs code;incoterms",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "CUSTM-HOLDS-RESOLUTION",
        "category": "policies",
        "section_title": "Resolving Customs Holds, Inspections and Documentation Audits",
        "content": "When a shipment status indicates 'On Hold - Customs', action depends on the hold category: HOLD-DOC requires an amended invoice or packing list within 24 hours; HOLD-VAL requires supplier payment proof or purchase order; HOLD-PGA requires partner government agency registrations (FDA, DEFRA, etc.); HOLD-PHYS requires a physical inspection at the customs exam station attended by a licensed FleetHarbor customs runner.",
        "tags": "customs hold;delays;inspection;red channel;resolution;customs clearance",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "COLD-PHARMA-CC-9921",
        "category": "commodity_handling",
        "section_title": "Pharmaceutical Cold-Chain Policy CC-POL-9921 Operating Guidelines",
        "content": "FleetHarbor Healthcare operations operate under Policy Code CC-POL-9921 complying with WHO GDP and EU Guidelines 2013/C 343/01. Validated ranges: Cryogenic / Dry Ice (-70°C to -80°C), Deep Frozen (-20°C to -10°C), Refrigerated (+2°C to +8°C, never freeze), and Controlled Room Temperature (+15°C to +25°C). All consignments carry calibrated real-time cellular/GPS sensors logging data every 10 minutes. Any temperature breach triggers immediate quarantine and a 24-hour RCA report.",
        "tags": "pharma;cold chain;cc-pol-9921;temperature;gdp;vaccine;excursion;dry ice",
        "last_updated": "2026-11-20"
    },
    {
        "doc_id": "HAZMAT-DANGEROUS-GOODS",
        "category": "commodity_handling",
        "section_title": "Dangerous Goods Packaging, Lithium Battery Rules and Hazmat Classes 1-9",
        "content": "Hazardous materials transport complies with IATA DGR and IMDG codes. FleetHarbor accepts Classes 2 through 9 in UN-certified packaging (e.g. 4G/4GV). Standalone lithium batteries (UN3480/UN3090) shipped by air are limited to maximum 30% State of Charge (SoC), require UN 38.3 test summaries, and must carry Cargo Aircraft Only (CAO) labels. Shipper's Declaration for Dangerous Goods (DGD) is mandatory.",
        "tags": "hazmat;dangerous goods;lithium batteries;un3480;iata;imdg;packaging",
        "last_updated": "2026-11-20"
    }
]

existing_ids = {row.get("doc_id") for row in existing_kb}
added_kb = 0
for entry in new_kb_entries:
    if entry["doc_id"] not in existing_ids:
        existing_kb.append(entry)
        existing_ids.add(entry["doc_id"])
        added_kb += 1

with open(kb_csv_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["doc_id", "category", "section_title", "content", "tags", "last_updated"])
    writer.writeheader()
    writer.writerows(existing_kb)
print(f"Augmented knowledge base CSV: {kb_csv_path} (Total rows: {len(existing_kb)}, Added: {added_kb})")


# ==============================================================================
# 5. GENERATE SUPABASE FULL SEED SQL SCRIPT
# ==============================================================================

sql_seed_path = _SQL_DIR / "supabase_full_seed.sql"
with open(sql_seed_path, "w", encoding="utf-8") as f:
    f.write("-- FleetHarbor Logistics PostgreSQL / Supabase Full Production Seed\n")
    f.write("-- Generated: 20 November 2026\n\n")
    f.write("-- 1. Create Shipments Table\n")
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

    f.write("-- 2. Seed Shipments Data\n")
    for s in shipments_rows:
        orig = s["origin"].replace("'", "''")
        dest = s["destination"].replace("'", "''")
        stat = s["status"].replace("'", "''")
        loc = (s["current_location"] or "").replace("'", "''")
        rte = (s["route"] or "").replace("'", "''")
        eta = f"'{s['estimated_delivery']}'" if s["estimated_delivery"] else "NULL"
        d_val = s["delay_reason"].replace("'", "''") if s["delay_reason"] else None
        c_val = s["customs_status"].replace("'", "''") if s["customs_status"] else None
        delay = f"'{d_val}'" if d_val else "NULL"
        cust = f"'{c_val}'" if c_val else "NULL"
        upd = f"'{s['last_updated']}'" if s["last_updated"] else "NULL"

        f.write(f"INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)\n")
        f.write(f"VALUES ('{s['shipment_id']}', '{orig}', '{dest}', '{stat}', '{loc}', '{rte}', {eta}, {delay}, {cust}, {upd})\n")
        f.write(f"ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;\n")

    f.write("\n-- End of Supabase Shipments Seed\n")

print(f"Generated Supabase Full SQL Seed: {sql_seed_path} ({sql_seed_path.stat().st_size} bytes)")
print("Data generation script completed successfully!")
