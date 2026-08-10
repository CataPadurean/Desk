// GENERAT DE SISTEM — nu edita manual. Se regenerează la: „procesează inbox", „generează teza", „loghează", „raport lunar".
window.DESK_DATA = {
  updated: "19.07.2026 (teza săptămânii 06.07–10.07.2026, generată 05.07)",
  week: "06.07–10.07.2026",
  // accounts: name = exact ca în blotter (coloana Cont) · type = Evaluation / Funded
  // (faza contului, cea după care se separă statisticile din Journal) · phase = etapa din playbook.
  // 10.08.2026: cont demo Fusion Markets adăugat pentru testarea pipeline-ului (statement → blotter),
  // NU ca reluare a trackingului pe demo — planul din 07.08 rămâne: testul real pornește pe Funded mic.
  accounts: [
    { name: "Fusion-Demo", strategy: "Swing + Intraday", type: "Demo", phase: "Test pipeline" }
  ],

  // ——— stratul de sinteză (mereu populat; ordinea = cele 7 criterii de confluență) ———
  regime: "RISK-ON, dar nu „curat”: Dow record 53.056, S&P +0,7%, Nasdaq +1,1%, VIX 16,06. DAR randamentele urcă din nou (10Y US 4,50%, maxim de 2 săptămâni, pe revenirea petrolului) și fast money e la extrem dublu — USD long de deceniu ($39,8 miliarde) + SOFR short record. Săptămâna se joacă pe evenimente: RBNZ 8.07 (hike devenit consens) + minute FOMC 8.07 (pivotul USD). BoC + MPR abia 15.07.",
  sentiment: { label: "RISK-ON (fragil)", note: "Indici la record, VIX 16 — favorabil monedelor pro-ciclice bătute (CAD, NZD, AUD). Fragil: randamentele urcă și USD long e la extrem de deceniu — minute FOMC hawkish pot inversa tonul." },
  // Sentiment NU mai are card aici — trăiește în caseta MARKET REGIME de pe Home (sentiment {label, note cu VIX}).
  // Rezumatele = VERDICTUL criteriului într-o frază-două, plus navigația către pagina de detaliu.
  // Detaliul per monedă stă în scorecard (tooltip pe fiecare celulă) și pe paginile p1–p6 —
  // aici NU se repetă cifrele, altfel Home devine raport în loc de tablou de bord.
  summaries: [
    { k: "Central Banks", pg: "p1_central_banks.html", v: "Doar NZD (8.07) și CAD (15.07) au eveniment propriu în fereastră — exact monedele cu teze active. Fed arbitrează restul tabelului prin minutele de miercuri; ECB, BoE, BoJ, RBA și SNB rămân fără catalizator." },
    { k: "Bank Reports", pg: "p2_bank_reports.html", v: "CAD e singurul bloc cu trei case aliniate din unghiuri diferite — de aici cea mai mare convingere. JPY e blocat de contradicția CACIB–MUFG, iar consensul bull pe dolar s-a rupt după datele pieței muncii." },
    { k: "Economic Indicators", pg: "p3_indicators.html", v: "Canada singura cu surpriză net pozitivă, Noua Zeelandă cu cea mai bună creștere și inflația la vârf de ciclu, Marea Britanie cea mai slabă combinație. Datele susțin ambele teze active și nu contrazic niciuna." },
    { k: "Yield Spreads", pg: "p4_yields.html", v: "Spread-urile 2Y rămân pro-dolar pe toată linia; îngustările de pe USDCAD și USDJPY sunt marginale. Criteriul contrazice pe față short-ul de USDCAD — teza ține pe catalizator, nu pe trend." },
    { k: "COT — Commitment of Traders", pg: "p5_cot.html", v: "Cinci poziționări extreme simultan: short pe EUR, CAD, JPY și NZD, long pe GBP la percentila 96. Short-urile pline sunt combustibil de squeeze pentru tezele CAD și NZD; long-ul pe liră e vulnerabil la orice dezamăgire." },
    { k: "Seasonality 10y", pg: "p6_seasonality.html", v: "Iulie susține NZD cu un hit rate decent (73%) și e irelevant pe CAD (45% — monedă aruncată). Cel mai puternic semnal al lunii e pro-yen, exact perechea unde băncile se contrazic." }
  ],

  // ——— BOOK UNIC (ipoteze condiționate, NU ordine de execuție) ———
  // Book-ul e ACȚIONABIL: intră DOAR ideile cu direcție angajată — LIVE / ARMED / WATCH.
  // Ce e „sub prag" NU se scrie aici; apare compact în Currency Scorecard, la finalul perechilor.
  // stage: "LIVE" (poziție deschisă) | "ARMED" (trigger la un pas, gata de execuție)
  //      | "WATCH" (devine trade dacă se întâmplă condiția din Trigger)
  // Stadiul nu are coloană proprie: se vede în Direction — LONG / SHORT (ARMED),
  // WATCH - LONG / WATCH - SHORT, LIVE - LONG / LIVE - SHORT.
  // id:    ID-ul stabil al ideii — AAAA-LL-ZZ-INSTRUMENT-L|S, data = ziua intrării în book.
  //        Se copiază în coloana «Idea ref» din blotter și rămâne același când ideea trece
  //        în history_data.js. Fără el, execuția și research-ul nu se pot compara niciodată.
  // opened: data intrării în book, în format afișat (dd.mm.yyyy)
  // type:  "Swing" (multi-day, 1-5 zile) | "Intraday" (Gold + US30, sesiunea NY)
  // thesis: diferența de scor din Currency Scorecard (gap-ul de rank) pentru ideile Swing;
  //         "—" pentru cele pur tactice (intraday). Book de la 6,0 · watch de la 5,0.
  // La invalidare/expirare, intrarea IESE de aici și se arhivează în history_data.js.
  trades: [
    { id: "2026-07-06-USDCAD-S", opened: "06.07.2026",
      stage: "ARMED", type: "Swing", instrument: "USDCAD", dir: "SHORT", conf: "3/5", thesis: "8,8",
      horizon: "multi-day, catalizator BoC 15.07",
      drivers: "Blocul de rapoarte cel mai aliniat (CACIB 1,35-1,40; Scotiabank + CIBC rebound) + GDP peste așteptări + short CAD extremă + CAD pro-risc. Catalizatorul (BoC + raportul de politică monetară) abia pe 15.07",
      trigger: "USD moale după minutele FOMC (non-hawkish) + confirmare tehnică sub nivelul-cheie",
      invalidation: "Minute FOMC hawkish / 10Y sus / date canadiene slabe. Contra: spread 2Y (+1,38) încă PRO-USD + USD long de deceniu" },

    { id: "2026-07-06-NZDUSD-L", opened: "06.07.2026",
      stage: "ARMED", type: "Swing", instrument: "NZDUSD", dir: "LONG", conf: "3/5", thesis: "10,0",
      horizon: "1-3 zile, eveniment RBNZ 8.07",
      drivers: "Majorare la 2,50% devenită consens (22 din 28) + CPI în urcare spre 4,3% + short Leveraged Funds la RECORD + risk-on cu NZD pro-ciclic = profil de squeeze",
      trigger: "Majorare sau ton clar hawkish pe 8.07 + risk-on intact + breakout tehnic din nivel",
      invalidation: "Hold dovish pe 8.07 → mort; minute FOMC hawkish relansează USD. Onest: câștig limitat (majorarea e prețuită), spread 2Y indisponibil" },

    { id: "2026-07-06-GBPNZD-S", opened: "06.07.2026",
      stage: "WATCH", type: "Swing", instrument: "GBPNZD", dir: "SHORT", conf: "2,5/5", thesis: "11,7",
      horizon: "multi-day, catalizator RBNZ 8.07",
      drivers: "Cea mai mare diferență de rank din tabel: extrema bearish (GBP, ultimul pe șase criterii din șapte) contra extremei bullish (NZD, primul). Fără dolar în mijloc, deci nu depinde de minutele FOMC",
      trigger: "Confirmare RBNZ pe 8.07 + rupere tehnică; se intră doar cu spread-ul brokerului acceptabil",
      invalidation: "Hold dovish RBNZ / catalizator pozitiv din Marea Britanie. Contra: nicio casă nu acoperă perechea direct — criteriul 2 e derivat din picioare, nu dintr-un raport" },

    { id: "2026-07-06-US30-L", opened: "06.07.2026",
      stage: "ARMED", type: "Intraday", instrument: "US30", dir: "LONG", conf: "3/5", thesis: "—",
      horizon: "sesiunea NY",
      drivers: "Risk-on, Dow la record 53.056, VIX 16. DAR randamentele urcă și minutele FOMC de miercuri aduc risc → convingere temperată",
      trigger: "Breakout M5 din nivel M30 + VIX în scădere + primele 8 componente verzi. NU în fereastra minutelor FOMC (±15-30 de minute de la ora 21:00, miercuri)",
      invalidation: "Minute FOMC hawkish / 10Y sus agresiv / VIX peste 20" },

    { id: "2026-07-06-GOLD-L", opened: "06.07.2026",
      stage: "WATCH", type: "Intraday", instrument: "GOLD", dir: "LONG", conf: "2,5/5",
      thesis: "—", horizon: "sesiunea NY",
      drivers: "Cumpărare la minime în metale prețioase + DXY sub 101. DAR randamentele reale urcă (10Y 4,50%) = vânt din față → convingere redusă",
      trigger: "DXY slab + randamente reale care nu mai urcă; breakout M5 din M30 cu retest",
      invalidation: "10Y peste 4,50% / DXY peste 101; trendul mare descendent intact — NU e trade de poziție" }
    // GBPUSD a ieșit din book: scorecard-ul îl dă la 1,7 diferență de rank — ambele picioare slabe,
    // adică zgomot, nu trade. Apare compact la «sub prag», în Currency Scorecard.
  ],
  // P&L / trade-uri: în journal_data.js (local, în .gitignore) — nu aici
};
