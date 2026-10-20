"""Ordine e rilievo delle notizie come sulla homepage originale di ogni testata."""
import re
from urllib.parse import urljoin, urlsplit

def norm(u):
    try:
        s = urlsplit(u.strip())
    except Exception:
        return ""
    h = s.netloc.lower()
    if h.startswith("www."): h = h[4:]
    if h == "bbc.co.uk": h = "bbc.com"
    p = re.sub(r"/+$", "", s.path)
    return h + p

_HREF = re.compile(r"""<a\b[^>]*?\bhref\s*=\s*["']([^"'#]+)""", re.I)

def links(html, base):
    out, seen = [], set()
    for m in _HREF.finditer(html):
        n = norm(urljoin(base, m.group(1)))
        if n and n not in seen:
            seen.add(n); out.append(n)
    return out

LANG = [(".fr", "fr-FR,fr;q=0.9"), (".at", "de-AT,de;q=0.9"), (".de", "de-DE,de;q=0.9"), (".es", "es-ES,es;q=0.9"),
        (".com.ar", "es-AR,es;q=0.9"), ("elpais.com", "es-ES,es;q=0.9"), ("as.com", "es-ES,es;q=0.9"), ("marca.com", "es-ES,es;q=0.9"),
        ("mundodeportivo.com", "es-ES,es;q=0.9"), ("relevo.com", "es-ES,es;q=0.9"), (".pt", "pt-PT,pt;q=0.9"), (".br", "pt-BR,pt;q=0.9"),
        ("globo.com", "pt-BR,pt;q=0.9"), (".nl", "nl-NL,nl;q=0.9"), (".dk", "da-DK,da;q=0.9"), (".tr", "tr-TR,tr;q=0.9"), (".it", "it-IT,it;q=0.9")]

def fetch_home(url, browser_ok=True):
    from fulltext import _need_browser, _browser, BUA
    from curl_cffi import requests as cr
    host = urlsplit(url).netloc.lower()
    lang = next((l for k, l in LANG if host.endswith(k)), "en-GB,en;q=0.9")
    st, h = 0, ""
    try:
        r = cr.get(url, impersonate="chrome131", timeout=20, headers={**BUA, "Accept-Language": lang})
        st, h = r.status_code, r.text or ""
    except Exception:
        pass
    if (st != 200 or _need_browser(url, st, h) or len(h) < 5000) and browser_ok:
        st2, h2 = _browser(url)
        if h2 and len(h2) > len(h): h = h2
    return h

def ranks(pages, browser_ok=True):
    """pages: lista di URL -> {url_normalizzato: posizione}"""
    R, n = {}, 0
    for p in pages:
        try:
            h = fetch_home(p, browser_ok)
        except Exception:
            h = ""
        for l in links(h, p):
            if l not in R: R[l] = n; n += 1
    return R

def order(items, R):
    """Ordina come la homepage; quelli non presenti dopo, in ordine di data. Ritorna (lista, n_trovati)."""
    hit = [i for i in items if norm(i["l"]) in R]
    hit.sort(key=lambda i: R[norm(i["l"])])
    rest = [i for i in items if norm(i["l"]) not in R]
    for k, i in enumerate(hit): i["rk"] = k
    for i in rest: i["rk"] = None
    return hit + rest, len(hit)
