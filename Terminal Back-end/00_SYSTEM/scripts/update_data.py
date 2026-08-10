#!/usr/bin/env python3
"""Runner: rulează update_cot.py + update_yields.py + update_regime.py + update_indicators.py,
compune ../data/macro_snapshot.md și regenerează 07_Dashboard/analysis_data.js.
Seasonality NU se rulează aici — se calculează O SINGURĂ DATĂ PE AN (început de an,
manual: `python3 update_seasonality.py`), ca să rămână fix tot anul (comparabil, nu
recalculat zilnic pe fereastra rulantă). Chenarul „luna curentă" din p7_seasonality.html
citește automat luna corectă din tabelul fix, fără să retrimită date.

Flags:
  --no-fetch     nu re-fetch-uiește nimic, doar recompune snapshot + analysis_data.js
                 din JSON-urile deja existente (folosit de jobul anual de seasonality).
  --skip-build   fetch normal (COT/randamente/regim/indicatori), dar NU rescrie
                 analysis_data.js. Adăugat 10.08.2026 pentru cron-ul zilnic din GitHub
                 Actions: analysis_data.js se compune din directions.json, editat la
                 comenzi explicite (procesează inbox / generează teza) — dacă bot-ul
                 îl rescrie și el zilnic, cele două scrieri intră în conflict de rebase
                 la push.command (motivul pauzei din 31.07.2026). Cu acest flag, cron-ul
                 zilnic atinge DOAR fișierele brute de date, niciodată directions.json
                 sau analysis_data.js.

Rulare (duminica, înainte de teză, sau manual oricând): python3 update_data.py"""
import json, subprocess, sys
from datetime import date
from pathlib import Path

from pricing import build_pricing
from scorecard import build_scorecard

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data'

COT_ORDER = ('DXY', 'EUR', 'GBP', 'CAD', 'JPY', 'CHF', 'AUD', 'NZD')
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
    for name in ('cot_latest', 'yields_latest', 'seasonality', 'directions', 'regime_latest',
                 'indicators_latest'):
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
           'currencies': d.get('currencies', {}),    # per monedă: {bias, cb, banks, core}
           # criteriul 1, cuantificat: cât e prețuit (2Y − dobânda de politică, în bp) vs. view-ul
           # desk-ului; edge = diferența. Narativul vine din directions.json, cifrele se calculează.
           'pricing': build_pricing(parts['yields_latest'], d),
           'playbook': d.get('playbook', []),        # Event Playbook: [{event, date, scenarios: [{name, odds, reaction, action}]}]
           'reports': d.get('reports', []),          # criteriul 2 — schema_bias.md, un rând per raport
           'reports_meta': d.get('reports_meta', {}),  # {processed, excluded, week}
           'indicators': d.get('indicators', {}),    # criteriul 3 — narativ per monedă (GDP/rate/CPI/unemp), afișaj p3
           # criteriul 3, cuantificat: index de surpriză actual-vs-consens (update_indicators.py,
           # Firecrawl pe calendarul TE din 10.08.2026). Separat de 'indicators' de mai sus —
           # ăla e narativul de afișaj, ăsta alimentează DOAR scorul din scorecard.
           'indicators_calc': parts['indicators_latest'],
           # criteriul 6, cuantificat: VIX + credit + momentum (update_regime.py)
           'regime_calc': parts['regime_latest'],
           'trades_fx': tfx or [],
           'trades_intraday': tin or [],
           'cot': parts['cot_latest'], 'yields': parts['yields_latest'],
           'seasonality': parts['seasonality']}

    # ——— CURRENCY SCORECARD (motorul de idei) ———
    # criteriile 1-2 din directions.json (judecată), 3-7 calculate mecanic din datele de mai sus.
    # Luna pentru seasonality: cea a săptămânii analizate, nu cea de azi — altfel scorecardul
    # unei teze vechi s-ar rescrie cu sezonalitatea lunii curente.
    try:
        wk = d.get('date') or date.today().isoformat()
        month = int(wk.split('-')[1]) if '-' in wk else date.today().month
        obj['scorecard'] = build_scorecard(parts['cot_latest'], parts['yields_latest'],
                                           parts['seasonality'], d, month,
                                           reg=parts['regime_latest'],
                                           pricing=obj['pricing'],
                                           ind=parts['indicators_latest'])
    except Exception as e:                                   # scorecardul nu trebuie să rupă pipeline-ul
        print(f'[RUNNER] scorecard EȘUAT: {e}', file=sys.stderr)
        obj['scorecard'] = None
    js = '// GENERAT de update_data.py / Claude — nu edita manual.\nwindow.ANALYSIS_DATA = ' \
         + json.dumps(obj, ensure_ascii=False, indent=1) + ';\n'
    (DATA.parent.parent / '07_Dashboard' / 'analysis_data.js').write_text(js)
    print('[RUNNER] analysis_data.js regenerat.')

def main():
    no_fetch = '--no-fetch' in sys.argv    # doar recompune snapshot + analysis_data.js
    skip_build = '--skip-build' in sys.argv  # doar fetch + macro_snapshot.md, FĂRĂ analysis_data.js
    # --skip-build există din 10.08.2026 pentru cron-ul zilnic: analysis_data.js se compune
    # din directions.json (editat manual/de Claude la comenzi), deci dacă bot-ul îl rescrie
    # în același timp cu o sesiune locală, apare conflict de rebase la push.command — exact
    # motivul pentru care cron-ul a stat pauzat din 31.07.2026. Fetch-ul de date brute
    # (yields/cot/regim) e sigur de automatizat oricând; recompunerea analysis_data.js
    # rămâne legată de comenzile explicite (procesează inbox / generează teza).
    ok_cot = ok_yld = ok_reg = ok_ind = True
    if not no_fetch:
        ok_cot = run('update_cot.py')
        ok_yld = run('update_yields.py')
        ok_reg = run('update_regime.py')       # criteriul 6 — VIX + credit + momentum
        ok_ind = run('update_indicators.py')   # criteriul 3 — index de surpriză (Firecrawl, 10.08.2026)
        # seasonality: NU se rulează aici, e anuală (vezi update_seasonality.py)

    lines = [f'# MACRO SNAPSHOT — {date.today().isoformat()}', '']
    cot = json.loads((DATA / 'cot_latest.json').read_text()) if (DATA / 'cot_latest.json').exists() else None
    yld = json.loads((DATA / 'yields_latest.json').read_text()) if (DATA / 'yields_latest.json').exists() else None
    sea = json.loads((DATA / 'seasonality.json').read_text()) if (DATA / 'seasonality.json').exists() else None
    reg = json.loads((DATA / 'regime_latest.json').read_text()) if (DATA / 'regime_latest.json').exists() else None

    if cot:
        lines += [f"## COT (as of {max(m['as_of'] for m in cot['markets'].values())}) — Leveraged Funds (TFF)", '',
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

    if reg and reg.get('score') is not None:
        lines += [f"## Regim de risc (criteriul 6) — scor {reg['score']:+d} ({reg.get('label', '')})"
                  + ('' if reg.get('status') == 'ok' else f" *({reg.get('status')})*"), '',
                  '| Componentă | Valoare | Percentilă 1y | Scor |', '|---|---|---|---|']
        for c in reg.get('components', []):
            lines.append(f"| {c['label']} | {c['value']} | "
                         f"{c['pctile'] if c.get('pctile') is not None else '—'} | {c['score']:+d} |")
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
    if skip_build:
        print('[RUNNER] --skip-build: analysis_data.js NU a fost rescris (rămâne pentru '
              'următoarea comandă explicită — procesează inbox / generează teza).')
    else:
        build_analysis_js()
    print(f"[RUNNER] macro_snapshot.md scris. COT={'ok' if ok_cot else 'EȘUAT'}, "
          f"Randamente={'ok' if ok_yld else 'EȘUAT'}, Regim={'ok' if ok_reg else 'EȘUAT'}, "
          f"Indicatori={'ok' if ok_ind else 'EȘUAT'}")

if __name__ == '__main__':
    main()
