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
  ];

  function fmtD(s) { return (s && /^\d{4}-\d{2}-\d{2}$/.test(s)) ? s.split('-').reverse().join('.') : (s || ''); }

  window.PADU_PAGES = PAGES;

  window.renderChrome = function (active) {
    var D = window.DESK_DATA || {}, A = window.ANALYSIS_DATA || {};
    var me = PAGES.filter(function (p) { return p.id === active; })[0] || PAGES[0];
    var upd = A.generated
      ? 'data generated: ' + fmtD(A.generated) + (A.regime_date ? ' · analiza: ' + fmtD(A.regime_date) : '')
      : (D.updated ? 'data generated: ' + D.updated : '');

    var items = PAGES.map(function (p) {
      var cls = p.id === active ? ' class="on"' : '';
      return '<a href="' + p.file + '"' + cls + '>' + p.label + '</a>';
    }).join('');

    document.getElementById('chrome').innerHTML =
      '<div class="top">' +
        '<h1>PADU TERMINAL</h1>' +
        '<div><div class="page">' + me.title + '</div>' +
        '<div class="meta"><span class="wk">' + (D.week || '') + '</span><span class="upd">' + upd + '</span></div></div>' +
        '<div></div>' +
      '</div>' +
      '<nav class="menu">' + items + '</nav>';

    // rezumat scurt sub casetele paginii (text alb), din DESK_DATA.summaries potrivit după fișier
    var ps = document.getElementById('pagesum');
    if (ps) {
      var sm = ((window.DESK_DATA || {}).summaries || []).filter(function (x) { return x.pg === me.file; })[0];
      ps.innerHTML = sm ? sm.v : '';
      if (!sm) ps.style.display = 'none';
    }

    // cache-busting când e servit prin http (GitHub Pages)
    if (location.protocol.indexOf('http') === 0) {
      var links = document.querySelectorAll('.menu a, a.sum');
      for (var i = 0; i < links.length; i++) (function (a) {
        a.addEventListener('click', function (e) {
          e.preventDefault();
          location.href = a.getAttribute('href') + '?t=' + Date.now();
        });
      })(links[i]);
    }
  };

  // helper-e comune de formatare, folosite de mai multe pagini
  window.fmtDate = fmtD;
  window.numCls = function (x) { return x > 0 ? 'pos' : (x < 0 ? 'neg' : ''); };
  window.fmtNum = function (x) { return (x === null || x === undefined || isNaN(x)) ? '—' : x.toLocaleString('en-US'); };
  window.sgn = function (x) { return (x === null || x === undefined || isNaN(x)) ? '—' : ((x > 0 ? '+' : '') + x.toLocaleString('en-US')); };
  window.dirBadge = function (d) {
    if (!d) return '';
    var su = String(d).toUpperCase();
    var c = su.indexOf('LONG') === 0 || su.indexOf('BULLISH') === 0 ? 'b-long'
      : su.indexOf('SHORT') === 0 || su.indexOf('BEARISH') === 0 ? 'b-short'
      : su.indexOf('WATCH') === 0 ? 'b-watch'
      : (su.indexOf('BULLISH') > -1 || su.indexOf('BEARISH') > -1) ? 'b-watch' : 'b-flat';
    return '<span class="badge ' + c + '">' + d + '</span>';
  };
  window.sentBadge = function (label) {
    if (!label) return '';
    var c = /ON/i.test(label) && !/OFF/i.test(label) ? 'b-long' : (/OFF/i.test(label) ? 'b-short' : 'b-flat');
    return '<span class="badge ' + c + '">' + label + '</span>';
  };
})();
