// 目次サイドバーの挙動
(function () {
  var toc = document.getElementById('toc');
  var btn = document.getElementById('toc-toggle');
  var cls = document.getElementById('toc-close');
  var grip = document.getElementById('toc-resize');
  var root = document.documentElement;
  if (!toc) return;

  // ---- 幅の復元 ----
  var saved = localStorage.getItem('tocWidth');
  if (saved) root.style.setProperty('--sidew', saved);

  // ---- 現在のページを強調し、その位置まで送る ----
  var here = location.pathname.split('/').pop() || 'book.html';
  var links = toc.querySelectorAll('a');
  var active = null;
  for (var i = 0; i < links.length; i++) {
    var href = links[i].getAttribute('href') || '';
    if (href.split('#')[0] === here) {
      links[i].parentNode.classList.add('active');
      if (!active) active = links[i];
    }
  }
  if (active) {
    var pos = sessionStorage.getItem('tocScroll');
    if (pos === null) {
      var t = active.offsetTop - toc.clientHeight / 3;
      toc.scrollTop = t > 0 ? t : 0;
    } else {
      toc.scrollTop = parseInt(pos, 10);
    }
  }
  toc.addEventListener('scroll', function () {
    sessionStorage.setItem('tocScroll', toc.scrollTop);
  });

  // ---- 幅の調整 ----
  if (grip) {
    var dragging = false;

    function move(x) {
      var min = 160, max = Math.min(window.innerWidth * 0.5, 640);
      var w = Math.max(min, Math.min(max, x));
      root.style.setProperty('--sidew', w + 'px');
    }

    function start(e) {
      dragging = true;
      grip.classList.add('dragging');
      document.body.classList.add('resizing');
      e.preventDefault();
    }
    function end() {
      if (!dragging) return;
      dragging = false;
      grip.classList.remove('dragging');
      document.body.classList.remove('resizing');
      localStorage.setItem('tocWidth',
        getComputedStyle(root).getPropertyValue('--sidew').trim());
    }

    grip.addEventListener('mousedown', start);
    document.addEventListener('mousemove', function (e) {
      if (dragging) move(e.clientX);
    });
    document.addEventListener('mouseup', end);

    grip.addEventListener('touchstart', start, { passive: false });
    document.addEventListener('touchmove', function (e) {
      if (dragging && e.touches[0]) move(e.touches[0].clientX);
    }, { passive: true });
    document.addEventListener('touchend', end);

    // ダブルクリックで既定幅に戻す
    grip.addEventListener('dblclick', function () {
      root.style.removeProperty('--sidew');
      localStorage.removeItem('tocWidth');
    });
  }

  // ---- 狭い画面での開閉 ----
  function close() { document.body.classList.remove('toc-open'); }
  if (btn) btn.addEventListener('click', function () {
    document.body.classList.toggle('toc-open');
  });
  if (cls) cls.addEventListener('click', close);
  toc.addEventListener('click', function (e) {
    if (e.target.tagName === 'A' && window.innerWidth < 900) close();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close();
  });
})();
