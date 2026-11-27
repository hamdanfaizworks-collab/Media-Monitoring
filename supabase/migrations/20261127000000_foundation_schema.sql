-- Fondasi skema Media Monitoring & PR Intelligence (PRD v1.0, bagian 16 & GOV01).
-- Setiap data bisnis memiliki workspace_id. Akses dibatasi dengan RLS berbasis membership.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Akses: workspaces, memberships, roles
-- ---------------------------------------------------------------------------
create table public.workspaces (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  timezone    text not null default 'Asia/Jakarta',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id      uuid not null references auth.users(id) on delete cascade,
  role         text not null check (role in (
                 'workspace_admin', 'analyst', 'pr_officer', 'pr_manager', 'viewer'
               )),
  created_at   timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

-- Helper untuk RLS. SECURITY DEFINER agar tidak rekursif terhadap RLS tabel membership.
create or replace function public.is_workspace_member(ws uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.workspace_members m
    where m.workspace_id = ws and m.user_id = auth.uid()
  );
$$;

create or replace function public.has_workspace_role(ws uuid, roles text[])
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.workspace_members m
    where m.workspace_id = ws
      and m.user_id = auth.uid()
      and m.role = any (roles)
  );
$$;

revoke execute on function public.is_workspace_member(uuid) from anon;
revoke execute on function public.has_workspace_role(uuid, text[]) from anon;

-- ---------------------------------------------------------------------------
-- Akuisisi: registry sumber (ACQ01) dan dokumen (ACQ02, ACQ05)
-- ---------------------------------------------------------------------------
create table public.sources (
  id                      uuid primary key default gen_random_uuid(),
  workspace_id            uuid not null references public.workspaces(id) on delete cascade,
  name                    text not null,
  domain                  text not null,
  kind                    text not null check (kind in ('news', 'social')),
  national_or_regional    text not null default 'nasional' check (national_or_regional in ('nasional', 'daerah')),
  timezone                text not null default 'Asia/Jakarta',
  -- Sumber tidak boleh dijadwalkan sebelum aturan akses disetujui (ACQ01).
  status                  text not null default 'pending' check (status in ('pending', 'active', 'partial', 'blocked', 'disabled')),
  access_basis            text,
  activation_approved_by  uuid references auth.users(id),
  activation_approved_at  timestamptz,
  maintainer_pic          text,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now(),
  unique (workspace_id, domain),
  constraint active_requires_approval check (
    status <> 'active' or (access_basis is not null and activation_approved_at is not null)
  )
);

create table public.documents (
  id              uuid primary key default gen_random_uuid(),
  workspace_id    uuid not null references public.workspaces(id) on delete cascade,
  source_id       uuid references public.sources(id) on delete set null,
  platform        text not null check (platform in ('news', 'x', 'instagram', 'facebook', 'tiktok', 'youtube', 'threads', 'linkedin')),
  url             text not null,
  canonical_url   text not null,
  title           text,
  body            text,                       -- hanya jika hak penggunaan mengizinkan (ACQ02)
  summary        text,
  author          text,
  category        text,
  published_at    timestamptz,                -- NULL bila tidak diketahui; jangan diisi fetched_at (PRD 15)
  discovered_at   timestamptz not null default now(),
  fetched_at      timestamptz,
  processed_at    timestamptz,
  indexed_at      timestamptz,
  first_seen_at   timestamptz not null default now(),
  last_seen_at    timestamptz not null default now(),
  content_hash    text,
  parser_version  text,
  access_method   text not null default 'http' check (access_method in ('http', 'browser', 'metadata_only', 'api', 'manual')),
  -- Penanda hasil backfill agar tidak memicu breaking news alert (OPS03).
  is_backfill     boolean not null default false,
  -- Cluster sindikasi (ACQ05). Repost tetap dihitung sebagai amplifikasi.
  cluster_id      uuid,
  deleted_at      timestamptz,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (workspace_id, canonical_url),
  fts tsvector generated always as (
    to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(body, ''))
  ) stored
);

create index documents_workspace_published_idx on public.documents (workspace_id, published_at desc);
create index documents_fts_idx on public.documents using gin (fts);
create index documents_content_hash_idx on public.documents (workspace_id, content_hash);

-- ---------------------------------------------------------------------------
-- Monitoring: topik dan kecocokan (MON01)
-- ---------------------------------------------------------------------------
create table public.topics (
  id           uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  name         text not null,
  -- Query Boolean (AND/OR/NOT, kurung, frasa). Versi query dicatat untuk laporan.
  query_text   text not null,
  query_version integer not null default 1,
  aliases      text[] not null default '{}',
  keywords     text[] not null default '{}',
  hashtags     text[] not null default '{}',
  excluded_terms text[] not null default '{}',
  is_active    boolean not null default false,
  created_by   uuid references auth.users(id),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

create table public.topic_matches (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  topic_id     uuid not null references public.topics(id) on delete cascade,
  document_id  uuid not null references public.documents(id) on delete cascade,
  query_version integer not null,
  matched_at   timestamptz not null default now(),
  primary key (topic_id, document_id)
);

-- ---------------------------------------------------------------------------
-- Audit (PRD bagian 16: audit_events). Hanya dapat ditambah, tidak diubah.
-- ---------------------------------------------------------------------------
create table public.audit_events (
  id           bigint generated always as identity primary key,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  actor_id     uuid references auth.users(id),
  action       text not null,
  entity       text not null,
  entity_id    uuid,
  detail       jsonb not null default '{}'::jsonb,
  created_at   timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- RLS: semua tabel bisnis wajib RLS (UAT10, GOV01)
-- ---------------------------------------------------------------------------
alter table public.workspaces        enable row level security;
alter table public.workspace_members enable row level security;
alter table public.sources           enable row level security;
alter table public.documents         enable row level security;
alter table public.topics            enable row level security;
alter table public.topic_matches     enable row level security;
alter table public.audit_events      enable row level security;

create policy workspaces_select on public.workspaces
  for select to authenticated using (public.is_workspace_member(id));

create policy workspaces_update_admin on public.workspaces
  for update to authenticated
  using (public.has_workspace_role(id, array['workspace_admin']))
  with check (public.has_workspace_role(id, array['workspace_admin']));

create policy members_select on public.workspace_members
  for select to authenticated using (public.is_workspace_member(workspace_id));

create policy members_admin_write on public.workspace_members
  for all to authenticated
  using (public.has_workspace_role(workspace_id, array['workspace_admin']))
  with check (public.has_workspace_role(workspace_id, array['workspace_admin']));

create policy sources_select on public.sources
  for select to authenticated using (public.is_workspace_member(workspace_id));

create policy sources_write on public.sources
  for all to authenticated
  using (public.has_workspace_role(workspace_id, array['workspace_admin', 'analyst']))
  with check (public.has_workspace_role(workspace_id, array['workspace_admin', 'analyst']));

create policy documents_select on public.documents
  for select to authenticated using (public.is_workspace_member(workspace_id));

create policy topics_select on public.topics
  for select to authenticated using (public.is_workspace_member(workspace_id));

create policy topics_write on public.topics
  for all to authenticated
  using (public.has_workspace_role(workspace_id, array['workspace_admin', 'analyst']))
  with check (public.has_workspace_role(workspace_id, array['workspace_admin', 'analyst']));

create policy topic_matches_select on public.topic_matches
  for select to authenticated using (public.is_workspace_member(workspace_id));

create policy audit_select_admin on public.audit_events
  for select to authenticated using (public.has_workspace_role(workspace_id, array['workspace_admin']));

-- Penulisan dokumen dan audit dilakukan worker/server dengan secret server (GOV01).
-- Tidak ada policy INSERT/UPDATE/DELETE untuk authenticated pada documents dan audit_events.
-- Audit tidak boleh diubah. Penghapusan tetap diizinkan agar hapus workspace (cascade) dan retensi berjalan.
create or replace function public.forbid_audit_update()
returns trigger language plpgsql as $$
begin
  raise exception 'audit_events is append-only';
end;
$$;

create trigger audit_events_no_update
  before update on public.audit_events
  for each row execute function public.forbid_audit_update();

-- Akses anon tidak diberikan pada tabel bisnis.
revoke all on all tables in schema public from anon;
