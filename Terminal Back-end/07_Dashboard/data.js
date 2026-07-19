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
  summaries: [
    { k: "1 · Central Banks (TMV)", v: "Fed hold 3,50-3,75%, ton hawkish (dot 3,8% = un hike pe masă) vs. pricing dovish post-NFP — minute 8.07 arbitrează; RBNZ 8.07: HIKE la 2,50% devenit consens (22/28); ECB hold, HICP moale; BoE split 7-2, PMI 48,8; BoC hold — MPR 15.07 (Tier 1 CAD); BoJ 1,00% + încă un hike; RBA/SNB hold." },
    { k: "2 · Rapoarte bancare", v: "CAD = blocul cel mai aliniat (CACIB 1,35-1,40; Scotia+CIBC rebound). USD: consensul bull era PRE-NFP, invalidat parțial. EUR neutru. GBP bearish fragil (PMI 48,8). JPY: contradicție CACIB (bull USDJPY 162-163) vs. MUFG (carry vulnerabil). Inbox gol → batch W27." },
    { k: "3 · Indicatori economici", v: "US: NFP +57k (miss), șomaj 4,2%. EZ: HICP 2,8% sub consens. Canada: GDP aprilie +0,55% beat, Q2 ~2,4% SAAR. UK: Services PMI 48,8 (min. ian. 2023). NZ: CPI 3,1% ↑ spre 4,3%." },
    { k: "4 · Yield spreads 2Y", v: "10Y US ↑ 4,50% (maxim 2 săpt., revenire petrol) = vânt din față pt. tezele anti-USD. USDCAD +1,38 — încă PRO-USD (contra short, onest). EURUSD ~−1,60 contra EUR. NZ 2Y indisponibil → criteriul 4 neutru pe NZDUSD." },
    { k: "5 · COT — Leveraged Funds (as-of 30.06)", v: "EXTREM DUBLU: USD long +$39,8 mld (maxim ≥10 ani, a 8-a săpt.) + SOFR short RECORD (~$750 mld). NZD short RECORD (−63k), JPY short maxim 2 ani (−155k), CAD/GBP/CHF short extreme. EUR spre neutru. Squeeze pe NZD/JPY în săpt. deciziilor; reversal anti-USD posibil." },
    { k: "6 · Sentiment (risk-on/off)", v: "RISK-ON fragil: apetit intact (indici record, VIX 16), dar randamentele urcă. CACIB: CAD și CHF pozitiv corelate cu risk-on, GBP negativ." },
    { k: "7 · Seasonality 10y (Iulie)", v: "Iulie ușor USD-negativ: EURUSD +0,48% (70%), GBPUSD +0,36% (70%), AUDUSD +0,49% (60%), NZDUSD +0,21% (70%), USDJPY −0,90% (30%, pro-JPY), USDCHF −0,81%, USDCAD −0,38% (hit 50%, slab). Vânt din spate, nu motiv." }
  ],

  // ——— posibile trade-uri (ipoteze condiționate, NU ordine de execuție) ———
  trades_fx: [
    { instrument: "NZDUSD", dir: "LONG (tactic, event 8.07)", conf: "3/5",
      rationale: "Hike la 2,50% consens (22/28) + CPI ↑ spre 4,3% + short lev funds la RECORD + risk-on cu NZD pro-ciclic = squeeze. Scor 5/7 (crit. 1+2 prezente)",
      activation: "Hike/ton clar hawkish 8.07 + risk-on intact + breakout tehnic din nivel",
      invalidation: "Hold dovish 8.07 → mort; minute FOMC hawkish relansează USD. Onest: câștig limitat (hike prețuit), spread 2Y indisponibil" },
    { instrument: "USDCAD", dir: "SHORT (bias, build spre 15.07)", conf: "3/5",
      rationale: "Blocul de rapoarte cel mai aliniat (CACIB 1,35-1,40; Scotia+CIBC rebound) + GDP beat + short CAD extremă + CAD pro-risk. Scor 5/7. Catalizatorul (BoC+MPR) abia 15.07",
      activation: "USD moale post-minute FOMC (non-hawkish) + confirmare tehnică sub nivel-cheie",
      invalidation: "Minute FOMC hawkish / 10Y sus / date CA slabe. Contra: spread 2Y (+1,38) încă PRO-USD + USD long de deceniu" },
    { instrument: "GBPUSD", dir: "WATCH (squeeze)", conf: "—",
      rationale: "Lev funds short pctl ~8 = combustibil de squeeze; dar Services PMI 48,8 + BoE split = fundamente slabe; lipsesc criteriile 1-2",
      activation: "Doar catalizator pozitiv UK + risk-on susținut", invalidation: "—" },
    { instrument: "EURUSD", dir: "STAI", conf: "—",
      rationale: "Ambele bănci centrale au pierdut hike-uri; spread 2Y încă contra EUR; poziționare neutră; criteriul 1 neutru → sub prag",
      activation: "—", invalidation: "Teză neclară = nu există trade (playbook §3.2)" }
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
    { pair: "NZDUSD", dir: "LONG (tactic)", score: "5/7", horizon: "1-3 zile, event RBNZ 8.07",
      invalidation: "Hold dovish 8.07 (ASB/Westpac) → mort; sau minute FOMC hawkish → USD relansat" },
    { pair: "USDCAD", dir: "SHORT (bias)", score: "5/7", horizon: "multi-day, catalizator BoC 15.07",
      invalidation: "Minute FOMC hawkish / 10Y sus / date CA slabe. Contra: spread 2Y +1,38 PRO-USD" }
  ],
  // P&L / trade-uri: în journal_data.js (local, în .gitignore) — nu aici
};
