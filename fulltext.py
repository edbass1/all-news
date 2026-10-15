"""Estrazione testo completo + rilevamento paywall."""
import re, requests, trafilatura
BUA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36", "Accept-Language": "it,en;q=0.8"}
# Solo URL chiaramente premium (non generici corriere.it)
URLPAY = re.compile(r"corriere\.it/.*/(abbonati|_premium)(/|$)|/premium/|nytimes\.com/athletic|/exklusiv", re.I)
FREE = re.compile(r'"isAccessibleForFree"\s*:\s*"?(true|false)', re.I)
MARK = re.compile(r"riservato agli abbonati|articolo riservato|Per continuare a leggere|riservato ai nostri abbonati|réservé aux abonnés|article réservé|Il vous reste \d+|Subscribe to continue|subscribe to read|This article is for subscribers|exklusiv für Abonnent|alleen voor abonnees|Kun for abonnenter|exclusivo para suscriptores|exclusivo para assinantes|premium-article-paywall|is-premium-article", re.I)
MINLEN = 900

def get_text(url, timeout=20):
    """-> (stato, testo). stato: ok | pay | short | err
    Soft paywall: se trafilatura estrae un articolo completo (>= MINLEN)
    senza marker espliciti nel testo, lo teniamo anche se lo schema JSON-LD
    dice isAccessibleForFree:false (falso positivo tipico di Corriere).
    """
    if URLPAY.search(url): return "pay", ""
    try:
        r = requests.get(url, headers=BUA, timeout=timeout)
        if r.status_code in (401, 402): return "pay", ""
        r.raise_for_status(); h = r.text
    except Exception as x:
        return "err", str(x)[:80]
    t = trafilatura.extract(h, url=url, include_comments=False, include_tables=False, favor_precision=True, deduplicate=True) or ""
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    # Marker espliciti nel corpo estratto → paywall duro
    if t and MARK.search(t[-500:]): return "pay", ""
    if len(t) >= MINLEN:
        return "ok", t[:40000]
    # Corpo corto/assente: controlla schema e marker di pagina
    fr = [m.group(1).lower() for m in FREE.finditer(h)]
    if "false" in fr or MARK.search(h): return "pay", ""
    if not t: return "err", "empty"
    return "short", t
