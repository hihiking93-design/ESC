// ESC 진정 인터루드 — 3호흡 그라운딩 (⑥심리안정). 세션 끝/모드 사이 공용.
// Interlude.run(onDone, {cycles}) → 오버레이 표시 후 onDone() 호출.
(function (global) {
  function run(onDone, opts) {
    opts = opts || {};
    var cycles = opts.cycles || 3;
    var IN = 4000, HOLD = 1500, OUT = 4000; // 들숨4 · 멈춤1.5 · 날숨4 (ms)

    var ov = document.createElement('div');
    ov.id = 'esc-interlude';
    ov.style.cssText =
      'position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;align-items:center;' +
      'justify-content:center;background:linear-gradient(160deg,#0b1220,#1e293b);color:#e2e8f0;' +
      'font-family:inherit;opacity:0;transition:opacity .5s ease;';
    ov.innerHTML =
      '<div style="font-size:17px;letter-spacing:.02em;margin-bottom:34px;opacity:.85">잠깐, 숨을 천천히 쉬어볼까요</div>' +
      '<div id="esc-il-circle" style="width:150px;height:150px;border-radius:50%;' +
        'background:radial-gradient(circle at 35% 30%,#60a5fa,#2563eb);transform:scale(.55);' +
        'transition:transform 4s ease-in-out;box-shadow:0 0 60px rgba(96,165,250,.45)"></div>' +
      '<div id="esc-il-label" style="margin-top:34px;font-size:20px;font-weight:600;min-height:26px">준비…</div>' +
      '<div id="esc-il-count" style="margin-top:6px;font-size:13px;opacity:.6"></div>' +
      '<button id="esc-il-skip" style="position:absolute;bottom:28px;background:transparent;border:0;' +
        'color:#94a3b8;font-size:13px;cursor:pointer;text-decoration:underline">건너뛰기</button>';
    document.body.appendChild(ov);
    requestAnimationFrame(function () { ov.style.opacity = '1'; });

    var circle = ov.querySelector('#esc-il-circle');
    var label = ov.querySelector('#esc-il-label');
    var count = ov.querySelector('#esc-il-count');
    var timers = [];
    var done = false;

    function t(fn, ms) { var id = setTimeout(fn, ms); timers.push(id); }
    function finish() {
      if (done) return; done = true;
      timers.forEach(clearTimeout);
      ov.style.opacity = '0';
      setTimeout(function () { if (ov.parentNode) ov.parentNode.removeChild(ov); if (onDone) onDone(); }, 500);
    }
    ov.querySelector('#esc-il-skip').onclick = finish;

    function cycle(n) {
      if (done) return;
      if (n > cycles) { label.textContent = '좋아요'; count.textContent = ''; t(finish, 900); return; }
      count.textContent = n + ' / ' + cycles;
      // 들숨
      label.textContent = '들이쉬고…';
      circle.style.transitionDuration = (IN / 1000) + 's';
      circle.style.transform = 'scale(1)';
      t(function () {
        // 멈춤
        label.textContent = '잠시 멈춤';
        t(function () {
          // 날숨
          label.textContent = '내쉬고…';
          circle.style.transitionDuration = (OUT / 1000) + 's';
          circle.style.transform = 'scale(.55)';
          t(function () { cycle(n + 1); }, OUT);
        }, HOLD);
      }, IN);
    }
    t(function () { cycle(1); }, 700);
  }

  global.Interlude = { run: run };
})(window);
