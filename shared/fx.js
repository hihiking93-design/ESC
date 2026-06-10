// ESC 축하 FX — 컨페티 (전 게임 결과 공용). FX.confetti()
(function (global) {
  var COLORS = ['#4C82E8','#2FB8A6','#E68A4E','#7C6CE0','#4FB477','#46AEC9','#F0892A','#E5634D','#FFC93C'];
  function confetti(n) {
    n = n || 110;
    for (var i = 0; i < n; i++) {
      (function (k) {
        var c = document.createElement('div');
        c.className = 'confetti';
        c.style.left = (Math.random() * 100) + 'vw';
        c.style.background = COLORS[k % COLORS.length];
        c.style.width = (6 + Math.random() * 8) + 'px';
        c.style.height = (10 + Math.random() * 9) + 'px';
        c.style.animationDuration = (2.2 + Math.random() * 2.1) + 's';
        c.style.animationDelay = (Math.random() * 0.5) + 's';
        document.body.appendChild(c);
        setTimeout(function () { if (c.parentNode) c.parentNode.removeChild(c); }, 5200);
      })(i);
    }
  }
  global.FX = { confetti: confetti };
})(window);
