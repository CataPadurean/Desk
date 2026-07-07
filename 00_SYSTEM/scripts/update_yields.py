#!/usr/bin/env python3
"""Randamente 2Y (criteriu principal) + 10Y (secundar) pe 8 monede
(US, EUR, GBP, CAD, JPY, CHF, AUD, NZD) + spread-uri vs USD pe cele 7 perechi.
Rulare: python3 update_yields.py  →  scrie ../data/yields_latest.json
Surse gratuite, fără cheie: FRED (US), ECB Data Portal (EUR), BoC Valet (CAD),
Stooq (GBP, JPY, CHF, AUD, NZD — simboluri candidate încercate pe rând)."""
import csv, io, json, sys, urllib.request
from datetime import date
from pathlib import Path

UA = {'User-Agent': 'Mozilla/5.0 (desk-system; personal research)'}

def get(url, tries=3):
    import time
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read().decode('utf-8', errors='replace')
        except Exception:
            if i == tries - 1: raise
            time.sleep(4)

def tail(series, n=20):
    """serie = list[(date, float)] sortată; păstrează ultimele n."""
    return sorted(series)[-n:]

def fred():
    txt = get('https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2,DGS10', tries=1)
    r = csv.reader(io.StringIO(txt)); head = next(r)
    i2, i10 = head.index('DGS2'), head.index('DGS10')
    s2, s10 = [], []
    for row in r:
        if row[i2] not in ('.', ''): s2.append((row[0], float(row[i2])))
        if row[i10] not in ('.', ''): s10.append((row[0], float(row[i10])))
    return {'2Y': tail(s2), '10Y': tail(s10)}

def treasury():
    """Fallback oficial pentru US: home.treasury.gov, XML zilnic."""
    import re
    y = date.today().year
    xml = get('https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml'
              f'?data=daily_treasury_yield_curve&field_tdr_date_value={y}')
    s2, s10 = [], []
    for entry in xml.split('<entry>')[1:]:
        d = re.search(r'<d:NEW_DATE[^>]*>([\d-]+)', entry)
        v2 = re.search(r'<d:BC_2YEAR[^>]*>([\d.]+)', entry)
        v10 = re.search(r'<d:BC_10YEAR[^>]*>([\d.]+)', entry)
        if d and v2: s2.append((d.group(1)[:10], float(v2.group(1))))
        if d and v10: s10.append((d.group(1)[:10], float(v10.group(1))))
    if not s2: raise RuntimeError('Treasury XML: fără date')
    return {'2Y': tail(s2), '10Y': tail(s10)}

def us():
    try:
        return fred()
    except Exception:
        return treasury()

def ecb():
    out = {}
    for lbl, code in (('2Y', 'SR_2Y'), ('10Y', 'SR_10Y')):
        series = []
        for curve in ('G_N_A', 'G_N_C'):  # AAA, apoi toți emitenții
            url = (f'https://data-api.ecb.europa.eu/service/data/YC/'
                   f'B.U2.EUR.4F.{curve}.SV_C_YM.{code}?format=csvdata&lastNObservations=20')
            try:
                r = csv.DictReader(io.StringIO(get(url)))
                series = [(row['TIME_PERIOD'], float(row['OBS_VALUE'])) for row in r if row.get('OBS_VALUE')]
            except Exception:
                series = []
            if series: break
        if not series: raise RuntimeError(f'ECB {code}: fără date')
        out[lbl] = tail(series)
    return out

def boc():
    url = 'https://www.bankofcanada.ca/valet/observations/BD.CDN.2YR.DQ.YLD,BD.CDN.10YR.DQ.YLD/json?recent=20'
    j = json.loads(get(url))
    s2, s10 = [], []
    for o in j['observations']:
        if o.get('BD.CDN.2YR.DQ.YLD', {}).get('v'): s2.append((o['d'], float(o['BD.CDN.2YR.DQ.YLD']['v'])))
        if o.get('BD.CDN.10YR.DQ.YLD', {}).get('v'): s10.append((o['d'], float(o['BD.CDN.10YR.DQ.YLD']['v'])))
    return {'2Y': tail(s2), '10Y': tail(s10)}

def stooq_series(sym):
    txt = get(f'https://stooq.com/q/d/l/?s={sym}&i=d')
    rows = list(csv.DictReader(io.StringIO(txt)))
    return [(r['Date'], float(r['Close'])) for r in rows if r.get('Close') not in (None, '', 'N/D')]

def stooq(candidates_2y, candidates_10y):
    """Încearcă simboluri candidate pe rând (Stooq își mai schimbă codurile)."""
    def first_ok(cands):
        for sym in cands:
            try:
                s = stooq_series(sym)
                if s: return s
            except Exception:
                continue
        raise RuntimeError(f'Stooq: niciun simbol valid din {cands}')
    return {'2Y': tail(first_ok(candidates_2y)), '10Y': tail(first_ok(candidates_10y))}

def snap(series):
    """latest + valoarea de acum ~5 ședințe → Δ."""
    if not series: return None
    d, v = series[-1]
    ref = series[-6][1] if len(series) >= 6 else series[0][1]
    return {'date': d, 'value': round(v, 3), 'delta_1w': round(v - ref, 3)}

def main():
    src = {
        'US':  us,
        'EUR': ecb,
        'CAD': boc,
        'GBP': lambda: stooq(['2yuky.b', '2ygby.b', '2ygb.b'], ['10yuky.b', '10ygby.b', '10ygb.b']),
        'JPY': lambda: stooq(['2yjpy.b', '2yjp.b'],   ['10yjpy.b', '10yjp.b']),
        'CHF': lambda: stooq(['2ychy.b', '2ych.b'],   ['10ychy.b', '10ych.b']),
        'AUD': lambda: stooq(['2yauy.b', '2yau.b'],   ['10yauy.b', '10yau.b']),
        'NZD': lambda: stooq(['2ynzy.b', '2ynz.b'],   ['10ynzy.b', '10ynz.b']),
    }
    data, status = {}, {}
    for k, fn in src.items():
        try:
            data[k] = fn(); status[k] = 'ok'
        except Exception as e:
            data[k] = None; status[k] = f'INDISPONIBIL: {e}'
            print(f'[YLD] {k} a picat: {e}', file=sys.stderr)

    out = {'updated': date.today().isoformat(), 'status': status, 'levels': {}, 'spreads': {}}
    for k, d in data.items():
        if d: out['levels'][k] = {t: snap(s) for t, s in d.items()}

    def spread(pair, a, b):
        """spread = prima valută din pereche − a doua (în creștere = suport pt. prima)."""
        for t in ('2Y', '10Y'):
            va, vb = out['levels'].get(a, {}).get(t), out['levels'].get(b, {}).get(t)
            if va and vb:
                out['spreads'].setdefault(pair, {})[t] = {
                    'value': round(va['value'] - vb['value'], 3),
                    'delta_1w': round(va['delta_1w'] - vb['delta_1w'], 3)}
    spread('EURUSD', 'EUR', 'US')
    spread('GBPUSD', 'GBP', 'US')
    spread('AUDUSD', 'AUD', 'US')
    spread('NZDUSD', 'NZD', 'US')
    spread('USDJPY', 'US', 'JPY')
    spread('USDCHF', 'US', 'CHF')
    spread('USDCAD', 'US', 'CAD')

    dst = Path(__file__).resolve().parents[1] / 'data'
    dst.mkdir(exist_ok=True)
    (dst / 'yields_latest.json').write_text(json.dumps(out, indent=1))
    ok = [k for k, s in status.items() if s == 'ok']
    print(f"[YLD] OK: {', '.join(ok) or 'NICIUNA'}" + (f" | PICATE: {[k for k in status if k not in ok]}" if len(ok) < 8 else ''))
    if not ok:
        sys.exit(1)

if __name__ == '__main__':
    main()
