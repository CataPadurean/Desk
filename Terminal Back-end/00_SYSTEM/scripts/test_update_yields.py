#!/usr/bin/env python3
"""Test offline pentru update_yields.py — fără rețea.
Validează fiecare parser cu mostre în formatul real al surselor
(MOF & SNB: copiate din răspunsurile reale; BoE/RBNZ: xlsx sintetic identic structural)
+ cache-ul last-known-good. Rulare: python3 test_update_yields.py"""
import io, json, sys, tempfile, zipfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_yields as uy

D = [ (date(2026, 6, 22) + timedelta(days=i)).isoformat() for i in (0,1,2,3,7,8,9,10,14,15,16) ]

# ————— mostre în formatul REAL al surselor —————
FRED = 'DATE,DGS2,DGS10\n' + '\n'.join(f'{d},{4.0+i/100},{4.4+i/100}' for i, d in enumerate(D))
ECB = 'KEY,FREQ,TIME_PERIOD,OBS_VALUE\n' + '\n'.join(f'YC.B.U2.EUR,B,{d},{2.5+i/100}' for i, d in enumerate(D))
BOC = json.dumps({'observations': [{'d': d, 'BD.CDN.2YR.DQ.YLD': {'v': str(2.7+i/100)},
                                    'BD.CDN.10YR.DQ.YLD': {'v': str(3.4+i/100)}} for i, d in enumerate(D)]})
MOF = ('Interest Rate (July 2026),,,,,,,,,,,,,,,(Unit : %)\n'
       'Date,1Y,2Y,3Y,4Y,5Y,6Y,7Y,8Y,9Y,10Y,15Y,20Y,25Y,30Y,40Y\n'
       + '\n'.join(f'{d.replace("-","/")},1.1,{1.35+i/100},1.5,1.7,1.9,2.0,2.2,2.4,2.5,{2.70+i/100},3.2,3.6,3.8,3.8,3.7'
                   for i, d in enumerate(D)) + '\n,,,,,,,,,,,,,,,\n"note",,,,,,,,,,,,,,,\n')
SNB = ('﻿"CubeId";"rendoblid"\n"PublishingDate";"2026-07-08 12:00"\n\n"Date";"D0";"Value"\n'
       + '\n'.join(f'"{d}";"2J";"{0.45+i/100}"\n"{d}";"10J0";"{0.95+i/100}"\n"{d}";"E";""' for i, d in enumerate(D)))
RBA = ('F2 CAPITAL MARKET YIELDS,,,\nTitle,AGS 2y,AGS 10y,x\nFrequency,Daily,Daily,x\n'
       'Series ID,FCMYGBAG2D,FCMYGBAG10D,XXX\n'
       + '\n'.join(f'{date.fromisoformat(d).strftime("%d-%b-%Y")},{3.9+i/100},{4.5+i/100},1' for i, d in enumerate(D)))
STOOQ = 'Date,Open,High,Low,Close,Volume\n' + '\n'.join(f'{d},4,4,4,{4.1+i/100},0' for i, d in enumerate(D))

def make_xlsx(sheets):
    """{nume: [ {col: (val, tip)} ]} → bytes xlsx minimal (tip: 'n' numeric, 's' string inline)."""
    NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    RNS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        names = list(sheets)
        z.writestr('[Content_Types].xml',
            f'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            f'<Default Extension="xml" ContentType="application/xml"/>'
            f'<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + ''.join(f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(names)))
            + '</Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml', f'<?xml version="1.0"?><workbook {NS} {RNS}><sheets>'
            + ''.join(f'<sheet name="{n}" sheetId="{i+1}" r:id="rId{i+1}"/>' for i, n in enumerate(names)) + '</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + ''.join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>' for i in range(len(names))) + '</Relationships>')
        for i, n in enumerate(names):
            xml = f'<?xml version="1.0"?><worksheet {NS}><sheetData>'
            for ri, row in enumerate(sheets[n], start=1):
                xml += f'<row r="{ri}">'
                for col, (val, typ) in row.items():
                    if typ == 's':
                        xml += f'<c r="{col}{ri}" t="inlineStr"><is><t>{val}</t></is></c>'
                    else:
                        xml += f'<c r="{col}{ri}"><v>{val}</v></c>'
                xml += '</row>'
            z.writestr(f'xl/worksheets/sheet{i+1}.xml', xml + '</sheetData></worksheet>')
    return buf.getvalue()

def xl_serial(d):
    return (date.fromisoformat(d) - date(1899, 12, 30)).days

# BoE: foaie «4. spot curve», rând-antet cu tenoruri 0.5…12, date pe col A
_tenors = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0]
_cols = [chr(66 + i) for i in range(len(_tenors))]                     # B, C, D, …
BOE_SHEET = [ {'A': ('years:', 's')},
              {'A': ('', 's'), **{c: (t, 'n') for c, t in zip(_cols, _tenors)}} ]
for i, d in enumerate(D):
    BOE_SHEET.append({'A': (xl_serial(d), 'n'),
                      _cols[3]: (3.85 + i/100, 'n'),                   # 2.0Y
                      _cols[12]: (4.55 + i/100, 'n')})                 # 10.0Y
BOE_XLSX = make_xlsx({'1. fwd curve': [{'A': ('x', 's')}], '4. spot curve': BOE_SHEET})
_zbuf = io.BytesIO()
with zipfile.ZipFile(_zbuf, 'w') as _z:
    _z.writestr('GLC Nominal daily data current month.xlsx', BOE_XLSX)
    _z.writestr('GLC Real daily data current month.xlsx', b'nu conteaza')
BOE_ZIP = _zbuf.getvalue()

# RBNZ: antet pe 2 rânduri — grupuri («Secondary market govt bond yields» / «Interest rate swap rates»)
RBNZ_SHEET = [
    {'A': ('Series Id', 's'), 'B': ('INM.MG.O.01', 's'), 'C': ('INM.MG.O.02', 's'), 'D': ('INM.MG.O.10', 's'), 'E': ('INM.MS.O.02', 's')},
    {'A': ('', 's'), 'B': ('Secondary market govt bond yields', 's'), 'E': ('Interest rate swap rates', 's')},
    {'A': ('Date', 's'), 'B': ('1 year', 's'), 'C': ('2 year', 's'), 'D': ('10 years', 's'), 'E': ('2 year', 's')},
]
for i, d in enumerate(D):
    RBNZ_SHEET.append({'A': (xl_serial(d), 'n'), 'B': (3.2, 'n'),
                       'C': (3.30 + i/100, 'n'), 'D': (4.10 + i/100, 'n'), 'E': (9.99, 'n')})
RBNZ_XLSX = make_xlsx({'README': [{'A': ('info', 's')}], 'Data': RBNZ_SHEET})

ROUTES = [('fred.stlouisfed.org', FRED), ('data-api.ecb.europa.eu', ECB), ('bankofcanada.ca', BOC),
          ('mof.go.jp', MOF), ('data.snb.ch', SNB), ('rba.gov.au', RBA),
          ('bankofengland.co.uk', BOE_ZIP), ('rbnz.govt.nz', RBNZ_XLSX), ('stooq.com', STOOQ)]

def fake_get(url, tries=3, binary=False, referer=None):
    for frag, resp in ROUTES:
        if frag in url:
            return resp if isinstance(resp, bytes) else resp
    raise RuntimeError(f'test: URL neacoperit {url}')

def offline_get(url, **kw):
    raise OSError('Tunnel connection failed: 403 Forbidden (simulare sandbox)')

def main():
    fails = []
    def check(name, cond, extra=''):
        print(('  ✔' if cond else '  ✘ FAIL'), name, extra)
        if not cond: fails.append(name)

    tmp = Path(tempfile.mkdtemp())
    uy.DATA, uy.OUT = tmp, tmp / 'yields_latest.json'
    uy.get = fake_get

    print('— parseri individuali —')
    for ccy, chain in uy.CHAINS.items():
        data, src = chain[0]()
        s2, s10 = data.get('2Y'), data.get('10Y')
        check(f'{ccy} [{src}]', bool(s2) and bool(s10),
              f"2Y={s2[-1] if s2 else None} 10Y={s10[-1] if s10 else None}")
    d, s = uy.src_stooq('2yuky.b', '10yuky.b')
    check('Stooq fallback', bool(d['2Y']) and bool(d['10Y']))

    print('— rulare completă (toate sursele ok) —')
    uy.main()
    j1 = json.loads(uy.OUT.read_text())
    check('8/8 monede în levels', len(j1['levels']) == 8, str(sorted(j1['levels'])))
    check('7/7 spread-uri', len(j1['spreads']) == 7, str(sorted(j1['spreads'])))
    check('toate ok', all(v == 'ok' for v in j1['status'].values()), str(j1['status']))
    check('delta_1w numeric', all(isinstance(j1['levels'][c][t]['delta_1w'], float) or isinstance(j1['levels'][c][t]['delta_1w'], int)
                                  for c in j1['levels'] for t in j1['levels'][c]))
    eu = j1['spreads']['EURUSD']['2Y']['value']
    exp = round(j1['levels']['EUR']['2Y']['value'] - j1['levels']['US']['2Y']['value'], 3)
    check('spread EURUSD = EUR−US', eu == exp, f'{eu} vs {exp}')

    print('— rulare fără rețea (cache last-known-good) —')
    uy.get = offline_get
    uy.main()
    j2 = json.loads(uy.OUT.read_text())
    check('levels păstrate din cache', j2['levels'] == j1['levels'])
    check('spreads păstrate', j2['spreads'] == j1['spreads'])
    check('status = stale', all(v.startswith('stale') for v in j2['status'].values()), str(list(j2['status'].values())[:2]))

    print('— degradare parțială (doar SNB pică) —')
    uy.get = lambda url, **kw: fake_get(url, **kw) if 'snb' not in url and 'stooq' not in url else (_ for _ in ()).throw(OSError('403'))
    uy.main()
    j3 = json.loads(uy.OUT.read_text())
    check('CHF stale, restul ok', j3['status']['CHF'].startswith('stale') and j3['status']['US'] == 'ok', j3['status']['CHF'])
    check('USDCHF spread încă prezent', '2Y' in j3['spreads'].get('USDCHF', {}))

    print()
    if fails:
        print(f'✘ {len(fails)} teste picate: {fails}'); sys.exit(1)
    print('✔ Toate testele au trecut.')

if __name__ == '__main__':
    main()
