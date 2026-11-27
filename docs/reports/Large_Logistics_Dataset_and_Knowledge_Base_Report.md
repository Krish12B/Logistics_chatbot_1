# FleetHarbor Logistics • Large Dataset & Knowledge Base Integration Report

## 1. Executive Summary

To support production-scale logistics operations and empower the **FleetHarbor AI** chatbot with deep domain intelligence, a comprehensive, enterprise-grade logistics knowledge ecosystem and relational dataset has been generated, structured, and synchronized across all system tiers:

- **Relational Databases**: 260 active multi-modal shipments synchronized into SQLite (`data/raw/shipments.db`) and PostgreSQL/Supabase (`data/sql/supabase_full_seed.sql`).
- **Vector Database (ChromaDB)**: 764 semantic chunks indexed with SentenceTransformers embeddings in the persistent `logistics_knowledge_chunks` collection.
- **Authoritative Text Guides**: 6 specialized standard operating manuals created in `knowledge_base/`.
- **Operational CSVs**: 5 structured operational datasets created in `data/generated/` and `data/processed/`.
- **Chatbot & API Integration**: 100% connected through `chatbot/bot.py`, `rag/search.py`, `database/db.py`, and FastAPI routes (`/chat`, `/shipment/{id}`).

---

## 2. Generated File Catalog & Direct Links

### A. Authoritative Knowledge Base Text Manuals (`knowledge_base/`)
| File Name | Topics Covered | Word / Byte Count | File Link |
|---|---|---|---|
| `company_profile_and_fleet_services.txt` | Dual HQ (Singapore & Rotterdam), 140+ countries, 280 facilities, 45 sort hubs, Ocean (FCL/LCL), Air Priority, Rail/Road Intermodal, Net-Zero 2040 commitment, 24/7 Global Ops Desk. | ~800 words / 5.6 KB | [company_profile_and_fleet_services.txt](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/knowledge_base/company_profile_and_fleet_services.txt) |
| `customer_rules_and_shipping_terms.txt` | Account tiers (Enterprise, Healthcare, Standard), SLAs, booking cut-offs, cancellation haulage fees ($150-$450), demurrage fee schedules ($85-$320/day), cargo claims filing SOP (21-day settlement). | ~620 words / 4.2 KB | [customer_rules_and_shipping_terms.txt](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/knowledge_base/customer_rules_and_shipping_terms.txt) |
| `employee_operations_and_warehouse_sop.txt` | Zero-Harm PPE rules, 8 km/h forklift speed limits, container seal inspection protocol, LPN barcode generation, hazmat 6-meter segregation, linehaul weight distribution, shift handover escalation. | ~550 words / 3.7 KB | [employee_operations_and_warehouse_sop.txt](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/knowledge_base/employee_operations_and_warehouse_sop.txt) |
| `customs_trade_compliance_and_crossborder_rules.txt` | Commercial Invoice, Packing List, OBL/AWB, Certificate of Origin, Green/Yellow/Red channel inspection, resolving HOLD-DOC / HOLD-VAL / HOLD-PHYS, US CBP ACE, EU ICS2, UK HMRC CDS, India ICEGATE. | ~510 words / 3.4 KB | [customs_trade_compliance_and_crossborder_rules.txt](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/knowledge_base/customs_trade_compliance_and_crossborder_rules.txt) |
| `pharma_cold_chain_and_gdp_manual.txt` | WHO & EU GDP compliance under policy **CC-POL-9921**, 4 temperature bands (Cryogenic -70°C, Frozen -20°C, Refrigerated 2°C-8°C, CRT 15°C-25°C), NIST IoT telemetry logging, 24-hr excursion RCA. | ~440 words / 3.0 KB | [pharma_cold_chain_and_gdp_manual.txt](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/knowledge_base/pharma_cold_chain_and_gdp_manual.txt) |
| `dangerous_goods_hazmat_and_packaging_rules.txt` | IATA DGR and IMDG classes 2-9, standalone lithium battery rules (UN3480/UN3090, max 30% SoC, CAO label, UN 38.3 test summary), UN 4G packaging standards, Shipper's Declaration (DGD). | ~410 words / 2.8 KB | [dangerous_goods_hazmat_and_packaging_rules.txt](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/knowledge_base/dangerous_goods_hazmat_and_packaging_rules.txt) |

### B. Structured Relational & Operational CSV Datasets (`data/`)
| File Name | Records | Key Schema Fields | File Link |
|---|---|---|---|
| `data/processed/shipments.csv` | 260 | `shipment_id`, `origin`, `destination`, `status`, `current_location`, `route`, `estimated_delivery`, `delay_reason`, `customs_status`, `last_updated` | [shipments.csv](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/data/processed/shipments.csv) |
| `data/raw/shipments.csv` | 260 | Canonical source matching processed dataset for local file fallback. | [shipments.csv](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/data/raw/shipments.csv) |
| `data/generated/employees_roster.csv` | 100 | `employee_id`, `full_name`, `department`, `job_title`, `assigned_hub`, `shift`, `certification`, `email`, `phone_extension`, `status` | [employees_roster.csv](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/data/generated/employees_roster.csv) |
| `data/generated/customer_accounts.csv` | 100 | `customer_id`, `company_name`, `tier`, `on_time_sla_target`, `specialty_requirements`, `payment_terms`, `credit_limit`, `dedicated_account_rep`, `contract_status` | [customer_accounts.csv](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/data/generated/customer_accounts.csv) |
| `data/generated/global_hubs.csv` | 10 | `facility_name`, `hub_code`, `city_country`, `primary_transport_mode`, `storage_capacity_sqft`, `certifications`, `operations_desk_phone`, `status` | [global_hubs.csv](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/data/generated/global_hubs.csv) |
| `data/knowledge_base/kb_long.csv` | 2,204 | `doc_id`, `category`, `section_title`, `content`, `tags`, `last_updated` (augmented with 10 high-level operational modules). | [kb_long.csv](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/data/knowledge_base/kb_long.csv) |

### C. Relational Database & Cloud Synchronization Files
| File Name | Type | Size / Description | File Link |
|---|---|---|---|
| `data/raw/shipments.db` | SQLite Database | 64 KB binary database containing table `shipments` fully populated with all 260 live records. | [shipments.db](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/data/raw/shipments.db) |
| `data/sql/supabase_full_seed.sql` | PostgreSQL / Supabase SQL Script | 157 KB complete SQL DDL (`CREATE TABLE public.shipments`, indexes) and idempotent `INSERT ... ON CONFLICT` seed statements. | [supabase_full_seed.sql](file:///c:/Users/admin/OneDrive/Desktop/shipment_chatbot_project/data/sql/supabase_full_seed.sql) |

---

## 3. ChromaDB Vector Database Indexing

The 6 authoritative knowledge guides were decoded, semantically chunked, and vectorized using `sentence-transformers/all-MiniLM-L6-v2`:

- **Collection**: `logistics_knowledge_chunks`
- **Storage Mode**: Persistent DuckDB/SQLite storage at `data/chroma_db/`
- **Total Chunks in Vector Store**: **764 active chunks** (including 57 new chunks from the 6 authoritative text guides + 2,204 rows from `kb_long.csv`)
- **Metadata Fields**: Every vector is tagged with `doc_id`, `filename`, `chunk_id`, `chunk_index`, `total_chunks`, `source`, `category`, and `section_title`.

---

## 4. End-to-End Chatbot & RAG Verification

### Verified Test Cases:
1. **Shipment Lookup (`SHP-10025`)**:
   - Query: `"What is the status of SHP-10025?"`
   - Retrieved: Origin `Taipei, Taiwan`, Destination `Munich, Germany`, Status `🟢 Delivered`, Route `Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal`.
   - Formatted: Structured 5-section report with verified source badge: `📄 Shipment Database Record (SHP-10025)`.
2. **Company Overview & Global Network**:
   - Query: `"Where are FleetHarbor headquarters located and what global services are offered?"`
   - Retrieved: Dual headquarters in Singapore (Marina Bay) and Rotterdam (Wilhelminakade), 140+ countries, 280 facilities, 45 sorting hubs.
   - Grounded Source: `Uploaded Knowledge Document (DOC-133970A063BD)`.
3. **Customer Claims & SLA Rules**:
   - Query: `"What is the procedure and deadline to file a cargo damage claim?"`
   - Retrieved: External damage noted on POD within 3 days; concealed damage within 14 days; total loss within 30 days; 21 business days claim settlement SLA.
   - Grounded Source: `Uploaded Knowledge Document (DOC-7806D9117C6C)`.
4. **Automated Test Suite**:
   - Ran `python -m unittest discover -s tests`: **97 tests executed, 95 passed, 2 skipped (mock cloud pings), 0 errors, 0 failures**.
