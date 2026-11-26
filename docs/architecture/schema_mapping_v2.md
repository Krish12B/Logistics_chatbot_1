# Supabase & SQLite Schema Mapping Document — Enterprise Supply Chain Integration (`Data_attach2.xlsx`)

## 1. Existing Database Audit vs New Workbook Schema

### Existing Production Tables (Preserved Unchanged)
1. **`public.shipments`** (Supabase + SQLite: 10,000 rows): Legacy/FleetHarbor parcel & linehaul tracking keyed by `SHP-10001` .. `SHP-20000` (`TEXT` primary key).
2. **`customers`** (SQLite: 100 rows): Legacy corporate SLA tier accounts keyed by `CUST-*` (`TEXT` primary key).
3. **`employees`** (SQLite: 500 rows): Employee directory roster (`EMP-20001` .. `EMP-20500`).
4. **`hubs`** (SQLite: 10 rows): Global sorting hub directory (`DXB-HUB-01`, etc.).
5. **`operational_records`** (SQLite: 124 rows): Operational incident/record tickets (`OPS-001` .. `OPS-124`).
6. **`public.documents`, `public.knowledge_base`, `public.conversations`, `public.conversation_messages`** (Supabase `schema.sql`): Document registry, 384-dim `pgvector` embeddings, and multi-turn conversation storage.

### Schema Conflict Analysis & Resolution
Two worksheet names in `Data_attach2.xlsx` (`Customers` and `Shipments`) use UUID primary keys and normalized dimension foreign keys (`booking_id`, `customer_id`, `product_id`, etc.) that are **structurally incompatible** with existing `shipments` (`SHP-*`) and SQLite `customers` (`CUST-*`).

To **preserve all existing tables, records, APIs, and `SHP-10001`..`SHP-20000` tracking without truncating or dropping production data**:
- `Customers` -> mapped to **`enterprise_customers`** (`UUID` PK)
- `Shipments` -> mapped to **`enterprise_shipments`** (`UUID` PK + unique `booking_id` `ALC-2025-*`)
- The remaining 12 sheets have zero table name conflicts and map directly to their canonical snake_case table names.

---

## 2. Complete Workbook-to-Database Mapping Table

| # | Excel Worksheet | Rows | Target Supabase / SQLite Table | Primary Key (Type) | Foreign Key Parents |
|---|---:|---:|---|---|---|
| 1 | `Customers` | 3,000 | `enterprise_customers` | `customer_id` (`UUID`) | — |
| 2 | `Products` | 5,000 | `products` | `product_id` (`UUID`) | — |
| 3 | `Carriers` | 5,000 | `carriers` | `carrier_id` (`UUID`) | — |
| 4 | `Warehouses` | 5,000 | `warehouses` | `warehouse_id` (`UUID`) | — |
| 5 | `Routes` | 3,000 | `routes` | `route_id` (`UUID`) | — |
| 6 | `Vehicles` | 5,000 | `vehicles` | `vehicle_id` (`UUID`) | — |
| 7 | `Weather` | 3,000 | `weather` | `weather_id` (`UUID`) | — |
| 8 | `Customs` | 5,000 | `customs` | `customs_id` (`UUID`) | — |
| 9 | `Shipments` | 5,000 | `enterprise_shipments` | `shipment_id` (`UUID`), `UNIQUE(booking_id)` | `enterprise_customers`, `products`, `carriers`, `warehouses`, `routes`, `vehicles`, `customs`, `weather` |
| 10 | `Shipment_Delivery_History` | 5,000 | `shipment_delivery_history` | `history_id` (`UUID`) | `enterprise_shipments(shipment_id)` |
| 11 | `AI_Model_Registry` | 5,000 | `ai_model_registry` | `model_id` (`UUID`) | — |
| 12 | `AI_Feature_Store` | 10,000 | `ai_feature_store` | `feature_record_id` (`UUID`) | `enterprise_shipments(shipment_id)` |
| 13 | `AI_Inference_Log` | 10,000 | `ai_inference_log` | `inference_id` (`UUID`) | `enterprise_shipments(shipment_id)`, `ai_model_registry(model_id)` |
| 14 | `AI_Monitoring_Alerts` | 10,000 | `ai_monitoring_alerts` | `alert_id` (`UUID`) | `enterprise_shipments(shipment_id)`, `ai_inference_log(inference_id)` |

**Total Relational Records Validated:** **79,000** rows across **14** tables (**0** foreign-key orphans).

---

## 3. Data Type Mapping Rules (Excel -> PostgreSQL & SQLite Mirror)

| Logical / Excel Type | PostgreSQL Column Type (`schema_v2_enterprise.sql`) | SQLite Mirror Affinity & Validation |
|---|---|---|
| 36-char UUID string | `UUID` | `TEXT CHECK (length(col) = 36)` |
| Short code (`booking_id`, `hs_code`, `model_version`) | `VARCHAR(32)` / `VARCHAR(64)` | `TEXT` |
| Descriptive strings / city / industry | `TEXT` | `TEXT` |
| Whole counts / capacity / latency | `INTEGER` | `INTEGER` |
| Weight / volume / declared value / rating | `NUMERIC(12,2)` / `NUMERIC(14,2)` | `REAL` |
| Continuous ML probability (`delay_probability`) | `DOUBLE PRECISION` | `REAL` |
| Boolean flags (`hazardous`, `insurance`, etc.) | `BOOLEAN` | `INTEGER CHECK (col IN (0, 1))` |
| Dates (`registration_date`, `booking_date`, `expected_delivery_date`, `actual_delivery_date`, `forecast_date`) | `DATE` | ISO-8601 `TEXT` (`YYYY-MM-DD`) |
| Timestamps (`feature_timestamp`, `prediction_timestamp`) | `TIMESTAMPTZ` | ISO-8601 `TEXT` (`YYYY-MM-DD HH:MM:SS`) |
| JSON feature payload (`feature_vector_json`) | `JSONB` | Validated JSON `TEXT` |

---

## 4. Foreign-Key Insertion Order

1. **Tier 1 (Independent Reference Dimensions):**
   `enterprise_customers`, `products`, `carriers`, `warehouses`, `routes`, `vehicles`, `weather`, `customs`, `ai_model_registry`
2. **Tier 2 (Core Fact Table):**
   `enterprise_shipments`
3. **Tier 3 (Shipment Children — Stage A):**
   `shipment_delivery_history`, `ai_feature_store`, `ai_inference_log`
4. **Tier 4 (Leaf Alerts Table — Stage B):**
   `ai_monitoring_alerts`

---

## 5. Special Preprocessing Rule (`delayed` Derivation)

Per the workbook `README` worksheet instruction:
> *"Target rule | Do not store delayed in Shipments. Derive it from Shipment_Delivery_History during preprocessing."*

- `enterprise_shipments` intentionally omits any `delayed` / `is_delayed` column.
- Empirical inspection across all 5,000 shipments shows:
  - `3,809` records have `delivery_status = 'Delivered'` (`actual_delivery_date - expected_delivery_date` in `[-1, +1]` days).
  - `1,191` records have `delivery_status = 'Delayed'` (`actual_delivery_date - expected_delivery_date` in `[1, 18]` days).
- Canonical runtime & view derivation (`v_enterprise_shipments_status`):
  - `is_delayed = (h.delivery_status = 'Delayed')`
  - `derived_status = h.delivery_status`
  - `delay_days = GREATEST(0, (h.actual_delivery_date - s.expected_delivery_date))` (SQLite: `MAX(0, CAST(julianday(h.actual_delivery_date) - julianday(s.expected_delivery_date) AS INTEGER))`)
