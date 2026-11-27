# Media-Monitoring

Sistem media monitoring dan public relations intelligence untuk media nasional Indonesia dan percakapan sosial publik. Spesifikasi lengkap ada di PRD v1.0.

## Struktur

- `docs/` — keputusan dan dokumentasi produk (`decisions.md`).
- `apps/` — aplikasi web (Next.js + TypeScript). Belum dibuat.
- `workers/` — scraper dan analisis (Python, Scrapy dan Playwright). Belum dibuat.
- `supabase/migrations/` — migrasi skema versi (Supabase Postgres, RLS per workspace).
- `tests/` — pengujian kualitas, keamanan, dan isolasi data. Belum dibuat.

## Status

- Skema fondasi sudah diterapkan ke project development Supabase (`ap-southeast-2`): workspaces, memberships, sources, documents, topics, topic_matches, audit_events, dengan RLS aktif.
- Belum ada aplikasi maupun worker.

## Migrasi

- `20261127000000_foundation_schema.sql` — skema awal dan RLS.
- Migrasi keamanan lanjutan diterapkan langsung ke project development dengan nama `foundation_security_hardening`. Pindahkan isinya ke folder migrasi agar tercatat di repo.

## Lingkungan

Project development: `ovdljunyjgdvwcubvcnd`. Belum ada project production.
