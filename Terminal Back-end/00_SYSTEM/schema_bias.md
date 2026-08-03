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
| Argumente-cheie | max 3, în cuvintele băncii, comprimate — DOAR raționament (macro, politică monetară, evaluare) |
| **Flux & poziționare** | ce a VĂZUT banca, nu ce crede: flux de clienți (real money, corporate, hedge funds), poziționarea agregată a bazei ei de clienți, ce a fost cumpărat/vândut și de cine. Vezi mai jos |
| Niveluri menționate | ținte, praguri, forecast-uri numerice |
| Invalidare | ce eveniment/nivel ar răsturna teza băncii |
| Schimbare vs. anterior | NOU / neschimbat / întărit / slăbit / întors |

### De ce are fluxul câmp separat

Prognoza direcțională a unei bănci pleacă spre mii de destinatari instituționali în aceeași
dimineață și e slab calibrată — nu e informație rară. Fluxul de clienți pe care îl vede
banca prin propriile cărți E informație rară: nimeni altcineva nu-l are, iar el spune ce
s-a întâmplat deja, nu ce crede cineva că se va întâmpla. Amestecat printre argumente,
se pierde. Separat, se poate compara cu COT (criteriul 5) și cu poziționarea implicită
din pricing.

Reguli de extracție:
- Se completează **doar dacă banca afirmă o observație de flux sau de poziționare.** Fără
  flux → `—`. Nu se deduce din ton, nu se inventează din „we expect".
- Formatul: `[cine] [ce a făcut] [pe ce] — [sursa afirmației]`.
  Ex.: `real money a cumpărat CAD două săptămâni la rând — flux propriu CACIB`;
  `baza de clienți e short EUR aproape de maxim de an — sondaj de poziționare ING`.
- Se marchează explicit când fluxul **contrazice** direcția scrisă a raportului. E cel mai
  valoros lucru dintr-un raport: banca spune bullish și își vede clienții vânzând.
- Nu intră aici: date publice de poziționare (COT — criteriul 5), sondaje de sentiment
  retail, comentarii de tip „piața pare poziționată pentru…" fără observație proprie.

Câmpul se scrie în `directions.json → reports[].flow` (string; `""` dacă lipsește) și
apare pe pagina Bank Reports, coloana **Flow / positioning**.

## Agregarea (Weekly Macro Note)

Per activ:
- **Consens:** câte bănci pe fiecare direcție (ex. EUR: 3 bullish / 1 neutru)
- **Contradicții:** cine diverge și pe ce argument — semnalul cel mai valoros
- **Schimbări de poziție:** cine și-a întors direcția săptămâna asta — al doilea semnal ca valoare
- **Flux vs. narativ:** ce spun observațiile de flux față de direcția scrisă a rapoartelor și
  față de COT. Trei cazuri de semnalat: fluxul confirmă narativul (nimic nou), fluxul
  contrazice narativul aceleiași bănci (semnal), fluxul confirmă o poziționare COT deja
  extremă (risc de squeeze, nu confirmare)

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
