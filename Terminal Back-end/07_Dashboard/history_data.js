// ISTORICUL RESEARCH-ULUI — tot ce a propus terminalul, cu deznodământ.
// NU e jurnalul de execuție (acela e journal_data.js, local, cu P&L). Aici stau IDEILE:
// teze din Weekly Note și trade-uri posibile din Daily Note, cu ce s-a ales de ele.
//
// Se scrie automat la comenzile sistemului:
//   • „generează teza săptămânală" → tezele care ies din listă (invalidate/expirate) se arhivează aici
//   • „procesează inbox"           → trade-urile posibile care s-au închis (declanșate sau ratate) se arhivează aici
//
// Schema unei intrări:
//   date        "31.07.2026"                     — data închiderii
//   opened      "27.07.2026"                     — data la care a apărut ideea
//   type        "Teză" | "Trade FX" | "Trade intraday"
//   instrument  "USDCAD"
//   dir         "SHORT" | "LONG" | "WATCH" | "STAI"
//   score       "5/7" (teze) | "3/5" (trade-uri) | "—"
//   outcome     "VALIDATĂ" | "INVALIDATĂ" | "EXPIRATĂ" | "DECLANȘATĂ" | "NEACTIVATĂ"
//   reason      2-3 rânduri: ce s-a întâmplat și de ce, în cuvinte
window.HISTORY_DATA = {
  entries: [
    // Se populează pe măsură ce tezele și trade-urile posibile se închid.
  ]
};
