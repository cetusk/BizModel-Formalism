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
  function mathLabel(cx, cy, mathmlHTML, w, h) {
    var fo = el('foreignObject', { x: cx - w / 2, y: cy - h / 2, width: w, height: h });
    fo.style.overflow = 'visible';
    var div = document.createElementNS(XHTMLNS, 'div');
    div.style.cssText = 'width:100%;height:100%;display:flex;align-items:center;justify-content:center;' +
      "font-family:'LM Math','LM Roman',serif;";
    div.innerHTML = mathmlHTML;
    fo.appendChild(div);
    return fo;
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

  // ---------- 表トグル（アクセシビリティ: 全データ図に表ビューを添える） ----------
  function addTableToggle(container, caption, headers, rows) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'fig-table-toggle';
    btn.textContent = '表で見る';
    var table = document.createElement('table');
    table.className = 'fig-datatable';
    var thead = document.createElement('thead');
    var htr = document.createElement('tr');
    headers.forEach(function (h) {
      var th = document.createElement('th');
      th.textContent = h;
      htr.appendChild(th);
    });
    thead.appendChild(htr);
    table.appendChild(thead);
    var tbody = document.createElement('tbody');
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      r.forEach(function (v) {
        var td = document.createElement('td');
        td.textContent = v;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    if (caption) {
      var cap = document.createElement('caption');
      cap.style.cssText = 'caption-side:top;text-align:left;font-size:.78rem;color:var(--muted);padding-bottom:.3rem';
      cap.textContent = caption;
      table.insertBefore(cap, thead);
    }
    btn.addEventListener('click', function () {
      var open = table.classList.toggle('visible');
      btn.textContent = open ? '表を閉じる' : '表で見る';
    });
    container.appendChild(btn);
    container.appendChild(table);
  }

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
        svg.appendChild(hit);
      });
      svg.appendChild(text(cx, H - m.bottom + 16, cat.label, 'fig-tick'));
    });

    if (opts.series.length > 1) svg.appendChild(legend(opts.series, W, m));
    if (opts.yAxisLabel) {
      svg.appendChild(text(m.left - 30, m.top - 8, opts.yAxisLabel, 'fig-muted', 'middle'));
    }
    container.appendChild(svg);
    if (opts.table) addTableToggle(container, opts.table.caption, opts.table.headers, opts.table.rows);
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
    var m = { top: 20, right: 20, bottom: 34, left: opts.leftMargin || 46 };
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
      svg.appendChild(text(W - m.right - 4, ry - 5, opts.refLineLabel || '', 'fig-muted', 'end'));
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

    if (opts.series.length > 1) svg.appendChild(legend(opts.series, W, m));
    container.appendChild(svg);
    if (opts.table) addTableToggle(container, opts.table.caption, opts.table.headers, opts.table.rows);
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
      yAxisLabel: '日', fmt: function (v) { return v + ' 日'; },
      table: {
        caption: '資本金階層別のDSOとDPO（全産業、2024年度、単位: 日）',
        headers: ['資本金階層', 'DSO', 'DPO'],
        rows: cats.map(function (c) { return [c.label, data[c.key].dso, data[c.key].dpo]; })
      }
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
      table: {
        caption: '取引額$50における実効料率（プラットフォーム別）',
        headers: ['プラットフォーム', '実効料率'],
        rows: cats.map(function (c) { return [c.label.replace('\n', ' '), data[c.key].v + '%']; })
      }
    });
  }

  var GSTAR_YEARS = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];
  var GSTAR_VALUES = [38.5, 30.4, 34.8, 42.3, 46.7, 47.3, 46.4, 43.0, 26.4, 26.2, 38.0, 36.3, 36.9, 44.0, 45.5, 47.1, 49.0, 52.4, 50.4, 41.8, 31.5, 37.6, 40.4, 45.7, 49.2];

  function figGstarTrend(container) {
    lineChart(container, {
      xValues: GSTAR_YEARS, xTickEvery: 4,
      xFmt: function (y) { return y; },
      series: [{ key: 'g', label: 'm/CCC', colorClass: 'fig-series-1', values: GSTAR_VALUES }],
      yDomain: [20, 60], yTicks: [20, 30, 40, 50, 60], yFmt: function (v) { return v; },
      refLine: 41.1, refLineLabel: '25年平均 41.1%',
      fmt: function (v) { return v.toFixed(1) + ' %'; },
      table: {
        caption: 'm/CCCの推移（全産業、営業利益率ベース、2000〜2024年度）',
        headers: ['年度', 'm/CCC'],
        rows: GSTAR_YEARS.map(function (y, i) { return [y, GSTAR_VALUES[i].toFixed(1) + '%']; })
      }
    });
  }

  var LAG_YEARS = GSTAR_YEARS;
  var LAG_CCC = [24.9, 26.5, 25.4, 23.7, 24.0, 24.4, 24.8, 26.6, 27.0, 28.0, 27.1, 28.4, 28.8, 28.7, 29.6, 30.6, 30.0, 30.4, 31.9, 32.5, 35.4, 36.4, 36.2, 36.9, 37.2];
  var LAG_NET = [9.8, 11.2, 9.8, 9.1, 9.9, 9.9, 10.3, 11.0, 12.3, 12.5, 12.2, 12.9, 13.3, 13.5, 13.8, 14.9, 14.9, 14.6, 15.2, 15.8, 17.5, 18.4, 17.7, 18.5, 18.5];

  function figLagCorr(container) {
    lineChart(container, {
      xValues: LAG_YEARS, xTickEvery: 4,
      xFmt: function (y) { return y; },
      series: [
        { key: 'ccc', label: 'CCC', colorClass: 'fig-series-1', values: LAG_CCC },
        { key: 'net', label: '正味与信ポジション', colorClass: 'fig-series-2', values: LAG_NET }
      ],
      yDomain: [0, 40], yTicks: [0, 10, 20, 30, 40], yFmt: function (v) { return v; },
      fmt: function (v) { return v.toFixed(1) + ' 日'; },
      table: {
        caption: '全産業のCCCと正味与信ポジションの推移（2000〜2024年度、単位: 日）',
        headers: ['年度', 'CCC', '正味与信ポジション'],
        rows: LAG_YEARS.map(function (y, i) { return [y, LAG_CCC[i].toFixed(1), LAG_NET[i].toFixed(1)]; })
      }
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
      log: true, leftMargin: 52,
      series: [
        { key: 'mag', label: '磁気型', colorClass: 'fig-series-1', values: magnetic },
        { key: 'pap', label: '紙型', colorClass: 'fig-series-2', values: paper },
        { key: 'srv', label: 'サーバ型', colorClass: 'fig-series-3', values: server },
        { key: 'ic', label: 'IC型', colorClass: 'fig-series-4', values: ic }
      ],
      yDomain: [10, 2000], yTicks: [10, 100, 1000], yFmt: function (v) { return v.toLocaleString(); },
      fmt: function (v) { return v.toLocaleString() + ' 日'; },
      table: {
        caption: '媒体別の滞留日数の推移（R2〜R6年度、族2、単位: 日）',
        headers: ['媒体', 'R2', 'R3', 'R4', 'R5', 'R6'],
        rows: [
          ['磁気型'].concat(magnetic), ['紙型'].concat(paper),
          ['サーバ型'].concat(server), ['IC型'].concat(ic)
        ]
      }
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
  function centered(t) { t.setAttribute('text-anchor', 'middle'); return t; }

  function figCollider(container) {
    var W = 500, H = 240;
    var svg = svgRoot(W, H);
    svg.appendChild(box(30, 100, 110, 44, ''));
    svg.appendChild(mathLabel(85, 122, '<math><mi>Φ</mi></math>', 40, 24));
    svg.appendChild(box(360, 100, 110, 44, ''));
    svg.appendChild(mathLabel(415, 122, '<math><mi>ε</mi></math>', 40, 24));
    svg.appendChild(box(195, 100, 110, 44, ''));
    svg.appendChild(mathLabel(250, 116, '<math><mi>S</mi><mo>=</mo><mn>1</mn></math>', 70, 24));
    svg.appendChild(arrow(140, 122, 190, 122));
    svg.appendChild(arrow(360, 122, 310, 122));
    svg.appendChild(centered(text(85, 90, '契約形態に由来する優位', 'fig-muted')));
    svg.appendChild(centered(text(415, 90, '外生的な衝撃', 'fig-muted')));
    svg.appendChild(centered(text(250, 168, '生存（合流点）', 'fig-muted')));
    container.appendChild(svg);
  }

  function figCreditFormation(container) {
    var W = 560, H = 300, m = { left: 40, right: 20, top: 20, bottom: 34 };
    var svg = svgRoot(W, H);
    var x0 = m.left, x1 = W - m.right, xm = (x0 + x1) / 2;
    var y0 = H - m.bottom, y1 = m.top;
    svg.appendChild(el('line', { x1: x0, x2: x0, y1: y1, y2: y0, class: 'fig-baseline' }));
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: y0, y2: y0, class: 'fig-baseline' }));
    // 在職中の破線区切りと競業避止の網掛け
    svg.appendChild(el('line', { x1: xm, x2: xm, y1: y1, y2: y0, stroke: 'var(--muted)', 'stroke-dasharray': '4,3' }));
    svg.appendChild(el('rect', { x: xm, y: y1, width: (x1 - xm) * 0.35, height: y0 - y1, fill: 'var(--line)', opacity: .35 }));
    // 利用可能な信用: 在職中は高い水準→退職で急落しゼロ
    svg.appendChild(el('path', { class: 'fig-line fig-series-1', d: 'M' + x0 + ',' + (y0 - 130) + ' L' + xm + ',' + (y0 - 140) + ' L' + xm + ',' + (y0 - 8) + ' L' + x1 + ',' + (y0 - 8) }));
    // 保有する信用: ずっとほぼゼロ
    svg.appendChild(el('path', { class: 'fig-line fig-series-2', d: 'M' + x0 + ',' + (y0 - 6) + ' L' + x1 + ',' + (y0 - 6) } ));
    // 変換原資: 退職前後で最大化し、以後指数的に減衰
    var d3 = 'M' + x0 + ',' + (y0 - 60);
    var steps = 20, decayStart = xm;
    d3 += ' L' + xm + ',' + (y0 - 170);
    for (var i = 0; i <= steps; i++) {
      var xx = xm + (x1 - xm) * i / steps;
      var yy = y0 - 170 * Math.exp(-2.2 * i / steps);
      d3 += ' L' + xx.toFixed(1) + ',' + yy.toFixed(1);
    }
    svg.appendChild(el('path', { class: 'fig-line fig-series-3', d: d3 }));
    svg.appendChild(legend([
      { label: '利用可能な信用', colorClass: 'fig-series-1' },
      { label: '保有する信用', colorClass: 'fig-series-2' },
      { label: '変換原資', colorClass: 'fig-series-3' }
    ], W, { left: m.left, right: m.right }));
    svg.appendChild(text(xm, y0 + 16, '退職', 'fig-tick'));
    container.appendChild(svg);
  }

  function figDeadline(container) {
    var W = 560, H = 280, m = { left: 40, right: 20, top: 30, bottom: 30 };
    var svg = svgRoot(W, H);
    var x0 = m.left, x1 = W - m.right, y0 = H - m.bottom, y1 = m.top;
    svg.appendChild(el('line', { x1: x0, x2: x0, y1: y1, y2: y0, class: 'fig-baseline' }));
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: y0, y2: y0, class: 'fig-baseline' }));
    var floorY = y0 - 30;
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: floorY, y2: floorY, stroke: 'var(--muted)', 'stroke-dasharray': '3,3' }));
    svg.appendChild(mathLabel(x1 - 32, floorY - 10, '<math><msub><mi>M</mi><mrow><mi>f</mi><mi>l</mi><mi>o</mi><mi>o</mi><mi>r</mi></mrow></msub></math>', 60, 18));
    // 給与所得者: 右肩上がり
    svg.appendChild(el('path', { class: 'fig-line fig-series-1', d: 'M' + x0 + ',' + (y0 - 90) + ' L' + x1 + ',' + (y1 + 20) }));
    // R1: 期限に向けて減少しゼロで打ち切り
    var r1end = x0 + (x1 - x0) * 0.62;
    svg.appendChild(el('path', { class: 'fig-line fig-series-2', d: 'M' + x0 + ',' + (y0 - 90) + ' L' + r1end + ',' + y0 }));
    svg.appendChild(el('circle', { class: 'fig-dot fig-series-2', cx: r1end, cy: y0, r: 4 }));
    // R2: 下限で下げ止まる
    svg.appendChild(el('path', { class: 'fig-line fig-series-3', d: 'M' + x0 + ',' + (y0 - 90) + ' L' + (x0 + (x1 - x0) * 0.4) + ',' + floorY + ' L' + x1 + ',' + floorY }));
    svg.appendChild(legend([
      { label: '給与所得者', colorClass: 'fig-series-1' },
      { label: 'R1（期限）', colorClass: 'fig-series-2' },
      { label: 'R2（下限）', colorClass: 'fig-series-3' }
    ], W, { left: m.left, right: m.right }));
    svg.appendChild(mathLabel(r1end, y0 + 16, '<math><mi>τ</mi><mo>=</mo><mi>E</mi><mo>(</mo><mn>0</mn><mo>)</mo><mo>/</mo><mi>c</mi></math>', 90, 20));
    container.appendChild(svg);
  }

  function figGrowthFcf(container) {
    var W = 480, H = 300, m = { left: 46, right: 20, top: 20, bottom: 30 };
    var svg = svgRoot(W, H);
    var x0 = m.left, x1 = W - m.right, ymid = (m.top + (H - m.bottom)) / 2;
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: ymid, y2: ymid, stroke: 'var(--rule)' }));
    svg.appendChild(el('line', { x1: x0, x2: x0, y1: m.top, y2: H - m.bottom, stroke: 'var(--rule)' }));
    var xIntercept = x0 + (x1 - x0) * 0.55;
    // CCC>0: 右下がり、g*でFCF=0
    svg.appendChild(el('path', { class: 'fig-line fig-series-1', d: 'M' + x0 + ',' + (m.top + 20) + ' L' + x1 + ',' + (H - m.bottom - 10) }));
    // CCC<0: 右上がり
    svg.appendChild(el('path', { class: 'fig-line fig-series-2', d: 'M' + x0 + ',' + (ymid - 10) + ' L' + x1 + ',' + (m.top) }));
    svg.appendChild(el('line', { x1: xIntercept, x2: xIntercept, y1: ymid, y2: ymid + 30, stroke: 'var(--muted)', 'stroke-dasharray': '3,3' }));
    svg.appendChild(mathLabel(xIntercept, ymid + 42, '<math><msup><mi>g</mi><mo>⋆</mo></msup></math>', 30, 20));
    svg.appendChild(mathLabel(x0 - 8, m.top + 14, '<math><mi>Φ</mi><mi>C</mi><mi>F</mi></math>', 40, 20));
    svg.appendChild(mathLabel(x1 - 10, H - m.bottom + 16, '<math><mi>g</mi></math>', 20, 18));
    svg.appendChild(legend([
      { label: 'CCC > 0', colorClass: 'fig-series-1' },
      { label: 'CCC < 0', colorClass: 'fig-series-2' }
    ], W, { left: m.left, right: m.right }));
    container.appendChild(svg);
  }

  function quadrantDiagram(container, labels, cellLabels, strongIdx) {
    // 左右のラベル（「κ > 0（後払）」等）は文字数が多いため、上下より広い
    // サイド余白（mSide）を確保する。プロット本体（象限の箱）は中央に
    // W/2 を軸として左右対称に配置されるので mTop/mSide が非対称でも崩れない。
    var W = 680, H = 380, mTop = 46, mSide = 140, mBottom = 46;
    var cw = (W - 2 * mSide) / 2, ch = (H - mTop - mBottom) / 2;
    var svg = svgRoot(W, H);
    svg.appendChild(el('line', { x1: mSide, x2: W - mSide, y1: H / 2, y2: H / 2, class: 'fig-baseline' }));
    svg.appendChild(el('line', { x1: W / 2, x2: W / 2, y1: mTop, y2: H - mBottom, class: 'fig-baseline' }));
    var cells = [
      { x: mSide, y: mTop, i: 0 }, { x: W / 2, y: mTop, i: 1 },
      { x: mSide, y: H / 2, i: 2 }, { x: W / 2, y: H / 2, i: 3 }
    ];
    cells.forEach(function (c) {
      var strong = c.i === strongIdx;
      var r = el('rect', {
        x: c.x + 4, y: c.y + 4, width: cw - 8, height: ch - 8, rx: 5,
        class: strong ? 'fig-box' : 'fig-box fig-boxfill',
        fill: strong ? 'var(--accent)' : null
      });
      if (strong) { r.setAttribute('opacity', '.15'); }
      svg.appendChild(r);
      var lines = cellLabels[c.i].split('\n');
      lines.forEach(function (line, li) {
        svg.appendChild(centered(text(c.x + cw / 2, c.y + ch / 2 - (lines.length - 1) * 8 + li * 16, line, 'fig-label')));
      });
    });
    svg.appendChild(centered(text(W / 2, mTop - 16, labels.top, 'fig-muted')));
    svg.appendChild(centered(text(W / 2, H - mBottom + 24, labels.bottom, 'fig-muted')));
    svg.appendChild(text(mSide - 10, H / 2, labels.left, 'fig-muted', 'end'));
    svg.appendChild(text(W - mSide + 10, H / 2, labels.right, 'fig-muted', 'start'));
    container.appendChild(svg);
  }

  function figKappaSchedule(container) {
    quadrantDiagram(container,
      { top: 'π が δ と独立（定額）', bottom: 'π が δ に連動（従量）', left: '', right: '' },
      [
        '会員制\nκ<0/κ>0（族2-1）',
        '定額アクセス\n認知余剰が生じうる',
        '従量課金\nκ≈0（族2-2）',
        '二部料金\n混合（族2-3）'
      ], 1);
  }

  function figSoloQuadrant(container) {
    quadrantDiagram(container,
      { top: '履行が人手に依存', bottom: '複製可能な履行', left: 'κ>0（後払）', right: 'κ<0（前受）' },
      [
        '対立しない領域\n（左上：R2の退職者）',
        '実現可能領域\n（右上：無資産の一人事業）',
        '実行不能',
        '信用のブートストラップ\n問題が残る領域'
      ], 1);
  }

  function figPhiQuadrant(container) {
    var W = 480, H = 300, m = { left: 40, right: 60, top: 20, bottom: 30 };
    var svg = svgRoot(W, H);
    var x0 = m.left, x1 = W - m.right, y0 = H - m.bottom, y1 = m.top;
    svg.appendChild(el('line', { x1: x0, x2: x0, y1: y1, y2: y0, class: 'fig-baseline' }));
    svg.appendChild(el('line', { x1: x0, x2: x1, y1: y0, y2: y0, class: 'fig-baseline' }));
    var dPath = 'M' + x0 + ',' + y0 + ' L' + x1 + ',' + (y0 - 200);
    var pPath = 'M' + x0 + ',' + y0 + ' L' + (x0 + (x1 - x0) * 0.4) + ',' + (y0 - 40) + ' L' + x1 + ',' + (y0 - 160);
    // D(t) より P(t) が上（前半、κ<0）→ 塗り分け、後半 P<D（κ>0）
    svg.appendChild(el('path', { class: 'fig-line fig-series-1', d: dPath }));
    svg.appendChild(el('path', { class: 'fig-line fig-series-2', d: pPath }));
    svg.appendChild(mathLabel(x1 + 32, y0 - 200, '<math><mi>D</mi><mo>(</mo><mi>t</mi><mo>)</mo></math>', 40, 20));
    svg.appendChild(mathLabel(x1 + 32, y0 - 160, '<math><mi>P</mi><mo>(</mo><mi>t</mi><mo>)</mo></math>', 40, 20));
    svg.appendChild(mathLabel(x0 + (x1 - x0) * 0.2, y0 - 30, '<math><mi>κ</mi><mo>&lt;</mo><mn>0</mn></math>', 44, 20));
    svg.appendChild(mathLabel(x0 + (x1 - x0) * 0.75, y0 - 130, '<math><mi>κ</mi><mo>&gt;</mo><mn>0</mn></math>', 44, 20));
    svg.appendChild(mathLabel(x1 - 6, y0 + 16, '<math><mi>t</mi></math>', 20, 18));
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
