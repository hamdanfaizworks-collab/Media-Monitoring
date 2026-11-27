-- Pengujian isolasi antarworkspace (UAT10, GOV01).
-- Dijalankan sebagai postgres. Seluruh data uji di-rollback melalui RAISE EXCEPTION,
-- sehingga tidak ada data tersisa. Hasil ditampilkan pada pesan error.
-- Hasil yang diharapkan: sources_visible_to_u1=1, workspaces_visible_to_u1=1, cross_insert_allowed=false.

do $$
declare
  u1 uuid := gen_random_uuid();
  u2 uuid := gen_random_uuid();
  wa uuid := gen_random_uuid();
  wb uuid := gen_random_uuid();
  n_src_a int;
  n_ws int;
  n_cross_insert_ok boolean := false;
begin
  insert into auth.users (id, email, aud, role) values
    (u1, 'rls-test-1-' || u1 || '@example.invalid', 'authenticated', 'authenticated'),
    (u2, 'rls-test-2-' || u2 || '@example.invalid', 'authenticated', 'authenticated');
  insert into public.workspaces (id, name) values (wa, 'RLS test A'), (wb, 'RLS test B');
  insert into public.workspace_members (workspace_id, user_id, role) values (wa, u1, 'analyst'), (wb, u2, 'analyst');
  insert into public.sources (workspace_id, name, domain, kind) values
    (wa, 'S-A', 'a.example.invalid', 'news'),
    (wb, 'S-B', 'b.example.invalid', 'news');

  set local role authenticated;
  perform set_config('request.jwt.claims', json_build_object('sub', u1, 'role', 'authenticated')::text, true);
  select count(*) into n_src_a from public.sources;
  select count(*) into n_ws from public.workspaces;
  begin
    insert into public.sources (workspace_id, name, domain, kind) values (wb, 'X', 'x.example.invalid', 'news');
    n_cross_insert_ok := true;
  exception when others then
    n_cross_insert_ok := false;
  end;
  reset role;

  raise exception 'RLS_TEST sources_visible_to_u1=% workspaces_visible_to_u1=% cross_insert_allowed=% (expected 1, 1, false)',
    n_src_a, n_ws, n_cross_insert_ok;
end $$;
