-- =====================================================================
-- Supabase PostgreSQL Schema & Migrations
-- Project: FleetHarbor Logistics AI Chatbot
-- Compatibility: Supabase PostgreSQL 15+ with pgvector
-- =====================================================================

-- 1. EXTENSIONS
create extension if not exists "uuid-ossp";
create extension if not exists vector;

-- 2. SHIPMENTS TABLE
-- Stores structured operational logistics shipment records.
create table if not exists public.shipments (
    shipment_id        text primary key,
    origin             text not null,
    destination        text not null,
    status             text not null,
    current_location   text,
    route              text,
    estimated_delivery date,
    delay_reason       text,
    customs_status     text,
    last_updated       timestamptz default now()
);

-- 3. SOURCE DOCUMENTS TABLE
-- Tracks uploaded/ingested documents, metadata, and background processing status.
create table if not exists public.documents (
    id                uuid primary key default gen_random_uuid(),
    title             text not null,
    file_name         text,
    file_type         text check (file_type in ('csv', 'pdf', 'txt', 'json', 'md')),
    file_size_bytes   bigint,
    storage_path      text,
    status            text not null default 'pending' check (status in ('pending', 'processing', 'completed', 'failed')),
    error_message     text,
    metadata          jsonb not null default '{}'::jsonb,
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now()
);

-- 4. KNOWLEDGE BASE & CHUNKS TABLE
-- Stores processed FAQ entries and document chunks with 384-dimensional vector embeddings.
create table if not exists public.knowledge_base (
    doc_id         text primary key,
    document_id    uuid references public.documents(id) on delete set null,
    category       text not null,
    section_title  text not null,
    content        text not null,
    tags           text,
    embedding      vector(384),
    last_updated   text default '2026-11-01',
    created_at     timestamptz not null default now()
);

-- 5. CONVERSATION SESSIONS TABLE
-- Persists chat sessions for multi-turn conversational memory.
create table if not exists public.conversations (
    id             uuid primary key default gen_random_uuid(),
    session_id     text not null unique,
    user_id        text,
    title          text,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now()
);

-- 6. CONVERSATION MESSAGES TABLE
-- Stores individual message turns (user query, context, and assistant reply).
create table if not exists public.conversation_messages (
    id              uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.conversations(id) on delete cascade,
    role            text not null check (role in ('user', 'assistant', 'system')),
    content         text not null,
    context         text,
    created_at      timestamptz not null default now()
);

-- ── INDEXES ──────────────────────────────────────────────────────────

-- Vector similarity search index using HNSW (Cosine distance)
-- HNSW offers faster query execution and higher recall without training requirements.
create index if not exists kb_embedding_hnsw_idx
    on public.knowledge_base
    using hnsw (embedding vector_cosine_ops)
    with (m = 16, ef_construction = 64);

-- Standard relational indexes for fast filters and joins
create index if not exists idx_shipments_status
    on public.shipments (status);

create index if not exists idx_kb_category
    on public.knowledge_base (category);

create index if not exists idx_documents_status
    on public.documents (status);

create index if not exists idx_messages_conversation_id
    on public.conversation_messages (conversation_id);

create index if not exists idx_conversations_session_id
    on public.conversations (session_id);

-- ── VECTOR SEARCH RPC FUNCTION ───────────────────────────────────────

create or replace function public.match_knowledge(
    query_embedding vector(384),
    match_threshold float default 0.3,
    match_count     int   default 5
)
returns table (
    doc_id        text,
    category      text,
    section_title text,
    content       text,
    similarity    float
)
language sql stable
as $$
    select
        kb.doc_id,
        kb.category,
        kb.section_title,
        kb.content,
        (1 - (kb.embedding <=> query_embedding))::float as similarity
    from public.knowledge_base kb
    where kb.embedding is not null
      and (1 - (kb.embedding <=> query_embedding)) >= match_threshold
    order by kb.embedding <=> query_embedding
    limit match_count;
$$;

-- ── ROW LEVEL SECURITY (RLS) POLICIES ────────────────────────────────

-- Enable RLS across all tables
alter table public.shipments enable row level security;
alter table public.documents enable row level security;
alter table public.knowledge_base enable row level security;
alter table public.conversations enable row level security;
alter table public.conversation_messages enable row level security;

-- Read policies: public/anon can read knowledge base and their shipment records
create policy "Allow read on shipments"
    on public.shipments
    for select
    to anon, authenticated
    using (true);

create policy "Allow read on knowledge_base"
    on public.knowledge_base
    for select
    to anon, authenticated
    using (true);

-- Backend service role has full access to all tables
create policy "Service role full access on shipments"
    on public.shipments
    for all
    to service_role
    using (true)
    with check (true);

create policy "Service role full access on documents"
    on public.documents
    for all
    to service_role
    using (true)
    with check (true);

create policy "Service role full access on knowledge_base"
    on public.knowledge_base
    for all
    to service_role
    using (true)
    with check (true);

create policy "Service role full access on conversations"
    on public.conversations
    for all
    to service_role
    using (true)
    with check (true);

create policy "Service role full access on messages"
    on public.conversation_messages
    for all
    to service_role
    using (true)
    with check (true);
