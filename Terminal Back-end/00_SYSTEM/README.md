# DESK SYSTEM — Manual de operare

Sistem de research & trading semi-automatizat. Stack: Trading Economics (macro), Financial Juice (news line), CFTC (COT), FRED (randamente). Fără LSEG (opțional, doar duminica pentru OIS).

## Structura

La rădăcina folderului „Padu Terminal" stau doar folderele cu care lucrezi tu (`1_Upload Reports`, `2_Daily_Note`, `3_Weekly_Note`) + `CLAUDE.md`. Restul (motorul) e sub `Terminal Back-end/`.

| Folder | Rol |
|---|---|
| `Terminal Back-end/00_SYSTEM` | Reguli, playbook, scheme, template-uri |
| `1_Upload Reports` | **Aici pui PDF-urile** (zilnic comerciale, săptămânal bănci centrale) |
| `Terminal Back-end/02_Rapoarte_Procesate` | Arhivă după procesare, pe săptămâni |
| `3_Weekly_Note` | Teza săptămânală (duminică) |
| `2_Daily_Note` | Daily Note — newsletter-ul zilnic pre-market |
| `Terminal Back-end/05_Trade_Blotter` | Jurnalul de trade-uri (Excel, statistici automate) |
| `Terminal Back-end/06_Risk_Reports` | Raport lunar de risc & performanță |
| `Terminal Back-end/07_Dashboard` | **Dashboard live** (offline, 3 pagini): `dashboard.html` = overview + posibile trade-uri (FX / intraday) · `analysis.html` = cele 7 criterii + secțiuni per monedă · `journal.html` = statistici blotter |

## Cadența (comenzile către Claude)

**Zilnic, dimineața** — pui rapoartele în `1_Upload Reports` și spui: **„procesează inbox"**
→ Claude: extrage tezele fiecărei bănci pe schema fixă, marchează consens/contradicții/schimbări de poziție, generează **Daily Note** în `2_Daily_Note`, arhivează PDF-urile în `Terminal Back-end/02_Rapoarte_Procesate`.

**Stilul notelor: scurt și narativ, nu raport de date.** Ce e deja în terminal (cifre COT, yield spreads, seasonality, detaliul criteriilor, raționamentul complet) NU se repetă în PDF. Daily Note ≈ o pagină: pe scurt · piața · știri & bănci centrale · de urmărit · bias-ul zilei (o linie per instrument). Weekly Note ≈ 1-2 pagini: rezumatul săptămânii încheiate + perspectivă scurtă pe cea care vine + tezele active în proză, cu un singur tabel mic de scor.

**Duminică seara** — spui: **„generează teza săptămânală"**
→ Claude: cele 7 criterii în ordinea importanței — (1) Central Banks Outlook (TMV + sweep), (2) rapoartele săptămânii, (3) indicatori economici, (4) yield spreads 2Y, (5) COT leveraged funds, (6) sentiment, (7) sezonalitate cu media lunii curente → Weekly Macro Note în `3_Weekly_Note`, cu scor de confluență **minim 5/7 (criteriile 1+2 obligatorii)** per pereche, pe universul de 8 monede (core: USD/EUR/GBP/CAD; secundare: JPY/CHF/AUD/NZD — semnalate la divergențe mari). Aceeași notă = schița newsletter-ului.

**După fiecare sesiune** — spui: **„loghează:"** + detaliile trade-urilor (sau dai statement-ul MT5)
→ Claude completează Blotter-ul; statisticile (expectancy per setup / strategie / cont) se calculează singure.

**Prima duminică din lună** — spui: **„raport lunar"**
→ Claude: Risk & Performance Report în `06` + propuneri de modificare a regulilor bazate pe date.

**Dashboard-ul** (`07_Dashboard/`) se actualizează automat la fiecare comandă de mai sus — Claude regenerează `data.js` (overview + trade-uri posibile) și `analysis_data.js` (criteriile + secțiunile per monedă, din `00_SYSTEM/data/directions.json`). Ții paginile deschise în browser și dai refresh.

## Împărțirea muncii

- **Claude:** stratul fundamental — direcție, convingere, context, zone de valoare, triaj rapoarte, jurnal, statistici, rapoarte.
- **Tu:** analiza tehnică, nivelurile exacte de intrare/ieșire, execuția, monitorizarea Financial Juice live.
- **Limitare asumată:** Claude nu monitorizează breaking news în timp real. Headline-urile instant = ecranul tău (Financial Juice). În schimb, oricând în sesiune poți spune **„verifică știrile"** → Claude caută pe surse publice (Reuters, CNBC, MarketWatch etc.) și îți dă sinteza cu impact per instrument, cu surse citate.

## Scripturile de date (00_SYSTEM/scripts)

`python3 00_SYSTEM/scripts/update_data.py` (din folderul Trading, ~30 sec) → scrie `00_SYSTEM/data/macro_snapshot.md` + regenerează `analysis_data.js`:
- **COT** (CFTC, gratuit): **Leveraged Funds din TFF** pe EUR/GBP/CAD/JPY/CHF/AUD/NZD/DXY + **Managed Money (Disaggregated)** pe Gold — net, Δ săptămânal, percentilă 52w, semnal de extremă (≥90 / ≤10).
- **Randamente** (gratuite, fără cheie API — reparate 08.07.2026): 2Y (principal) & 10Y (secundar) pentru toate 8 monedele + spread-urile vs USD pe cele 7 perechi, cu Δ pe ~5 ședințe. Surse oficiale per monedă, cu fallback: US=FRED→Treasury, EUR=ECB (curba AAA), GBP=BoE (ZIP curba GLC), CAD=BoC Valet, JPY=MOF, CHF=SNB (10Y; 2Y doar din piață — SNB a discontinuat curba zilnică în 2025), AUD=RBA F2 zilnic, NZD=RBNZ B2 (xlsx); Stooq = fallback de piață. **Cache last-known-good**: dacă o sursă pică, rămâne ultima valoare bună cu status «stale» — tabelul nu mai rămâne niciodată gol. Refresh zilnic automat din GitHub Actions (11:00 UTC ≈ 14:00 RO). Test offline: `python3 00_SYSTEM/scripts/test_update_yields.py`. Recompunere fără rețea: `update_data.py --no-fetch`.
- **Sezonalitate 10 ani** (FRED/Stooq): 7 perechi FX + Gold + US30, cu blocul lunii curente (medie % + hit rate).

Rulează-l duminica înainte de „generează teza" (sau lasă-l pe Claude să încerce; dacă rețeaua lui e restricționată, îl rulezi tu — e o singură comandă). Fără dependențe: doar Python 3 standard, deja instalat pe Mac.

## Reguli de numire (recomandat, nu obligatoriu)

`YYYY-MM-DD_Banca_Subiect.pdf` (ex. `2026-07-02_JPM_FX-Daily.pdf`). Dacă numele diferă, Claude se descurcă din conținut.

## Conturi

- Strategia A (FX intra-week) → cont dedicat (țintă: FTMO Swing)
- Strategia B (intraday Dow/Gold) → cont dedicat (țintă: Alpha Swing)
- Fiecare trade din Blotter e etichetat pe cont și strategie; statisticile nu se amestecă.
