# Schema fixă de extracție — rapoarte bănci

Universul: **8 monede** — USD, EUR, GBP, CAD (core) + JPY, CHF, AUD, NZD (secundare, semnalate la divergențe mari / setup-uri „sigure") + Gold, US30 (intraday).

Fiecare raport procesat produce un rând per valută/activ menționat:

| Câmp | Descriere |
|---|---|
| Banca | CACIB / JPM / ING / HSBC / MUFG / UniCredit / Natixis / TMV / alta |
| Data raportului | data publicării, nu a încărcării |
| Activ | una din cele 8 monede, Gold, indici |
| Direcție | Bullish / Bearish / Neutru |
| Orizont | zile / săptămâni / trimestru |
| Convingere | 1–5 (dedusă din limbaj: „we expect" > „risks are tilted") |
| Argumente-cheie | max 3, în cuvintele băncii, comprimate |
| Niveluri menționate | ținte, praguri, forecast-uri numerice |
| Invalidare | ce eveniment/nivel ar răsturna teza băncii |
| Schimbare vs. anterior | NOU / neschimbat / întărit / slăbit / întors |

## Agregarea (Weekly Macro Note)

Per activ:
- **Consens:** câte bănci pe fiecare direcție (ex. EUR: 3 bullish / 1 neutru)
- **Contradicții:** cine diverge și pe ce argument — semnalul cel mai valoros
- **Schimbări de poziție:** cine și-a întors direcția săptămâna asta — al doilea semnal ca valoare

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
