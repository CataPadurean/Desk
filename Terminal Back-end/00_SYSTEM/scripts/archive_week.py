#!/usr/bin/env python3
"""ARHIVA SĂPTĂMÂNALĂ — salvează output-ul terminalului, nu terminalul.

Terminalul se rescrie la fiecare comandă, și așa trebuie: nu ține istoric de ecrane,
ca niciun terminal. Ce NU se poate reconstitui din date mai târziu e judecata —
scorurile, verdictele, ce a fost respins și de ce. Doar aia se arhivează.

Salvează per săptămână, în `4_Archive/`:
  · scorecard — scorurile celor 8 monede pe cele 7 criterii + perechile cu verdict,
    inclusiv cele sub prag (respinse), fiindcă absența trade-ului e o decizie
  · trades    — book-ul acționabil, cu gap, trigger și invalidare

Formatul e JSON, nu PDF: tot ce urmează (dacă diferența de rank prezice mișcarea,
dacă scala de conviction e calibrată, ce bănci au dreptate) se CALCULEAZĂ din serii,
nu se citește din documente.

Rulare:  python3 archive_week.py            → arhivează săptămâna din terminal
         python3 archive_week.py --list     → ce săptămâni sunt deja arhivate
         python3 archive_week.py --show     → afișează ultima arhivă, citibil
         python3 archive_week.py --show 06.07–10.07.2026
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent   # …/Padu Terminal
DASH = ROOT / 'Terminal Back-end' / '07_Dashboard'
ARCHIVE = ROOT / '4_Archive'

CRIT_LABEL = {'cb': 'CB', 'bnk': 'BNK', 'ind': 'IND', 'yld': 'YLD',
              'cot': 'COT', 'reg': 'REG', 'sea': 'SEA'}
CRIT_ORDER = ('cb', 'bnk', 'ind', 'yld', 'cot', 'reg', 'sea')


def _strip_js_comments(txt: str) -> str:
    """Scoate comentariile // și /* */, respectând șirurile.
    Necesar fiindcă data.js e scris de mână și comentariile conțin ghilimele
    românești nepereche („…") care ar deraia orice numărare naivă de acolade."""
    out, i, n = [], 0, len(txt)
    in_str = quote = None
    while i < n:
        ch = txt[i]
        if in_str:
            out.append(ch)
            if ch == '\\' and i + 1 < n:
                out.append(txt[i + 1]); i += 2; continue
            if ch == quote:
                in_str = False
            i += 1
        elif ch in '"\'':
            in_str, quote = True, ch
            out.append(ch); i += 1
        elif ch == '/' and i + 1 < n and txt[i + 1] == '/':
            while i < n and txt[i] != '\n':
                i += 1
        elif ch == '/' and i + 1 < n and txt[i + 1] == '*':
            i = txt.find('*/', i + 2)
            i = n if i < 0 else i + 2
        else:
            out.append(ch); i += 1
    return ''.join(out)


def _read_js_object(path: Path, var: str) -> dict:
    """Extrage obiectul dintr-un fișier `window.X = {...};`.
    analysis_data.js e generat (JSON curat), data.js e scris de mână (obiect JS:
    chei fără ghilimele, virgule în plus) — deci normalizăm înainte de parsare."""
    txt = _strip_js_comments(path.read_text(encoding='utf-8'))
    start = txt.index('{', txt.index(var))
    depth, in_str, esc = 0, False, False
    end = -1
    for j in range(start, len(txt)):
        ch = txt[j]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    if end < 0:
        raise ValueError(f'{path.name}: obiect neînchis pentru {var}')

    body = txt[start:end]
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        body = re.sub(r'([{,]\s*)([A-Za-z_$][\w$]*)(\s*:)', r'\1"\2"\3', body)  # chei fără ghilimele
        body = re.sub(r',(\s*[}\]])', r'\1', body)                              # virgule în plus
        return json.loads(body)


def _week_slug(week: str) -> str:
    """„06.07–10.07.2026" → „2026-07-06" (lunea săptămânii), ca fișierele să se sorteze."""
    m = re.match(r'(\d{2})\.(\d{2})\D+\d{2}\.\d{2}\.(\d{4})', week or '')
    if m:
        d, mo, y = m.groups()
        return f'{y}-{mo}-{d}'
    return date.today().isoformat()


def build_entry() -> dict:
    """Compune intrarea de arhivă din starea curentă a terminalului."""
    A = _read_js_object(DASH / 'analysis_data.js', 'window.ANALYSIS_DATA')
    D = _read_js_object(DASH / 'data.js', 'window.DESK_DATA')
    sc = A.get('scorecard') or {}
    pairs = sc.get('pairs', [])

    # doar ideile acționabile — book-ul, exact ce se vede pe Home
    trades = [t for t in (D.get('trades') or [])
              if 'LONG' in str(t.get('dir', '')).upper() or 'SHORT' in str(t.get('dir', '')).upper()]
    gaps = {p['pair']: p for p in pairs}
    trades_out = []
    for t in trades:
        p = gaps.get(t.get('instrument'), {})
        trades_out.append({
            'instrument': t.get('instrument'), 'type': t.get('type'),
            'stage': t.get('stage'), 'dir': t.get('dir'), 'conf': t.get('conf'),
            'gap': p.get('gap'), 'verdict': p.get('verdict'),
            'catalyst': p.get('catalyst', ''), 'horizon': t.get('horizon'),
            'drivers': t.get('drivers'), 'trigger': t.get('trigger'),
            'invalidation': t.get('invalidation'),
        })

    return {
        'week': D.get('week', ''),
        'archived': datetime.now().isoformat(timespec='seconds'),
        'analysis_date': A.get('regime_date', ''),
        'data_generated': A.get('generated', ''),
        'regime': {'label': (A.get('sentiment') or {}).get('label', ''),
                   'score': sc.get('regime_score')},
        'scorecard': {
            'weights': sc.get('weights', {}),
            'thresholds': sc.get('thresholds', {}),
            'month': sc.get('month'),
            'ranked': sc.get('ranked', []),
            'currencies': {c: {'rank': v.get('rank'), 'total': v.get('total'),
                               'scores': v.get('scores'), 'missing': v.get('missing'),
                               'catalyst': v.get('catalyst', ''), 'contra': v.get('contra', ''),
                               'why': v.get('why', {})}
                           for c, v in (sc.get('currencies') or {}).items()},
            # TOATE perechile, inclusiv cele sub prag: ce ai respins face parte din decizie
            'pairs': [{'pair': p['pair'], 'gap': p['gap'], 'dir': p['dir'],
                       'verdict': p['verdict'], 'catalyst': p.get('catalyst', ''),
                       'blind': p.get('blind', []), 'cross': p.get('cross', False)}
                      for p in pairs],
        },
        'trades': trades_out,
    }


def save(entry: dict, force: bool = False) -> Path:
    ARCHIVE.mkdir(exist_ok=True)
    slug = _week_slug(entry['week'])
    path = ARCHIVE / f'{slug}_scorecard.json'
    if path.exists() and not force:
        print(f'[ARHIVA] {path.name} există deja — se rescrie (aceeași săptămână, stare nouă).')
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding='utf-8')
    return path


# ══════════════════════════════════════════════════════════════════════════
# citire
# ══════════════════════════════════════════════════════════════════════════

def list_weeks():
    files = sorted(ARCHIVE.glob('*_scorecard.json'))
    if not files:
        print('Arhiva e goală.')
        return
    print(f'{len(files)} săptămâni arhivate în {ARCHIVE.name}/:\n')
    for f in files:
        e = json.loads(f.read_text(encoding='utf-8'))
        sc = e.get('scorecard', {})
        rk = sc.get('ranked', [])
        book = [t['instrument'] for t in e.get('trades', [])]
        print(f"  {f.name:34} {e.get('week',''):22} "
              f"top {rk[0] if rk else '—'} / jos {rk[-1] if rk else '—'}  ·  book: {', '.join(book) or '—'}")


def show(week_arg: str | None):
    files = sorted(ARCHIVE.glob('*_scorecard.json'))
    if not files:
        print('Arhiva e goală.')
        return
    f = files[-1]
    if week_arg:
        hits = [x for x in files if week_arg in x.name or week_arg in
                json.loads(x.read_text(encoding='utf-8')).get('week', '')]
        if not hits:
            print(f'Nicio arhivă pentru „{week_arg}". Rulează --list.')
            return
        f = hits[-1]

    e = json.loads(f.read_text(encoding='utf-8'))
    sc, cur = e['scorecard'], e['scorecard']['currencies']
    th = sc.get('thresholds', {})

    print(f"\n  SĂPTĂMÂNA {e['week']}   ·   regim: {e['regime'].get('label','—')}"
          f"   ·   arhivat {e['archived'][:10]}")
    print(f"  {f}\n")

    print('  ' + 'CURRENCY'.ljust(10) + ' '.join(CRIT_LABEL[k].rjust(5) for k in CRIT_ORDER) + '   SCORE')
    for c in sc['ranked']:
        v = cur[c]
        cells = ' '.join(('—' if v['scores'].get(k) is None else '%+d' % v['scores'][k]).rjust(5)
                         for k in CRIT_ORDER)
        line = '  %-10s%s  %+6.1f' % (f"{v['rank']} {c}", cells, v['total'])
        if v.get('missing'):
            line += '   [orb: %s]' % ', '.join(v['missing'])
        print(line)

    print(f"\n  PERECHI   (book de la {th.get('book','?')} · watch de la {th.get('watch','?')})")
    for p in sc['pairs']:
        if p['verdict'] == 'SUB PRAG':
            continue
        print('  %-9s %+6.1f  %-6s %-6s %s' % (p['pair'], p['gap'], p['verdict'], p['dir'],
                                               p.get('catalyst') or '—'))
    subs = [p for p in sc['pairs'] if p['verdict'] == 'SUB PRAG']
    if subs:
        print('  sub prag: ' + ' · '.join('%s %.1f' % (p['pair'], abs(p['gap'])) for p in subs))

    print('\n  BOOK')
    for t in e['trades']:
        print('  %-9s %-14s %-10s gap %-6s %s' % (
            t['instrument'], t['dir'], t['stage'],
            '—' if t['gap'] is None else '%.1f' % abs(t['gap']),
            (t.get('catalyst') or '—')))
        if t.get('trigger') and t['trigger'] != '—':
            print('            trigger:    %s' % t['trigger'])
        if t.get('invalidation') and t['invalidation'] != '—':
            print('            invalidare: %s' % t['invalidation'])
    print()


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--list' in args:
        list_weeks()
    elif '--show' in args:
        rest = [a for a in args if not a.startswith('--')]
        show(rest[0] if rest else None)
    else:
        entry = build_entry()
        p = save(entry, force='--force' in args)
        n = len(entry['scorecard']['pairs'])
        print(f"[ARHIVA] {p.name} scris — săptămâna {entry['week']}: "
              f"8 monede, {n} perechi, {len(entry['trades'])} idei în book.")
        print(f"[ARHIVA] Citește-l cu:  python3 archive_week.py --show")
