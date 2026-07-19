#!/usr/bin/env python3
"""Runner: rulează update_cot.py + update_yields.py + update_seasonality.py,
compune ../data/macro_snapshot.md și regenerează 07_Dashboard/analysis_data.js.
Rulare (duminica, înainte de teză): python3 update_data.py"""
import json, subprocess, sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data'

COT_ORDER = ('DXY', 'EUR', 'GBP', 'CAD', 'JPY', 'CHF', 'AUD', 'NZD', 'GOLD')
YLD_ORDER = ('US', 'EUR', 'GBP', 'CAD', 'JPY', 'CHF', 'AUD', 'NZD')
PAIR_ORDER = ('EURUSD', 'GBPUSD', 'USDCAD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD')

def run(script):
    r = subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.stderr.strip(): print(r.stderr.strip(), file=sys.stderr)
    return r.returncode == 0

def build_analysis_js():
    """Compune 07_Dashboard/analysis_data.js din toate JSON-urile de date.
    directions.json (scris de Claude la „procesează inbox"/„generează teza") aduce stratul
    narativ: regim, sentiment, comentarii COT/yields, secțiunile per monedă, trade-urile split."""
    parts = {}
    for name in ('cot_latest', 'yields_latest', 'seasonality', 'directions'):
        p = DATA / f'{name}.json'
        parts[name] = json.loads(p.read_text()) if p.exists() else None
    d = parts['directions'] or {}

    # compatibilitate cu schema veche: 'directions' listă unică → split pe strategie
    tfx, tin = d.get('trades_fx'), d.get('trades_intraday')
    if tfx is None and tin is None and d.get('directions'):
        tfx = [t for t in d['directions'] if t.get('strat') == 'A']
        tin = [t for t in d['directions'] if t.get('strat') == 'B']

    obj = {'generated': date.today().isoformat(),
           'regime': d.get('regime', ''), 'regime_date': d.get('date', ''),
           'sentiment': d.get('sentiment'),          # {label, comment}
           'comments': d.get('comments', {}),        # {cot, yields}
           'currencies': d.get('currencies', {}),    # per monedă: {bias, cb, banks, core}
           'trades_fx': tfx or [],
           'trades_intraday': tin or [],
           'cot': parts['cot_latest'], 'yields': parts['yields_latest'],
           'seasonality': parts['seasonality']}
    js = '// GENERAT de update_data.py / Claude — nu edita manual.\nwindow.ANALYSIS_DATA = ' \
         + json.dumps(obj, ensure_ascii=False, indent=1) + ';\n'
    (DATA.parent.parent / '07_Dashboard' / 'analysis_data.js').write_text(js)
    print('[RUNNER] analysis_data.js regenerat.')

def main():
    no_fetch = '--no-fetch' in sys.argv   # doar recompune snapshot + analysis_data.js
    ok_cot = ok_yld = True
    if not no_fetch:
        ok_cot = run('update_cot.py')
        ok_yld = run('update_yields.py')
        run('update_seasonality.py')

    lines = [f'# MACRO SNAPSHOT — {date.today().isoformat()}', '']
    cot = json.loads((DATA / 'cot_latest.json').read_text()) if (DATA / 'cot_latest.json').exists() else None
    yld = json.loads((DATA / 'yields_latest.json').read_text()) if (DATA / 'yields_latest.json').exists() else None
    sea = json.loads((DATA / 'seasonality.json').read_text()) if (DATA / 'seasonality.json').exists() else None

    if cot:
        lines += [f"## COT (as of {max(m['as_of'] for m in cot['markets'].values())}) — Leveraged Funds (TFF) / Managed Money (GOLD)", '',
                  '| Activ | Net | Δ 1w | % din OI | Percentilă 52w | Extremă |',
                  '|---|---|---|---|---|---|']
        for k in COT_ORDER:
            m = cot['markets'].get(k)
            if m:
                lines.append(f"| {k} | {m['net']:+,} | {m['delta_1w']:+,} | "
                             f"{m['pct_oi'] if m['pct_oi'] is not None else '—'}% | {m['percentile_52w']} | {m['extreme'] or '—'} |")
        lines.append('')
    else:
        lines += ['## COT — INDISPONIBIL (verifică manual pe cftc.gov)', '']

    if yld:
        lines += ['## Randamente 2Y/10Y (Δ = ~5 ședințe)', '',
                  '| | 2Y | Δ2Y | 10Y | Δ10Y |', '|---|---|---|---|---|']
        def cell(x, key):
            return (f"{x[key]['value']}", f"{x[key]['delta_1w']:+}") if x and x.get(key) else ('—', '—')
        for k in YLD_ORDER:
            lv = yld['levels'].get(k)
            v2, d2 = cell(lv, '2Y'); v10, d10 = cell(lv, '10Y')
            note = '' if yld['status'].get(k) == 'ok' else f" *({yld['status'].get(k, '?').split('(')[0].strip()})*"
            lines.append(f'| {k}{note} | {v2} | {d2} | {v10} | {d10} |')
        lines += ['', '## Spread-uri 2Y/10Y vs USD (criteriul 4)', '',
                  '| Pereche | Spread 2Y | Δ | Spread 10Y | Δ |', '|---|---|---|---|---|']
        for p in PAIR_ORDER:
            s = yld['spreads'].get(p, {})
            v2, d2 = cell(s, '2Y'); v10, d10 = cell(s, '10Y')
            lines.append(f'| {p} | {v2} | {d2} | {v10} | {d10} |')
        lines.append('')
        lines.append('*Interpretare: spread 2Y în creștere = suport pentru prima valută din pereche (playbook §3.1.3).*')
        lines.append('')

    if sea and sea.get('current_month', {}).get('instruments'):
        cm = sea['current_month']
        lines += [f"## Sezonalitate — luna curentă ({cm['name']}, medie {sea['years']} ani)", '',
                  '| Instrument | Medie % | Hit rate |', '|---|---|---|']
        for k, v in cm['instruments'].items():
            lines.append(f"| {k} | {v['avg']:+}% | {v['hit']}% |")
        lines.append('')

    DATA.mkdir(exist_ok=True)
    (DATA / 'macro_snapshot.md').write_text('\n'.join(lines))
    build_analysis_js()
    print(f"[RUNNER] macro_snapshot.md scris. COT={'ok' if ok_cot else 'EȘUAT'}, Randamente={'ok' if ok_yld else 'EȘUAT'}")

if __name__ == '__main__':
    main()
