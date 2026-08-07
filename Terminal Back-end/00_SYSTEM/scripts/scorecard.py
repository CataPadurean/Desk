#!/usr/bin/env python3
"""CURRENCY SCORECARD — scorul cross-secțional pe cele 8 monede.

Motorul de generare a ideilor. Fiecare monedă primește un scor −2…+2 pe fiecare dintre
cele 7 criterii; scorul sintetic se normalizează la ±10 și dă rank-ul. Perechile rezultă
din diferența de rank, nu din intuiție.

Împărțirea muncii (decisă 02.08.2026):
  · criteriile 1-2 (Bank Reports, Central Banks) = JUDECATĂ — scrise de Claude în
    directions.json → scorecard.judgment, cu justificare per monedă;
  · criteriile 3-7 (Indicators, Yields, COT, Regime, Seasonality) = AUTOMAT, calculate aici
    — IND din eticheta manuală (directions.json → indicators), restul din cot_latest.json /
    yields_latest.json / seasonality.json / regime_latest.json, cu praguri fixe.

03.08.2026 — criteriul 6 a trecut de la etichetă la date: REG citește regime_latest.json
(VIX + HY OAS + momentum S&P; update_regime.py). `regime_score` din directions.json
rămâne fallback dacă FRED e mort.

07.08.2026 — criteriul 3 a revenit la etichetă manuală. Varianta mecanică (index de
surpriză actual-vs-consens, update_indicators.py) corela +0,8+ cu CB și BNK — aceleași
publicări citate deja în argumentele lor — și depindea de un feed de calendar mort care
cerea o corvoadă săptămânală prin Chrome doar ca să dea „fără date". Cătălin urmărește
oricum calendarul live pentru execuție; eticheta scrisă la procesarea rapoartelor
(„Macro state per currency") rămâne singura sursă a criteriului 3.

PRAGURILE SE ÎNGHEAȚĂ. Ajustarea lor retroactiv, ca să iasă scorul dorit, e cel mai
comun mod de a strica un scorecard. Se modifică doar la review lunar, pe date, ca
playbook-ul.
"""
from __future__ import annotations

# ——— ponderi (total 10,0 → normalizare la ±10) ———
# Rebalansate 07.08.2026, varianta „regim dublu":
#   · BNK trece peste CB — rapoartele bancare sunt materialul cel mai bogat din inbox
#     și criteriul pe care Cătălin îl citește efectiv săptămână de săptămână;
#   · REG urcă de la 0,5 la 1,0 și YLD de la ... la 1,5 — sunt singurele criterii care
#     hrănesc și execuția intraday (VIX pentru Dow, randamente reale pentru Gold),
#     nu doar rank-ul cross-secțional de pe FX;
#   · IND coboară la 1,0 — e etichetă manuală și corelează puternic cu CB/BNK
#     (aceleași publicări, citate deja în argumentele lor).
# Totalul e 10,0 ca ponderea să se citească direct („BNK = 3 din 10"). Normalizarea
# la ±10 se face oricum pe suma criteriilor disponibile, deci schimbarea totalului
# de la 12,5 la 10,0 nu mută niciun scor — doar raportul dintre criterii o face.
WEIGHTS = {
    'bnk': 3.00,   # 1. Bank Reports   (judecată)
    'cb':  2.00,   # 2. Central Banks  (judecată)
    'ind': 1.00,   # 3. Economic Indicators (etichetă manuală)
    'yld': 1.50,   # 4. Yield Spreads
    'cot': 1.00,   # 5. COT
    'reg': 1.00,   # 6. Risk Regime
    'sea': 0.50,   # 7. Seasonality
}
CRIT_ORDER = ('bnk', 'cb', 'ind', 'yld', 'cot', 'reg', 'sea')
CRIT_LABEL = {'cb': 'CB', 'bnk': 'BNK', 'ind': 'IND', 'yld': 'YLD',
              'cot': 'COT', 'reg': 'REG', 'sea': 'SEA'}
JUDGMENT = ('bnk', 'cb')

CCY_ORDER = ('USD', 'EUR', 'GBP', 'CAD', 'JPY', 'CHF', 'AUD', 'NZD')

# perechile evaluate: cele 7 cu dolar + crosses lichide (cross-secțiunea plătește
# tocmai pe non-USD, unde nicio bancă nu scrie un raport dedicat)
USD_PAIRS = ('EURUSD', 'GBPUSD', 'USDCAD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD')
CROSSES   = ('EURGBP', 'EURJPY', 'GBPJPY', 'AUDNZD', 'CADJPY', 'GBPNZD')

# ——— criteriul 5: COT (contrarian la extreme — combustibil de squeeze, nu confirmare) ———
COT_MARKET = {'USD': 'DXY', 'EUR': 'EUR', 'GBP': 'GBP', 'CAD': 'CAD',
              'JPY': 'JPY', 'CHF': 'CHF', 'AUD': 'AUD', 'NZD': 'NZD'}
COT_BANDS = ((10, 2), (20, 1), (79, 0), (89, -1), (100, -2))   # (percentilă max, scor)

# ——— criteriul 4: yields — Δ2Y pe ~5 ședințe, RELATIV la media celorlalte monede ———
YLD_BANDS = ((0.12, 2), (0.05, 1), (-0.05, 0), (-0.12, -1))    # peste prag → scor; sub tot → −2

# ——— criteriul 3: surprize macro (provizoriu: din câmpul `surprise`, până la un
#     index real actual-vs-consens; vezi TODO în README) ———
IND_MAP = {'foarte pozitiv': 2, 'pozitiv': 1, 'mixt': 0, 'neutru': 0,
           'negativ': -1, 'foarte negativ': -2}

# ——— criteriul 6: beta la regimul de risc (regime_score × beta, rotunjit, plafonat ±2) ———
# CHF pozitiv, nu negativ: CACIB semnalează corelația atipică a francului cu apetitul de risc.
RISK_BETA = {'USD': -0.5, 'EUR': 0.0, 'GBP': -0.3, 'CAD': 1.0,
             'JPY': -1.0, 'CHF': 0.5, 'AUD': 1.0, 'NZD': 1.0}

# ——— criteriul 7: seasonality — plafonat ±1 (vânt din spate, niciodată motiv principal) ———
SEA_HIT_HI, SEA_HIT_LO = 65, 35

# ——— filtrul scorecard → book ———
GAP_BOOK, GAP_WATCH = 6.0, 5.0


def _round_half_up(x: float) -> int:
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def _clamp(x: int, lo: int = -2, hi: int = 2) -> int:
    return max(lo, min(hi, x))


def _band(value: float, bands, below: int):
    """bands = ((prag, scor), …) în ordine descrescătoare a pragului."""
    for edge, sc in bands:
        if value >= edge:
            return sc
    return below


# ══════════════════════════════════════════════════════════════════════════
# criteriile mecanice
# ══════════════════════════════════════════════════════════════════════════

def score_cot(cot: dict | None) -> dict:
    """Percentila 52w → scor contrarian. Long aglomerat = vulnerabil, short aglomerat = combustibil."""
    out = {}
    mk = (cot or {}).get('markets', {})
    for ccy in CCY_ORDER:
        m = mk.get(COT_MARKET[ccy])
        p = (m or {}).get('percentile_52w')
        if p is None:
            out[ccy] = (None, 'feed COT indisponibil')
            continue
        sc = next(s for edge, s in COT_BANDS if p <= edge)
        if sc > 0:
            why = f'short aglomerat (percentila {p}) — combustibil de squeeze'
        elif sc < 0:
            why = f'long aglomerat (percentila {p}) — vulnerabil la dezamăgire'
        else:
            why = f'poziționare neutră (percentila {p})'
        out[ccy] = (sc, why)
    return out


def score_yields(yld: dict | None) -> dict:
    """Δ2Y pe ~5 ședințe, raportat la media celorlalte monede — mișcarea relativă contează."""
    lv = (yld or {}).get('levels', {})
    deltas, used = {}, {}
    for ccy in CCY_ORDER:
        key = 'US' if ccy == 'USD' else ccy
        node = lv.get(key) or {}
        for tenor in ('2Y', '10Y'):
            d = (node.get(tenor) or {}).get('delta_1w')
            if d is not None:
                deltas[ccy], used[ccy] = float(d), tenor
                break
    out = {}
    for ccy in CCY_ORDER:
        if ccy not in deltas:
            st = ((yld or {}).get('status', {}) or {}).get('US' if ccy == 'USD' else ccy, '')
            out[ccy] = (None, 'randamente indisponibile' + (f' ({str(st).split(":")[0]})' if st else ''))
            continue
        others = [v for k, v in deltas.items() if k != ccy]
        rel = deltas[ccy] - (sum(others) / len(others) if others else 0.0)
        sc = _band(rel, YLD_BANDS, -2)
        tag = '' if used[ccy] == '2Y' else ' [10Y — 2Y indisponibil]'
        out[ccy] = (sc, f'Δ{used[ccy]} {deltas[ccy]:+.3f}, adică {rel:+.3f} față de media grupului{tag}')
    return out


def score_indicators(directions: dict) -> dict:
    """Etichetă manuală, scrisă la procesarea rapoartelor (Macro state per currency).
    Vezi nota din 07.08.2026 din header: varianta mecanică a fost eliminată."""
    out = {}
    for ccy in CCY_ORDER:
        s = str(((directions.get('indicators', {}) or {}).get(ccy) or {})
                .get('surprise', '')).strip().lower()
        if s in IND_MAP:
            out[ccy] = (IND_MAP[s], f'etichetă manuală „{s}"')
        else:
            out[ccy] = (None, 'fără citire de surpriză')
    return out


def score_regime(directions: dict, reg: dict | None = None) -> dict:
    """regime_score (−2…+2, risk-on pozitiv) × beta monedei.
    Scorul vine calculat din regime_latest.json; directions.json e doar plasă de siguranță."""
    src = 'calculat'
    rs = (reg or {}).get('score')
    if rs is None:
        rs, src = directions.get('regime_score'), 'manual'
    out = {}
    for ccy in CCY_ORDER:
        if rs is None:
            out[ccy] = (None, 'regim indisponibil (rulează update_regime.py)')
            continue
        b = RISK_BETA.get(ccy, 0.0)
        sc = _clamp(_round_half_up(float(rs) * b))
        why = f'regim {float(rs):+.0f} × beta {b:+.1f}'
        why += f" ({(reg or {}).get('why')})" if src == 'calculat' and (reg or {}).get('why') \
            else ' [scor manual din directions.json]'
        out[ccy] = (sc, why)
    return out


def score_seasonality(sea: dict | None, month: int) -> dict:
    """Media lunii curente pe 10 ani, orientată per monedă. Plafonat ±1."""
    inst = (sea or {}).get('instruments', {})
    legs: dict[str, list] = {c: [] for c in CCY_ORDER}
    for pair in USD_PAIRS:
        node = (inst.get(pair) or {}).get(str(month))
        if not node or node.get('avg') is None:
            continue
        avg, hit = float(node['avg']), float(node.get('hit', 50))
        base, quote = pair[:3], pair[3:]
        legs[base].append((avg, hit))
        legs[quote].append((-avg, 100 - hit))

    out = {}
    for ccy in CCY_ORDER:
        rows = legs.get(ccy) or []
        if not rows:
            out[ccy] = (None, 'seasonality indisponibilă')
            continue
        s = sum(r[0] for r in rows) / len(rows)
        h = sum(r[1] for r in rows) / len(rows)
        if s > 0 and h >= SEA_HIT_HI:
            sc = 1
        elif s < 0 and h <= SEA_HIT_LO:
            sc = -1
        else:
            sc = 0
        out[ccy] = (sc, f'media lunii {s:+.2f}%, hit {h:.0f}% ({len(rows)} perechi)')
    return out


# ══════════════════════════════════════════════════════════════════════════
# agregare
# ══════════════════════════════════════════════════════════════════════════

def _total(scores: dict) -> tuple[float | None, list]:
    """Normalizare la ±10 DOAR pe criteriile disponibile — un feed mort nu trebuie
    să tragă scorul spre zero pe tăcute; se semnalează în `missing`."""
    num = 0.0
    wsum = 0.0
    missing = []
    for k in CRIT_ORDER:
        sc = scores.get(k)
        if sc is None:
            missing.append(CRIT_LABEL[k])
            continue
        num += sc * WEIGHTS[k]
        wsum += WEIGHTS[k]
    if wsum == 0:
        return None, missing
    return round(num / (2 * wsum) * 10, 1), missing


def build_scorecard(cot: dict | None, yld: dict | None, sea: dict | None,
                    directions: dict, month: int,
                    reg: dict | None = None) -> dict:
    """Compune scorecard-ul complet: scoruri per monedă, rank, perechi cu verdict."""
    judgment = (directions.get('scorecard') or {}).get('judgment', {}) or {}
    catalysts = directions.get('catalysts', {}) or {}

    mech = {'ind': score_indicators(directions), 'yld': score_yields(yld),
            'cot': score_cot(cot), 'reg': score_regime(directions, reg),
            'sea': score_seasonality(sea, month)}

    rows = {}
    for ccy in CCY_ORDER:
        j = judgment.get(ccy, {}) or {}
        scores, why = {}, {}
        for k in JUDGMENT:
            v = j.get(k)
            scores[k] = None if v is None else _clamp(int(v))
            why[k] = j.get(k + '_why', '')
        for k, table in mech.items():
            sc, w = table[ccy]
            scores[k] = sc
            why[k] = w
        total, missing = _total(scores)
        rows[ccy] = {'scores': scores, 'why': why, 'total': total,
                     'missing': missing, 'contra': j.get('contra', ''),
                     'catalyst': catalysts.get(ccy, '')}

    ranked = sorted((c for c in CCY_ORDER if rows[c]['total'] is not None),
                    key=lambda c: rows[c]['total'], reverse=True)
    for i, c in enumerate(ranked, 1):
        rows[c]['rank'] = i

    return {'weights': WEIGHTS, 'crit_order': list(CRIT_ORDER), 'crit_label': CRIT_LABEL,
            'judgment_crit': list(JUDGMENT), 'ccy_order': list(CCY_ORDER),
            'month': month,
            'regime_score': (reg or {}).get('score', directions.get('regime_score')),
            'regime_src': 'calculat' if (reg or {}).get('score') is not None else 'manual',
            'regime_why': (reg or {}).get('why', ''),
            'currencies': rows, 'ranked': ranked,
            'pairs': _build_pairs(rows),
            'thresholds': {'book': GAP_BOOK, 'watch': GAP_WATCH}}


def _build_pairs(rows: dict) -> list:
    """Perechile, ordonate după diferența de scor. Verdictul aplică regulile de desk:
    criteriile 1-2 trebuie să confirme direcția, altfel ideea coboară la WATCH."""
    out = []
    for pair in USD_PAIRS + CROSSES:
        base, quote = pair[:3], pair[3:]
        b, q = rows.get(base), rows.get(quote)
        if not b or not q or b['total'] is None or q['total'] is None:
            continue
        gap = round(b['total'] - q['total'], 1)
        direction = 'LONG' if gap > 0 else 'SHORT'

        # criteriile 1-2 obligatorii: contribuția lor trebuie să aibă același semn ca gap-ul
        def jsum(node):
            return sum(node['scores'][k] * WEIGHTS[k] for k in JUDGMENT
                       if node['scores'].get(k) is not None)
        jgap = jsum(b) - jsum(q)
        j_ok = (jgap > 0) == (gap > 0) and abs(jgap) > 0

        cat = ' · '.join(x for x in (b['catalyst'], q['catalyst']) if x)
        blind = sorted(set(b['missing']) | set(q['missing']))

        if abs(gap) >= GAP_BOOK and j_ok and cat:
            verdict, note = 'BOOK', 'diferență peste prag, criteriile 1-2 confirmă, catalizator în fereastră'
        elif abs(gap) >= GAP_BOOK and j_ok:
            verdict, note = 'WATCH', 'diferență peste prag, dar fără catalizator — rank fără eveniment sângerează timp'
        elif abs(gap) >= GAP_BOOK:
            verdict, note = 'WATCH', 'diferență peste prag, dar criteriile 1-2 nu confirmă direcția'
        elif abs(gap) >= GAP_WATCH:
            verdict, note = 'WATCH', 'diferență moderată — devine idee doar cu catalizator'
        else:
            verdict, note = 'SUB PRAG', 'diferență în zona de zgomot — fără trade'

        out.append({'pair': pair, 'gap': gap, 'dir': direction, 'verdict': verdict,
                    'note': note, 'catalyst': cat, 'blind': blind,
                    'cross': pair in CROSSES,
                    'legs': {'base': base, 'quote': quote,
                             'base_total': b['total'], 'quote_total': q['total']}})
    out.sort(key=lambda r: abs(r['gap']), reverse=True)
    return out


if __name__ == '__main__':
    import json
    import sys
    from datetime import date
    from pathlib import Path
    D = Path(__file__).resolve().parent.parent / 'data'

    def load(n):
        p = D / f'{n}.json'
        return json.loads(p.read_text()) if p.exists() else None

    month = int(sys.argv[1]) if len(sys.argv) > 1 else date.today().month
    sc = build_scorecard(load('cot_latest'), load('yields_latest'), load('seasonality'),
                         load('directions') or {}, month, reg=load('regime_latest'))

    print('CURRENCY SCORECARD — luna %d\n' % month)
    print('%-5s ' % '' + ' '.join('%4s' % CRIT_LABEL[k] for k in CRIT_ORDER) + '  TOTAL')
    for c in sc['ranked']:
        r = sc['currencies'][c]
        cells = []
        for k in CRIT_ORDER:
            v = r['scores'][k]
            cells.append('%4s' % ('—' if v is None else '%+d' % v))
        line = '%-5s %s  %+5.1f' % (c, ' '.join(cells), r['total'])
        if r['missing']:
            line += '   [orb: %s]' % ', '.join(r['missing'])
        print(line)

    print('\nPERECHI')
    for p in sc['pairs']:
        if p['verdict'] != 'SUB PRAG':
            print('%-8s %+6.1f  %-8s %-5s — %s' % (p['pair'], p['gap'], p['verdict'],
                                                   p['dir'], p['note']))
    sub = [p for p in sc['pairs'] if p['verdict'] == 'SUB PRAG']
    if sub:
        print('sub prag: ' + ' · '.join('%s %.1f' % (p['pair'], abs(p['gap'])) for p in sub))
