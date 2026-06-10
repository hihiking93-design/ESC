// ESC 데일리 — 오늘의 영역 로테이션 + 일일 퀘스트 (텔레메트리 기반, 로컬)
(function (global) {
  var PILLARS = [
    { id:'listening', name:'듣기', face:'quokka_listen',   c:'--m-listen',    href:'listening.html', emoji:'🎧' },
    { id:'focus',     name:'집중', face:'friend_owl',      c:'--m-focus',     href:'focus.html',     emoji:'🦉' },
    { id:'speed',     name:'속도', face:'friend_rabbit',   c:'--m-speed',     href:'schulte.html',   emoji:'🐰' },
    { id:'challenge', name:'도전', face:'friend_hedgehog', c:'--m-challenge', href:'stroop.html',    emoji:'🦔' },
    { id:'grit',      name:'끈기', face:'friend_turtle',   c:'--m-grit',      href:'grit.html',      emoji:'🐢' },
    { id:'calm',      name:'진정', face:'quokka_calm',     c:'--m-calm',      href:'calm.html',      emoji:'🫧' }
  ];
  function todayKey() { var d = new Date(); return d.getFullYear() + '-' + (d.getMonth()+1) + '-' + d.getDate(); }
  function dayIndex() { var d = new Date(); return Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000); }
  function todayPillar() { return PILLARS[((dayIndex() % 6) + 6) % 6]; }

  function todayEvents() {
    try {
      var key = todayKey();
      return (ESCT.dump() || []).filter(function (e) {
        if (e.event !== 'session_completed') return false;
        var t = new Date(e.ts);
        return (t.getFullYear() + '-' + (t.getMonth()+1) + '-' + t.getDate()) === key;
      });
    } catch (e) { return []; }
  }
  function stats() {
    var ev = todayEvents(), games = {};
    ev.forEach(function (e) { games[(e.game || e.mode || '?')] = 1; });
    return { plays: ev.length, variety: Object.keys(games).length };
  }
  function quests() {
    var s = stats();
    return [
      { id:'count',   label:'오늘 2판 완료',      cur: Math.min(s.plays, 2),   target:2, done: s.plays >= 2 },
      { id:'variety', label:'서로 다른 게임 2개', cur: Math.min(s.variety, 2), target:2, done: s.variety >= 2 }
    ];
  }
  function allDone() { return quests().every(function (q) { return q.done; }); }

  global.ESCDaily = { pillars: PILLARS, todayKey: todayKey, todayPillar: todayPillar, stats: stats, quests: quests, allDone: allDone };
})(window);
