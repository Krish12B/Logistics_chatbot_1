-- =====================================================================
-- Supabase PostgreSQL Schema Extension v2 (Enterprise Supply Chain)
-- Source: Data_attach2.xlsx (14 Relational Datasets, 76,000 Rows)
-- Preserves existing public.shipments, documents, knowledge_base,
-- conversations, and conversation_messages without modification.
-- Compatibility: Supabase PostgreSQL 15+
-- =====================================================================

create extension if not exists "uuid-ossp";

-- ── TIER 1: DIMENSION & REGISTRY TABLES ──────────────────────────────

create table if not exists public.enterprise_customers (
    customer_id        uuid primary key,
    customer_name      text not null,
    customer_type      text not null,
    industry           text not null,
    city               text not null,
    state              text not null,
    country            text not null,
    registration_date  date not null,
    customer_status    text not null
);

create table if not exists public.products (
    product_id             uuid primary key,
    product_name           text not null,
    category               text not null,
    hs_code                varchar(32) not null,
    hazardous              boolean not null default false,
    perishable             boolean not null default false,
    temperature_controlled boolean not null default false,
    fragile                boolean not null default false,
    weight_per_unit        numeric(12, 2) not null,
    supplier_name          text not null
);

create table if not exists public.carriers (
    carrier_id       uuid primary key,
    carrier_name     text not null,
    carrier_type     text not null,
    average_rating   numeric(4, 2),
    fleet_size       integer,
    years_of_service integer,
    headquarters     text
);

create table if not exists public.warehouses (
    warehouse_id        uuid primary key,
    warehouse_name      text not null,
    city                text not null,
    state               text not null,
    warehouse_capacity  integer not null,
    current_utilization numeric(6, 2),
    warehouse_type      text not null
);

create table if not exists public.routes (
    route_id             uuid primary key,
    origin_city          text not null,
    destination_city     text not null,
    origin_country       text not null,
    destination_country  text not null,
    origin_port          text not null,
    destination_port     text not null,
    distance_km          numeric(12, 2) not null,
    average_transit_days integer not null,
    route_risk           text not null,
    traffic_index        integer not null
);

create table if not exists public.vehicles (
    vehicle_id         uuid primary key,
    vehicle_number     varchar(64) not null,
    vehicle_type       text not null,
    capacity_kg        numeric(14, 2) not null,
    fuel_type          text not null,
    maintenance_status text not null,
    vehicle_age        integer not null
);

create table if not exists public.weather (
    weather_id        uuid primary key,
    city              text not null,
    forecast_date     date not null,
    weather_condition text not null,
    temperature       numeric(6, 2),
    rainfall          numeric(8, 2),
    humidity          numeric(6, 2),
    wind_speed        numeric(8, 2),
    visibility        numeric(8, 2)
);

create table if not exists public.customs (
    customs_id             uuid primary key,
    customs_required       boolean not null,
    documentation_complete boolean not null,
    inspection_required    boolean not null,
    cargo_type             text not null,
    destination_country    text not null
);

create table if not exists public.ai_model_registry (
    model_id                 uuid primary key,
    model_name               text not null,
    model_version            varchar(32) not null,
    model_type               text not null,
    training_dataset_version varchar(64) not null,
    artifact_uri             text not null,
    deployment_status        text not null
);

-- ── TIER 2: ENTERPRISE SHIPMENTS (NO STORED 'delayed' COLUMN) ────────

create table if not exists public.enterprise_shipments (
    shipment_id            uuid primary key,
    booking_id             varchar(32) not null unique,
    customer_id            uuid not null references public.enterprise_customers(customer_id),
    product_id             uuid not null references public.products(product_id),
    carrier_id             uuid not null references public.carriers(carrier_id),
    warehouse_id           uuid not null references public.warehouses(warehouse_id),
    route_id               uuid not null references public.routes(route_id),
    vehicle_id             uuid not null references public.vehicles(vehicle_id),
    customs_id             uuid not null references public.customs(customs_id),
    weather_id             uuid not null references public.weather(weather_id),
    booking_date           date not null,
    ship_date              date not null,
    expected_delivery_date date not null,
    shipping_mode          text not null,
    shipment_type          text not null,
    priority               text not null,
    weight_kg              numeric(12, 2) not null,
    volume_cbm             numeric(12, 2) not null,
    declared_value         numeric(14, 2) not null,
    insurance              boolean not null default false,
    fragile                boolean not null default false
);

-- ── TIER 3 & 4: DELIVERY HISTORY & AI OBSERVABILITY TABLES ───────────

create table if not exists public.shipment_delivery_history (
    history_id           uuid primary key,
    shipment_id          uuid not null references public.enterprise_shipments(shipment_id),
    actual_delivery_date date not null,
    delivery_status      text not null,
    delivery_attempts    integer not null
);

create table if not exists public.ai_feature_store (
    feature_record_id         uuid primary key,
    shipment_id               uuid not null references public.enterprise_shipments(shipment_id),
    feature_timestamp         timestamptz not null,
    route_delay_rate          numeric(6, 2) not null,
    carrier_reliability_score numeric(6, 2) not null,
    weather_severity_score    numeric(6, 2) not null,
    feature_vector_json       jsonb not null
);

create table if not exists public.ai_inference_log (
    inference_id         uuid primary key,
    shipment_id          uuid not null references public.enterprise_shipments(shipment_id),
    model_id             uuid not null references public.ai_model_registry(model_id),
    prediction_timestamp timestamptz not null,
    delay_probability    double precision not null,
    risk_category        text not null,
    latency_ms           integer not null
);

create table if not exists public.ai_monitoring_alerts (
    alert_id           uuid primary key,
    shipment_id        uuid not null references public.enterprise_shipments(shipment_id),
    inference_id       uuid not null references public.ai_inference_log(inference_id),
    alert_type         text not null,
    severity           text not null,
    recommended_action text not null,
    alert_status       text not null
);

-- ── INDEXES ──────────────────────────────────────────────────────────

create index if not exists idx_ent_shipments_booking_id on public.enterprise_shipments (booking_id);
create index if not exists idx_ent_shipments_customer_id on public.enterprise_shipments (customer_id);
create index if not exists idx_ent_shipments_carrier_id on public.enterprise_shipments (carrier_id);
create index if not exists idx_ent_shipments_route_id on public.enterprise_shipments (route_id);
create index if not exists idx_delivery_history_shipment_id on public.shipment_delivery_history (shipment_id);
create index if not exists idx_delivery_history_status on public.shipment_delivery_history (delivery_status);
create index if not exists idx_ai_features_shipment_id on public.ai_feature_store (shipment_id);
create index if not exists idx_ai_inference_shipment_id on public.ai_inference_log (shipment_id);
create index if not exists idx_ai_alerts_shipment_id on public.ai_monitoring_alerts (shipment_id);
create index if not exists idx_ent_customers_name on public.enterprise_customers (customer_name);
create index if not exists idx_carriers_name on public.carriers (carrier_name);
create index if not exists idx_warehouses_city on public.warehouses (city);

-- ── DERIVED DELAY VIEW (PER WORKBOOK README RULE) ────────────────────

create or replace view public.v_enterprise_shipments_status as
select
    s.*,
    h.history_id,
    h.actual_delivery_date,
    h.delivery_status as derived_status,
    h.delivery_attempts,
    (h.delivery_status = 'Delayed') as is_delayed,
    greatest(0, (h.actual_delivery_date - s.expected_delivery_date)) as delay_days
from public.enterprise_shipments s
left join public.shipment_delivery_history h
    on h.shipment_id = s.shipment_id;

-- ── ROW LEVEL SECURITY (RLS) ─────────────────────────────────────────

alter table public.enterprise_customers enable row level security;
alter table public.products enable row level security;
alter table public.carriers enable row level security;
alter table public.warehouses enable row level security;
alter table public.routes enable row level security;
alter table public.vehicles enable row level security;
alter table public.weather enable row level security;
alter table public.customs enable row level security;
alter table public.enterprise_shipments enable row level security;
alter table public.shipment_delivery_history enable row level security;
alter table public.ai_model_registry enable row level security;
alter table public.ai_feature_store enable row level security;
alter table public.ai_inference_log enable row level security;
alter table public.ai_monitoring_alerts enable row level security;

do $$
declare
    tbl text;
    tbls text[] := array[
        'enterprise_customers', 'products', 'carriers', 'warehouses',
        'routes', 'vehicles', 'weather', 'customs',
        'enterprise_shipments', 'shipment_delivery_history',
        'ai_model_registry', 'ai_feature_store', 'ai_inference_log', 'ai_monitoring_alerts'
    ];
begin
    foreach tbl in array tbls loop
        execute format('drop policy if exists "Service role full access" on public.%I', tbl);
        execute format('create policy "Service role full access" on public.%I for all to service_role using (true) with check (true)', tbl);
        execute format('drop policy if exists "Read access for app roles" on public.%I', tbl);
        execute format('create policy "Read access for app roles" on public.%I for select to anon, authenticated using (true)', tbl);
    end loop;
end $$;
