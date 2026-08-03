#!/usr/bin/env python3
"""CRITERIUL 6 — regimul de risc, calculat din date proprii.

Până la 03.08.2026 `regime_score` era un număr scris de mână în directions.json și
înmulțit cu beta fiecărei monede în scorecard. Un criteriu care intră în scorul final
nu are voie să fie o impresie: aici se calculează din trei componente publice, cu
praguri ÎNGHEȚATE (se schimbă doar la review lunar, pe date, ca playbook-ul).

Componente (toate din FRED, gratuit, fără cheie):
  · VIXCLS         — volatilitatea implicită S&P; percentila pe 1 an (nu nivelul absolut,
                     care înseamnă altceva în 2020 față de 2026)
  · BAMLH0A0HYM2   — ICE BofA US High Yield OAS; creditul se rupe înaintea acțiunilor,
                     de aceea cântărește la fel de mult ca VIX
  · SP500          — momentum 20 de zile și 5 zile; direcția, nu nivelul

Scor final −2…+2 (risk-on pozitiv), din media ponderată a celor trei. Comentariul
narativ din caseta MARKET REGIME rămâne scris de Claude — dar peste acest număr,
nu în locul lui.

Rulare: python3 update_regime.py [--dry]
"""
from __future__ import annotations

import csv
import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
OUT = DATA / 'regime_latest.json'

FRED = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id={ids}&cosd={start}'
SERIES = ('VIXCLS', 'BAMLH0A0HYM2', 'SP500')

# ——— praguri ÎNGHEȚATE ———
WEIGHTS = {'vix': 0.35, 'credit': 0.35, 'momentum': 0.30}
# percentila 1 an → scor (mai mic = mai calm = risk-on)
PCTL_BANDS = ((20, 2), (40, 1), (65, 0), (85, -1))          # peste 85 → −2
RET20_BANDS = ((3.0, 2), (1.0, 1), (-1.0, 0), (-3.0, -1))   # % pe 20 de ședințe
RET5_BANDS = ((1.5, 2), (0.5, 1), (-0.5, 0), (-1.5, -1))    # % pe 5 ședințe
LABELS = {2: 'RISK-ON', 1: 'RISK-ON (fragil)', 0: 'NEUTRU',
          -1: 'RISK-OFF (incipient)', -2: 'RISK-OFF'}


def fetch(url, tries=3):
    """Curl cu UA-ul lui implicit — FRED respinge UA-uri de browser fără fingerprint
    TLS de browser (vezi nota din update_yields.py)."""
    import subprocess
    import time
    import urllib.request
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(['curl', '-sSL', '--fail', '--max-time', '45', url],
                               capture_output=True, timeout=60)
            if r.returncode == 0 and r.stdout:
                return r.stdout.decode('utf-8', errors='replace')
            last = RuntimeError(f'curl rc={r.returncode}')
        except Exception as e:
            last = e
        try:
            return urllib.request.urlopen(url, timeout=45).read().decode('utf-8', 'replace')
        except Exception as e:
            last = e
        if i < tries - 1:
            time.sleep(3 * (i + 1))
    raise last


def band(x, bands, below):
    for edge, sc in bands:
        if x >= edge:
            return sc
    return below


def band_desc(x, bands, below):
    """Aceleași praguri, dar în ordine crescătoare (percentile: mic = bine)."""
    for edge, sc in bands:
        if x <= edge:
            return sc
    return below


def pull():
    """→ {serie: [(dată, valoare)]} pe ~400 de zile calendaristice."""
    start = (date.today() - timedelta(days=400)).isoformat()
    txt = fetch(FRED.format(ids=','.join(SERIES), start=start))
    rows = list(csv.reader(io.StringIO(txt)))
    head = rows[0]
    idx = {s: head.index(s) for s in SERIES if s in head}
    if len(idx) < len(SERIES):
        raise RuntimeError(f'FRED: lipsesc coloane ({sorted(set(SERIES) - set(idx))})')
    out = {s: [] for s in SERIES}
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        for s, i in idx.items():
            if i < len(r):
                try:
                    out[s].append((r[0][:10], float(r[i])))
                except ValueError:
                    pass                      # FRED scrie «.» pentru zilele fără cotație
    for s in SERIES:
        if len(out[s]) < 30:
            raise RuntimeError(f'FRED {s}: doar {len(out[s])} observații')
    return out


def pctile(series, n=252):
    """Percentila ultimei valori în ultimele n observații."""
    vals = [v for _, v in series[-n:]]
    last = vals[-1]
    return round(100.0 * sum(1 for v in vals if v <= last) / len(vals)), last


def ret(series, k):
    """Randament % pe k ședințe."""
    if len(series) <= k:
        return None
    a, b = series[-(k + 1)][1], series[-1][1]
    return round(100.0 * (b - a) / a, 2) if a else None


def build(raw):
    vix, oas, spx = raw['VIXCLS'], raw['BAMLH0A0HYM2'], raw['SP500']

    p_vix, v_vix = pctile(vix)
    s_vix = band_desc(p_vix, PCTL_BANDS, -2)

    p_oas, v_oas = pctile(oas)
    s_oas = band_desc(p_oas, PCTL_BANDS, -2)

    r20, r5 = ret(spx, 20), ret(spx, 5)
    parts = [band(r20, RET20_BANDS, -2)] if r20 is not None else []
    if r5 is not None:
        parts.append(band(r5, RET5_BANDS, -2))
    s_mom = round(sum(parts) / len(parts)) if parts else 0

    total = (s_vix * WEIGHTS['vix'] + s_oas * WEIGHTS['credit'] + s_mom * WEIGHTS['momentum'])
    score = max(-2, min(2, int(total + 0.5) if total >= 0 else -int(-total + 0.5)))

    comps = [
        {'key': 'vix', 'label': 'VIX', 'value': round(v_vix, 2), 'pctile': p_vix,
         'score': s_vix, 'weight': WEIGHTS['vix'], 'asof': vix[-1][0],
         'why': f'VIX {v_vix:.2f}, percentila {p_vix} pe 1 an'},
        {'key': 'credit', 'label': 'HY OAS', 'value': round(v_oas, 2), 'pctile': p_oas,
         'score': s_oas, 'weight': WEIGHTS['credit'], 'asof': oas[-1][0],
         'why': f'spread high yield {v_oas:.2f}%, percentila {p_oas} pe 1 an'},
        {'key': 'momentum', 'label': 'S&P momentum', 'value': r20, 'pctile': None,
         'score': s_mom, 'weight': WEIGHTS['momentum'], 'asof': spx[-1][0],
         'why': f'S&P {r20:+.2f}% pe 20 de ședințe, {r5:+.2f}% pe 5'},
    ]
    why = ' · '.join(c['why'] for c in comps)
    return {'updated': date.today().isoformat(), 'asof': max(c['asof'] for c in comps),
            'score': score, 'raw': round(total, 2), 'label': LABELS[score],
            'vix': round(v_vix, 2), 'components': comps, 'why': why,
            'weights': WEIGHTS, 'status': 'ok'}


def main():
    dry = '--dry' in sys.argv
    try:
        out = build(pull())
    except Exception as e:
        print(f'[REG] FRED indisponibil: {type(e).__name__}: {e}', file=sys.stderr)
        if OUT.exists():                      # last-known-good, marcat ca atare
            old = json.loads(OUT.read_text())
            old['status'] = f"stale — ultima valoare bună {old.get('asof', '?')} ({type(e).__name__})"
            if not dry:
                OUT.write_text(json.dumps(old, ensure_ascii=False, indent=1))
            print(f"[REG] păstrez last-known-good: {old['score']:+d} ({old.get('asof')})")
            return
        print('[REG] fără cache — criteriul 6 rămâne pe valoarea din directions.json',
              file=sys.stderr)
        sys.exit(1)

    if dry:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    DATA.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"[REG] regime_score {out['score']:+d} ({out['label']}) — {out['why']}")


if __name__ == '__main__':
    main()
