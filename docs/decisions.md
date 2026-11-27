# Keputusan awal

Dokumen ini mencatat keputusan yang sudah disetujui atau diterapkan pada fondasi. Sumber lengkap ada di PRD v1.0 (23 Oktober 2026).

| Tanggal | Keputusan | Dasar |
|---|---|---|
| 2026-11-27 | Stack aplikasi web: Next.js + TypeScript | Disetujui pemilik produk |
| 2026-11-27 | Stack worker scraping dan analisis: Python (Scrapy, Playwright) | Disetujui pemilik produk; PRD bagian 16 |
| 2026-11-27 | Region Supabase: `ap-southeast-2` (Sydney), project "Media Monitoring" | Disetujui pemilik produk |
| 2026-11-27 | Project Supabase yang dipakai saat ini adalah development | Tahap pengembangan (PRD bagian 19) |
| 2026-11-27 | Semua tabel bisnis memiliki `workspace_id` dan RLS aktif | PRD bagian 16, GOV01 |
| 2026-11-27 | Dokumen dan kecocokan topik disimpan per workspace, bukan dibagi lintas workspace | Isolasi data (UAT10) lebih sederhana dan lebih aman |
| 2026-11-27 | Penulisan dokumen dan audit dilakukan worker dengan secret server, bukan dari browser | GOV01 |
| 2026-11-27 | `audit_events` bersifat append-only (update diblokir oleh trigger) | PRD bagian 16, audit |
| 2026-11-27 | Sumber sosial tidak dapat berstatus `active` tanpa `access_basis` dan persetujuan aktivasi | ACQ01, bagian 5 (PoC sosial) |

## Belum diputuskan

- Dua platform sosial pertama (ditentukan setelah PoC).
- Industri, entitas awal, pesaing, dan pengguna pilot (pemilik produk).
- Daftar sumber berita pilot dan status aksesnya.
- Ambang alert dan kebutuhan penjagaan (pemilik organisasi dan engineering).
- Paket Supabase dan anggaran operasional.
