#!/usr/bin/env python3
"""COT (CFTC): FX + DXY = Leveraged Funds din TFF (Traders in Financial Futures);
GOLD = Managed Money din raportul Disaggregated (echivalentul pe mărfuri).
Metrici: net, Δ săptămânal, % din OI, percentilă 52w, flag extremă (≥90/≤10), istoric 13w.
Rulare: python3 update_cot.py  →  scrie ../data/cot_latest.json
Surse (gratuite, fără cheie):
  https://www.cftc.gov/files/dea/history/fut_fin_txt_{AN}.zip     (TFF futures-only)
  https://www.cftc.gov/files/dea/history/fut_disagg_txt_{AN}.zip  (Disaggregated futures-only)"""
import csv, io, json, sys, urllib.request, zipfile
from datetime import date
from pathlib import Path

# piețe TFF (financiale) — pattern-uri de potrivire în Market_and_Exchange_Names
TFF_MARKETS = {
    'EUR': ('EURO FX',),
    'GBP': ('BRITISH POUND',),
    'CAD': ('CANADIAN DOLLAR',),
    'JPY': ('JAPANESE YEN',),
    'CHF': ('SWISS FRANC',),
    'AUD': ('AUSTRALIAN DOLLAR',),
    'NZD': ('NZ DOLLAR', 'NEW ZEALAND DOLLAR'),
    'DXY': ('USD INDEX', 'U.S. DOLLAR INDEX', 'DOLLAR INDEX'),
}
# piețe Disaggregated (mărfuri)
DISAGG_MARKETS = {
    'GOLD': ('GOLD - COMMODITY EXCHANGE',),
}
EXCLUDE = ['MICRO', 'E-MINI', ' MINI', 'XRATE', '/']
ORDER = ['EUR', 'GBP', 'CAD', 'JPY', 'CHF', 'AUD', 'NZD', 'DXY', 'GOLD']
UA = {'User-Agent': 'Mozilla/5.0 (desk-system; personal research)'}

def fetch_zip_txt(url):
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=90).read()
    zf = zipfile.ZipFile(io.BytesIO(raw))
    name = [n for n in zf.namelist() if n.lower().endswith('.txt')][0]
    return zf.read(name).decode('utf-8', errors='replace')

def col_index(header, *needles):
    """Găsește indexul coloanei al cărei nume conține toate needles (case-insensitive)."""
    for i, h in enumerate(header):
        hl = h.strip().lower()
        if all(n.lower() in hl for n in needles):
            return i
    raise RuntimeError(f'Coloană negăsită: {needles}')

def parse(text, markets, long_col, short_col, rows, category):
    rdr = csv.reader(io.StringIO(text))
    header = next(rdr)
    idx = {
        'name':  col_index(header, 'market_and_exchange_names'),
        'date':  col_index(header, 'report_date_as_yyyy-mm-dd'),
        'oi':    col_index(header, 'open_interest_all'),
        'long':  col_index(header, *long_col),
        'short': col_index(header, *short_col),
    }
    for r in rdr:
        if len(r) <= max(idx.values()): continue
        name = r[idx['name']].strip().upper()
        if any(x in name for x in EXCLUDE): continue
        for key, pats in markets.items():
            if any(p in name for p in pats):
                try:
                    rows.setdefault(key, {'category': category, 'series': {}})['series'][r[idx['date']].strip()] = {
                        'net': int(float(r[idx['long']])) - int(float(r[idx['short']])),
                        'oi': int(float(r[idx['oi']])) or None}
                except ValueError:
                    pass

def main():
    rows = {}
    year = date.today().year
    jobs = [
        # (url_template, markets, long-col needles, short-col needles, etichetă)
        ('https://www.cftc.gov/files/dea/history/fut_fin_txt_{y}.zip',
         TFF_MARKETS, ('lev_money', 'long'), ('lev_money', 'short'), 'Leveraged Funds (TFF)'),
        ('https://www.cftc.gov/files/dea/history/fut_disagg_txt_{y}.zip',
         DISAGG_MARKETS, ('m_money', 'long'), ('m_money', 'short'), 'Managed Money (Disagg)'),
    ]
    for tmpl, mkts, lc, sc, cat in jobs:
        for y in (year - 1, year):
            try:
                parse(fetch_zip_txt(tmpl.format(y=y)), mkts, lc, sc, rows, cat)
            except Exception as e:
                print(f'[COT] avertisment {cat} {y}: {e}', file=sys.stderr)
    if not rows:
        sys.exit('[COT] EROARE: nicio dată descărcată.')

    out = {'updated': date.today().isoformat(),
           'source': 'CFTC TFF (Leveraged Funds) + Disaggregated (Managed Money, GOLD)',
           'markets': {}}
    for key in ORDER:
        if key not in rows: continue
        pts = sorted(rows[key]['series'].items())[-60:]
        if len(pts) < 2: continue
        nets = [v['net'] for _, v in pts]
        last_d, last = pts[-1]; prev = pts[-2][1]
        win = nets[-52:]
        pctl = round(100 * sum(1 for x in win if x <= last['net']) / len(win))
        out['markets'][key] = {
            'category': rows[key]['category'],
            'as_of': last_d,
            'net': last['net'],
            'delta_1w': last['net'] - prev['net'],
            'pct_oi': round(100 * last['net'] / last['oi'], 1) if last['oi'] else None,
            'percentile_52w': pctl,
            'extreme': 'LONG' if pctl >= 90 else ('SHORT' if pctl <= 10 else None),
            'history_13w': nets[-13:],
        }
    dst = Path(__file__).resolve().parents[1] / 'data'
    dst.mkdir(exist_ok=True)
    (dst / 'cot_latest.json').write_text(json.dumps(out, indent=1))
    print(f"[COT] OK — {len(out['markets'])} piețe, as of {max(m['as_of'] for m in out['markets'].values())}")

if __name__ == '__main__':
    main()
