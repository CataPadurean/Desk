#!/usr/bin/env python3
"""CRITERIUL 3 — index de surpriză macro (actual vs. consens), nu etichetă.

Până la 03.08.2026 criteriul 3 era o etichetă scrisă de mână („pozitiv"/„mixt") și
mapată direct în scor. Asta însemna că un criteriu cu pondere 2,0 din 12,5 se sprijinea
pe impresie. Aici se calculează din date: pentru fiecare indicator publicat în ultimele
~30 de zile se ia surpriza (actual − consens), se normalizează la scara istorică a
indicatorului respectiv, se ponderează cu impactul și cu recența, iar media ponderată
per monedă se traduce în −2…+2 pe praguri ÎNGHEȚATE.

Surse, în ordine:
  1. Calendarul public în JSON (faireconomy/ForexFactory), săptămâna curentă + cea
     anterioară. **Testat 03.08.2026: întoarce 403 și de pe Mac** — rămâne în lanț
     dacă revine, dar azi NU e sursa de lucru.
  2. Sursa reală, azi: `indicators_events` în directions.json, completat la
     „generează teza" din calendarul Trading Economics (tradingeconomics.com/calendar
     se citește normal și dă Actual + Consensus + Previous per publicare; se ia
     coloana **Consensus**, nu «Forecast», care e prognoza casei TE, nu a pieței).
     Se combină cu feed-ul, nu îl înlocuiește — dublurile se elimină pe cheia
     monedă|indicator|dată.
Dacă nu rămâne nimic pentru o monedă, criteriul e ORB (None) — nu zero. Zero ar
însemna „date neutre", ceea ce e o afirmație, nu o lipsă de date.

Normalizarea: scara unui indicator = deviația standard a surprizelor lui istorice,
odată ce s-au strâns ≥6 observații în `indicators_history.json` (se acumulează
săptămână de săptămână, de la prima rulare). Până atunci se folosesc scări implicite
per familie de indicatori — provizorii prin construcție, marcate ca atare în output.

Rulare: python3 update_indicators.py [--window 30] [--dry]
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
OUT = DATA / 'indicators_latest.json'
HIST = DATA / 'indicators_history.json'

CCY_ORDER = ('USD', 'EUR', 'GBP', 'CAD', 'JPY', 'CHF', 'AUD', 'NZD')

FEEDS = ('https://nfs.faireconomy.media/ff_calendar_lastweek.json',
         'https://nfs.faireconomy.media/ff_calendar_thisweek.json')

# ——— parametri ÎNGHEȚAȚI (se schimbă doar la review lunar, pe date) ———
WINDOW_DAYS = 30        # cât în urmă contează o publicare
HALF_LIFE = 10.0        # zile — ponderea unei surprize se înjumătățește la 10 zile
IMPACT_W = {'high': 1.0, 'medium': 0.5, 'low': 0.2, 'holiday': 0.0}
Z_CLIP = 3.0            # o surpriză nu poate cântări mai mult de 3 deviații
MIN_OBS = 6             # observații necesare ca să folosesc σ istoric în loc de scara implicită
MIN_WEIGHT = 0.6        # sub atâta pondere cumulată, moneda rămâne oarbă (nu zero)
IND_BANDS = ((0.75, 2), (0.25, 1), (-0.25, 0), (-0.75, -1))   # sub tot → −2
HIST_KEEP = 40

# indicatori la care o valoare MAI MARE e negativă pentru monedă
INVERTED = ('unemployment', 'jobless', 'claimant', 'claims', 'layoff',
            'bankrupt', 'delinquen', 'foreclosure', 'misery')

# scări implicite per familie, în unitățile native ale publicării (provizorii,
# până se strânge σ istoric per indicator)
FAMILY_SCALE = (
    ('unemployment rate', 0.15),
    ('unemployment change', 15.0),
    ('claimant', 15.0),
    ('claims', 15.0),
    ('non-farm', 45.0), ('nonfarm', 45.0), ('payroll', 45.0),
    ('employment change', 20.0),
    ('cpi', 0.20), ('ppi', 0.25), ('inflation', 0.20), ('price index', 0.30),
    ('gdp', 0.30),
    ('pmi', 1.20), ('ism', 1.50),
    ('zew', 4.00), ('ifo', 1.50),
    ('confidence', 2.50), ('sentiment', 2.50),
    ('retail sales', 0.40),
    ('trade balance', 1.50),
    ('wage', 0.30), ('earnings', 0.30),
    ('rate decision', 0.10), ('cash rate', 0.10), ('bank rate', 0.10),
)


# ══════════════════════════════════════════════════════════════════════════
# utilitare
# ══════════════════════════════════════════════════════════════════════════

def fetch(url, tries=2):
    """Același tipar ca update_yields.py: curl întâi, urllib ca plasă de siguranță."""
    import subprocess
    import urllib.request
    last = None
    for _ in range(tries):
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
    raise last


def num(x):
    """«3.2%» → 3.2 · «250K» → 250 · «1.2M» → 1200 · «-0.1» → −0.1 · «» → None.
    Sufixele K/M/B se aduc la aceeași unitate (mii), ca surpriza să fie comparabilă
    cu istoricul aceluiași indicator."""
    if x is None:
        return None
    s = str(x).strip().replace(',', '').replace('%', '').replace('<', '').replace('>', '')
    if not s or s in ('-', '—', 'n/a'):
        return None
    mult = 1.0
    if s and s[-1] in 'KkMmBbTt':
        mult = {'k': 1.0, 'm': 1e3, 'b': 1e6, 't': 1e9}[s[-1].lower()]
        s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def norm_title(t):
    """Titlul, curățat de sufixele care se schimbă de la o lună la alta, ca să pot
    lega observațiile aceluiași indicator în istoric."""
    t = re.sub(r'\([^)]*\)', '', str(t or '')).strip().lower()
    t = re.sub(r'\s+', ' ', t)
    return t


def scale_for(title, forecast, hist_sigma):
    """σ istoric dacă există, altfel scara familiei, altfel 15% din consens."""
    if hist_sigma:
        return hist_sigma, 'σ istoric'
    t = norm_title(title)
    for key, sc in FAMILY_SCALE:
        if key in t:
            return sc, 'scară implicită'
    return max(0.15 * abs(forecast or 0), 0.10), 'scară relativă'


def inverted(title):
    t = norm_title(title)
    return any(k in t for k in INVERTED)


def band(x, bands, below):
    for edge, sc in bands:
        if x >= edge:
            return sc
    return below


# ══════════════════════════════════════════════════════════════════════════
# colectarea evenimentelor
# ══════════════════════════════════════════════════════════════════════════

def from_feed():
    """Evenimente cu actual ȘI consens din calendarul public."""
    out, errs = [], []
    for url in FEEDS:
        try:
            rows = json.loads(fetch(url))
        except Exception as e:
            errs.append(f'{url.rsplit("/", 1)[-1]}: {type(e).__name__}: {e}')
            continue
        for r in rows if isinstance(rows, list) else []:
            ccy = str(r.get('country') or r.get('currency') or '').upper()
            if ccy not in CCY_ORDER:
                continue
            a, f = num(r.get('actual')), num(r.get('forecast'))
            if a is None or f is None:
                continue                      # fără consens nu există surpriză
            d = str(r.get('date') or '')[:10]
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', d):
                continue
            out.append({'ccy': ccy, 'date': d, 'name': str(r.get('title') or '').strip(),
                        'actual': a, 'consensus': f,
                        'impact': str(r.get('impact') or 'medium').strip().lower(),
                        'src': 'feed'})
    return out, errs


def from_manual(directions):
    """Fallback scris de mână în directions.json → indicators_events."""
    out = []
    for r in directions.get('indicators_events') or []:
        ccy = str(r.get('ccy') or '').upper()
        a, f = num(r.get('actual')), num(r.get('consensus', r.get('forecast')))
        d = str(r.get('date') or '')[:10]
        if ccy in CCY_ORDER and a is not None and f is not None and re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            out.append({'ccy': ccy, 'date': d, 'name': str(r.get('name') or '').strip(),
                        'actual': a, 'consensus': f,
                        'impact': str(r.get('impact') or 'high').strip().lower(),
                        'src': 'manual'})
    return out


def dedup(events):
    """Cheia monedă|indicator|dată — feed-ul și lista manuală se pot suprapune."""
    seen, out = set(), []
    for e in sorted(events, key=lambda x: (x['date'], x['ccy'])):
        k = (e['ccy'], norm_title(e['name']), e['date'])
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out


# ══════════════════════════════════════════════════════════════════════════
# istoricul surprizelor (σ per indicator, acumulat în timp)
# ══════════════════════════════════════════════════════════════════════════

def load_history():
    if HIST.exists():
        try:
            return json.loads(HIST.read_text())
        except Exception:
            pass
    return {'events': {}}


def hist_key(e):
    return f"{e['ccy']}|{norm_title(e['name'])}"


def update_history(hist, events):
    for e in events:
        k = hist_key(e)
        rows = {r[0]: r for r in hist['events'].get(k, [])}
        rows[e['date']] = [e['date'], e['actual'], e['consensus'],
                           round(e['actual'] - e['consensus'], 4)]
        hist['events'][k] = sorted(rows.values())[-HIST_KEEP:]
    hist['updated'] = date.today().isoformat()
    return hist


def sigma(hist, e):
    """σ al surprizelor istorice — DOAR cele dinaintea observației curente, ca să nu
    normalizez o surpriză cu ea însăși."""
    rows = [r for r in hist['events'].get(hist_key(e), []) if r[0] < e['date']]
    if len(rows) < MIN_OBS:
        return None
    xs = [float(r[3]) for r in rows]
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return (var ** 0.5) or None


# ══════════════════════════════════════════════════════════════════════════
# scorul
# ══════════════════════════════════════════════════════════════════════════

def build(events, hist, today=None, window=WINDOW_DAYS):
    today = today or date.today()
    lim = (today - timedelta(days=window)).isoformat()
    per = {c: [] for c in CCY_ORDER}

    for e in events:
        if e['date'] < lim or e['date'] > today.isoformat():
            continue
        w_impact = IMPACT_W.get(e['impact'], 0.5)
        if w_impact <= 0:
            continue
        sc, how = scale_for(e['name'], e['consensus'], sigma(hist, e))
        if not sc:
            continue
        raw = (e['actual'] - e['consensus']) / sc
        if inverted(e['name']):
            raw = -raw
        z = max(-Z_CLIP, min(Z_CLIP, raw))
        days = (today - datetime.strptime(e['date'], '%Y-%m-%d').date()).days
        w = w_impact * (0.5 ** (days / HALF_LIFE))
        per[e['ccy']].append({'name': e['name'], 'date': e['date'], 'impact': e['impact'],
                              'actual': e['actual'], 'consensus': e['consensus'],
                              'z': round(z, 2), 'w': round(w, 3), 'scale': round(sc, 4),
                              'scale_src': how, 'src': e['src']})

    out = {}
    for ccy in CCY_ORDER:
        rows = sorted(per[ccy], key=lambda r: abs(r['z'] * r['w']), reverse=True)
        wsum = sum(r['w'] for r in rows)
        if not rows or wsum < MIN_WEIGHT:
            out[ccy] = {'score': None, 'z': None, 'n': len(rows), 'weight': round(wsum, 2),
                        'why': 'prea puține publicări cu consens în fereastră',
                        'top': rows[:3], 'events': rows}
            continue
        z = sum(r['z'] * r['w'] for r in rows) / wsum
        score = band(z, IND_BANDS, -2)
        top = rows[:3]
        prov = sum(1 for r in rows if r['scale_src'] != 'σ istoric')
        why = (f"surpriză ponderată {z:+.2f}σ din {len(rows)} publicări · "
               + ' · '.join(f"{r['name']} {r['z']:+.1f}σ" for r in top))
        if prov:
            why += f' · {prov}/{len(rows)} pe scări provizorii'
        out[ccy] = {'score': score, 'z': round(z, 2), 'n': len(rows),
                    'weight': round(wsum, 2), 'why': why, 'top': top, 'events': rows}
    return out


def main():
    window = WINDOW_DAYS
    if '--window' in sys.argv:
        window = int(sys.argv[sys.argv.index('--window') + 1])
    dry = '--dry' in sys.argv

    directions = {}
    p = DATA / 'directions.json'
    if p.exists():
        try:
            directions = json.loads(p.read_text())
        except Exception as e:
            print(f'[IND] directions.json necitibil: {e}', file=sys.stderr)

    feed, errs = from_feed()
    manual = from_manual(directions)
    for e in errs:
        print(f'[IND] feed: {e}', file=sys.stderr)
    events = dedup(feed + manual)

    hist = load_history()
    hist = update_history(hist, events)
    cur = build(events, hist, window=window)

    src = []
    if feed:
        src.append(f'calendar public ({len(feed)} publicări cu consens)')
    if manual:
        src.append(f'listă manuală ({len(manual)})')
    out = {'updated': date.today().isoformat(), 'window_days': window,
           'half_life_days': HALF_LIFE, 'bands': IND_BANDS,
           'source': ' + '.join(src) or 'fără date',
           'feed_errors': errs, 'currencies': cur}

    if dry:
        print(json.dumps(out['currencies'], ensure_ascii=False, indent=1))
        return
    DATA.mkdir(exist_ok=True)
    if not events and OUT.exists():
        # o rulare picată nu are voie să șteargă datele bune de săptămâna trecută:
        # păstrez fișierul vechi, marcat stale, și las fallback-ul manual să decidă
        old = json.loads(OUT.read_text())
        old['status'] = f"stale — ultima colectare {old.get('updated', '?')} (feed indisponibil)"
        OUT.write_text(json.dumps(old, ensure_ascii=False, indent=1))
        print(f"[IND] feed mort — păstrez colectarea din {old.get('updated', '?')}", file=sys.stderr)
        sys.exit(1)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    HIST.write_text(json.dumps(hist, ensure_ascii=False, indent=1))
    line = ' '.join(f"{c}:{'—' if cur[c]['score'] is None else '%+d' % cur[c]['score']}"
                    for c in CCY_ORDER)
    print(f"[IND] {out['source']} → {line}")
    if not events:
        print('[IND] nicio publicare cu consens — criteriul 3 rămâne ORB '
              '(completează indicators_events în directions.json)', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
