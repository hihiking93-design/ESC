// ESC 효과음 — Web Audio 합성 (에셋 불필요). SFX.play('correct') 등.
// 음소거: localStorage esc_sound='off'. 사용자 제스처(탭)에서 호출되므로 autoplay 정책 OK.
(function (global) {
  var ctx = null;
  function ac() {
    if (!ctx) { try { ctx = new (global.AudioContext || global.webkitAudioContext)(); } catch (e) {} }
    if (ctx && ctx.state === 'suspended') { try { ctx.resume(); } catch (e) {} }
    return ctx;
  }
  function tone(c, freq, t0, dur, type, gain) {
    var o = c.createOscillator(), g = c.createGain();
    o.type = type || 'sine'; o.frequency.value = freq;
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(gain || 0.16, t0 + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g); g.connect(c.destination);
    o.start(t0); o.stop(t0 + dur + 0.03);
  }
  function muted() { try { return localStorage.getItem('esc_sound') === 'off'; } catch (e) { return false; } }

  var SFX = {
    muted: muted,
    setMuted: function (on) { try { localStorage.setItem('esc_sound', on ? 'off' : 'on'); } catch (e) {} },
    play: function (name) {
      if (muted()) return;
      var c = ac(); if (!c) return; var t = c.currentTime;
      switch (name) {
        case 'tap':     tone(c, 440, t, 0.10, 'sine', 0.10); break;
        case 'select':  tone(c, 560, t, 0.10, 'triangle', 0.13); break;
        case 'correct': tone(c, 660, t, 0.12, 'sine', 0.17); tone(c, 988, t + 0.09, 0.20, 'sine', 0.17); break;
        case 'wrong':   tone(c, 311, t, 0.14, 'sine', 0.15); tone(c, 233, t + 0.10, 0.22, 'sine', 0.15); break;
        case 'star':    tone(c, 880, t, 0.08, 'triangle', 0.13); tone(c, 1320, t + 0.06, 0.12, 'triangle', 0.11); break;
        case 'complete':[523, 659, 784, 1047].forEach(function (f, i) { tone(c, f, t + i * 0.10, 0.24, 'triangle', 0.15); }); break;
      }
    }
  };
  global.SFX = SFX;
})(window);
