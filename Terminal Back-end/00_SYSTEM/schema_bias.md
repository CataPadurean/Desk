# Schema fixă de extracție — rapoarte bănci

Universul: **8 monede** — USD, EUR, GBP, CAD (core) + JPY, CHF, AUD, NZD (secundare, semnalate la divergențe mari / setup-uri „sigure") + Gold, US30 (intraday).

Fiecare raport procesat produce un rând per valută/activ menționat:

| Câmp | Descriere |
|---|---|
| Banca | CACIB / JPM / ING / HSBC / MUFG / UniCredit / Natixis / TMV / alta |
| Data raportului | data publicării, nu a încărcării |
| Activ | **strict codul monedei** (una din cele 8), `Gold` sau `US30` — o pereche citată în raport se trece pe moneda de bază, cu direcția raportată la ea (raport bearish EUR/USD → `EUR` / Bearish) |
| Direcție | Bullish / Bearish / Neutru |
| Orizont | zile / săptămâni / trimestru |
| Convingere | 1–5 (dedusă din limbaj: „we expect" > „risks are tilted") |
| Argumente-cheie | max 3, în cuvintele băncii, comprimate — DOAR raționament (macro, politică monetară, evaluare) |
| Schimbare vs. anterior | NOU / neschimbat / întărit / slăbit / întors |

Câmpurile **Flux & poziționare, Niveluri menționate și Invalidare au fost scoase din schemă
(12.08.2026)** — nu se mai extrag și nu mai există în `directions.json → reports[]`. Motivul:
tabelul se citește acum pe verticală, per monedă, iar detaliul de raport individual nu mai
avea unde să se afișeze. Poziționarea rămâne acoperită de COT (criteriul 5); nivelurile și
invalidarea trăiesc acolo unde se execută — în book-ul de trade-uri (`trigger` / `invalidation`).

### Afișarea: comasat pe monedă (12.08.2026)

Pagina Bank Reports NU mai listează un rând per raport. Cele 8 monede apar una sub alta, în
ordinea din regula 0 (`USD, EUR, GBP, JPY, CHF, CAD, AUD, NZD`), apoi `Gold` și `US30` dacă
există rapoarte pe ele. Un rând = **o monedă + o direcție**, cu toate băncile care au scris-o:

`Date | Asset | Direction | Horizon | Conviction | Banks`

- **Date** = raportul cel mai recent din grup · **Horizon** = orizontul dominant · **Conviction**
  = media grupului (cifra exactă în tooltip) · **Banks** = băncile, cu data fiecăreia în tooltip.
- O monedă fără rapoarte în săptămâna curentă rămâne pe pagină, marcată explicit — absența
  acoperirii e informație, nu un rând lipsă.
- Contradicția (aceeași monedă cu bănci bullish ȘI bearish) se marchează cu ⚔ pe monedă.
- Argumentele NU apar în tabel — sinteza lor per monedă stă în cardul de sub tabel
  (`currencies[ccy].banks`).

## Agregarea (Weekly Macro Note)

Per activ:
- **Consens:** câte bănci pe fiecare direcție (ex. EUR: 3 bullish / 1 neutru)
- **Contradicții:** cine diverge și pe ce argument — semnalul cel mai valoros
- **Schimbări de poziție:** cine și-a întors direcția săptămâna asta — al doilea semnal ca valoare
- **Narativ vs. COT:** unde consensul bancar bate cu poziționarea leveraged funds și unde nu.
  Consensul care confirmă o poziționare COT deja extremă (≥90/≤10) e risc de squeeze, nu confirmare

## Scorul de confluență — 7 criterii, în ordinea importanței

| # | Criteriu | Sursă |
|---|---|---|
| 1 | **Weekly Central Banks Outlook** (obligatoriu) | TMV săptămânal + sweep-ul Claude (decizii, retorică, pricing) |
| 2 | **Rapoartele bancare** (obligatoriu) | schema de mai sus, agregată |
| 3 | Indicatori economici | integrați în comentariul per monedă: ultimele date cheie + cum au evoluat |
| 4 | Yield spreads 2Y | spread-ul perechii + Δ săptămânal (10Y secundar) |
| 5 | COT — **Leveraged Funds (TFF)**; Gold = Managed Money (Disaggregated) | net, Δ, percentilă 52w; extremele ≥90/≤10 se semnalează mereu (risc de squeeze, nu confirmare) |
| 6 | Sentiment / regim de risc | verdict global risk-on/off (VIX, equities, credit, corelații) |
| 7 | Seasonality 10y | media de change % a lunii curente per instrument — vânt din spate/față, niciodată motiv principal |

**Prag: minim 5/7, criteriile 1 și 2 obligatorii.** Maximum 2–3 teze active, fiecare cu invalidare fundamentală explicită. Criteriile care contrazic teza se scriu explicit în tabel (onestitate înaintea convingerii).
