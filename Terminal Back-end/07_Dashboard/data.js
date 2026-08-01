// GENERAT DE SISTEM — nu edita manual. Se regenerează la: „procesează inbox", „generează teza", „loghează", „raport lunar".
window.DESK_DATA = {
  updated: "19.07.2026 (teza săptămânii 06.07–10.07.2026, generată 05.07)",
  week: "06.07–10.07.2026",
  accounts: [
    { name: "Demo-A", strategy: "A", phase: "Faza 0 — validare" },
    { name: "Demo-B", strategy: "B", phase: "Faza 0 — validare" }
  ],

  // ——— stratul de sinteză (mereu populat; ordinea = cele 7 criterii de confluență) ———
  regime: "RISK-ON, dar nu „curat”: Dow record 53.056, S&P +0,7%, Nasdaq +1,1%, VIX 16,06. DAR randamentele urcă din nou (10Y US 4,50%, maxim 2 săpt., pe revenirea petrolului) și fast money e la extrem dublu — USD long de deceniu ($39,8 mld) + SOFR short record. Săptămâna se joacă pe evenimente: RBNZ 8.07 (hike devenit consens) + minute FOMC 8.07 (pivotul USD). BoC + MPR abia 15.07.",
  sentiment: { label: "RISK-ON (fragil)", note: "Indici la record, VIX 16 — favorabil monedelor pro-ciclice bătute (CAD, NZD, AUD). Fragil: randamentele urcă și USD long e la extrem de deceniu — minute FOMC hawkish pot inversa tonul." },
  // Sentiment NU mai are card aici — trăiește în caseta MARKET REGIME de pe Home (sentiment {label, note cu VIX}).
  summaries: [
    { k: "Central Banks", pg: "p1_central_banks.html", v: "Doar două monede au eveniment propriu în fereastra asta, și sunt exact cele cu teze active: NZD (decizie 8.07 — majorarea la 2,50% e deja consens, 22 din 28 de economiști) și CAD (decizie + raport de politică monetară 15.07, singurul Tier 1 pe CAD). Fed rămâne arbitrul pentru restul tabelului: minutele de miercuri decid dacă repricing-ul dovish continuă sau se rupe. ECB, BoE, BoJ, RBA și SNB — fără catalizator în fereastră, deci fără teze." },
    { k: "Bank Reports", pg: "p2_bank_reports.html", v: "CAD e singurul bloc unde trei case spun același lucru din unghiuri diferite — CACIB dă nivelurile (1,35-1,40), Scotiabank creșterea, CIBC dobânda — de aici cea mai mare convingere din tabel. JPY e blocat de o contradicție deschisă: CACIB bullish USDJPY 162-163 vs. MUFG, care avertizează că poziționarea de carry e prea aglomerată; direcția netă se anulează. USD: consensul bull era construit pre-NFP și s-a rupt. EUR, GBP, CHF, AUD, NZD — fără teză completă, cu ținte și orizont." },
    { k: "Economic Indicators", pg: "p3_indicators.html", v: "Canada e singura care surprinde net pozitiv: inflația de bază la minim de cinci ani și șomajul în scădere la 6,5%. Noua Zeelandă are cea mai bună creștere din grup (+0,8% t/t) cu inflația la vârf de ciclu (3,9%) — exact combinația care a forțat majorarea. La polul opus, Marea Britanie: șomaj 4,9%, cel mai ridicat din grup. SUA dau semnal mixt: creștere înjumătățită (+1,5% anualizat), dar inflație în sfârșit în scădere (3,5%). Concluzie: datele susțin ambele teze active și nu contrazic niciuna." },
    { k: "Yield Spreads", pg: "p4_yields.html", v: "Spread-urile 2Y rămân pro-dolar pe toată linia: −1,52 pe EURUSD, +1,38 pe USDCAD, +2,73 pe USDJPY. Singurele mișcări care ajută sunt îngustările de −0,03 pe USDCAD și −0,14 pe USDJPY — adică fix perechile cu teze anti-dolar, dar plecând de la un nivel încă advers. Concluzie: criteriul contrazice pe față short-ul de USDCAD. Teza rămâne validă doar fiindcă celelalte criterii o susțin, și are nevoie de catalizator (BoC 15.07), nu de trend." },
    { k: "COT — Commitment of Traders", pg: "p5_cot.html", v: "Cinci poziționări extreme simultan: EUR short (percentila 2), CAD short (2), JPY short (4), NZD short (4) și GBP LONG (96). Δ săptămânal continuă în aceeași direcție pe EUR (−8,5k) și CAD (−4,1k), deci aglomerarea încă se adâncește. Concluzie: pe CAD și NZD poziționarea lucrează în favoarea tezelor — sunt short-uri prea pline, deci combustibil de squeeze. Pe GBP, extrema e în cealaltă parte: un long aglomerat, vulnerabil la orice dezamăgire." },
    { k: "Seasonality 10y", pg: "p6_seasonality.html", v: "Iulie, medii pe 10 ani: NZDUSD +0,35% (hit 73%), USDCAD −0,40% (hit 45%), EURUSD +0,46% (73%), USDJPY −0,89% (27%). Concluzie: pe NZD sezonalitatea susține teza cu un hit rate decent; pe CAD e practic irelevantă — 45% înseamnă monedă aruncată, deci nici nu adaugă, nici nu scade din scor. Cel mai puternic semnal din tabel e pe USDJPY, pro-yen, exact perechea unde băncile se contrazic." }
  ],

  // ——— posibile trade-uri (ipoteze condiționate, NU ordine de execuție) ———
  trades_fx: [
    { instrument: "EURUSD", dir: "STAI", conf: "—",
      rationale: "Ambele bănci centrale au pierdut hike-uri; spread 2Y încă contra EUR; poziționare neutră; criteriul 1 neutru → sub prag",
      activation: "—", invalidation: "Teză neclară = nu există trade (playbook §3.2)" },
    { instrument: "GBPUSD", dir: "WATCH (squeeze)", conf: "—",
      rationale: "Lev funds short pctl ~8 = combustibil de squeeze; dar Services PMI 48,8 + BoE split = fundamente slabe; lipsesc criteriile 1-2",
      activation: "Doar catalizator pozitiv UK + risk-on susținut", invalidation: "—" },
    { instrument: "USDCAD", dir: "SHORT (bias, build spre 15.07)", conf: "3/5",
      rationale: "Blocul de rapoarte cel mai aliniat (CACIB 1,35-1,40; Scotia+CIBC rebound) + GDP beat + short CAD extremă + CAD pro-risk. Scor 5/7. Catalizatorul (BoC+MPR) abia 15.07",
      activation: "USD moale post-minute FOMC (non-hawkish) + confirmare tehnică sub nivel-cheie",
      invalidation: "Minute FOMC hawkish / 10Y sus / date CA slabe. Contra: spread 2Y (+1,38) încă PRO-USD + USD long de deceniu" },
    { instrument: "NZDUSD", dir: "LONG (tactic, event 8.07)", conf: "3/5",
      rationale: "Hike la 2,50% consens (22/28) + CPI ↑ spre 4,3% + short lev funds la RECORD + risk-on cu NZD pro-ciclic = squeeze. Scor 5/7 (crit. 1+2 prezente)",
      activation: "Hike/ton clar hawkish 8.07 + risk-on intact + breakout tehnic din nivel",
      invalidation: "Hold dovish 8.07 → mort; minute FOMC hawkish relansează USD. Onest: câștig limitat (hike prețuit), spread 2Y indisponibil" }
  ],
  trades_intraday: [
    { instrument: "US30", dir: "LONG (intraday)", conf: "3/5",
      rationale: "Risk-on, Dow record 53.056, VIX 16. DAR randamentele urcă + minute FOMC miercuri = risc → convingere temperată",
      activation: "Breakout M5 din nivel M30 + VIX ↓ + top-8 verzi. NU în blackout minute FOMC (±15-30 min de la 21:00 mie)",
      invalidation: "Minute FOMC hawkish / 10Y sus agresiv / VIX peste 20" },
    { instrument: "GOLD", dir: "LONG (tactic, prudent)", conf: "2,5/5",
      rationale: "Bottom-fishing în metale prețioase + DXY sub 101. DAR randamentele reale urcă (10Y 4,50%) = vânt din față → convingere redusă",
      activation: "DXY slab + randamente reale care nu mai urcă; breakout M5 din M30 cu retest",
      invalidation: "10Y peste 4,50% / DXY peste 101; downtrend mare intact — NU trade de poziție" }
  ],

  // Teze active: min. 5/7, criteriile 1+2 obligatorii
  theses: [
    { pair: "USDCAD", dir: "SHORT (bias)", score: "5/7", horizon: "multi-day, catalizator BoC 15.07",
      invalidation: "Minute FOMC hawkish / 10Y sus / date CA slabe. Contra: spread 2Y +1,38 PRO-USD" },
    { pair: "NZDUSD", dir: "LONG (tactic)", score: "5/7", horizon: "1-3 zile, event RBNZ 8.07",
      invalidation: "Hold dovish 8.07 (ASB/Westpac) → mort; sau minute FOMC hawkish → USD relansat" }
  ],
  // P&L / trade-uri: în journal_data.js (local, în .gitignore) — nu aici
};
