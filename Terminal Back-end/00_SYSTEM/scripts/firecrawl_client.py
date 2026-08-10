#!/usr/bin/env python3
"""Client minimal pentru Firecrawl (api.firecrawl.dev).

Rol în sistem: sursă de FALLBACK pentru pagini blocate la fetch direct (WAF/TLS
fingerprint — ex. RBNZ) sau pentru calendarul economic (TradingEconomics), NU
înlocuitor pentru sursele oficiale care deja funcționează (FRED/ECB/BoC/MOF/RBA/
CFTC) — acelea rămân gratuite, stabile și primele în lanț.

Cheia se citește STRICT din variabila de mediu FIRECRAWL_API_KEY — niciodată din
cod sau din fișierele de date. Local: `export FIRECRAWL_API_KEY=fc-...` înainte de
rulare. În GitHub Actions: secret de repo cu același nume, injectat ca env la pasul
care rulează scripturile (vezi .github/workflows/update.yml).

Notă onestă (10.08.2026): sandbox-ul Claude nu are acces de rețea la api.firecrawl.dev
(alături de multe alte domenii — doar github.com e pe allowlist), deci funcțiile de
mai jos NU au putut fi testate live din acea sesiune. Se validează fie local pe Mac
(`python3 -c "from firecrawl_client import scrape_html; print(len(scrape_html('https://example.com')))"`),
fie printr-o rulare manuală („Run workflow") din GitHub Actions, care are acces
normal la internet.

Doar stdlib — nicio dependență nouă de instalat.
"""
import json
import os
import urllib.error
import urllib.request

API_BASE = 'https://api.firecrawl.dev/v1'


class FirecrawlError(RuntimeError):
    pass


def _key():
    k = os.environ.get('FIRECRAWL_API_KEY', '').strip()
    if not k:
        raise FirecrawlError('FIRECRAWL_API_KEY lipsește din mediu — sursa se sare, nu se inventează')
    return k


def _post(path, payload, timeout=75):
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'{API_BASE}/{path}', data=body, method='POST',
        headers={'Authorization': f'Bearer {_key()}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:300]
        raise FirecrawlError(f'HTTP {e.code}: {detail}') from e
    except urllib.error.URLError as e:
        raise FirecrawlError(f'conexiune eșuată: {e.reason}') from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise FirecrawlError(f'răspuns non-JSON: {raw[:200]!r}') from e
    if not data.get('success'):
        raise FirecrawlError(f'scrape eșuat: {data.get("error", data)}')
    return data.get('data') or {}


def scrape(url, formats=('markdown',), timeout=75):
    """Întoarce dict cu cheile cerute în `formats` (markdown/html/rawHtml/links).
    1 credit per pagină pe planul de bază (fără JSON/Enhanced mode)."""
    return _post('scrape', {'url': url, 'formats': list(formats)}, timeout=timeout)


def scrape_markdown(url, timeout=75):
    data = scrape(url, formats=('markdown',), timeout=timeout)
    md = data.get('markdown', '')
    if not md:
        raise FirecrawlError(f'{url}: răspuns fără markdown')
    return md


def scrape_html(url, timeout=75):
    """rawHtml, ca să poată fi reutilizate parserele regex existente (ex. tabelul RBNZ),
    scrise inițial pentru HTML brut, nu pentru markdown curățat."""
    data = scrape(url, formats=('rawHtml',), timeout=timeout)
    html = data.get('rawHtml') or data.get('html', '')
    if not html:
        raise FirecrawlError(f'{url}: răspuns fără html')
    return html


if __name__ == '__main__':
    import sys
    u = sys.argv[1] if len(sys.argv) > 1 else 'https://example.com'
    print(scrape_markdown(u)[:500])
