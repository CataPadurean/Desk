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
| `Terminal Back-end/07_Dashboard` | **Dashboard live** (offline, 8 pagini): `dashboard.html` = Home (regim+sentiment cu VIX, rezumatele criteriilor, teze, posibile trade-uri) · `p1_central_banks` · `p2_bank_reports` · `p3_indicators` · `p4_yields` · `p5_cot` · `p6_seasonality` = câte o pagină per criteriu (sentimentul stă doar pe Home, fără pagină) · `journal.html` = statistici blotter + **Research history** (deznodământul ideilor închise). Meniul comun: `nav.js`; stilul comun: `style.css`. Denumiri UI în engleză, fără numere |

## Cadența (comenzile către Claude)

**Zilnic, dimineața** — pui rapoartele în `1_Upload Reports` și spui: **„procesează inbox"**
→ Claude: extrage tezele fiecărei bănci pe schema fixă, marchează consens/contradicții/schimbări de poziție, generează **Daily Note** în `2_Daily_Note`, arhivează PDF-urile în `Terminal Back-end/02_Rapoarte_Procesate`.

**Stilul notelor: scurt și narativ, nu raport de date.** Ce e deja în terminal (cifre COT, yield spreads, seasonality, detaliul criteriilor, raționamentul complet) NU se repetă în PDF. Daily Note ≈ o pagină: pe scurt · piața · știri & bănci centrale · de urmărit · bias-ul zilei (o linie per instrument). Weekly Note ≈ 1-2 pagini: rezumatul săptămânii încheiate + perspectivă scurtă pe cea care vine + tezele active în proză, cu un singur tabel mic de scor.

**Duminică seara** — spui: **„generează teza săptămânală"**
→ Claude: cele 7 criterii în ordinea importanței — (1) rapoartele săptămânii (singura judecată), (2) Policy vs. Market Pricing — cât e deja în preț, calculat din `view_bp` scris la teză, (3) indicatori economici, (4) yield spreads 2Y, (5) COT leveraged funds, (6) regim de risc, (7) sezonalitate cu media lunii curente → Weekly Macro Note în `3_Weekly_Note`, cu scor de confluență **minim 5/7 (criteriile 1+2 obligatorii)** per pereche, pe universul de 8 monede (core: USD/EUR/GBP/CAD; secundare: JPY/CHF/AUD/NZD — semnalate la divergențe mari). Aceeași notă = schița newsletter-ului.

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
- **COT** (CFTC, gratuit): **Leveraged Funds din TFF** pe EUR/GBP/CAD/JPY/CHF/AUD/NZD/DXY — net, Δ săptămânal, percentilă 52w, semnal de extremă (≥90 / ≤10). Gold scos din COT pe 07.08.2026.
- **Randamente** (gratuite, fără cheie API — reparate 08.07.2026, extinse 03.08.2026): 2Y (principal) & 10Y (secundar) pentru toate 8 monedele + spread-urile vs USD pe cele 7 perechi, cu Δ pe ~5 ședințe. Surse oficiale per monedă, cu fallback: US=FRED→Treasury, EUR=ECB (curba AAA), GBP=BoE (ZIP curba GLC), CAD=BoC Valet, JPY=MOF, CHF=SNB (10Y; 2Y doar din piață — SNB a discontinuat curba zilnică în 2025, și nu s-a găsit nicio altă pagină publică cu 2Y, verificat inclusiv prin Firecrawl pe 10.08.2026 — gol structural confirmat), AUD=RBA F2 zilnic, NZD=pagina B2 direct → **Firecrawl pe aceeași pagină** (adăugat 10.08.2026 — curl nu poate trece niciodată de blocajul Akamai pe amprentă TLS, indiferent de UA; Firecrawl randează într-un browser real, deci ar trebui să vadă tabelul) → xlsx-ul oficial (rar reușește) → **serie manuală din pagina B2**, scrisă la „generează teza" în `directions.json → yields_manual.NZD` dacă toate cele de dinaintea ei pică; Stooq = fallback de piață, dar din 08.2026 întoarce HTML în loc de CSV — practic mort. `src_manual` închide fiecare lanț: serie completă de ~10 ședințe (nu valori izolate, altfel Δ pe 5 ședințe n-are din ce se calcula), cu `source` și `asof`; orice sursă automată care revine la viață are prioritate. **Lanțul umple per TENOR**, nu per monedă: o sursă care aduce doar 10Y nu mai oprește căutarea pentru 2Y (asta lăsa CHF fără criteriul 4 pe tenorul principal). **UA per sursă**: RBNZ și Stooq primesc UA de browser (WAF-ul lor respinge «curl/x» cu 403), FRED rămâne pe UA-ul curl — acolo e invers. **Cache last-known-good**: dacă o sursă pică, rămâne ultima valoare bună cu status «stale» — tabelul nu mai rămâne niciodată gol. Status nou: «parțial» = un singur tenor proaspăt. Refresh zilnic automat din GitHub Actions (11:00 UTC ≈ 14:00 RO, repornit 10.08.2026 — vezi nota despre `--skip-build` mai jos). Test offline: `python3 00_SYSTEM/scripts/test_update_yields.py`. **Diagnostic per sursă: `python3 00_SYSTEM/scripts/update_yields.py --probe NZD CHF`** — spune exact ce întoarce fiecare sursă din lanț (rulează-l pe Mac: IP-ul laptopului nu e blocat la fel ca sandbox-ul, dar sandbox-ul Claude e SUPLIMENTAR blocat pe api.firecrawl.dev — de validat pe Mac sau prin „Run workflow" manual). Recompunere fără rețea: `update_data.py --no-fetch`.
- **Regim de risc** (`update_regime.py`, criteriul 6): VIX (percentila 1 an), ICE BofA US High Yield OAS (percentila 1 an), momentum S&P 5/20 de ședințe — toate din FRED → `regime_score` −2…+2 în `data/regime_latest.json`, cu praguri înghețate. `regime_score` din directions.json rămâne doar fallback dacă FRED e mort.
- **Indicatori economici** (`update_indicators.py`, criteriul 3, revenit mecanic 10.08.2026): index de surpriză actual-vs-consens din calendarul public (mort din 03.08.2026) → **Firecrawl pe tradingeconomics.com/calendar** (necesită `FIRECRAWL_API_KEY`) → fallback manual (`indicators_events` în directions.json). Scrie `data/indicators_latest.json`, citit de `scorecard.py → score_indicators()`; dacă o monedă n-are date mecanice suficiente (prag: ≥2 publicări, ≥2 zile diferite, pondere ≥1,0), cade pe eticheta manuală din `directions.json → indicators`. **Notă de metodă:** prima variantă mecanică a fost scoasă pe 07.08.2026 fiindcă corela +0,81 cu BNK (aceleași publicări citate deja acolo) — a revenit la cerere explicită, dar `why`-ul din tooltip rămâne marcat cu avertismentul, ca dubla-numărare să se vadă, nu să dispară tăcut.
- **Sezonalitate 10 ani** (FRED/Stooq): 7 perechi FX + Gold + US30, cu blocul lunii curente (medie % + hit rate).

**Firecrawl** (`firecrawl_client.py`): folosit DOAR ca fallback pentru pagini blocate la fetch direct (NZD, calendarul TE) — niciodată ca înlocuitor al surselor oficiale gratuite care funcționează. Cheia vine din variabila de mediu `FIRECRAWL_API_KEY` — local, `export FIRECRAWL_API_KEY=fc-...` înainte de rulare; în GitHub Actions, secret de repo cu același nume. Nu se scrie niciodată în cod sau în fișierele de date.

Rulează-l duminica înainte de „generează teza" (sau lasă-l pe Claude să încerce; dacă rețeaua lui e restricționată, îl rulezi tu — e o singură comandă). Fără dependențe noi de instalat: doar Python 3 standard + `urllib`/`curl`, deja pe Mac. **Cron-ul zilnic din GitHub Actions** (repornit 10.08.2026) rulează `update_data.py --skip-build`: fetch normal, dar NU rescrie `analysis_data.js` — fișierul acela se compune DOAR la comenzi explicite (procesează inbox / generează teza), ca să nu mai intre în conflict de rebase cu editările manuale (motivul pauzei din 31.07.2026).

## Reguli de numire (recomandat, nu obligatoriu)

`YYYY-MM-DD_Banca_Subiect.pdf` (ex. `2026-07-02_JPM_FX-Daily.pdf`). Dacă numele diferă, Claude se descurcă din conținut.

## Conturi

- Strategia A (FX intra-week) → cont dedicat (țintă: FTMO Swing)
- Strategia B (intraday Dow/Gold) → cont dedicat (țintă: Alpha Swing)
- Fiecare trade din Blotter e etichetat pe cont, strategie și **fază** (coloana W: Evaluation / Funded); statisticile nu se amestecă — nici între strategii, nici între faze.
- **Idea ref** (coloana V) leagă execuția de ideea din terminal: ID-ul `AAAA-LL-ZZ-INSTRUMENT-L|S` afișat sub instrument în Home și în History. Journal-ul arată fiecare trade lângă ideea lui și deznodământul ei; trade-urile fără ID apar ca `off-book`. KPI-ul „From book" e o măsură de disciplină, nu un scor de performanță.
