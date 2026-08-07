// ISTORICUL RESEARCH-ULUI — trade-urile propuse de terminal, cu deznodământ.
// NU e jurnalul de execuție (acela e journal_data.js, local, cu P&L). Aici stau IDEILE de trade
// din Daily Note / Possible Trades, cu ce s-a ales de fiecare. Tezele NU se arhivează separat:
// fiecare teză se reflectă în trade-ul pe care l-a produs.
//
// Se scrie la „procesează inbox" / „generează teza săptămânală", când o idee se închide.
//
// Schema unei intrări:
//   id          "2026-07-06-USDCAD-S"            — ID-ul ideii, identic cu cel din data.js
//                                                  (AAAA-LL-ZZ-INSTRUMENT-L|S) — cheia de legătură cu blotter-ul
//   date        "16.07.2026"                     — data închiderii ideii
//   opened      "06.07.2026"                     — data la care a apărut în terminal
//   type        "Swing" | "Intraday"
//   instrument  "USDCAD"
//   dir         "SHORT" | "LONG" | "—" (fără direcție angajată)
//   score       "3/5" — convingerea din tabelul de trade-uri
//   criteria    criteriile care au cântărit, pe scurt; contra-criteriile în paranteză
//   outcome     "VALIDATĂ" | "INVALIDATĂ" | "BREAKEVEN" | "EXPIRATĂ" | "NEACTIVATĂ"
//               (BREAKEVEN / EXPIRATĂ / NEACTIVATĂ nu intră în rata de validare — sunt neconcludente)
//   gap         9.2 — diferența de rank din scorecard la data deschiderii (numeric, nu text).
//               Se copiază din book la închidere: fără ea nu se poate afla niciodată dacă
//               un gap mare chiar prezice o mișcare mai mare
//   move_atr    1.8 — mișcarea realizată în direcția ideii, de la `opened` la `date`,
//               măsurată în ATR(14) zilnic al instrumentului la deschidere. Negativ = a mers
//               invers. ATR, nu pipi, ca GBPNZD și EURUSD să fie comparabile.
//               null cât nu e măsurată
//   reason      2-3 rânduri: ce s-a întâmplat și de ce, în cuvinte
//
// De ce `gap` + `move_atr`: perechea lor e singura cale de a afla dacă pragul de 6,0 din
// scorecard e bun sau ales din burtă. Cu ~30 de idei închise se poate regresa move_atr pe
// gap; până atunci sunt doar două coloane care se acumulează.
window.HISTORY_DATA = {
  entries: [
    {
      id: "2026-07-06-NZDUSD-L", opened: "06.07.2026", date: "10.07.2026", type: "Swing",
      instrument: "NZDUSD", dir: "LONG", score: "3/5",
      criteria: "Central Banks · Bank Reports · Indicators · COT (contra: Yields — 2Y indisponibil)",
      outcome: "VALIDATĂ",
      reason: "RBNZ a majorat dobânda la 2,50% pe 8.07, prima creștere din 2023, exact catalizatorul pe care se sprijinea ideea. NZDUSD a urcat 0,53% în ziua deciziei, spre 0,5706, și a continuat peste 0,58 până spre finalul lunii. Avertismentul din teză — câștig limitat fiindcă majorarea era deja prețuită — s-a dovedit prea prudent."
    },
    {
      id: "2026-07-06-USDCAD-S", opened: "06.07.2026", date: "16.07.2026", type: "Swing",
      instrument: "USDCAD", dir: "SHORT", score: "3/5",
      criteria: "Bank Reports · Central Banks · Indicators · COT (contra: Yields — spread 2Y pro-USD)",
      outcome: "VALIDATĂ",
      reason: "BoC a ținut dobânda pe 15.07 cu ton neutru-hawkish, iar petrolul aproape de 80 $ a susținut loonie-ul. USDCAD a coborât de la ~1,418 spre 1,4047, iar dolarul canadian a atins maximul ultimelor patru săptămâni. Direcția a fost corectă, dar zona-țintă a băncilor, 1,35-1,40, n-a fost atinsă."
    },
    {
      id: "2026-07-06-US30-L", opened: "06.07.2026", date: "10.07.2026", type: "Intraday",
      instrument: "US30", dir: "LONG", score: "3/5",
      criteria: "Sentiment (risk-on, VIX 16) · Central Banks (minute FOMC) — contra: randamente în creștere",
      outcome: "VALIDATĂ",
      reason: "Regimul risk-on s-a menținut, iar indicele a mers bullish din nivelul record atins la începutul săptămânii. Riscul semnalat la deschidere — minutele FOMC de miercuri — n-a rupt trendul, iar VIX-ul a rămas sub pragul de 20 care ar fi anulat setup-ul."
    },
    {
      id: "2026-07-06-GOLD-L", opened: "06.07.2026", date: "10.07.2026", type: "Intraday",
      instrument: "GOLD", dir: "LONG", score: "2,5/5",
      criteria: "Sentiment · DXY sub 101 — contra: randamente reale în urcare (10Y 4,50%)",
      outcome: "BREAKEVEN",
      reason: "Setup-ul s-a activat, dar mișcarea n-a avut continuare și poziția s-a închis la zero. Vântul din față semnalat încă de la deschidere — randamentele reale în creștere — a anulat suportul venit din slăbiciunea dolarului. Convingerea redusă, 2,5/5, s-a dovedit corect calibrată."
    }
  ]
};
