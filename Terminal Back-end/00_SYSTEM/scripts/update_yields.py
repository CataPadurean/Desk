#!/usr/bin/env python3
"""Randamente 2Y (criteriu principal) + 10Y (secundar) pe 8 monede
(US, EUR, GBP, CAD, JPY, CHF, AUD, NZD) + spread-uri vs USD pe cele 7 perechi.

Rulare: python3 update_yields.py  →  scrie ../data/yields_latest.json

Arhitectură „merge întotdeauna":
  1. Surse oficiale primare + fallback-uri, toate gratuite și fără cheie API:
       US  : FRED (fredgraph CSV)            → US Treasury (XML)
       EUR : ECB Data Portal (curba AAA)     → curba „toți emitenții" → Stooq Bund
       GBP : BoE — ZIP curba GLC (xlsx)      → Stooq
       CAD : Bank of Canada Valet (JSON)
       JPY : MOF Japonia (jgbcme CSV)        → Stooq
       CHF : SNB cub «rendoblid» (2J/10J0)   → Stooq
       AUD : RBA F2 zilnic (FCMYGBAG2D/10D)  → RBA F2.1 lunar → Stooq
       NZD : RBNZ B2 zilnic (xlsx)           → Stooq
  2. Cache «last-known-good»: dacă o sursă pică azi, păstrăm ultima valoare
     bună din yields_latest.json (status = stale), NU dispare din dashboard.
  3. history per monedă/tenor (ultimele ~30 obs.) pentru Δ stabil.
Doar stdlib — rulează identic pe Mac, GitHub Actions sau alt sandbox."""
import csv, io, json, re, sys, time, urllib.request, zipfile
import datetime as dt
from datetime import date, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

DATA = Path(__file__).resolve().parents[1] / 'data'
OUT = DATA / 'yields_latest.json'
HIST_KEEP = 30          # observații păstrate per serie
DELTA_SESSIONS = 5      # Δ = ultima valoare − valoarea de acum ~5 ședințe

# ————————————————————————— utilitare —————————————————————————
def get(url, tries=3, binary=False, referer=None):
    """Fetch cu curl și UA-ul lui implicit (curl/x). NU spoof-ui «Mozilla/…»:
    FRED (Akamai) tarpit-ează UA-uri de browser venite fără fingerprint TLS de
    browser real (lecția din 04.07.2026). Fallback: urllib fără UA custom."""
    import subprocess
    last = None
    for i in range(tries):
        try:
            cmd = ['curl', '-sSL', '--fail', '--max-time', '60']
            if referer: cmd += ['-e', referer]
            r = subprocess.run(cmd + [url], capture_output=True, timeout=75)
            if r.returncode == 0 and r.stdout:
                return r.stdout if binary else r.stdout.decode('utf-8', errors='replace')
            last = RuntimeError(f'curl rc={r.returncode}: {r.stderr.decode("utf-8", "replace")[:100]}')
        except Exception as e:
            last = e
        try:  # fallback urllib, fără User-Agent custom
            req = urllib.request.Request(url, headers={'Referer': referer} if referer else {})
            raw = urllib.request.urlopen(req, timeout=60).read()
            return raw if binary else raw.decode('utf-8', errors='replace')
        except Exception as e:
            last = e
        if i < tries - 1: time.sleep(3 * (i + 1))
    raise last

def _iso(s):
    """normalizează data la YYYY-MM-DD (sortare corectă)."""
    s = (s or '').strip()
    for fmt in ('%Y-%m-%d', '%d-%b-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y/%m/%d', '%d %b %Y', '%b %Y'):
        try: return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError: pass
    return s

def _f(x):
    try:
        v = float(str(x).replace(',', '').strip())
        return v if -5.0 < v < 30.0 else None      # sanity: randament plauzibil
    except (TypeError, ValueError):
        return None

def series_clean(pairs):
    """[(date,val)] → sortat, dedup pe dată (ultima câștigă), doar valori valide."""
    d = {}
    for k, v in pairs:
        k = _iso(k); v = _f(v)
        if v is not None and re.match(r'^\d{4}-\d{2}-\d{2}$', k or ''):
            d[k] = v
    return sorted(d.items())[-250:]

def xl_date(serial):
    """număr serial Excel → YYYY-MM-DD."""
    try:
        return (dt.date(1899, 12, 30) + timedelta(days=int(float(serial)))).isoformat()
    except (TypeError, ValueError):
        return None

def xlsx_sheets(raw):
    """xlsx (bytes) → {nume_foaie: [ {col_letter: valoare} per rând ]} — stdlib only."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).iter(NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    # map nume foaie → fișier, via workbook + rels
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = {r.get('Id'): r.get('Target')
            for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    out = {}
    for sh in wb.iter(NS + 'sheet'):
        target = rels.get(sh.get(RNS + 'id'), '')
        path = 'xl/' + target.lstrip('/') if not target.startswith('xl/') else target
        if path not in z.namelist(): continue
        rows = []
        for row in ET.fromstring(z.read(path)).iter(NS + 'row'):
            cells = {}
            for c in row.iter(NS + 'c'):
                col = ''.join(ch for ch in (c.get('r') or '') if ch.isalpha())
                v = c.find(NS + 'v')
                val = v.text if v is not None else None
                if c.get('t') == 's' and val is not None:
                    val = shared[int(val)]
                elif c.get('t') == 'inlineStr':
                    val = ''.join(t.text or '' for t in c.iter(NS + 't'))
                cells[col] = val
            rows.append(cells)
        out[sh.get('name')] = rows
    return out

def col_num(letter):
    n = 0
    for ch in letter: n = n * 26 + ord(ch) - 64
    return n

# ————————————————————————— surse per monedă —————————————————————————
def src_fred():
    start = (date.today() - timedelta(days=90)).isoformat()
    txt = get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2,DGS10&cosd={start}')
    r = csv.reader(io.StringIO(txt)); head = next(r)
    i2, i10 = head.index('DGS2'), head.index('DGS10')
    s2, s10 = [], []
    for row in r:
        if len(row) > max(i2, i10):
            s2.append((row[0], row[i2])); s10.append((row[0], row[i10]))
    return {'2Y': series_clean(s2), '10Y': series_clean(s10)}, 'FRED'

def src_treasury():
    y = date.today().year
    xml = get('https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml'
              f'?data=daily_treasury_yield_curve&field_tdr_date_value={y}')
    s2, s10 = [], []
    for entry in xml.split('<entry>')[1:]:
        d = re.search(r'<d:NEW_DATE[^>]*>([\d-]+)', entry)
        v2 = re.search(r'<d:BC_2YEAR[^>]*>([\d.]+)', entry)
        v10 = re.search(r'<d:BC_10YEAR[^>]*>([\d.]+)', entry)
        if d and v2: s2.append((d.group(1)[:10], v2.group(1)))
        if d and v10: s10.append((d.group(1)[:10], v10.group(1)))
    if not s2: raise RuntimeError('Treasury XML: fără date')
    return {'2Y': series_clean(s2), '10Y': series_clean(s10)}, 'US Treasury'

def src_ecb():
    out = {}
    for lbl, code in (('2Y', 'SR_2Y'), ('10Y', 'SR_10Y')):
        series = []
        for curve in ('G_N_A', 'G_N_C'):          # AAA, apoi toți emitenții
            url = (f'https://data-api.ecb.europa.eu/service/data/YC/'
                   f'B.U2.EUR.4F.{curve}.SV_C_YM.{code}?format=csvdata&lastNObservations=40')
            try:
                rows = csv.DictReader(io.StringIO(get(url, tries=2)))
                series = [(r['TIME_PERIOD'], r['OBS_VALUE']) for r in rows if r.get('OBS_VALUE')]
            except Exception:
                series = []
            if series: break
        if not series: raise RuntimeError(f'ECB {code}: fără date')
        out[lbl] = series_clean(series)
    return out, 'ECB (curba AAA euro area)'

def src_boc():
    url = 'https://www.bankofcanada.ca/valet/observations/BD.CDN.2YR.DQ.YLD,BD.CDN.10YR.DQ.YLD/json?recent=40'
    j = json.loads(get(url))
    s2 = [(o['d'], o['BD.CDN.2YR.DQ.YLD']['v']) for o in j['observations'] if o.get('BD.CDN.2YR.DQ.YLD', {}).get('v')]
    s10 = [(o['d'], o['BD.CDN.10YR.DQ.YLD']['v']) for o in j['observations'] if o.get('BD.CDN.10YR.DQ.YLD', {}).get('v')]
    return {'2Y': series_clean(s2), '10Y': series_clean(s10)}, 'BoC Valet'

def src_boe_glc():
    """GBP oficial: ZIP-ul BoE cu curba GLC nominală (spot, toate tenorurile).
    Foile «spot curve» au: un rând-antet cu tenoruri (2.0 … 10.0), datele pe coloana A (serial Excel)."""
    raw = get('https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/latest-yield-curve-data.zip',
              binary=True, referer='https://www.bankofengland.co.uk/statistics/yield-curves')
    z = zipfile.ZipFile(io.BytesIO(raw))
    s2, s10 = [], []
    for name in z.namelist():
        if 'nominal' not in name.lower() or not name.lower().endswith('.xlsx'): continue
        for sheet, rows in xlsx_sheets(z.read(name)).items():
            if 'spot' not in sheet.lower(): continue
            hdr_i = c2 = c10 = None
            for i, r in enumerate(rows[:12]):
                cols2 = [c for c, v in r.items() if _f(v) == 2.0]
                cols10 = [c for c, v in r.items() if _f(v) == 10.0]
                # rândul cu tenoruri are multe valori 0.5,1.0,1.5…
                numeric = [v for v in r.values() if _f(v) is not None]
                if cols2 and cols10 and len(numeric) >= 10:
                    hdr_i, c2, c10 = i, cols2[0], cols10[0]; break
            if hdr_i is None: continue
            for r in rows[hdr_i + 1:]:
                d = xl_date(r.get('A'))
                if not d: continue
                if r.get(c2) is not None: s2.append((d, r[c2]))
                if r.get(c10) is not None: s10.append((d, r[c10]))
    if not s2 and not s10: raise RuntimeError('BoE GLC: nu am găsit foaia spot')
    return {'2Y': series_clean(s2), '10Y': series_clean(s10)}, 'BoE (curba GLC nominală)'

def src_mof():
    """JPY oficial: MOF — luna curentă; dacă are <7 ședințe, adaug istoricul complet."""
    base = 'https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/'
    def parse(txt):
        rows = list(csv.reader(io.StringIO(txt)))
        hdr_i = i2 = i10 = None
        for ri, r in enumerate(rows[:8]):
            cells = [c.strip().upper() for c in r]
            if '2Y' in cells and '10Y' in cells:
                hdr_i, i2, i10 = ri, cells.index('2Y'), cells.index('10Y'); break
            if '2' in cells and '10' in cells:      # varianta fără sufix Y
                hdr_i, i2, i10 = ri, cells.index('2'), cells.index('10'); break
        if hdr_i is None: return [], []
        s2, s10 = [], []
        for r in rows[hdr_i + 1:]:
            if len(r) <= max(i2, i10) or not r[0].strip(): continue
            s2.append((r[0], r[i2])); s10.append((r[0], r[i10]))
        return s2, s10
    s2, s10 = parse(get(base + 'jgbcme.csv'))
    if len(s2) < 7:
        try:
            a2, a10 = parse(get(base + 'jgbcme_all.csv'))
            s2, s10 = a2[-60:] + s2, a10[-60:] + s10
        except Exception as e:
            print(f'[YLD]   MOF istoric complet indisponibil ({e}) — merg pe luna curentă', file=sys.stderr)
    if not s2 and not s10: raise RuntimeError('MOF: fără date')
    return {'2Y': series_clean(s2), '10Y': series_clean(s10)}, 'MOF Japonia'

def src_snb():
    """CHF oficial: cuburi SNB cu spot Confederație (D0: 2J=2Y, 10J0=10Y).
    Atenție: «rendoblid» a fost discontinuat în 2025 (ultimele date 2025-07-31) —
    guard-ul de prospețime din main() respinge datele vechi; încerc și candidați noi."""
    frm = (date.today() - timedelta(days=90)).isoformat()
    last_err = ''
    for cube in ('rendoblid', 'rendeidglfd', 'rendeidglf'):
        for url in (f'https://data.snb.ch/api/cube/{cube}/data/csv/en?fromDate={frm}',
                    f'https://data.snb.ch/api/cube/{cube}/data/csv/en'):
            try:
                txt = get(url, tries=1)
            except Exception as e:
                last_err = f'{cube}: {e}'; continue
            s2, s10 = [], []
            for line in txt.splitlines():
                p = [x.strip().strip('"') for x in line.split(';')]
                if len(p) < 3: continue
                d, code, val = p[0], p[1].upper(), p[2]
                if code == '2J': s2.append((d, val))
                elif code in ('10J0', '10J'): s10.append((d, val))
            if s2 or s10:
                return {'2Y': series_clean(s2), '10Y': series_clean(s10)}, f'SNB ({cube})'
            last_err = f'{cube}: fără 2J/10J0'
    raise RuntimeError(f'SNB cuburi: {last_err}')

def src_snb_rss():
    """CHF fallback oficial: RSS «Current interest rates» — DOAR 10Y (ultima valoare).
    Istoricul se acumulează în cache de la o rulare zilnică la alta."""
    xml = get('https://www.snb.ch/public/rss/en/interestRates')
    best = None
    for item in re.split(r'<item[\s>]', xml)[1:]:
        text = re.sub(r'<[^>]+>', ' ', item)
        if not re.search(r'confederation', text, re.I): continue
        mv = re.search(r'(-?\d+(?:[.,]\d+))\s*%', text)
        md = (re.search(r'(\d{4}-\d{2}-\d{2})', item)
              or re.search(r'(\d{2}\.\d{2}\.\d{4})', text))
        if mv:
            d = md.group(1) if md else date.today().isoformat()
            if '.' in d and len(d) == 10 and d[2] == '.':
                d = '-'.join(reversed(d.split('.')))
            best = (d, mv.group(1).replace(',', '.'))
    if not best: raise RuntimeError('SNB RSS: randamentul Confederației negăsit')
    return {'2Y': [], '10Y': series_clean([best])}, 'SNB RSS (doar 10Y)'

def _rba_parse(txt, want2, want10):
    rows = list(csv.reader(io.StringIO(txt)))
    idrow = next((r for r in rows if r and r[0].strip().lower() == 'series id'), None)
    if not idrow: raise RuntimeError('RBA: rând «Series ID» negăsit')
    def cidx(codes):
        for code in codes:
            for i, c in enumerate(idrow):
                if c.strip().upper() == code: return i
        return None
    i2, i10 = cidx(want2), cidx(want10)
    if i2 is None and i10 is None: raise RuntimeError(f'RBA: coloanele {want2}/{want10} negăsite')
    s2, s10 = [], []
    for r in rows:
        if not r or not r[0].strip(): continue
        d = _iso(r[0])
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', d): continue
        if i2 is not None and i2 < len(r): s2.append((d, r[i2]))
        if i10 is not None and i10 < len(r): s10.append((d, r[i10]))
    return {'2Y': series_clean(s2), '10Y': series_clean(s10)}

def src_rba():
    """AUD oficial: F2 ZILNIC (seriile cu sufix D); fallback F2.1 lunar."""
    try:
        out = _rba_parse(get('https://www.rba.gov.au/statistics/tables/csv/f2-data.csv'),
                         ('FCMYGBAG2D', 'FCMYGBAG2'), ('FCMYGBAG10D', 'FCMYGBAG10'))
        if out['2Y'] or out['10Y']: return out, 'RBA F2 zilnic'
    except Exception as e:
        print(f'[YLD]   RBA zilnic a picat ({e}) — încerc F2.1 lunar', file=sys.stderr)
    out = _rba_parse(get('https://www.rba.gov.au/statistics/tables/csv/f2.1-data.csv'),
                     ('FCMYGBAG2',), ('FCMYGBAG10',))
    return out, 'RBA F2.1 lunar'

def src_rbnz():
    """NZD oficial: RBNZ B2 zilnic (xlsx). Caut coloanele «Govt bond yields … 2/10 year(s)»."""
    raw = get('https://www.rbnz.govt.nz/-/media/project/sites/rbnz/files/statistics/series/b/b2/hb2-daily.xlsx',
              binary=True, referer='https://www.rbnz.govt.nz/statistics/series/exchange-and-interest-rates/wholesale-interest-rates')
    for sheet, rows in xlsx_sheets(raw).items():
        if sheet.lower().startswith('read') or not rows: continue     # sar peste foaia README
        # titlul coloanei = concatenarea celulelor de antet (primele ~8 rânduri) pe coloană,
        # cu grupurile îmbinate propagate spre dreapta
        hdr_rows = rows[:8]
        cols = sorted({c for r in hdr_rows for c in r}, key=col_num)
        titles, carry = {}, {}
        for ri, r in enumerate(hdr_rows):
            last = ''
            for c in cols:
                v = (r.get(c) or '').strip() if isinstance(r.get(c), str) else ''
                if v: last = v
                carry.setdefault(ri, {})[c] = v or last
        for c in cols:
            titles[c] = ' '.join(carry[ri][c] for ri in carry).lower()
        def pick(tenor):
            best = None
            for c, t in titles.items():
                if re.search(rf'(?<!\d){tenor}\s*year', t) and 'bond' in t and 'swap' not in t and 'inflation' not in t:
                    best = c; break
            return best
        c2, c10 = pick(2), pick(10)
        if not (c2 and c10): continue
        s2, s10 = [], []
        for r in rows:
            d = xl_date(r.get('A')) or (_iso(r.get('A')) if isinstance(r.get('A'), str) else None)
            if not d or not re.match(r'^\d{4}-\d{2}-\d{2}$', d): continue
            if r.get(c2) is not None: s2.append((d, r[c2]))
            if r.get(c10) is not None: s10.append((d, r[c10]))
        if s2 or s10:
            return {'2Y': series_clean(s2), '10Y': series_clean(s10)}, 'RBNZ B2 zilnic'
    raise RuntimeError('RBNZ B2: coloanele bond 2y/10y negăsite')

def src_stooq(sym2, sym10):
    """Fallback de piață. Stooq limitează IP-urile agresiv («Exceeded the daily hits limit»)."""
    d1 = (date.today() - timedelta(days=90)).strftime('%Y%m%d')
    d2 = date.today().strftime('%Y%m%d')
    def one(sym):
        txt = get(f'https://stooq.com/q/d/l/?s={sym}&d1={d1}&d2={d2}&i=d', tries=2)
        first = txt.split('\n', 1)[0].strip()
        if not first.lower().startswith('date'):
            raise RuntimeError(f'{sym}: răspuns non-CSV ({first[:60]!r})')
        rows = list(csv.DictReader(io.StringIO(txt)))
        s = [(r['Date'], r['Close']) for r in rows if r.get('Close') not in (None, '', 'N/D')]
        if not s: raise RuntimeError(f'{sym}: CSV gol')
        return series_clean(s)
    s2 = s10 = None; errs = []
    for sym in ([sym2] if isinstance(sym2, str) else sym2):
        try: s2 = one(sym); break
        except Exception as e: errs.append(str(e))
    for sym in ([sym10] if isinstance(sym10, str) else sym10):
        try: s10 = one(sym); break
        except Exception as e: errs.append(str(e))
    if not s2 and not s10: raise RuntimeError('Stooq: ' + '; '.join(errs[:2]))
    return {'2Y': s2 or [], '10Y': s10 or []}, 'Stooq'

# ————————————————————————— lanțuri primar→fallback —————————————————————————
CHAINS = {
    'US':  [src_fred, src_treasury],
    'EUR': [src_ecb,  lambda: src_stooq('2ydey.b', '10ydey.b')],
    'GBP': [src_boe_glc, lambda: src_stooq('2yuky.b', '10yuky.b')],
    'CAD': [src_boc],
    'JPY': [src_mof,  lambda: src_stooq('2yjpy.b', '10yjpy.b')],
    'CHF': [src_snb,  lambda: src_stooq('2ychy.b', '10ychy.b'), src_snb_rss],
    'AUD': [src_rba,  lambda: src_stooq('2yauy.b', '10yauy.b')],
    'NZD': [src_rbnz, lambda: src_stooq('2ynzy.b', '10ynzy.b')],
}
PAIRS = (('EURUSD', 'EUR', 'US'), ('GBPUSD', 'GBP', 'US'), ('AUDUSD', 'AUD', 'US'),
         ('NZDUSD', 'NZD', 'US'), ('USDJPY', 'US', 'JPY'), ('USDCHF', 'US', 'CHF'),
         ('USDCAD', 'US', 'CAD'))

def snap(series):
    """[(date,val)] → {date, value, delta_1w} (Δ vs ~DELTA_SESSIONS ședințe)."""
    if not series: return None
    d, v = series[-1]
    ref = series[-(DELTA_SESSIONS + 1)][1] if len(series) > DELTA_SESSIONS else series[0][1]
    return {'date': d, 'value': round(v, 3), 'delta_1w': round(v - ref, 3)}

def main():
    prev = {}
    if OUT.exists():
        try: prev = json.loads(OUT.read_text())
        except Exception: prev = {}
    prev_hist = prev.get('history', {})
    if not prev_hist and prev.get('levels'):
        # migrare de la schema veche (fără history): 2 puncte pseudo-istorice
        # care conservă și valoarea, și delta_1w existente
        for ccy, lv in prev['levels'].items():
            for tenor, s in (lv or {}).items():
                if s and s.get('value') is not None:
                    d0 = (dt.date.fromisoformat(s['date']) - timedelta(days=7)).isoformat()
                    prev_hist.setdefault(ccy, {})[tenor] = [
                        [d0, round(s['value'] - (s.get('delta_1w') or 0), 3)],
                        [s['date'], s['value']]]

    history, status, sources = {}, {}, {}
    for ccy, chain in CHAINS.items():
        fetched, src_name, err = None, None, None
        fresh_lim = (date.today() - timedelta(days=28)).isoformat()
        for fn in chain:
            try:
                fetched, src_name = fn()
                if fetched:   # guard: sursă care întoarce doar date vechi = sursă picată
                    for t in ('2Y', '10Y'):
                        s = fetched.get(t) or []
                        if s and s[-1][0] < fresh_lim:
                            print(f'[YLD]   {ccy} {src_name} {t}: date vechi ({s[-1][0]}) — resping', file=sys.stderr)
                            fetched[t] = []
                if fetched and (fetched.get('2Y') or fetched.get('10Y')): break
                err = err or f'{src_name}: fără date recente'
                fetched = None
            except Exception as e:
                err = f'{type(e).__name__}: {e}'
                print(f'[YLD]   {ccy} {getattr(fn, "__name__", "fallback")}: {err}', file=sys.stderr)
        # merge cu istoricul anterior (last-known-good) — nu pierdem nimic
        history[ccy] = {}
        for tenor in ('2Y', '10Y'):
            old = {d: v for d, v in prev_hist.get(ccy, {}).get(tenor, [])}
            new = dict(fetched.get(tenor) or []) if fetched else {}
            merged = sorted({**old, **new}.items())[-HIST_KEEP:]
            history[ccy][tenor] = merged
        if fetched:
            status[ccy] = 'ok'; sources[ccy] = src_name
        elif history[ccy]['2Y'] or history[ccy]['10Y']:
            last_d = max((s[-1][0] for s in history[ccy].values() if s), default='?')
            status[ccy] = f'stale — ultima valoare {last_d} ({err})'
            sources[ccy] = prev.get('sources', {}).get(ccy, 'cache')
            print(f'[YLD] {ccy}: sursă picată, păstrez last-known-good ({last_d})', file=sys.stderr)
        else:
            status[ccy] = f'INDISPONIBIL: {err}'
            print(f'[YLD] {ccy} complet indisponibil: {err}', file=sys.stderr)

    out = {'updated': date.today().isoformat(), 'status': status, 'sources': sources,
           'levels': {}, 'spreads': {}, 'history': history}
    for ccy, h in history.items():
        lv = {t: snap(s) for t, s in h.items() if s}
        if lv: out['levels'][ccy] = lv

    for pair, a, b in PAIRS:
        for t in ('2Y', '10Y'):
            va, vb = out['levels'].get(a, {}).get(t), out['levels'].get(b, {}).get(t)
            if va and vb:
                out['spreads'].setdefault(pair, {})[t] = {
                    'value': round(va['value'] - vb['value'], 3),
                    'delta_1w': round(va['delta_1w'] - vb['delta_1w'], 3)}

    DATA.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    ok = [k for k, s in status.items() if s == 'ok']
    stale = [k for k, s in status.items() if s.startswith('stale')]
    dead = [k for k in status if k not in ok and k not in stale]
    print(f"[YLD] OK: {', '.join(ok) or '—'}"
          + (f" | STALE(cache): {', '.join(stale)}" if stale else '')
          + (f" | INDISPONIBILE: {', '.join(dead)}" if dead else ''))
    if not ok and not stale:
        sys.exit(1)

if __name__ == '__main__':
    main()
