// PADU TERMINAL — header + meniu comun. O pagină nouă = o linie în PAGES, nimic altceva.
// Se încarcă DUPĂ data.js și analysis_data.js. Fiecare pagină cheamă: renderChrome('p4').
(function () {
  var PAGES = [
    { id: 'home', file: 'dashboard.html',        label: 'Home',          title: 'HOME' },
    { id: 'p1',   file: 'p1_central_banks.html', label: 'Central Banks', title: 'CENTRAL BANKS' },
    { id: 'p2',   file: 'p2_bank_reports.html',  label: 'Bank Reports',  title: 'BANK REPORTS' },
    { id: 'p3',   file: 'p3_indicators.html',    label: 'Indicators',    title: 'ECONOMIC INDICATORS' },
    { id: 'p4',   file: 'p4_yields.html',        label: 'Yields',        title: 'YIELD SPREADS' },
    { id: 'p5',   file: 'p5_cot.html',           label: 'COT',           title: 'COT — COMMITMENT OF TRADERS' },
    { id: 'p6',   file: 'p6_seasonality.html',   label: 'Seasonality',   title: 'SEASONALITY 10Y' },
    { id: 'journal', file: 'journal.html',       label: 'Journal',       title: 'JOURNAL' }
    // History nu mai are pagină proprie (07.08.2026): trăiește ca secțiune în Journal,
    // lângă „Idea → execution" — ideea și execuția ei se citesc în același loc.
  ];

  function fmtD(s) { return (s && /^\d{4}-\d{2}-\d{2}$/.test(s)) ? s.split('-').reverse().join('.') : (s || ''); }

  window.PADU_PAGES = PAGES;

  window.renderChrome = function (active) {
    var D = window.DESK_DATA || {}, A = window.ANALYSIS_DATA || {};
    var me = PAGES.filter(function (p) { return p.id === active; })[0] || PAGES[0];
    var upd = A.generated
      ? 'data generated: ' + fmtD(A.generated) + (A.regime_date ? ' · analiza: ' + fmtD(A.regime_date) : '')
      : (D.updated ? 'data generated: ' + D.updated : '');

    var items = PAGES.filter(function (p) { return !p.header; }).map(function (p) {
      var cls = p.id === active ? ' class="on"' : '';
      return '<a href="' + p.file + '"' + cls + '>' + p.label + '</a>';
    }).join('');

    var hist = PAGES.filter(function (p) { return p.header; })[0];

    document.getElementById('chrome').innerHTML =
      '<div class="top">' +
        '<h1>PADU TERMINAL</h1>' +
        '<div><div class="page">' + me.title + '</div>' +
        '<div class="meta"><span class="wk">' + (D.week || '') + '</span><span class="upd">' + upd + '</span></div></div>' +
        (hist ? '<a class="hist' + (active === hist.id ? ' on' : '') + '" href="' + hist.file + '">' + hist.label + '</a>' : '<div></div>') +
      '</div>' +
      '<nav class="menu">' + items + '</nav>';

    // aliniere: butonul HISTORY primește exact lățimea ultimului item din meniu (Journal),
    // ca să stea fix deasupra lui. Ambele sunt lipite de marginea dreaptă, deci se suprapun perfect.
    var syncHist = function () {
      var last = document.querySelector('.menu a:last-child');
      var h = document.querySelector('.top a.hist');
      if (!last || !h) return;
      var w = last.getBoundingClientRect().width;
      if (w > 0) h.style.width = w + 'px';   // 0 = layout încă nefăcut; lăsăm lățimea naturală
    };
    syncHist();
    window.addEventListener('resize', syncHist);
    if (window.requestAnimationFrame) requestAnimationFrame(syncHist);

    // cache-busting când e servit prin http (GitHub Pages)
    if (location.protocol.indexOf('http') === 0) {
      var links = document.querySelectorAll('.menu a, a.sum, a.hist');
      for (var i = 0; i < links.length; i++) (function (a) {
        a.addEventListener('click', function (e) {
          e.preventDefault();
          location.href = a.getAttribute('href') + '?t=' + Date.now();
        });
      })(links[i]);
    }
  };

  // Convingere ca puncte: "3/5" → ●●●○○, "2,5/5" → ●●◐○○, lipsă → —
  window.convDots = function (c) {
    if (c === null || c === undefined || c === '' || c === '—') return '<span class="dim">—</span>';
    var m = String(c).replace(',', '.').match(/([\d.]+)\s*\/\s*5/);
    var n = m ? parseFloat(m[1]) : parseFloat(String(c).replace(',', '.'));
    if (isNaN(n)) return '<span class="dim">' + c + '</span>';
    var s = '', i;
    for (i = 1; i <= 5; i++) s += (n >= i ? '●' : (n >= i - 0.5 ? '◐' : '○'));
    return '<span title="' + c + '">' + s + '</span>';
  };

  // ——— ID-ul unei idei: singura punte între research și execuție ———
  // Format: AAAA-LL-ZZ-INSTRUMENT-L|S|X, data = ziua în care ideea a intrat în book
  // (lunea săptămânii, pentru Swing). Se scrie în `id` în data.js / history_data.js și
  // se copiază în coloana «Idea ref» din blotter. Dacă `id` lipsește, se recalculează
  // din (opened, instrument, dir) — deci vechile intrări rămân legabile.
  window.ideaId = function (o) {
    if (!o) return '';
    if (o.id) return o.id;
    var d = String(o.opened || o.date || '').trim();          // acceptă „06.07.2026" sau ISO
    var m = d.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
    var iso = m ? (m[3] + '-' + m[2] + '-' + m[1]) : (/^\d{4}-\d{2}-\d{2}$/.test(d) ? d : '');
    var dir = String(o.dir || '').toUpperCase();
    var L = dir.indexOf('LONG') > -1 ? 'L' : (dir.indexOf('SHORT') > -1 ? 'S' : 'X');
    return iso ? iso + '-' + String(o.instrument || '?').toUpperCase() + '-' + L : '';
  };
  // eticheta de copiat lângă instrument (click = selectează textul)
  window.ideaTag = function (o) {
    var id = window.ideaId(o);
    return id ? '<span class="idtag" title="ID-ul ideii — se trece în coloana «Idea ref» din blotter">'
                + id + '</span>' : '';
  };

  // helper-e comune de formatare, folosite de mai multe pagini
  window.fmtDate = fmtD;
  window.numCls = function (x) { return x > 0 ? 'pos' : (x < 0 ? 'neg' : ''); };
  window.fmtNum = function (x) { return (x === null || x === undefined || isNaN(x)) ? '—' : x.toLocaleString('en-US'); };
  window.sgn = function (x) { return (x === null || x === undefined || isNaN(x)) ? '—' : ((x > 0 ? '+' : '') + x.toLocaleString('en-US')); };
  window.dirBadge = function (d) {
    if (!d) return '';
    var su = String(d).toUpperCase();
    if (su.indexOf('WATCH') === 0) return '<span class="badge b-watch">' + d + '</span>';
    var core = su.replace(/^LIVE\s*-\s*/, '');   // „LIVE - LONG" se colorează după direcție
    var c = core.indexOf('LONG') === 0 || core.indexOf('BULLISH') === 0 ? 'b-long'
      : core.indexOf('SHORT') === 0 || core.indexOf('BEARISH') === 0 ? 'b-short'
      : (core.indexOf('BULLISH') > -1 || core.indexOf('BEARISH') > -1) ? 'b-watch' : 'b-flat';
    return '<span class="badge ' + c + '">' + d + '</span>';
  };
  window.sentBadge = function (label) {
    if (!label) return '';
    var c = /ON/i.test(label) && !/OFF/i.test(label) ? 'b-long' : (/OFF/i.test(label) ? 'b-short' : 'b-flat');
    return '<span class="badge ' + c + '">' + label + '</span>';
  };
})();
