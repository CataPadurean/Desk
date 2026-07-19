#!/usr/bin/env python3
"""Sezonalitate 10 ani: randament mediu lunar + hit rate per instrument, pe toate cele 12 luni.
Instrumente: cele 7 perechi FX + US30 + GOLD.
Surse: FRED (FX zilnic + DJIA, fără cheie; DJIA are istoric rolling de fix ~10 ani = fereastra noastră)
și LBMA (Gold PM fix USD, JSON public prices.lbma.org.uk). Stooq/Yahoo rămân blocate anti-bot.

RULARE: O SINGURĂ DATĂ PE AN, la început de an (ex. prima săptămână din ianuarie), manual:
    python3 update_seasonality.py
Tabelul rămâne FIX tot anul — asta e intenționat: Cătălin vrea să compare performanța
reală a anului curent față de un reper de sezonalitate care nu se mișcă sub el (nu o
fereastră rulantă recalculată zilnic). NU se apelează din update_data.py și NU rulează
în GitHub Actions zilnic — doar din workflow-ul anual dedicat sau manual pe Mac.

Chenarul „luna curentă" din analysis.html NU mai vine din date scrise aici — se
calculează live în browser (JS: new Date().getMonth()) și citește luna corespunzătoare
din acest tabel fix. Deci chenarul se actualizează singur pe 1 ale fiecărei luni,
fără nicio rulare de script."""
import csv, io, json, subprocess, sys
from datetime import date
from pathlib import Path

YEARS = 10

def get(url, tries=3):
    """Fetch prin curl, cu User-Agent-ul IMPLICIT al lui curl (`curl/x`).
    NU pune un UA de tip `Mozilla/...`: FRED e în spatele Akamai, care pentru UA-uri
    de browser pornește protecție anti-bot și, cum curl n-are amprenta TLS/HTTP2 a unui
    browser real, resetează stream-ul (exit 92) sau tarpit-ează (timeout, exit 28).
    Cu UA-ul cinstit `curl/x`, livrează CSV-ul curat (verificat 2026-07-04: 200 în 0.5s).
    urllib pica din același motiv (folosea același UA fals)."""
    import time
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(
                ['curl', '-sS', '-f', '--http1.1', '--max-time', '45', url],
                capture_output=True, timeout=60)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.decode('utf-8', errors='replace')
            last = RuntimeError(
                f'curl exit={r.returncode}, {len(r.stdout)}B, {r.stderr.decode("utf-8","replace")[:120]}')
        except Exception as e:
            last = e
        if i < tries - 1:
            time.sleep(3)
    raise last

def monthly_from_fred(series_id):
    """FRED zilnic → ultima valoare din fiecare lună → [(YYYY-MM, close)]."""
    txt = get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}')
    r = csv.reader(io.StringIO(txt)); head = next(r)
    iv = head.index(series_id)
    m = {}
    for row in r:
        if row[iv] not in ('.', ''):
            m[row[0][:7]] = float(row[iv])  # cheia YYYY-MM, suprascrie → rămâne ultima zi
    return sorted(m.items())

def monthly_from_lbma(url='https://prices.lbma.org.uk/json/gold_pm.json'):
    """LBMA JSON [{'d':'YYYY-MM-DD','v':[USD,GBP,EUR]}, ...] → [(YYYY-MM, close USD)]."""
    data = json.loads(get(url))
    m = {}
    for row in data:
        v = row.get('v') or []
        if v and v[0]:
            m[row['d'][:7]] = float(v[0])  # suprascrie → rămâne ultima zi din lună
    return sorted(m.items())

def seasonality(series):
    """[(YYYY-MM, close)] → per lună calendaristică: medie %, hit rate, n (ultimii YEARS ani)."""
    rets = []
    for (m0, v0), (m1, v1) in zip(series, series[1:]):
        if v0: rets.append((m1, 100 * (v1 - v0) / v0))
    cutoff = f'{date.today().year - YEARS}-01'
    rets = [x for x in rets if x[0] >= cutoff]
    out = {}
    for mo in range(1, 13):
        xs = [r for m, r in rets if int(m[5:7]) == mo]
        if xs:
            out[str(mo)] = {'avg': round(sum(xs) / len(xs), 2),
                            'hit': round(100 * sum(1 for x in xs if x > 0) / len(xs)),
                            'n': len(xs)}
    return out

def main():
    src = {
        # ordinea canonică (CLAUDE.md, regula 0): perechi FX, apoi US30, apoi GOLD
        'EURUSD': lambda: monthly_from_fred('DEXUSEU'),
        'GBPUSD': lambda: monthly_from_fred('DEXUSUK'),
        'USDCAD': lambda: monthly_from_fred('DEXCAUS'),
        'USDJPY': lambda: monthly_from_fred('DEXJPUS'),
        'USDCHF': lambda: monthly_from_fred('DEXSZUS'),
        'AUDUSD': lambda: monthly_from_fred('DEXUSAL'),
        'NZDUSD': lambda: monthly_from_fred('DEXUSNZ'),
        'US30':   lambda: monthly_from_fred('DJIA'),
        'GOLD':   monthly_from_lbma,
    }
    out = {'updated': date.today().isoformat(), 'years': YEARS, 'instruments': {}, 'status': {}}
    for k, fn in src.items():
        try:
            out['instruments'][k] = seasonality(fn())
            out['status'][k] = 'ok'
        except Exception as e:
            out['status'][k] = f'INDISPONIBIL: {e}'
            print(f'[SEZON] {k} a picat: {e}', file=sys.stderr)

    dst = Path(__file__).resolve().parents[1] / 'data'
    dst.mkdir(exist_ok=True)
    (dst / 'seasonality.json').write_text(json.dumps(out, ensure_ascii=False))
    ok = [k for k, s in out['status'].items() if s == 'ok']
    print(f"[SEZON] OK: {', '.join(ok) or 'NICIUNA'}" + (f" | PICATE: {[k for k in out['status'] if k not in ok]}" if len(ok) < len(src) else ''))
    if not ok: sys.exit(1)

if __name__ == '__main__':
    main()
