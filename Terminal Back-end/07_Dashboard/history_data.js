// ISTORICUL RESEARCH-ULUI — trade-urile propuse de terminal, cu deznodământ.
// NU e jurnalul de execuție (acela e journal_data.js, local, cu P&L). Aici stau IDEILE de trade
// din Daily Note / Possible Trades, cu ce s-a ales de fiecare. Tezele NU se arhivează separat:
// fiecare teză se reflectă în trade-ul pe care l-a produs.
//
// Se scrie la „procesează inbox" / „generează teza săptămânală", când o idee se închide.
//
// Schema unei intrări:
//   date        "16.07.2026"                     — data închiderii ideii
//   opened      "06.07.2026"                     — data la care a apărut în terminal
//   type        "Trade FX" | "Trade intraday"
//   instrument  "USDCAD"
//   dir         "SHORT" | "LONG" | "WATCH" | "STAI"
//   score       "3/5" — convingerea din tabelul de trade-uri
//   criteria    criteriile care au cântărit, pe scurt; contra-criteriile în paranteză
//   outcome     "VALIDATĂ" | "INVALIDATĂ" | "EXPIRATĂ" | "NEACTIVATĂ"
//   reason      2-3 rânduri: ce s-a întâmplat și de ce, în cuvinte
window.HISTORY_DATA = {
  entries: [
    {
      opened: "06.07.2026", date: "10.07.2026", type: "Trade FX",
      instrument: "NZDUSD", dir: "LONG", score: "3/5",
      criteria: "Central Banks · Bank Reports · Indicators · COT (contra: Yields — 2Y indisponibil)",
      outcome: "VALIDATĂ",
      reason: "RBNZ a majorat dobânda la 2,50% pe 8.07, prima creștere din 2023, exact catalizatorul pe care se sprijinea ideea. NZDUSD a urcat 0,53% în ziua deciziei, spre 0,5706, și a continuat peste 0,58 până spre finalul lunii. Avertismentul din teză — câștig limitat fiindcă majorarea era deja prețuită — s-a dovedit prea prudent."
    },
    {
      opened: "06.07.2026", date: "16.07.2026", type: "Trade FX",
      instrument: "USDCAD", dir: "SHORT", score: "3/5",
      criteria: "Bank Reports · Central Banks · Indicators · COT (contra: Yields — spread 2Y pro-USD)",
      outcome: "VALIDATĂ",
      reason: "BoC a ținut dobânda pe 15.07 cu ton neutru-hawkish, iar petrolul aproape de 80 $ a susținut loonie-ul. USDCAD a coborât de la ~1,418 spre 1,4047, iar dolarul canadian a atins maximul ultimelor patru săptămâni. Direcția a fost corectă, dar zona-țintă a băncilor, 1,35-1,40, n-a fost atinsă."
    }
  ]
};
