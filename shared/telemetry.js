// ESC 텔레메트리 — 가명 이벤트 로거 (비의료, PII 없음)
// 초기: console + localStorage 링버퍼. 추후 Firehose→S3 이벤트의 원형.
// 임상지표(d′ 등)는 여기 사용자 비노출 데이터로만 파생, 화면 표기 금지.
(function (global) {
  var ANON_KEY = 'esc_anon_id';
  var BUF_KEY = 'esc_events';
  var BUF_CAP = 500;

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
    return rec;
  }

  function dump() { try { return JSON.parse(localStorage.getItem(BUF_KEY) || '[]'); } catch (e) { return []; } }
  function clear() { localStorage.removeItem(BUF_KEY); }

  global.ESCT = { anonId: anonId, log: log, dump: dump, clear: clear };
})(window);
