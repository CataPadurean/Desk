#!/usr/bin/env python3
"""POLICY vs. MARKET PRICING — criteriul 1, cuantificat în puncte de bază.

„Piața e prea dovish" e opinie. „Piața prețuiește −38bp până la orizontul de 2 ani,
desk-ul vede −10bp, deci edge +28bp pro-monedă" e research. Diferența dintre cele două
formulări e diferența dintre un comentariu și un desk.

MĂSURA FOLOSITĂ (calculabilă din date gratuite, fără terminal plătit):
    implied_bp = (randament 2Y − dobânda de politică monetară) × 100
Randamentul la 2 ani e, în esență, media așteptată a dobânzii overnight pe doi ani plus
o primă mică de termen. Diferența față de dobânda curentă = cât de multă mișcare de
politică monetară e deja în preț, cumulat, pe orizontul respectiv. E aproximarea standard
de shorthand a unui desk de rate când nu are curba OIS la îndemână.

LIMITE, scrise pe față (onestitate înaintea convingerii):
  · include primă de termen — supraestimează ușor înăsprirea prețuită;
  · e cumulat pe 2 ani, nu pe ședința următoare. Pentru ședința imediată se folosesc
    probabilitățile publice (FedWatch etc.), scrise manual în `next_meeting`;
  · dacă 2Y lipsește (feed mort), moneda apare „indisponibil", nu cu zero.

`view_bp` (ce vede desk-ul) e JUDECATĂ — se scrie în directions.json → pricing[CCY].view_bp,
împreună cu argumentul. Edge = view − market. Semnul edge-ului dă direcția:
un desk mai hawkish decât piața (edge pozitiv) e PRO-monedă.
"""
from __future__ import annotations

CCY_ORDER = ('USD', 'EUR', 'GBP', 'CAD', 'JPY', 'CHF', 'AUD', 'NZD')
YLD_KEY = {'USD': 'US'}          # restul monedelor au aceeași cheie în yields_latest.json

# Pragul de la care o divergență e „edge", nu zgomot. Nu e ales estetic: randamentul 2Y
# conține o primă de termen de ordinul a 20-30bp, care umflă sistematic „cât e prețuit".
# Sub 25bp, diferența dintre market și view nu se distinge de prima de termen.
EDGE_MIN_BP = 25


def _policy_rate(directions: dict, ccy: str):
    """Dobânda de politică monetară, din indicators (criteriul 3) — ex. „3,75%" → 3.75."""
    raw = ((directions.get('indicators', {}) or {}).get(ccy) or {}).get('rate')
    if raw is None:
        return None
    try:
        return float(str(raw).replace('%', '').replace(',', '.').strip())
    except ValueError:
        return None


def build_pricing(yields: dict | None, directions: dict) -> dict:
    """Compune blocul `pricing` — partea numerică e calculată, narativul vine din directions.json."""
    lv = (yields or {}).get('levels', {}) or {}
    narrative = directions.get('pricing', {}) or {}
    out = {}

    for ccy in CCY_ORDER:
        n = dict(narrative.get(ccy) or {})
        pol = _policy_rate(directions, ccy)
        node = lv.get(YLD_KEY.get(ccy, ccy)) or {}
        y2 = (node.get('2Y') or {}).get('value')
        d2 = (node.get('2Y') or {}).get('delta_1w')
        tenor = '2Y'
        if y2 is None:                       # fallback onest, marcat ca atare
            y2 = (node.get('10Y') or {}).get('value')
            d2 = (node.get('10Y') or {}).get('delta_1w')
            tenor = '10Y'

        market_bp = None if (y2 is None or pol is None) else round((float(y2) - pol) * 100)
        delta_bp = None if d2 is None else round(float(d2) * 100)
        view_bp = n.get('view_bp')
        edge_bp = None if (market_bp is None or view_bp is None) else int(view_bp) - market_bp

        if edge_bp is None:
            direction = n.get('dir') or 'INDISPONIBIL'
        elif abs(edge_bp) < EDGE_MIN_BP:
            direction = 'ALINIAT'
        else:
            direction = ('PRO-' if edge_bp > 0 else 'ANTI-') + ccy

        n.update({
            'policy_rate': pol, 'yield': y2, 'tenor': tenor,
            'market_bp': market_bp, 'market_delta_bp': delta_bp,
            'view_bp': view_bp, 'edge_bp': edge_bp,
            'dir': direction,
            'method': f'({tenor} {y2} − politică {pol}) × 100' if market_bp is not None else 'randament indisponibil',
        })
        out[ccy] = n

    # Citirea CROSS-SECȚIONALĂ, mai curată decât cea absolută: prima de termen e aproximativ
    # aceeași în toate economiile dezvoltate, deci se anulează la comparație. „Cât e prețuit
    # aici față de restul grupului" e întrebarea care contează pentru cine tranzacționează perechi.
    vals = [v['market_bp'] for v in out.values() if v['market_bp'] is not None]
    avg = (sum(vals) / len(vals)) if vals else None
    for v in out.values():
        v['group_avg_bp'] = None if avg is None else round(avg)
        v['rel_bp'] = None if (avg is None or v['market_bp'] is None) else round(v['market_bp'] - avg)
    return out


if __name__ == '__main__':
    import json
    from pathlib import Path
    D = Path(__file__).resolve().parent.parent / 'data'
    y = json.loads((D / 'yields_latest.json').read_text())
    d = json.loads((D / 'directions.json').read_text())
    pr = build_pricing(y, d)
    print('%-5s %8s %8s %10s %8s %8s   %s' % ('', 'POLICY', '2Y', 'MARKET', 'VIEW', 'EDGE', 'DIRECȚIE'))
    for c in CCY_ORDER:
        p = pr[c]
        f = lambda v, s='': '—' if v is None else f'{v:+d}{s}' if isinstance(v, int) else f'{v}{s}'
        print('%-5s %8s %8s %10s %8s %8s   %s' % (
            c,
            '—' if p['policy_rate'] is None else f"{p['policy_rate']:.2f}%",
            '—' if p['yield'] is None else f"{p['yield']:.3f}",
            f(p['market_bp'], 'bp'), f(p['view_bp'], 'bp'), f(p['edge_bp'], 'bp'), p['dir']))
