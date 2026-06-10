-- ESC 익명 세션 통계 (개인정보 최소 — 익명ID·닉네임·게임·정확도·시각만)
-- Supabase SQL Editor에 붙여넣고 Run.

create table if not exists public.esc_sessions (
  id          bigint generated always as identity primary key,
  anon_id     text not null,
  nickname    text,
  game        text,
  mode        text,
  accuracy    numeric,
  payload     jsonb,
  created_at  timestamptz not null default now()
);

alter table public.esc_sessions enable row level security;

-- 익명(anon) 키로는 INSERT만 허용, SELECT는 막음(프라이버시).
-- 교사/관리자 통계 조회는 service_role 또는 대시보드에서.
drop policy if exists "esc anon insert" on public.esc_sessions;
create policy "esc anon insert"
  on public.esc_sessions for insert to anon
  with check (true);

create index if not exists esc_sessions_game_idx on public.esc_sessions (game);
create index if not exists esc_sessions_anon_idx on public.esc_sessions (anon_id);
create index if not exists esc_sessions_created_idx on public.esc_sessions (created_at);
