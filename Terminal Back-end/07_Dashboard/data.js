// GENERAT DE SISTEM — nu edita manual. Se regenerează la: „procesează inbox", „generează teza", „loghează", „raport lunar".
window.DESK_DATA = {
  updated: "11.08.2026 (procesează inbox — 39 rapoarte, săptămâna 10.08–14.08.2026; date mecanice reîmprospătate 11.08)",
  week: "10.08–14.08.2026",
  // accounts: name = exact ca în blotter (coloana Cont) · type = Evaluation / Funded
  // (faza contului, cea după care se separă statisticile din Journal) · phase = etapa din playbook.
  // 10.08.2026: cont demo Fusion Markets adăugat pentru testarea pipeline-ului (statement → blotter),
  // NU ca reluare a trackingului pe demo — planul din 07.08 rămâne: testul real pornește pe Funded mic.
  accounts: [
    { name: "Fusion-Demo", strategy: "Swing + Intraday", type: "Demo", phase: "Test pipeline" }
  ],

  // ——— stratul de sinteză (mereu populat; ordinea = cele 7 criterii de confluență) ———
  regime: "RISK-ON curat, confirmat de date proaspete (refresh 11.08): VIX 14,9 (percentila 8, minim de an), spread high-yield 2,70% (percentila 9) și S&P +3,16% pe 20 de ședințe — toate la extreme calme. Petrolul a urcat brusc (Brent +7%, spre 87-88$) pe eșecul negocierilor SUA-Iran despre Hormuz, iar aurul a spart în sus (~4.388-4.400$) pe repricing dovish Fed + cerere de refugiu — ambele urcă simultan cu bursa, semn de acoperire sub suprafață chiar și într-un risk-on curat. NFP iulie a ratat masiv (-23k vs +80k așteptat), a tăiat șansele de hike Fed din septembrie de la 55% spre ~42% și a lăsat dolarul la extrem de poziționare: COT DXY la percentila 100 (long plin), cu EUR/CAD/CHF/NZD toate short adânc (percentila 4-9) — combustibil de squeeze. CPI SUA de mâine (12.08) e catalizatorul central al săptămânii.",
  sentiment: { label: "RISK-ON (curat, dar cu haven bid neobișnuit)", note: "VIX la minim de an (14,9), credit calm, acțiuni cu moment puternic — regim calculat +2, curat, nu fragil. Excepția: aurul și petrolul urcă simultan cu bursa. Poziționarea e la extrem: USD long la percentila 100, monede majore short adânc — teren clasic de squeeze, reflectat direct în scorecard (5 din 7 perechi principale peste pragul de BOOK)." },
  // Sentiment NU mai are card aici — trăiește în caseta MARKET REGIME de pe Home (sentiment {label, note cu VIX}).
  // Rezumatele = VERDICTUL criteriului într-o frază-două, plus navigația către pagina de detaliu.
  summaries: [
    { k: "Central Banks", pg: "p1_central_banks.html", v: "8 bănci centrale, toate rapoarte TMV din 10.08 — niciuna cu ședință chiar în fereastră, dar CAD, AUD, JPY și NZD au trecut de la bias de relaxare la bias de întărire. RBNZ (mâine, 12.08) e singurul catalizator CB real al săptămânii." },
    { k: "Bank Reports", pg: "p2_bank_reports.html", v: "41 rânduri din 24 rapoarte procesate. AUD e cel mai aliniat bloc (4 surse independente, bullish). JPY rămâne cel mai contestat — chiar MUFG s-a întors de la bullish la neutru în 3 zile. USD are tilt bearish, dar Danske (convingere maximă) rămâne structural bullish." },
    { k: "Economic Indicators", pg: "p3_indicators.html", v: "CAD are cea mai curată combinație pozitivă (GDP +3,4% vs 2,5% proiectat). USD are cea mai slabă — NFP -23k, revizuiri -103k. NZD e mixt: CPI peste bandă, dar șomaj la maxim de 11 ani." },
    { k: "Yield Spreads", pg: "p4_yields.html", v: "Randamente reîmprospătate 11.08 — confirmă tiltul bearish USD pe criteriul mecanic; vezi pagina pentru delta pe 5 ședințe per monedă." },
    { k: "COT — Commitment of Traders", pg: "p5_cot.html", v: "Date proaspete (as of 04.08): DXY long la percentila 100 (extrem plin), EUR/CAD/CHF/NZD short adânc (percentila 4-9, combustibil de squeeze), GBP long la percentila 85." },
    { k: "Seasonality 10y", pg: "p6_seasonality.html", v: "August, medie 10 ani — vezi pagina pentru citirea per pereche; folosit doar ca vânt din spate/față, niciodată motiv principal." }
  ],

  // ——— BOOK UNIC (ipoteze condiționate, NU ordine de execuție) ———
  // Consistent cu Currency Scorecard 11.08 (date mecanice reîmprospătate): AUDUSD, USDCAD, NZDUSD, EURUSD,
  // USDCHF = BOOK (gap 6,0-9,8); USDJPY = WATCH (gap 5,8). Toate WATCH ca stadiu azi — prima zi a ciclului,
  // fără confirmare tehnică încă din partea lui Cătălin.
  trades: [
    { id: "2026-08-10-AUDUSD-L", opened: "10.08.2026",
      stage: "WATCH", type: "Swing", instrument: "AUDUSD", dir: "WATCH - LONG", conf: "4/5", thesis: "9,8",
      horizon: "multi-day, fără catalizator CB nou (RBA a ținut azi, hawkish)",
      drivers: "Cel mai aliniat bloc din tot batch-ul: TMV, MUFG (de două ori, inclusiv idee Long AUD/JPY) și ING converg independent bullish — RBA hawkish-hold, ~44% analiști încă văd hike, plus petrol/cupru la maxime. Regim risk-on curat (+2) și COT DXY la extrem plin (percentila 100) întăresc scorul mecanic",
      trigger: "Confirmare tehnică proprie (Cătălin) pe breakout/retest, cu risk-on intact și fără reversal la CPI SUA de mâine",
      invalidation: "CPI SUA fierbinte care relansează USD pe toată linia / dezescaladare Orient Mijlociu care taie petrolul brusc. Contra: SEA -1 (august sezonier slab pt. AUD)" },

    { id: "2026-08-10-USDCAD-S", opened: "10.08.2026",
      stage: "WATCH", type: "Swing", instrument: "USDCAD", dir: "WATCH - SHORT", conf: "4/5", thesis: "-9,5",
      horizon: "multi-day, spre CPI SUA 12.08",
      drivers: "GDP T2 CAD a bătut cu mult proiecția proprie BoC (3,4% vs 2,5%), bias BoC mutat spre hike; petrolul mai ridicat (Iran/Hormuz) susține CAD direct. COT CAD short la percentila 4 (combustibil de squeeze) + regim risk-on curat întăresc scorul, deși breadth bancar rămâne subțire (doar TMV, MUFG)",
      trigger: "USD moale post-CPI + confirmare tehnică sub nivel-cheie",
      invalidation: "CPI SUA fierbinte relansează USD global / dezescaladare care taie petrolul" },

    { id: "2026-08-10-NZDUSD-L", opened: "10.08.2026",
      stage: "WATCH", type: "Swing", instrument: "NZDUSD", dir: "WATCH - LONG", conf: "3/5", thesis: "8,5",
      horizon: "foarte scurt, event RBNZ 12.08",
      drivers: "Prima majorare RBNZ din 2023 (iulie), ciclu deschis spre ~3,00% OCR — sursă unică (TMV), dar COT NZD short la percentila 4 (squeeze) și regim risk-on curat compensează breadth-ul redus. Șomaj la maxim de 11 ani (5,6%) rămâne risc dovish real la Declarație",
      trigger: "Confirmare hawkish la Declarația RBNZ de mâine + breakout tehnic propriu",
      invalidation: "Semnal explicit de oprire a ciclului la RBNZ → teza moare pe loc, fără repoziționare aceeași zi" },

    { id: "2026-08-10-EURUSD-L", opened: "10.08.2026",
      stage: "WATCH", type: "Swing", instrument: "EURUSD", dir: "WATCH - LONG", conf: "2,5/5", thesis: "7,5",
      horizon: "multi-day, spre CPI SUA 12.08",
      drivers: "TMV + MUFG văd ECB mai hawkish (inflație 2,9%, a doua lună peste țintă); COT EUR short la percentila 8 (squeeze) împinge scorul mecanic sus. Contra puternic rămâne: Danske (convingere maximă din tot batch-ul, 5/5) e structural bearish EUR/USD pe 12 luni",
      trigger: "CPI SUA moale + confirmare tehnică peste rezistența 1,160 (ING)",
      invalidation: "CPI SUA hawkish blochează ruperea peste 1,160. Onest: contradicție reală cu Danske, nu zgomot — criteriul 1 e plafonat la 0" },

    { id: "2026-08-10-USDCHF-S", opened: "10.08.2026",
      stage: "WATCH", type: "Swing", instrument: "USDCHF", dir: "WATCH - SHORT", conf: "2/5", thesis: "-6,0",
      horizon: "multi-day, spre CPI SUA 12.08 — sursă unică, de tratat cu rezervă",
      drivers: "Scorul vine mai ales din COT (CHF short la percentila 8, squeeze) și regim risk-on, NU din bănci — nicio casă comercială nu are teză proprie pe franc. Singura sursă fundamentală (TMV) e internă contradictorie: politică SNB dovish (posibile dobânzi negative în septembrie), dar prognoza tot bullish CHF pe fluxuri de refugiu",
      trigger: "CPI SUA moale + confirmare tehnică proprie",
      invalidation: "CPI SUA hawkish / SNB confirmă tăiere efectivă care reușește să slăbească francul. Onest: cea mai fragilă idee din book pe partea fundamentală — mecanic peste prag, dar sursă unică și intern contradictorie" },

    { id: "2026-08-10-USDJPY-S", opened: "10.08.2026",
      stage: "WATCH", type: "Swing", instrument: "USDJPY", dir: "WATCH - SHORT", conf: "2/5", thesis: "-5,8",
      horizon: "multi-day, spre CPI SUA 12.08 — monedă cu contradicție activă",
      drivers: "Scorul rămâne sub pragul de BOOK — regimul risk-on curat taie JPY (safe-haven) la -2, contrabalansând restul. Blocul comercial (ING, Westpac, CACIB) arată short JPY reconstruit după intervenție, în timp ce TMV (hike BoJ octombrie ~96% prețuit) rămâne bullish JPY; MUFG însuși s-a întors de la bullish (07.08) la neutru (10.08) în 3 zile",
      trigger: "CPI SUA moale + semnal clar de epuizare a vânzării de yeni (fără garanție azi)",
      invalidation: "Continuarea trend-ului de short JPY reconstruit anulează teza tehnic, chiar dacă scorul rămâne. Onest: criteriul 1 explicit plafonat la 0" },

    { id: "2026-08-10-US30-L", opened: "11.08.2026",
      stage: "WATCH", type: "Intraday", instrument: "US30", dir: "WATCH - LONG", conf: "3/5", thesis: "—",
      horizon: "sesiunea NY",
      drivers: "MUFG (proxy S&P): sezon T2 aproape încheiat, 86% peste consens EPS, P/E fwd 20,0x nu pare supraevaluat, reziliență în fața incertitudinilor geopolitice. Regim risk-on curat (VIX 14,9, moment S&P +3,16%/20 ședințe) susține direct teza",
      trigger: "Breakout M5 din nivel M30 + VIX în scădere + top-8 componente verzi. Atenție la CPI SUA de mâine (fereastră de blackout tehnic)",
      invalidation: "CPI SUA hawkish / urcare bruscă a randamentelor 10Y/30Y — risc semnalat explicit pentru reziliența acțiunilor" },

    { id: "2026-08-10-GOLD-L", opened: "11.08.2026",
      stage: "WATCH", type: "Intraday", instrument: "GOLD", dir: "WATCH - LONG", conf: "3/5", thesis: "—",
      horizon: "sesiunea NY",
      drivers: "Repricing dovish Fed (term premium + breakeven 5y5y la maxim) + cerere de refugiu (Iran/Hormuz) — aurul a spart în sus spre 4.388-4.400$, MUFG confirmă. Urcă simultan cu risk-on curat, semn de acoperire sub suprafață",
      trigger: "DXY slab + randamente reale care nu urcă; breakout M5 din M30 cu retest",
      invalidation: "CPI SUA fierbinte care relansează randamentele reale / dezescaladare Iran care taie brusc cererea de refugiu" }
  ]
  // P&L / trade-uri: în journal_data.js (local, în .gitignore) — nu aici
};
