// 目次サイドバーの挙動
(function () {
  var toc = document.getElementById('toc');
  var btn = document.getElementById('toc-toggle');
  var cls = document.getElementById('toc-close');
  if (!toc) return;

  // 現在のページに対応する項目を強調し、その位置までスクロールする
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
    // 復元したスクロール位置がなければ現在項目を見せる
    var saved = sessionStorage.getItem('tocScroll');
    if (saved === null) {
      var t = active.offsetTop - toc.clientHeight / 3;
      toc.scrollTop = t > 0 ? t : 0;
    } else {
      toc.scrollTop = parseInt(saved, 10);
    }
  }

  // ページ遷移してもスクロール位置を保つ
  toc.addEventListener('scroll', function () {
    sessionStorage.setItem('tocScroll', toc.scrollTop);
  });

  // 狭い画面での開閉
  function open() { document.body.classList.add('toc-open'); }
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
