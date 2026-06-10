// ESC 텔레메트리 — 가명 이벤트 로거 (비의료, PII 없음)
// 초기: console + localStorage 링버퍼. 추후 Firehose→S3 이벤트의 원형.
// 임상지표(d′ 등)는 여기 사용자 비노출 데이터로만 파생, 화면 표기 금지.
(function (global) {
  var ANON_KEY = 'esc_anon_id';
  var BUF_KEY = 'esc_events';
  var BUF_CAP = 500;
  // Supabase 익명 통계 동기화 (anon=공개키, RLS로 INSERT만 허용)
  var SB_URL = 'https://nxyahagtfnlrsegvjxgi.supabase.co';
  var SB_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im54eWFoYWd0Zm5scnNlZ3ZqeGdpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwNzk3NzgsImV4cCI6MjA5NjY1NTc3OH0.EFWrHilevUFrhiHrFly5JdhiAXWYLRtN_YBezbHsRDc';

  function anonId() {
    var id = localStorage.getItem(ANON_KEY);
    if (!id) {
      id = (global.crypto && crypto.randomUUID)
        ? crypto.randomUUID()
        : 'anon-' + Date.now().toString(36) + '-' + Math.floor(performance.now()).toString(36);
      localStorage.setItem(ANON_KEY, id);
    }
    return id;
  }

  function log(event, props) {
    var rec = Object.assign({ event: event, anonId: anonId(), ts: new Date().toISOString() }, props || {});
    try {
      var buf = JSON.parse(localStorage.getItem(BUF_KEY) || '[]');
      buf.push(rec);
      while (buf.length > BUF_CAP) buf.shift();
      localStorage.setItem(BUF_KEY, JSON.stringify(buf));
    } catch (e) { /* 저장 실패는 무시 */ }
    if (global.console) console.log('[ESC]', event, rec);
    if (event === 'session_completed') syncSupabase(rec);
    return rec;
  }

  function syncSupabase(rec) {
    if (!SB_URL || SB_URL.indexOf('http') !== 0) return;
    var nick = null; try { nick = localStorage.getItem('esc_nick') || null; } catch (e) {}
    try {
      fetch(SB_URL + '/rest/v1/esc_sessions', {
        method: 'POST',
        headers: { 'apikey': SB_ANON, 'Authorization': 'Bearer ' + SB_ANON, 'Content-Type': 'application/json', 'Prefer': 'return=minimal' },
        body: JSON.stringify({
          anon_id: rec.anonId,
          nickname: nick,
          game: (rec.game || rec.mode || null),
          mode: (rec.mode || null),
          accuracy: (typeof rec.overallAccuracy === 'number' ? rec.overallAccuracy : null),
          payload: rec
        }),
        keepalive: true
      }).catch(function () {});
    } catch (e) {}
  }

  function dump() { try { return JSON.parse(localStorage.getItem(BUF_KEY) || '[]'); } catch (e) { return []; } }
  function clear() { localStorage.removeItem(BUF_KEY); }

  global.ESCT = { anonId: anonId, log: log, dump: dump, clear: clear };
})(window);
