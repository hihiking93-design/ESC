# ESC Supabase 백엔드

익명 학습 세션 통계 수집 + 상위 N% 백분위. **비의료·PII 없음.**

- **Project ref:** `nxyahagtfnlrsegvjxgi` (URL `https://nxyahagtfnlrsegvjxgi.supabase.co`)
- **anon 공개키**는 `shared/telemetry.js`에 있음(공개해도 되는 키, RLS로 INSERT만 허용).
- **Service/Access 토큰은 절대 커밋 금지.**

## 스키마
[`migrations/20260611000000_esc_sessions_and_top_percent.sql`](migrations/20260611000000_esc_sessions_and_top_percent.sql)
- `esc_sessions` 테이블 (anon_id·nickname·game·mode·accuracy·payload·created_at)
- RLS: `anon`은 **INSERT만** (조회 불가 → 개인행 비노출)
- `esc_top_percent(p_anon, p_game)` RPC: SECURITY DEFINER로 집계만 반환(프로필 분포 그래프용)

## 적용 방법
이 프로젝트는 Supabase CLI를 링크하지 않고, Management API로 SQL을 실행해 적용해 왔다.
새 환경에 재현하려면 위 migration SQL을 Supabase **SQL Editor**에 붙여넣고 실행하면 된다.
(또는 `supabase link` 후 `supabase db push`로 CLI 워크플로 전환 가능.)
