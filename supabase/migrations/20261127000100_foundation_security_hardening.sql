-- Hardening keamanan lanjutan (sudah diterapkan ke project development sebagai foundation_security_hardening).
revoke execute on function public.is_workspace_member(uuid) from public, anon;
revoke execute on function public.has_workspace_role(uuid, text[]) from public, anon;
grant execute on function public.is_workspace_member(uuid) to authenticated;
grant execute on function public.has_workspace_role(uuid, text[]) to authenticated;

alter function public.forbid_audit_update() set search_path = public;
