"""Estrazione testo completo + rilevamento paywall (soft)."""
import re, threading, trafilatura

BUA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8,fr;q=0.7,de;q=0.6,nl;q=0.5,es;q=0.4",
}
# Solo URL chiaramente riservati agli abbonati
URLPAY = re.compile(
    r"corriere\.it/.*/(abbonati|_premium)(/|$)|/abonnement/offres",
    re.I,
)
FREE = re.compile(r'"isAccessibleForFree"\s*:\s*"?(true|false)', re.I)
MARK = re.compile(
    r"riservato agli abbonati|articolo riservato|Per continuare a leggere|riservato ai nostri abbonati|"
    r"réservé aux abonnés|article réservé|Il vous reste \d+|Subscribe to continue|subscribe to read|"
    r"This article is for subscribers|exklusiv für Abonnent|alleen voor abonnees|Kun for abonnenter|"
    r"exclusivo para suscriptores|exclusivo para assinantes|premium-article-paywall|is-premium-article",
    re.I,
)
MINLEN = 400
# Domini che spesso richiedono un browser reale (Cloudflare / privacy gate)
BROWSER_HINT = ("sofoot.com", "volkskrant.nl", "derstandard.at")
_BLOCK = re.compile(r"Access Denied|Just a moment|enable JS|Verifying your device|Privacy Gate|cf-browser-verification|Attention Required", re.I)

_lock = threading.Lock()
IMG = {}
_OG = re.compile(r"""<meta[^>]+(?:property|name)=["'](?:og:image|og:image:url|twitter:image)["'][^>]*content=["']([^"']+)|<meta[^>]+content=["']([^"']+)["'][^>]*(?:property|name)=["'](?:og:image|twitter:image)["']""", re.I)

def og_image(html):
    import html as H
    m = _OG.search(html[:400000] if html else "")
    u = H.unescape((m.group(1) or m.group(2)).strip()) if m else ""
    return u if u.startswith("http") else ""
_pw = {"browser": None, "page": None, "n": 0, "max": 80}


def _curl(url, timeout=25):
    from curl_cffi import requests as cr
    r = cr.get(url, impersonate="chrome131", timeout=timeout, headers=BUA, allow_redirects=True)
    return r.status_code, r.text or ""


def _need_browser(url, status, html):
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
    if any(h in host for h in BROWSER_HINT):
        return True
    if status in (401, 402, 403, 429):
        return True
    if status == 200 and (len(html) < 8000 and _BLOCK.search(html[:4000])):
        return True
    if status == 200 and "DPG Media Privacy Gate" in html:
        return True
    return False


def _accept_cookies(page):
    sels = [
        "button:has-text('Alles accepteren')",
        "button:has-text('Accepteren')",
        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
        "button:has-text('J'accepte')",
        "button:has-text('Accepter')",
        "button:has-text('Agree')",
        "button:has-text('I agree')",
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Einverstanden')",
        "button:has-text('Zustimmen')",
        "button:has-text('Akzeptieren')",
        "#didomi-notice-agree-button",
        "button[id*='accept' i]",
    ]
    for sel in sels:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(timeout=400):
                b.click(timeout=1200)
                page.wait_for_timeout(1200)
                return
        except Exception:
            pass
    for fr in page.frames:
        for sel in sels:
            try:
                b = fr.locator(sel).first
                if b.count() and b.is_visible(timeout=300):
                    b.click(timeout=1000)
                    page.wait_for_timeout(1000)
                    return
            except Exception:
                pass


def _browser_impl(url, timeout=45):
    """Fetch via headless Chromium: gira SEMPRE nel thread dedicato _BEX."""
    from playwright.sync_api import sync_playwright
    with _lock:
        if _pw["n"] >= _pw["max"]:
            return 0, ""
        try:
            if _pw["browser"] is None:
                pw = sync_playwright().start()
                try:
                    browser = pw.chromium.launch(headless=True, channel="chrome")
                except Exception:
                    browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(
                    locale="it-IT",
                    user_agent=BUA["User-Agent"],
                    extra_http_headers={"Accept-Language": BUA["Accept-Language"]},
                )
                page = ctx.new_page()
                page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
                _pw["browser"] = browser
                _pw["page"] = page
                _pw["pw"] = pw
            page = _pw["page"]
            page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            page.wait_for_timeout(2000)
            _accept_cookies(page)
            page.wait_for_timeout(800)
            html = page.content()
            _pw["n"] += 1
            return 200, html
        except Exception as x:
            return 0, str(x)[:80]


def _extract(url, html):
    t = trafilatura.extract(
        html, url=url, include_comments=False, include_tables=False,
        favor_precision=True, deduplicate=True,
    ) or ""
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def get_text(url, timeout=20):
    """-> (stato, testo). stato: ok | pay | short | err

    Soft paywall: se estraiamo un corpo sufficiente senza marker espliciti
    nel testo, lo teniamo anche se lo schema dice isAccessibleForFree:false.
    """
    if URLPAY.search(url):
        return "pay", ""
    if "lequipe.fr" in url:
        r = _lequipe(url)
        if r: return r
    status, html = 0, ""
    err = ""
    try:
        status, html = _curl(url, timeout=timeout)
    except Exception as x:
        err = str(x)[:80]
    if (not html or _need_browser(url, status, html)) and _pw["n"] < _pw["max"]:
        st2, h2 = _browser(url)
        if h2 and len(h2) > len(html or ""):
            status, html = (st2 or 200), h2
            err = ""
    if not html:
        if status in (401, 402):
            return "pay", ""
        return "err", err or f"http {status}"
    # Bot-wall / access denied pages
    if len(html) < 8000 and _BLOCK.search(html[:4000]) and "trafilatura" not in html:
        t0 = _extract(url, html)
        if len(t0) < MINLEN:
            return "err", "blocked"
    IMG[url] = og_image(html)
    t = _extract(url, html)
    if t and MARK.search(t[-500:]):
        return "pay", ""
    if len(t) >= MINLEN:
        return "ok", t[:40000]
    # Corpo corto: paywall solo se marker di pagina o schema false CON poco testo
    fr = [m.group(1).lower() for m in FREE.finditer(html)]
    if MARK.search(html) and len(t) < MINLEN:
        return "pay", ""
    if "false" in fr and len(t) < MINLEN // 2:
        return "pay", ""
    if not t:
        return "err", "empty"
    return "short", t


from concurrent.futures import ThreadPoolExecutor as _TPE
_BEX = _TPE(max_workers=1)  # playwright sync non è thread-safe: un solo thread proprietario


def _browser(url, timeout=45):
    if _pw["n"] >= _pw["max"]:
        return 0, ""
    try:
        return _BEX.submit(_browser_impl, url, timeout).result(timeout=timeout + 30)
    except Exception as x:
        return 0, str(x)[:80]


def _close_impl():
    with _lock:
        try:
            if _pw.get("browser"):
                _pw["browser"].close()
            if _pw.get("pw"):
                _pw["pw"].stop()
        except Exception:
            pass
        _pw["browser"] = _pw["page"] = None
        _pw["pw"] = None

def _lequipe(url):
    """L'Équipe: API pubblica dell'app (dwh.lequipe.fr). Solo is_premium=false."""
    import html as H
    m = re.search(r"lequipe\.fr/.+/(\d{5,})(?:[#?].*)?$", url)
    if not m: return None
    from curl_cffi import requests as cr
    try:
        j = cr.get(f"https://dwh.lequipe.fr/api/edito/news/{m.group(1)}", impersonate="chrome131", timeout=20).json()
    except Exception as x:
        return "err", str(x)[:80]
    s = __import__("json").dumps(j)
    if re.search(r'"is_premium"\s*:\s*true', s): return "pay", ""
    paras = []
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("paragraphs"), list):
                for pp in o["paragraphs"]:
                    c = pp.get("content") if isinstance(pp, dict) else None
                    if c: paras.append(re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", c))).strip())
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(j)
    t = "\n\n".join(dict.fromkeys(p for p in paras if p))
    if len(t) >= MINLEN: return "ok", t[:40000]
    return ("short", t) if t else ("err", "empty")


def close_browser():
    try:
        _BEX.submit(_close_impl).result(timeout=30)
    except Exception:
        pass
