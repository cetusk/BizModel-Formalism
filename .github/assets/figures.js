// HTML版の図。PDF版のTikZとは完全に独立した実装（book.tex側の \insertfig は
// <div class="htmlfig" data-fig="..."> というプレースホルダを出すだけで、
// 実際の描画はここで行う。JS無効環境では <noscript> 内の静的SVGにフォールバックする。
(function () {
  'use strict';
  var SVGNS = 'http://www.w3.org/2000/svg';
  var XHTMLNS = 'http://www.w3.org/1999/xhtml';

  // ---------- 汎用DOMヘルパー ----------
  function el(tag, attrs) {
    var e = document.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function text(x, y, str, cls, anchor) {
    var t = el('text', { x: x, y: y, 'text-anchor': anchor || 'middle' });
    if (cls) t.setAttribute('class', cls);
    t.textContent = str;
    return t;
  }
  function svgRoot(vbw, vbh) {
    return el('svg', { viewBox: '0 0 ' + vbw + ' ' + vbh, role: 'img' });
  }
  // mathmlHTML は本ファイル内で手書きした固定文字列のみを渡す（外部/利用者データは含めない）
  // cls は text() の class 相当（fig-muted/fig-label）。指定時は対応するCSSと同じ色・サイズを直接指定する
  // （foreignObject 内は SVG の class セレクタが効かないため fill/font-size を明示する必要がある）。
  var CLS_STYLE = {
    'fig-muted': 'color:var(--muted); font-size:.72rem;',
    'fig-label': 'color:var(--fg); font-size:.78rem;',
    'fig-tick': 'color:var(--muted); font-size:.66rem;'
  };
  function mathLabel(cx, cy, mathmlHTML, w, h, cls) {
    var fo = el('foreignObject', { x: cx - w / 2, y: cy - h / 2, width: w, height: h });
    fo.style.overflow = 'visible';
    var div = document.createElementNS(XHTMLNS, 'div');
    div.style.cssText = 'width:100%;height:100%;display:flex;align-items:center;justify-content:center;' +
      'white-space:nowrap;' +
      "font-family:'LM Math','LM Roman',serif;" + (cls && CLS_STYLE[cls] ? CLS_STYLE[cls] : '');
    div.innerHTML = mathmlHTML;
    fo.appendChild(div);
    return fo;
  }

  // ---------- 和文と数式記号（κ π δ ε Φ τ 等）が混在するラベル ----------
  // 文字列を自動でギリシャ文字/数式記号部分（<mi>）と地の文（<mtext>）に分割し、
  // 1個の <math> に混在させて描画する。MathML はネイティブに mtext を挟めるため
  // 手組みの水平レイアウトが不要。地の文と数式記号が混じる図中ラベル全般に使う。
  var MATH_CHAR_RE = /[κπδεΦτ]/;
  function splitMathText(str) {
    var parts = [], buf = '', bufIsMath = null;
    for (var i = 0; i < str.length; i++) {
      var ch = str[i], isMath = MATH_CHAR_RE.test(ch);
      if (bufIsMath === null) bufIsMath = isMath;
      if (isMath !== bufIsMath) { parts.push({ math: bufIsMath, s: buf }); buf = ''; bufIsMath = isMath; }
      buf += ch;
    }
    if (buf) parts.push({ math: bufIsMath, s: buf });
    return parts;
  }
  function escapeXml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  // 和文全角・数式記号とも概算 12 単位/字（凡例の幅見積もりと同じ基準）で幅を確保する。
  function smartWidth(str) { return str.length * 16 + 10; }
  function smartMathML(str) {
    return '<math>' + splitMathText(str).map(function (p) {
      return p.math ? '<mi>' + escapeXml(p.s) + '</mi>' : '<mtext>' + escapeXml(p.s) + '</mtext>';
    }).join('') + '</math>';
  }
  // text() の代替。ギリシャ文字/数式記号を含む文字列だけ自動でMathML経由（Latin Modern）にする。
  function smartText(cx, cy, str, cls, anchor, h) {
    if (!MATH_CHAR_RE.test(str)) return text(cx, cy, str, cls, anchor);
    var w = smartWidth(str);
    var x = cx;
    if (anchor === 'end') x = cx - w / 2;
    else if (anchor === 'start') x = cx + w / 2;
    return mathLabel(x, cy - 6, smartMathML(str), w, h || 20, cls);
  }

  // ---------- ツールチップ（全図共通の単一インスタンス） ----------
  var Tooltip = (function () {
    var node;
    function ensure() {
      if (!node) {
        node = document.createElement('div');
        node.className = 'chart-tooltip';
        document.body.appendChild(node);
      }
      return node;
    }
    function show(title, rows, clientX, clientY) {
      var n = ensure();
      n.textContent = '';
      if (title) {
        var t = document.createElement('div');
        t.className = 'tt-title';
        t.textContent = title;
        n.appendChild(t);
      }
      rows.forEach(function (r) {
        var row = document.createElement('div');
        row.className = 'tt-row';
        var key = document.createElement('span');
        key.className = 'tt-key' + (r.colorClass ? ' ' + r.colorClass : '');
        row.appendChild(key);
        var name = document.createElement('span');
        name.className = 'tt-name';
        name.textContent = r.name;
        row.appendChild(name);
        var val = document.createElement('span');
        val.className = 'tt-val';
        val.textContent = r.value;
        row.appendChild(val);
        n.appendChild(row);
      });
      n.classList.add('visible');
      position(clientX, clientY);
    }
    function position(clientX, clientY) {
      var n = ensure();
      var pad = 14;
      var rect = n.getBoundingClientRect();
      var x = clientX + pad, y = clientY + pad;
      if (x + rect.width > window.innerWidth - 8) x = clientX - rect.width - pad;
      if (y + rect.height > window.innerHeight - 8) y = clientY - rect.height - pad;
      n.style.left = x + 'px';
      n.style.top = y + 'px';
    }
    function hide() { if (node) node.classList.remove('visible'); }
    return { show: show, hide: hide };
  })();

  // ---------- スケール ----------
  function linearScale(domain, range) {
    var d0 = domain[0], d1 = domain[1], r0 = range[0], r1 = range[1];
    return function (v) { return r0 + (v - d0) / (d1 - d0) * (r1 - r0); };
  }
  function logScale(domain, range) {
    var d0 = Math.log10(domain[0]), d1 = Math.log10(domain[1]), r0 = range[0], r1 = range[1];
    return function (v) { return r0 + (Math.log10(v) - d0) / (d1 - d0) * (r1 - r0); };
  }

  var M = { top: 20, right: 22, bottom: 40, left: 48 }; // 標準プロットマージン

  function drawFrame(svg, W, H, m, yTicks, yFmt, yScale, xLabelY) {
    var g = el('g', { class: 'fig-axis' });
    yTicks.forEach(function (t) {
      var y = yScale(t);
      g.appendChild(el('line', { class: 'fig-gridline', x1: m.left, x2: W - m.right, y1: y, y2: y }));
      g.appendChild(text(m.left - 8, y + 3, yFmt(t), 'fig-tick', 'end'));
    });
    g.appendChild(el('line', { x1: m.left, x2: m.left, y1: m.top, y2: H - m.bottom }));
    g.appendChild(el('line', { x1: m.left, x2: W - m.right, y1: H - m.bottom, y2: H - m.bottom }));
    svg.appendChild(g);
  }

  // ---------- 棒グラフ（1〜2系列のグループ化対応） ----------
  function barChart(container, opts) {
    var W = 640, H = 340;
    var m = { top: 20, right: 20, bottom: 56, left: 46 };
    var svg = svgRoot(W, H);
    var plotW = W - m.left - m.right, plotH = H - m.top - m.bottom;
    var y = linearScale([0, opts.yMax], [H - m.bottom, m.top]);
    drawFrame(svg, W, H, m, opts.yTicks, opts.yFmt, y, 0);

    var n = opts.categories.length, s = opts.series.length;
    var slot = plotW / n;
    var barW = Math.min(24, slot * 0.72 / s);
    var groupW = barW * s + (s > 1 ? 4 * (s - 1) : 0);

    opts.categories.forEach(function (cat, ci) {
      var cx = m.left + slot * ci + slot / 2;
      var gx0 = cx - groupW / 2;
      opts.series.forEach(function (ser, si) {
        var v = opts.data[cat.key][ser.key];
        if (v == null) return;
        var bx = gx0 + si * (barW + 4);
        var by = y(v), bh = (H - m.bottom) - by;
        var bar = el('rect', {
          class: 'fig-bar fig-mark ' + ser.colorClass,
          x: bx, y: by, width: barW, height: Math.max(0, bh), rx: 3, ry: 3
        });
        var hit = el('rect', {
          class: 'fig-hit', x: bx - 2, y: m.top, width: barW + 4, height: plotH
        });
        (function (cat, ser, v) {
          function on(evt) {
            Tooltip.show(cat.label, [{ colorClass: ser.colorClass, name: ser.label, value: opts.fmt(v) }],
              evt.clientX, evt.clientY);
            bar.classList.add('is-active');
          }
          hit.addEventListener('pointermove', on);
          hit.addEventListener('pointerenter', on);
          hit.addEventListener('pointerleave', function () { Tooltip.hide(); });
          hit.tabIndex = 0;
          hit.addEventListener('focus', function (e) {
            var r = hit.getBoundingClientRect();
            on({ clientX: r.left + r.width / 2, clientY: r.top });
          });
          hit.addEventListener('blur', function () { Tooltip.hide(); });
        })(cat, ser, v);
        svg.appendChild(bar);
        if (opts.valueLabel) {
          svg.appendChild(text(bx + barW / 2, by - 6, opts.valueLabel(v), 'fig-tick'));
        }
        svg.appendChild(hit);
      });
      svg.appendChild(text(cx, H - m.bottom + 16, cat.label, 'fig-tick'));
    });

    if (opts.series.length > 1) svg.appendChild(legend(opts.series, W, m));
    if (opts.yAxisLabel) {
      svg.appendChild(text(m.left - 30, m.top - 8, opts.yAxisLabel, 'fig-muted', 'middle'));
    }
    container.appendChild(svg);
  }

  // 凡例。和文混じりのラベル幅は文字数からの粗い見積もり（1文字12単位、
  // 全角想定の安全側の値）で確保する。DOM未接続の時点で呼ばれるため getBBox は使わない。
  function legendItemWidth(label) { return 17 + label.length * 12 + 20; }
  function legend(series, W, m) {
    var g = el('g', { class: 'fig-legend' });
    var totalW = series.reduce(function (a, s) { return a + legendItemWidth(s.label); }, 0);
    var x = W - m.right - totalW;
    if (x < m.left) x = m.left;
    series.forEach(function (s) {
      g.appendChild(el('rect', { class: s.colorClass, x: x, y: 2, width: 12, height: 12, rx: 2 }));
      var t = text(x + 17, 12, s.label, null, 'start');
      g.appendChild(t);
      x += legendItemWidth(s.label);
    });
    return g;
  }

  // ---------- 折れ線グラフ（複数系列、線形/対数） ----------
  function lineChart(container, opts) {
    var W = 640, H = 340;
    // 右余白: 原図（TikZ）は凡例ではなく各線の終点に直接ラベルを置く（末尾の年の右）ため、
    // その分のスペースを確保する。
    var m = { top: 20, right: 58, bottom: 34, left: opts.leftMargin || 46 };
    var svg = svgRoot(W, H);
    var plotW = W - m.left - m.right;
    var xs = opts.xValues;
    var x = linearScale([xs[0], xs[xs.length - 1]], [m.left, W - m.right]);
    var y = opts.log ? logScale(opts.yDomain, [H - m.bottom, m.top]) : linearScale(opts.yDomain, [H - m.bottom, m.top]);
    drawFrame(svg, W, H, m, opts.yTicks, opts.yFmt, y, 0);

    if (opts.refLine != null) {
      var ry = y(opts.refLine);
      svg.appendChild(el('line', {
        x1: m.left, x2: W - m.right, y1: ry, y2: ry,
        stroke: 'var(--muted)', 'stroke-width': 1, 'stroke-dasharray': '3,3'
      }));
    }

    opts.series.forEach(function (ser) {
      var d = ser.values.map(function (v, i) {
        return (i === 0 ? 'M' : 'L') + x(xs[i]).toFixed(1) + ',' + y(v).toFixed(1);
      }).join(' ');
      svg.appendChild(el('path', { class: 'fig-line ' + ser.colorClass, d: d }));
    });

    // x軸目盛
    var xTickEvery = opts.xTickEvery || 1;
    xs.forEach(function (xv, i) {
      if (i % xTickEvery !== 0 && i !== xs.length - 1) return;
      svg.appendChild(text(x(xv), H - m.bottom + 16, opts.xFmt ? opts.xFmt(xv) : xv, 'fig-tick'));
    });

    // クロスヘア + 全系列ツールチップ（最も近いXにスナップ）
    var hit = el('rect', { class: 'fig-hit', x: m.left, y: m.top, width: plotW, height: H - m.top - m.bottom });
    var crosshair = el('line', { class: 'fig-crosshair', y1: m.top, y2: H - m.bottom, visibility: 'hidden' });
    var dots = opts.series.map(function (ser) {
      var d = el('circle', { class: 'fig-dot ' + ser.colorClass, r: 4, visibility: 'hidden' });
      svg.appendChild(d);
      return d;
    });
    svg.appendChild(crosshair);

    function nearestIndex(clientX) {
      var svgRect = svg.getBoundingClientRect();
      var scaleX = svgRect.width / W;
      var localX = (clientX - svgRect.left) / scaleX;
      var best = 0, bestD = Infinity;
      xs.forEach(function (xv, i) {
        var d = Math.abs(x(xv) - localX);
        if (d < bestD) { bestD = d; best = i; }
      });
      return best;
    }
    function onMove(evt) {
      var i = nearestIndex(evt.clientX);
      var xv = xs[i];
      crosshair.setAttribute('x1', x(xv));
      crosshair.setAttribute('x2', x(xv));
      crosshair.setAttribute('visibility', 'visible');
      var rows = [];
      opts.series.forEach(function (ser, si) {
        var v = ser.values[i];
        dots[si].setAttribute('cx', x(xv));
        dots[si].setAttribute('cy', y(v));
        dots[si].setAttribute('visibility', 'visible');
        rows.push({ colorClass: ser.colorClass, name: ser.label, value: opts.fmt(v) });
      });
      Tooltip.show(opts.xFmt ? opts.xFmt(xv) : String(xv), rows, evt.clientX, evt.clientY);
    }
    function onLeave() {
      crosshair.setAttribute('visibility', 'hidden');
      dots.forEach(function (d) { d.setAttribute('visibility', 'hidden'); });
      Tooltip.hide();
    }
    hit.addEventListener('pointermove', onMove);
    hit.addEventListener('pointerenter', onMove);
    hit.addEventListener('pointerleave', onLeave);
    hit.tabIndex = 0;
    hit.addEventListener('keydown', function (e) {
      var cur = dots[0].getAttribute('visibility') === 'visible' ?
        xs.indexOf(parseFloat(crosshair.getAttribute('x1')) ? xs[nearestIndexFromAttr()] : xs[0]) : 0;
      function nearestIndexFromAttr() {
        var cx = parseFloat(crosshair.getAttribute('x1'));
        var best = 0, bestD = Infinity;
        xs.forEach(function (xv, i) { var d = Math.abs(x(xv) - cx); if (d < bestD) { bestD = d; best = i; } });
        return best;
      }
      var idx = cur;
      if (e.key === 'ArrowRight') idx = Math.min(xs.length - 1, idx + 1);
      else if (e.key === 'ArrowLeft') idx = Math.max(0, idx - 1);
      else return;
      e.preventDefault();
      var r = svg.getBoundingClientRect();
      var scaleX = r.width / W;
      onMove({ clientX: r.left + x(xs[idx]) * scaleX, clientY: r.top + y(opts.yDomain[0]) * (r.height / H) });
    });
    svg.appendChild(hit);

    // 系列ラベルは原図同様、凡例ではなく各線の終点の右に直接置く（refLineLabel も同列で扱う）。
    // 終点の高さが近い系列は重なるため、最小間隔を確保して上下にずらす。
    (function () {
      var xEnd = x(xs[xs.length - 1]) + 6;
      var items = opts.series.map(function (ser) {
        return { y: y(ser.values[ser.values.length - 1]), label: ser.label, cls: ser.colorClass };
      });
      if (opts.refLine != null) {
        items.push({ y: y(opts.refLine), label: opts.refLineLabel || '', cls: null });
      }
      items.sort(function (a, b) { return a.y - b.y; });
      var minGap = 13, lo = m.top + 6, hi = H - m.bottom - 6;
      for (var i = 1; i < items.length; i++) {
        if (items[i].y - items[i - 1].y < minGap) items[i].y = items[i - 1].y + minGap;
      }
      // 下端で軸ラベル（年度）と衝突しないよう、あふれた分だけ集団ごと上へ戻す
      var overflow = items.length ? items[items.length - 1].y - hi : 0;
      if (overflow > 0) items.forEach(function (it) { it.y -= overflow; });
      if (items.length && items[0].y < lo) items.forEach(function (it) { it.y += lo - items[0].y; });
      items.forEach(function (it) {
        var t = text(xEnd, it.y + 4, it.label, it.cls || 'fig-muted', 'start');
        t.style.fontSize = '.7rem';
        svg.appendChild(t);
      });
    })();
    if (opts.yAxisLabel) {
      svg.appendChild(text(m.left - 30, m.top - 8, opts.yAxisLabel, 'fig-muted', 'middle'));
    }
    if (opts.xAxisLabel) {
      svg.appendChild(text(W - m.right + 4, H - m.bottom + 28, opts.xAxisLabel, 'fig-muted', 'start'));
    }
    container.appendChild(svg);
  }

  // ================================================================
  // データ図5件
  // ================================================================

  function figCccTrend(container) {
    var cats = [
      { key: 't1', label: '10億円以上' }, { key: 't2', label: '1億~10億円' },
      { key: 't3', label: '5千万~1億円' }, { key: 't4', label: '2千万~5千万' },
      { key: 't5', label: '1千万~2千万' }, { key: 't6', label: '1千万円未満' }
    ];
    var data = {
      t1: { dso: 71, dpo: 44 }, t2: { dso: 61, dpo: 47 }, t3: { dso: 47, dpo: 37 },
      t4: { dso: 49, dpo: 39 }, t5: { dso: 53, dpo: 35 }, t6: { dso: 35, dpo: 21 }
    };
    barChart(container, {
      categories: cats, data: data,
      series: [
        { key: 'dso', label: 'DSO（売上債権）', colorClass: 'fig-series-1' },
        { key: 'dpo', label: 'DPO（仕入債務）', colorClass: 'fig-series-2' }
      ],
      yMax: 80, yTicks: [0, 20, 40, 60, 80], yFmt: function (v) { return v; },
      yAxisLabel: '日', fmt: function (v) { return v + ' 日'; }
    });
  }

  function figFeeLadder(container) {
    var cats = [
      { key: 'a', label: 'Stripe' }, { key: 'b', label: 'Polar' }, { key: 'c', label: 'Paddle' },
      { key: 'd', label: 'Gumroad直販' }, { key: 'e', label: 'App Store小' },
      { key: 'f', label: 'App Store標準' }, { key: 'g', label: 'Gumroad Discover' }
    ];
    var data = { a: { v: 3.6 }, b: { v: 5.0 }, c: { v: 6.0 }, d: { v: 14.5 }, e: { v: 15.0 }, f: { v: 30.0 }, g: { v: 34.5 } };
    barChart(container, {
      categories: cats, data: data,
      series: [{ key: 'v', label: '実効料率', colorClass: 'fig-series-1' }],
      yMax: 40, yTicks: [0, 10, 20, 30, 40], yFmt: function (v) { return v; },
      yAxisLabel: '%', fmt: function (v) { return v + ' %'; },
      valueLabel: function (v) { return v.toFixed(1); }
    });
  }

  var GSTAR_YEARS = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];
  var GSTAR_VALUES = [38.5, 30.4, 34.8, 42.3, 46.7, 47.3, 46.4, 43.0, 26.4, 26.2, 38.0, 36.3, 36.9, 44.0, 45.5, 47.1, 49.0, 52.4, 50.4, 41.8, 31.5, 37.6, 40.4, 45.7, 49.2];

  function figGstarTrend(container) {
    lineChart(container, {
      xValues: GSTAR_YEARS, xTickEvery: 4,
      xFmt: function (y) { return y; }, xAxisLabel: '年度', yAxisLabel: '%',
      series: [{ key: 'g', label: 'm/CCC', colorClass: 'fig-series-1', values: GSTAR_VALUES }],
      yDomain: [20, 60], yTicks: [20, 30, 40, 50, 60], yFmt: function (v) { return v; },
      refLine: 41.1, refLineLabel: '平均 41.1',
      fmt: function (v) { return v.toFixed(1) + ' %'; }
    });
  }

  var LAG_YEARS = GSTAR_YEARS;
  var LAG_CCC = [24.9, 26.5, 25.4, 23.7, 24.0, 24.4, 24.8, 26.6, 27.0, 28.0, 27.1, 28.4, 28.8, 28.7, 29.6, 30.6, 30.0, 30.4, 31.9, 32.5, 35.4, 36.4, 36.2, 36.9, 37.2];
  var LAG_NET = [9.8, 11.2, 9.8, 9.1, 9.9, 9.9, 10.3, 11.0, 12.3, 12.5, 12.2, 12.9, 13.3, 13.5, 13.8, 14.9, 14.9, 14.6, 15.2, 15.8, 17.5, 18.4, 17.7, 18.5, 18.5];

  function figLagCorr(container) {
    lineChart(container, {
      xValues: LAG_YEARS, xTickEvery: 4,
      xFmt: function (y) { return y; }, xAxisLabel: '年度', yAxisLabel: '日',
      series: [
        { key: 'ccc', label: 'CCC', colorClass: 'fig-series-1', values: LAG_CCC },
        { key: 'net', label: 'DSO－DPO', colorClass: 'fig-series-2', values: LAG_NET }
      ],
      yDomain: [0, 40], yTicks: [0, 10, 20, 30, 40], yFmt: function (v) { return v; },
      fmt: function (v) { return v.toFixed(1) + ' 日'; }
    });
  }

  function figMediaPanel(container) {
    var years = [2020, 2021, 2022, 2023, 2024]; // R2-R6
    var labels = ['R2', 'R3', 'R4', 'R5', 'R6'];
    var magnetic = [1307, 1630, 1338, 1916, 1904];
    var paper = [775, 758, 668, 764, 845];
    var server = [16, 15, 17, 16, 17];
    var ic = [15, 14, 16, 15, 15];
    lineChart(container, {
      xValues: years, xTickEvery: 1,
      xFmt: function (y) { return labels[years.indexOf(y)]; },
      xAxisLabel: '年度', yAxisLabel: '滞留日数',
      log: true, leftMargin: 52,
      series: [
        { key: 'mag', label: '磁気型', colorClass: 'fig-series-1', values: magnetic },
        { key: 'pap', label: '紙型', colorClass: 'fig-series-2', values: paper },
        { key: 'srv', label: 'サーバ型', colorClass: 'fig-series-3', values: server },
        { key: 'ic', label: 'IC型', colorClass: 'fig-series-4', values: ic }
      ],
      yDomain: [10, 2000], yTicks: [10, 100, 1000], yFmt: function (v) { return v.toLocaleString(); },
      fmt: function (v) { return v.toLocaleString() + ' 日'; }
    });
  }

  // ================================================================
  // 概念図7件（データを持たない静的な模式図。ホバーは付けない）
  // ================================================================

  function box(x, y, w, h, label, cls) {
    var g = el('g');
    g.appendChild(el('rect', { class: 'fig-box fig-boxfill', x: x, y: y, width: w, height: h, rx: 4 }));
    var t = text(x + w / 2, y + h / 2 + 4, label, cls || 'fig-label');
    t.setAttribute('text-anchor', 'middle');
    g.appendChild(t);
    return g;
  }
  function arrow(x1, y1, x2, y2) {
    var g = el('g');
    g.appendChild(el('line', { class: 'fig-arrow', x1: x1, y1: y1, x2: x2, y2: y2 }));
    var ang = Math.atan2(y2 - y1, x2 - x1);
    var ah = 7;
    var p1x = x2 - ah * Math.cos(ang - Math.PI / 7), p1y = y2 - ah * Math.sin(ang - Math.PI / 7);
    var p2x = x2 - ah * Math.cos(ang + Math.PI / 7), p2y = y2 - ah * Math.sin(ang + Math.PI / 7);
    g.appendChild(el('polygon', { class: 'fig-arrowhead', points: x2 + ',' + y2 + ' ' + p1x + ',' + p1y + ' ' + p2x + ',' + p2y }));
    return g;
  }
  // 矢じり単体（角度 ang [rad] の方向を指す）を (x,y) の位置に描く
  function arrowheadAt(x, y, ang) {
    var ah = 7;
    var p1x = x - ah * Math.cos(ang - Math.PI / 7), p1y = y - ah * Math.sin(ang - Math.PI / 7);
    var p2x = x - ah * Math.cos(ang + Math.PI / 7), p2y = y - ah * Math.sin(ang + Math.PI / 7);
    return el('polygon', { class: 'fig-arrowhead', points: x + ',' + y + ' ' + p1x + ',' + p1y + ' ' + p2x + ',' + p2y });
  }

  function figCollider(container) {
    // 元図（collider.tex）: Φ を左上、ε を左下、S を右に置き、両方から S へ矢印。
    // Φ と ε の間には「条件づけで生じる見かけの相関」を示す湾曲した双方向矢印を引く。
    var W = 560, H = 300;
    var svg = svgRoot(W, H);
    var phiBox = { x: 30, y: 40, w: 190, h: 56 };
    var epsBox = { x: 30, y: 204, w: 190, h: 56 };
    var sBox = { x: 340, y: 122, w: 190, h: 56 };
    [phiBox, epsBox, sBox].forEach(function (b, i) {
      svg.appendChild(el('rect', {
        x: b.x, y: b.y, width: b.w, height: b.h, rx: 6,
        class: i === 2 ? 'fig-box' : 'fig-box fig-boxfill', fill: i === 2 ? 'var(--side)' : null
      }));
    });
    svg.appendChild(mathLabel(phiBox.x + phiBox.w / 2, phiBox.y + 20,
      '<math><mi>Φ</mi><mtext>：ビジネスモデル</mtext></math>', 180, 20));
    svg.appendChild(text(phiBox.x + phiBox.w / 2, phiBox.y + 44, '調べたい構造', 'fig-muted'));
    svg.appendChild(mathLabel(epsBox.x + epsBox.w / 2, epsBox.y + 20,
      '<math><mi>ε</mi><mtext>：衝撃・運</mtext></math>', 180, 20));
    svg.appendChild(text(epsBox.x + epsBox.w / 2, epsBox.y + 44, '外生的な変動', 'fig-muted'));
    svg.appendChild(mathLabel(sBox.x + sBox.w / 2, sBox.y + 20,
      '<math><mi>S</mi><mtext>：生存・開示</mtext></math>', 180, 20));
    svg.appendChild(mathLabel(sBox.x + sBox.w / 2, sBox.y + 44,
      '<math><mi>S</mi><mo>=</mo><mn>1</mn><mtext> で条件づけ</mtext></math>', 180, 18));
    svg.appendChild(arrow(phiBox.x + phiBox.w, phiBox.y + phiBox.h / 2, sBox.x, sBox.y + sBox.h / 2 - 10));
    svg.appendChild(arrow(epsBox.x + epsBox.w, epsBox.y + epsBox.h / 2, sBox.x, sBox.y + sBox.h / 2 + 10));
    // Φ⇔ε の湾曲した双方向矢印（見かけの相関）
    var cx1 = phiBox.x + phiBox.w + 60, cx2 = epsBox.x + epsBox.w + 60;
    var py = phiBox.y + phiBox.h, ey = epsBox.y;
    var sx = phiBox.x + phiBox.w - 10, ex = epsBox.x + epsBox.w - 10;
    var c1x = cx1, c1y = py + 30, c2x = cx2, c2y = ey - 30;
    var curve = 'M' + sx + ',' + py + ' C' + c1x + ',' + c1y + ' ' + c2x + ',' + c2y + ' ' + ex + ',' + ey;
    svg.appendChild(el('path', { d: curve, class: 'fig-arrow', 'stroke-dasharray': '4,3' }));
    svg.appendChild(arrowheadAt(sx, py, Math.atan2(py - c1y, sx - c1x))); // Φ側の矢じり
    svg.appendChild(arrowheadAt(ex, ey, Math.atan2(ey - c2y, ex - c2x))); // ε側の矢じり
    svg.appendChild(text((c1x + c2x) / 2 + 26, (py + ey) / 2, '条件づけで生じる', 'fig-muted'));
    svg.appendChild(text((c1x + c2x) / 2 + 26, (py + ey) / 2 + 16, '見かけの相関', 'fig-muted'));
    container.appendChild(svg);
  }

  function figCreditFormation(container) {
    var W = 560, H = 300, m = { left: 40, right: 20, top: 44, bottom: 34 };
    var svg = svgRoot(W, H);
    var x0 = m.left, x1 = W - m.right, xm = (x0 + x1) / 2;
    var y0 = H - m.bottom, y1 = m.top;
    var xm = x0 + (x1 - x0) * 0.42;   // 退職
    var x2 = x0 + (x1 - x0) * 0.56;   // 競業避止の終了
    svg.appendChild(el('line', { x1: x0, x2: x0, y1: y1, y2: y0, class: 'fig-baseline' }));
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: y0, y2: y0, class: 'fig-baseline' }));
    svg.appendChild(text(x1 - 4, y0 + 16, '時間', 'fig-muted', 'end'));
    // 退職〜競業避止の終了の網掛けと縦の目印
    svg.appendChild(el('rect', { x: xm, y: y1, width: x2 - xm, height: y0 - y1, fill: 'var(--line)', opacity: .35 }));
    svg.appendChild(el('line', { x1: xm, x2: xm, y1: y1, y2: y0, stroke: 'var(--muted)', 'stroke-dasharray': '4,3' }));
    svg.appendChild(el('line', { x1: x2, x2: x2, y1: y1, y2: y0, stroke: 'var(--muted)', 'stroke-dasharray': '4,3' }));
    svg.appendChild(text(xm, y1 + 14, '退職', 'fig-tick'));
    svg.appendChild(text(x2, y1 + 14, '競業避止の終了', 'fig-tick'));
    // 利用可能な信用: 在職中は高い水準で一定→退職で急落しゼロ近くで一定（原図では両区間とも水平）
    svg.appendChild(el('path', {
      class: 'fig-line fig-series-1',
      d: 'M' + x0 + ',' + (y0 - 130) + ' L' + xm + ',' + (y0 - 130) + ' L' + xm + ',' + (y0 - 10) + ' L' + x1 + ',' + (y0 - 10)
    }));
    // 変換原資: 退職前後で緩やかに山なりになり、その後も高い水準を保ったまま緩降下する
    var d2 = 'M' + x0 + ',' + (y0 - 70);
    d2 += ' C' + (x0 + (xm - x0) * 0.5) + ',' + (y0 - 95) + ' ' + (xm - 20) + ',' + (y0 - 140) + ' ' + xm + ',' + (y0 - 150);
    d2 += ' C' + (xm + (x1 - xm) * 0.35) + ',' + (y0 - 125) + ' ' + (xm + (x1 - xm) * 0.7) + ',' + (y0 - 95) + ' ' + x1 + ',' + (y0 - 60);
    svg.appendChild(el('path', { class: 'fig-line fig-series-2', d: d2 }));
    // 変換の自由度: 競業避止の終了までは低いまま、そこで一段上がる（在職中の守秘義務が解ける）
    svg.appendChild(el('path', {
      class: 'fig-line fig-series-3',
      d: 'M' + x0 + ',' + (y0 - 20) + ' L' + x2 + ',' + (y0 - 20) + ' L' + x2 + ',' + (y0 - 190) + ' L' + x1 + ',' + (y0 - 190)
    }));
    // 系列ラベルは原図同様、凡例ではなく各線の近くに直接置く
    (function () {
      var l1 = text(x0 + 4, y0 - 130 - 8, '利用可能な信用', 'fig-series-1', 'start');
      l1.style.fontSize = '.72rem'; svg.appendChild(l1);
      var l2 = text(x0 + (x1 - x0) * 0.26, y0 - 100, '変換原資', 'fig-series-2', 'start');
      l2.style.fontSize = '.72rem'; svg.appendChild(l2);
      var l3 = text(x0 + (x1 - x0) * 0.635, y0 - 190 - 8, '変換の自由度', 'fig-series-3', 'start');
      l3.style.fontSize = '.72rem'; svg.appendChild(l3);
    })();
    svg.appendChild(text((xm + x2) / 2, y0 + 16, '原資は減衰を始めるが変換できない', 'fig-tick'));
    container.appendChild(svg);
  }

  function figDeadline(container) {
    var W = 560, H = 280, m = { left: 40, right: 40, top: 30, bottom: 30 };
    var svg = svgRoot(W, H);
    var x0 = m.left, x1 = W - m.right, y0 = H - m.bottom, y1 = m.top;
    svg.appendChild(el('line', { x1: x0, x2: x0, y1: y1, y2: y0, class: 'fig-baseline' }));
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: y0, y2: y0, class: 'fig-baseline' }));
    svg.appendChild(text(x1 - 4, y0 + 16, '時間', 'fig-muted', 'end'));
    svg.appendChild(text(m.left, y1 - 8, '資産', 'fig-muted', 'middle'));
    // 下限（原図: 軸最大4.6に対し1.5の高さ＝32.6%）
    var floorY = y0 - (y0 - y1) * 0.326;
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: floorY, y2: floorY, stroke: 'var(--muted)', 'stroke-dasharray': '3,3' }));
    svg.appendChild(text(x1 + 4, floorY + 4, '下限', 'fig-muted', 'start'));
    // 給与所得者: (0,2.3)→(8.6,4.0) と R1/R2 より低い位置から始まり右肩上がり（原図に忠実、凡例ではなく直接ラベル）
    var salStartY = y0 - (y0 - y1) * 0.5, salEndY = y0 - (y0 - y1) * 0.87;
    svg.appendChild(el('path', { class: 'fig-line fig-series-1', d: 'M' + x0 + ',' + salStartY + ' L' + x1 + ',' + salEndY }));
    var salLabelX = x0 + (x1 - x0) * 0.23;
    var salLabel = text(salLabelX, salStartY + (salEndY - salStartY) * 0.23 - 8, '給与所得者', 'fig-series-1', 'start');
    salLabel.style.fontSize = '.72rem';
    svg.appendChild(salLabel);
    // R1・R2 は共通の始点 (0,3.5) から分岐する（原図では給与所得者より高い位置から出発）
    var r12StartY = y0 - (y0 - y1) * 0.76;
    // R1: 期限に向けて減少しゼロで打ち切り
    var r1end = x0 + (x1 - x0) * 0.62;
    svg.appendChild(el('path', { class: 'fig-line fig-series-2', d: 'M' + x0 + ',' + r12StartY + ' L' + r1end + ',' + y0 }));
    svg.appendChild(el('circle', { class: 'fig-dot fig-series-2', cx: r1end, cy: y0, r: 4 }));
    var r1Label = text(x0 + (x1 - x0) * 0.42, y0 - (y0 - y1) * 0.24, 'R1', 'fig-series-2', 'start');
    r1Label.style.fontSize = '.72rem';
    svg.appendChild(r1Label);
    // R2: 下限で下げ止まる
    var r2bendX = x0 + (x1 - x0) * 0.36;
    svg.appendChild(el('path', { class: 'fig-line fig-series-3', d: 'M' + x0 + ',' + r12StartY + ' L' + r2bendX + ',' + floorY + ' L' + x1 + ',' + floorY }));
    var r2Label = text(x0 + (x1 - x0) * 0.8, floorY - 8, 'R2', 'fig-series-3', 'middle');
    r2Label.style.fontSize = '.72rem';
    svg.appendChild(r2Label);
    svg.appendChild(mathLabel(r1end, y0 + 16, '<math><mi>τ</mi><mo>=</mo><mi>E</mi><mo>(</mo><mn>0</mn><mo>)</mo><mo>/</mo><mi>c</mi></math>', 90, 20));
    container.appendChild(svg);
  }

  function figGrowthFcf(container) {
    // 元図（growth-fcf.tex）: 縦軸は -1.2〜3.2 で g=0 の縦軸交点（1.5, どちらの直線も共有）が
    // 全体の61%の高さに来る非対称な範囲。CCC>0 は g=8 で -1.0 まで（横軸=0のさらに下）下がり、
    // CCC<0 は 2.9 まで上がる。2直線は横軸切片ではなく、この共有の縦軸切片から分岐する。
    var W = 520, H = 300, m = { left: 56, right: 90, top: 34, bottom: 34 };
    var svg = svgRoot(W, H);
    var x0 = m.left, x1 = W - m.right, y0 = H - m.bottom, y1 = m.top;
    var zeroY = y0 - (y0 - y1) * 0.273;   // g軸（FCF/r=0）
    var startY = y0 - (y0 - y1) * 0.614;  // 共有の縦軸切片 m+d-I/r
    var cccPosEndY = y0 - (y0 - y1) * 0.045;
    var cccNegEndY = y0 - (y0 - y1) * 0.932;
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: zeroY, y2: zeroY, stroke: 'var(--rule)' }));
    svg.appendChild(el('line', { x1: x0, x2: x0, y1: y1, y2: y0, stroke: 'var(--rule)' }));
    var xIntercept = x0 + (x1 - x0) * 0.585;
    svg.appendChild(el('path', { class: 'fig-line fig-series-1', d: 'M' + x0 + ',' + startY + ' L' + x1 + ',' + cccPosEndY }));
    svg.appendChild(el('path', { class: 'fig-line fig-series-2', d: 'M' + x0 + ',' + startY + ' L' + x1 + ',' + cccNegEndY }));
    svg.appendChild(el('line', { x1: xIntercept, x2: xIntercept, y1: zeroY, y2: zeroY + 30, stroke: 'var(--muted)', 'stroke-dasharray': '3,3' }));
    svg.appendChild(mathLabel(xIntercept, zeroY + 42, '<math><msup><mi>g</mi><mo>⋆</mo></msup></math>', 30, 20));
    // 縦軸: FCF/r（FCFは \FCF=\mathrm{FCF} の立体、Φではない）、横軸: g
    svg.appendChild(mathLabel(x0 - 4, y1 - 18,
      '<math><mi mathvariant="normal">F</mi><mi mathvariant="normal">C</mi><mi mathvariant="normal">F</mi><mo>/</mo><mi>r</mi></math>', 70, 20));
    svg.appendChild(mathLabel(x1 - 6, H - 10, '<math><mi>g</mi></math>', 20, 18));
    // 縦軸切片: m+d-I/r（両直線が分岐する共有の始点）
    svg.appendChild(mathLabel(x0 - 6, startY - 4,
      '<math><mi>m</mi><mo>+</mo><mi>d</mi><mo>&#8722;</mo><mfrac><mi>I</mi><mi>r</mi></mfrac></math>', 90, 22));
    // 直線右端に直接ラベル（凡例ではなく原図と同じ直接注記）
    svg.appendChild(mathLabel(x1 + 40, cccPosEndY, '<math><mi mathvariant="normal">C</mi><mi mathvariant="normal">C</mi><mi mathvariant="normal">C</mi><mo>&gt;</mo><mn>0</mn></math>', 74, 18));
    svg.appendChild(mathLabel(x1 + 40, cccNegEndY, '<math><mi mathvariant="normal">C</mi><mi mathvariant="normal">C</mi><mi mathvariant="normal">C</mi><mo>&lt;</mo><mn>0</mn></math>', 74, 18));
    container.appendChild(svg);
  }

  // 2x2の象限図。左側に行ラベル（上段／下段、κ等の数式混在可）、
  // 上下に列方向の説明、任意で列ごとの下部注記（kappa-scheduleの権利/行使の乖離など）、
  // 任意で1セルの強調（accent色の薄い塗り、solo-quadrantの「実現可能領域」など）を持つ。
  function quadrantDiagram(container, opts) {
    // 左のラベル（「κ<0 前受」等）は文字数が多いため、上下より広いサイド余白を確保する。
    var W = 760, H = 400, mTop = 46, mSide = 170, mBottom = 46;
    var cw = (W - 2 * mSide) / 2, ch = (H - mTop - mBottom) / 2;
    var svg = svgRoot(W, H);
    svg.appendChild(el('line', { x1: mSide, x2: W - mSide, y1: H / 2, y2: H / 2, class: 'fig-baseline' }));
    svg.appendChild(el('line', { x1: W / 2, x2: W / 2, y1: mTop, y2: H - mBottom, class: 'fig-baseline' }));
    var cells = [
      { x: mSide, y: mTop, i: 0 }, { x: W / 2, y: mTop, i: 1 },
      { x: mSide, y: H / 2, i: 2 }, { x: W / 2, y: H / 2, i: 3 }
    ];
    cells.forEach(function (c) {
      var cell = opts.cells[c.i];
      var strong = !!cell.strong;
      var r = el('rect', {
        x: c.x + 4, y: c.y + 4, width: cw - 8, height: ch - 8, rx: 5,
        class: strong ? 'fig-box' : 'fig-box fig-boxfill',
        fill: strong ? 'var(--accent)' : null
      });
      if (strong) { r.setAttribute('opacity', '.15'); }
      svg.appendChild(r);
      var lines = [cell.title].concat(cell.lines || []);
      var cy0 = c.y + ch / 2 - (lines.length - 1) * 9;
      lines.forEach(function (line, li) {
        svg.appendChild(smartText(c.x + cw / 2, cy0 + li * 18, line, li === 0 ? 'fig-label' : 'fig-muted', 'middle'));
      });
    });
    var colX = [mSide + cw / 2, W / 2 + cw / 2];
    // 上部注記は原図（TikZ）でも左右の列ごとに別々に置かれており、中央にまたがる
    // 単一キャプションではない。topCols も bottomCols と同じ列位置に揃える。
    opts.topCols.forEach(function (colLabel, ci) {
      svg.appendChild(typeof colLabel === 'function'
        ? colLabel(colX[ci], mTop - 16)
        : smartText(colX[ci], mTop - 16, colLabel, 'fig-muted', 'middle'));
    });
    svg.appendChild(smartText(mSide - 10, mTop + ch / 2, opts.rowTop, 'fig-muted', 'end'));
    svg.appendChild(smartText(mSide - 10, H / 2 + ch / 2, opts.rowBottom, 'fig-muted', 'end'));
    if (opts.bottomCols) {
      opts.bottomCols.forEach(function (colLabel, ci) {
        svg.appendChild(typeof colLabel === 'function'
          ? colLabel(colX[ci], H - mBottom + 40)
          : smartText(colX[ci], H - mBottom + 40, colLabel, 'fig-muted', 'middle'));
      });
    }
    container.appendChild(svg);
  }

  function figKappaSchedule(container) {
    quadrantDiagram(container, {
      topCols: ['π が δ と独立', 'π が δ に連動'],
      rowTop: 'κ<0 決済が先行', rowBottom: 'κ>0 決済が後行',
      bottomCols: [
        function (cx, cy) {
          return mathLabel(cx, cy - 6, '<math><mtext>権利 </mtext><mover><mi>δ</mi><mo>&#175;</mo></mover>' +
            '<mtext> と行使 </mtext><mi>δ</mi><mtext> が乖離しうる</mtext></math>', 220, 20, 'fig-muted');
        },
        'δ に張り付くため乖離しない'
      ],
      cells: [
        { title: '前受・定額型', lines: ['サブスク、会費', '保険料、ギフトカード', 'オプション・保証'] },
        { title: '前受・精算型', lines: ['プリペイド従量', '予約＋当日精算', '受注生産の前金'] },
        { title: '後払・定額型', lines: ['月額後払サブスク', '基本料金、保守契約', 'リース・レンタル'] },
        { title: '後払・連動型', lines: ['従量課金、成果報酬', 'レベニューシェア', '掛売・卸'] }
      ]
    });
  }

  function figSoloQuadrant(container) {
    quadrantDiagram(container, {
      topCols: ['履行が人手に依存', '履行が複製可能'],
      rowTop: 'κ<0 前受', rowBottom: 'κ>0 後払',
      cells: [
        { title: '頭打ち', lines: ['前受コンサル', '受注制作の前金', '容量が先に尽きる'] },
        { title: '実現可能領域', strong: true, lines: ['年払いSaaS', 'デジタル商品の売切り', '掲載課金・スポンサー'] },
        { title: '成立しない', lines: ['成果報酬', '受託の後払い', '与信も容量も不足'] },
        { title: '条件付き可', lines: ['月末後払いSaaS', '広告・レベニューシェア', 'κ は小さいが正'] }
      ]
    });
  }

  function figPhiQuadrant(container) {
    // 元図（phi-quadrant.tex）: D(t) は原点から右上へ引く1本の対角線（基準線）。
    // その上側の三角形が κ<0（顧客が企業に与信）、下側の三角形が κ>0（企業が顧客に与信）。
    // 上辺・左辺に沿う破線（即時決済の極限）と、右辺・下辺に沿う点線（決済を最大限遅らせる極限）で
    // P(t) の取りうる範囲を境界づける（原図の dashed/dotted の「への字」）。
    var W = 480, H = 300, m = { left: 44, right: 90, top: 20, bottom: 34 };
    var svg = svgRoot(W, H);
    var x0 = m.left, x1 = W - m.right, y0 = H - m.bottom, y1 = m.top;
    svg.appendChild(el('polygon', { points: x0 + ',' + y0 + ' ' + x0 + ',' + y1 + ' ' + x1 + ',' + y1, fill: 'var(--line)', opacity: .45 }));
    svg.appendChild(el('polygon', { points: x0 + ',' + y0 + ' ' + x1 + ',' + y1 + ' ' + x1 + ',' + y0, fill: 'var(--line)', opacity: .2 }));
    svg.appendChild(el('line', { x1: x0, x2: x0, y1: y1, y2: y0, class: 'fig-baseline' }));
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: y0, y2: y0, class: 'fig-baseline' }));
    // 前受の極限（左上の「への字」、破線）
    svg.appendChild(el('path', {
      d: 'M' + x0 + ',' + y0 + ' L' + x0 + ',' + y1 + ' L' + x1 + ',' + y1,
      stroke: 'var(--muted)', 'stroke-width': 1.4, 'stroke-dasharray': '6,3', fill: 'none'
    }));
    // 後払の極限（右下の「への字」、点線）
    svg.appendChild(el('path', {
      d: 'M' + x0 + ',' + y0 + ' L' + x1 + ',' + y0 + ' L' + x1 + ',' + y1,
      stroke: 'var(--muted)', 'stroke-width': 1.4, 'stroke-dasharray': '1.5,3', fill: 'none'
    }));
    svg.appendChild(el('path', { class: 'fig-line fig-series-1', d: 'M' + x0 + ',' + y0 + ' L' + x1 + ',' + y1 }));
    svg.appendChild(text(x0 - 4, y1 - 4, '累積額', 'fig-muted', 'end'));
    svg.appendChild(mathLabel(x1 - 8, y0 + 16, '<math><mi>t</mi></math>', 20, 18));
    svg.appendChild(mathLabel(x0 + (x1 - x0) * 0.45 + 16, y0 + (y1 - y0) * 0.45 + 12,
      '<math><mi>D</mi><mo>(</mo><mi>t</mi><mo>)</mo></math>', 40, 18));
    svg.appendChild(mathLabel((x0 + x1) / 2 - 30, y1 + (y0 - y1) * 0.28, '<math><mi>κ</mi><mo>&lt;</mo><mn>0</mn><mtext>：顧客が企業に与信</mtext></math>', 200, 20));
    svg.appendChild(mathLabel((x0 + x1) / 2 + 20, y1 + (y0 - y1) * 0.72, '<math><mi>κ</mi><mo>&gt;</mo><mn>0</mn><mtext>：企業が顧客に与信</mtext></math>', 200, 20));
    svg.appendChild(mathLabel(x1 + 42, y1 + 6, '<math><mi>P</mi><mo>(</mo><mi>t</mi><mo>)</mo><mtext> 前受</mtext></math>', 84, 18));
    svg.appendChild(mathLabel(x1 + 42, y0 - 6, '<math><mi>P</mi><mo>(</mo><mi>t</mi><mo>)</mo><mtext> 後払</mtext></math>', 84, 18));
    container.appendChild(svg);
  }

  // ================================================================
  // ディスパッチ
  // ================================================================
  var REGISTRY = {
    'ccc-trend': figCccTrend, 'fee-ladder': figFeeLadder, 'gstar-trend': figGstarTrend,
    'lag-corr': figLagCorr, 'media-panel': figMediaPanel,
    'collider': figCollider, 'credit-formation': figCreditFormation, 'deadline': figDeadline,
    'growth-fcf': figGrowthFcf, 'kappa-schedule': figKappaSchedule,
    'phi-quadrant': figPhiQuadrant, 'solo-quadrant': figSoloQuadrant
  };

  document.querySelectorAll('.htmlfig[data-fig]').forEach(function (c) {
    var name = c.getAttribute('data-fig');
    var fn = REGISTRY[name];
    if (fn) {
      try { fn(c); } catch (e) { /* 失敗時は noscript フォールバックの静的SVGに委ねる */ console.error('figure render failed:', name, e); }
    }
  });
})();
