#!/usr/bin/env python3
"""ALL NEWS - aggregatore gratuito: legge i feed RSS, traduce titoli e sommari, genera docs/."""
import json, html, os, re, shutil, datetime, hashlib, calendar
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo
import feedparser, requests, socket
socket.setdefaulttimeout(30)

e = html.escape
TZ = ZoneInfo("Europe/Rome")
NOW = datetime.datetime.now(TZ)
MAXAGE = datetime.timedelta(days=3)
MAXN = 60
UA = {"User-Agent": "Mozilla/5.0"}
TABS = [("italia", "Italia"), ("mondo", "Mondo"), ("sport", "Sport"), ("torino", "Torino")]
OUT = json.load(open("data/outlets.json"))
TRF = "data/translations.json"
TR = json.load(open(TRF)) if os.path.exists(TRF) else {}
M = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
USSPORT = re.compile(r"\b(NFL|NBA|WNBA|MLB|NHL|MLS|NCAA|college football|college basketball|Super ?Bowl|World Series|Stanley Cup|touchdown|quarterback|Yankees|Dodgers|Lakers|Celtics|Knicks|Warriors|Chiefs|Cowboys|Patriots|Eagles|49ers|Packers|Steelers|Raptors|fantasy football|March Madness|playoffs NBA|béisbol|beisebol|hockey sobre hielo)\b", re.I)
LIVE = re.compile(r"(\blive\b|\bdiretta\b|en directo|en vivo|ao vivo|\bin direct\b|en direct|\bliveticker\b|minute[- ]by[- ]minute|\bcanlı\b|as it happened)", re.I)

def clean(t, n=250):
    t = re.sub(r"<!\[CDATA\[|\]\]>", "", t or "")
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", html.unescape(t)).strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"

PT = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}
def ptdate(s):
    m = re.search(r"(\d{1,2}) (\w{3}) (\d{4}) (\d\d):(\d\d):?(\d\d)? ([+-]\d{4})", s or "")
    if not m or m.group(2).lower() not in PT: return None
    z = int(m.group(7)); off = datetime.timedelta(hours=abs(z)//100, minutes=abs(z)%100) * (1 if z > 0 else -1)
    return datetime.datetime(int(m.group(3)), PT[m.group(2).lower()], int(m.group(1)), int(m.group(4)), int(m.group(5)), tzinfo=datetime.timezone(off)).astimezone(TZ)

def fetch(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        r.raise_for_status()
        f = feedparser.parse(r.content)
    except Exception as x:
        print("ERR", url, x); return []
    items = []
    for it in f.entries:
        tm = it.get("published_parsed") or it.get("updated_parsed")
        if tm: dt = datetime.datetime.fromtimestamp(calendar.timegm(tm), datetime.timezone.utc).astimezone(TZ)
        else:
            dt = ptdate(it.get("published", ""))
            if not dt: continue
        if dt > NOW + datetime.timedelta(hours=2) or NOW - dt > MAXAGE: continue
        t = clean(it.get("title", ""), 300); l = it.get("link", "")
        if not t or not l.startswith("http"): continue
        items.append({"t": t, "s": clean(it.get("summary", "") or it.get("description", "")), "l": l, "d": dt})
    print(f"{len(items):4d} {url}")
    return items

# ---------- scraping dai siti ufficiali (per testate senza feed RSS) ----------
from bs4 import BeautifulSoup
from urllib.parse import urljoin
SCF = "data/scrape_cache.json"
SC = json.load(open(SCF)) if os.path.exists(SCF) else {}
BUA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36", "Accept-Language": "it,en;q=0.8"}

def pdate(v):
    try:
        dt = datetime.datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
        return (dt if dt.tzinfo else dt.replace(tzinfo=TZ)).astimezone(TZ)
    except Exception: return None

def get(url):
    r = requests.get(url, headers=BUA, timeout=25); r.raise_for_status(); return r

def from_sitemap(sp):
    out = []
    xml = get(sp["sitemap"]).content.decode("utf-8", "replace")
    for blk in re.findall(r"<url>(.*?)</url>", xml, re.S):
        g = lambda t: (re.search(rf"<{t}>(.*?)</{t}>", blk, re.S) or [None, ""])[1]
        l = clean(g("loc")); t = clean(g("news:title"), 300)
        if not l or (sp.get("match") and not re.search(sp["match"], l)) or (sp.get("exclude") and re.search(sp["exclude"], l)): continue
        out.append({"t": t, "s": "", "l": l, "d": pdate(clean(g("news:publication_date") or g("lastmod")))})
    return out

def from_page(sp):
    out, seen = [], set()
    soup = BeautifulSoup(get(sp["page"]).content, "html.parser")
    for a in soup.find_all("a", href=True):
        l = urljoin(sp["page"], a["href"]).split("#")[0]
        if not re.search(sp["match"], l) or (sp.get("exclude") and re.search(sp["exclude"], l)) or l in seen: continue
        h = a.find(["h1", "h2", "h3", "h4"]) or (a.parent.find(["h1", "h2", "h3", "h4"]) if a.parent else None)
        t = clean(h.get_text(" ") if h and len(h.get_text(strip=True)) > 20 else a.get_text(" "), 300)
        if len(t) < 25: continue
        seen.add(l); out.append({"t": t, "s": "", "l": l, "d": None})
    return out

def meta(url):
    """Sommario e data dall'articolo (og:description, article:published_time, JSON-LD). In cache."""
    if url in SC: return SC[url]
    s, d, t = "", None, ""
    try:
        soup = BeautifulSoup(get(url).content, "html.parser")
        m = lambda *ks: next((x["content"] for k in ks for x in soup.find_all("meta", attrs={"property": k}) + soup.find_all("meta", attrs={"name": k}) if x.get("content")), "")
        s = clean(m("og:description", "description", "twitter:description"))
        t = clean(m("og:title", "twitter:title"), 300)
        d = m("article:published_time", "pubdate", "publish-date", "date")
        if not d:
            mm = re.search(r'"datePublished"\s*:\s*"([^"]+)"', str(soup)); d = mm.group(1) if mm else ""
    except Exception as x:
        print("meta ERR", url[:80], str(x)[:60])
    dd = pdate(d) if d else None
    SC[url] = [s, (dd or NOW).isoformat(), t]  # se manca la data uso il primo momento in cui la vedo
    return SC[url]

def scrape(specs):
    res = []
    for sp in specs:
        try:
            L = from_sitemap(sp) if "sitemap" in sp else from_page(sp)
            print(f"{len(L):4d} [scrape] {sp.get('sitemap') or sp.get('page')}")
            res += L
        except Exception as x:
            print("ERR scrape", sp.get("sitemap") or sp.get("page"), str(x)[:80])
    seen, uniq = set(), []
    for i in res:
        k = i["l"].split("?")[0]
        if k not in seen: seen.add(k); i["l"] = k if "?" in i["l"] and "corriere" in k else i["l"]; uniq.append(i)
    uniq = [i for i in uniq if not i["d"] or NOW - i["d"] <= MAXAGE][:MAXN]
    with ThreadPoolExecutor(6) as ex:
        for i, (s, d, t) in zip(uniq, ex.map(lambda i: meta(i["l"]), uniq)):
            i["s"] = s; i["d"] = i["d"] or pdate(d) or NOW
            if not i["t"]: i["t"] = t
    return [i for i in uniq if i["t"] and NOW - i["d"] <= MAXAGE and i["d"] <= NOW + datetime.timedelta(hours=2)]

def gather(urls, sport, specs=()):
    seen, res = set(), []
    lists = list(ThreadPoolExecutor(4).map(fetch, urls)) + ([scrape(specs)] if specs else [])
    if True:
        for L in lists:
            for i in L:
                k = i["l"].split("?")[0]
                if k in seen or i["t"].lower() in seen: continue
                if sport and USSPORT.search(i["t"] + " " + i["s"]): continue
                seen |= {k, i["t"].lower()}; res.append(i)
    return sorted(res, key=lambda i: i["d"], reverse=True)[:MAXN]

def key(s): return hashlib.sha1(s.encode()).hexdigest()[:16]
from deep_translator import GoogleTranslator
import time
DEADLINE = time.time() + 12 * 60  # massimo 12 minuti di traduzioni per esecuzione
FAILS = [0]
def tr_batch(L):
    """Traduce un gruppo di stringhe: endpoint gratuito Google (più testi per richiesta), poi deep-translator."""
    if time.time() > DEADLINE or FAILS[0] >= 4: return [None] * len(L)
    try:
        r = requests.post("https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=it",
                          data=[("q", x) for x in L], headers=UA, timeout=30)
        r.raise_for_status(); j = r.json()
        out = [(x[0] if isinstance(x, list) else x) for x in j]
        if len(out) == len(L): FAILS[0] = 0; return [html.unescape(x) if x else None for x in out]
    except Exception as x:
        print("TR fail (gtx)", str(x)[:80], flush=True)
    try:
        r = GoogleTranslator(source="auto", target="it").translate("\n".join(L))
        out = [x.strip() for x in (r or "").split("\n")]
        if len(out) == len(L): FAILS[0] = 0; return out
    except Exception as x:
        print("TR fail (deep)", str(x)[:80], flush=True)
    FAILS[0] += 1; time.sleep(5)
    return [None] * len(L)

def translate(items_all):
    todo = sorted({s for s in items_all if s and key(s) not in TR})
    print("da tradurre:", len(todo))
    batches, cur, n = [], [], 0
    for s in todo:
        if cur and (n + len(s) > 4000 or len(cur) >= 40): batches.append(cur); cur, n = [], 0
        cur.append(s); n += len(s) + 1
    if cur: batches.append(cur)
    ok = 0
    for bt in batches:
        if time.time() > DEADLINE or FAILS[0] >= 4: print("traduzioni interrotte, riprendo al prossimo giro"); break
        for s, r in zip(bt, tr_batch(bt)):
            if r: TR[key(s)] = r; ok += 1
        time.sleep(0.5)
    print("tradotte:", ok, "in", len(batches), "richieste")
    return len(todo), ok

from fulltext import get_text
from encrypt_page import encrypt
import gzip, base64
ARTF = "cache/articles.json"; os.makedirs("cache", exist_ok=True)
ART = json.load(open(ARTF)) if os.path.exists(ARTF) else {}

def fd(dt): return f"{dt.day} {M[dt.month-1]} · {dt:%H:%M}"

def card(i, src, first, op):
    cls = ("q" if first else "") + (" op" if op else "")
    s = f"<p>{e(i['s'])}</p>" if i["s"] else ""
    return (f'<a class="card {cls}" href="#" data-i="{i["id"]}"><div class="meta">{fd(i["d"])}<span class="srcb">{e(src)}</span></div>'
            f'<h3>{e(i["t"])}</h3>{s}<span class="ext">Leggi l\'articolo completo →</span></a>')

def block(items, op, color):
    cards, briefs = [], []
    for i in items:
        if LIVE.search(i["t"]):
            briefs.append(f'<a class="brief" href="#" data-i="{i["id"]}"><span class="tag">{i["d"]:%H:%M}</span>{e(i["t"])}<span class="srcb">{e(i["src"])}</span></a>')
        else:
            cards.append(card(i, i["src"], not cards, op))
    bx = '<div class="briefs"><h4>Dirette e risultati in breve</h4>' + "".join(briefs) + "</div>" if briefs else ""
    return f'<section class="blk" style="--k:{color}"><div><div class="bg">' + "".join(cards) + f"</div>{bx}</div></section>"

def group(gk, news, ops):
    ob = '<button data-v="o" onclick="sv(\'o\')" style="--k:#64d2ff">Opinioni</button>' if ops else ""
    o = block(ops, True, "#64d2ff") if ops else ""
    return (f'<div class="og" data-o="{gk}"><div class="sb" style="--k:#ff2d55"><button data-v="n" onclick="sv(\'n\')">Notizie</button>{ob}</div>'
            f'<div class="sv" data-v="n">{block(news, False, "#ff2d55")}</div><div class="sv" data-v="o">{o}</div></div>')

def main():
    data = {}
    for o in OUT:
        sp = o["tab"] == "sport"
        n = gather(o.get("news", []), sp, o.get("scrape", [])); p = gather(o.get("op", []), sp, o.get("scrape_op", []))
        for i in n + p: i["src"] = o["label"]
        data[o["key"]] = (n, p)
    foreign = [o for o in OUT if o["tab"] in ("mondo", "sport")]
    strs = [s for o in foreign for L in data[o["key"]] for i in L for s in (i["t"], i["s"])]
    ntodo, nok = translate(strs)
    for o in foreign:
        for L in data[o["key"]]:
            for i in L:
                i["t"] = TR.get(key(i["t"]), i["t"]); i["s"] = TR.get(key(i["s"]), i["s"]) if i["s"] else ""
    # ---- testo completo: solo articoli gratuiti ----
    allit = {i["l"]: i for o in OUT for L in data[o["key"]] for i in L}
    todo = [u for u in allit if u not in ART or ART[u][0] == "err"]
    print("testi da scaricare:", len(todo), flush=True)
    t0 = time.time(); done = [0]
    def save_art():
        json.dump({u: v for u, v in ART.items()}, open(ARTF, "w"), ensure_ascii=False)
    def job(u):
        if time.time() - t0 > 10 * 60: return u, None
        return u, get_text(u)
    with ThreadPoolExecutor(8) as ex:
        for u, r in ex.map(job, todo):
            if r:
                ART[u] = list(r); done[0] += 1
                if done[0] % 40 == 0: save_art(); print(f"  cache articoli {done[0]}/{len(todo)}", flush=True)
    save_art()
    excl = {"pay": 0, "short": 0, "err": 0, "pending": 0}
    foreign_keys = {o["key"] for o in OUT if o["tab"] in ("mondo", "sport")}
    for o in OUT:
        kept = []
        for L in data[o["key"]]:
            K = []
            for i in L:
                st = ART.get(i["l"], ["pending"])[0]
                if st == "ok":
                    i["xo"] = ART[i["l"]][1]; i["id"] = key(i["l"]); i["fx"] = o["key"] in foreign_keys; K.append(i)
                else: excl[st] = excl.get(st, 0) + 1
            kept.append(K)
        data[o["key"]] = tuple(kept)
    # ---- traduci testi completi esteri (paragrafo per paragrafo, in cache) ----
    BTRF = "cache/body_tr.json"
    BTR = json.load(open(BTRF)) if os.path.exists(BTRF) else {}
    paras = []
    for o in OUT:
        if o["key"] not in foreign_keys: continue
        for L in data[o["key"]]:
            for i in L:
                for p in i["xo"].split("\n\n"):
                    p = p.strip()
                    if p and key(p) not in BTR: paras.append(p)
    paras = list(dict.fromkeys(paras))
    print("paragrafi da tradurre:", len(paras), flush=True)
    FAILS[0] = 0; DEADLINE_BODY = time.time() + 8 * 60
    batches, cur, n = [], [], 0
    for p in paras:
        if cur and (n + len(p) > 3500 or len(cur) >= 25): batches.append(cur); cur, n = [], 0
        cur.append(p); n += len(p) + 1
    if cur: batches.append(cur)
    bok = 0
    for bi, bt in enumerate(batches):
        if time.time() > DEADLINE_BODY or FAILS[0] >= 4:
            print("traduzione corpi interrotta, riprendo al prossimo giro", flush=True); break
        for p, r in zip(bt, tr_batch(bt)):
            if r: BTR[key(p)] = r; bok += 1
        time.sleep(0.6)
        if (bi + 1) % 10 == 0:
            json.dump(BTR, open(BTRF, "w"), ensure_ascii=False)
            print(f"  body tr {bok}/{len(paras)}", flush=True)
    json.dump(BTR, open(BTRF, "w"), ensure_ascii=False)
    tr_stats = {"paragrafi": len(paras), "ok": bok, "cache": len(BTR)}
    for o in OUT:
        for L in data[o["key"]]:
            for i in L:
                if i.get("fx"):
                    parts = []
                    for p in i["xo"].split("\n\n"):
                        p = p.strip()
                        if not p: continue
                        parts.append(BTR.get(key(p), p))
                    i["x"] = "\n\n".join(parts)
                else:
                    i["x"] = i["xo"]
    # prune cache
    live = set(allit)
    json.dump({k: v for k, v in SC.items() if k in live}, open(SCF, "w"), ensure_ascii=False, indent=0, sort_keys=True)
    used = {key(s) for s in strs}
    json.dump({k: v for k, v in TR.items() if k in used}, open(TRF, "w"), ensure_ascii=False, indent=0, sort_keys=True)

    stats = {}; body = ""
    for k, name in TABS:
        OK = [o for o in OUT if o["tab"] == k and data[o["key"]][0]]
        body += f'<div class="tab" data-k="{k}">'
        if k == "torino":
            allits = sorted([i for o in OK for i in data[o["key"]][0] + data[o["key"]][1]], key=lambda i: i["d"], reverse=True)
            body += group("all", allits, [])
            stats[k] = {"Torino (vista unica)": len(allits)} | {o["label"]: len(data[o["key"]][0]) for o in OK}
        else:
            body += (f'<div class="osw"><button class="ar" onclick="st(-1)" aria-label="Giornale precedente">‹</button><div class="ot"><b class="onm">{e(OK[0]["label"])}</b>'
                     f'<button class="ocn" onclick="tl()"><span class="oi">1</span> / {len(OK)} · tutti i giornali ▾</button></div><button class="ar" onclick="st(1)" aria-label="Giornale successivo">›</button></div><div class="ol">'
                     + "".join(f'<button data-o="{o["key"]}" data-n="{e(o["label"])}" onclick="so(\'{o["key"]}\')">{e(o["label"])}<small>{e(o["country"])}</small></button>' for o in OK) + "</div>")
            for o in OK:
                body += group(o["key"], *data[o["key"]])
            stats[k] = {o["label"]: f'{len(data[o["key"]][0])}+{len(data[o["key"]][1])} op' for o in OK}
        body += "</div>"
    empty = [o["label"] for o in OUT if not data[o["key"]][0]]
    bar = "".join(f'<button data-t="{k}" onclick="sh(\'{k}\')">{n}</button>' for k, n in TABS)
    items = {i["id"]: {"t": i["t"], "s": i["s"], "x": i["x"], "xo": i["xo"], "fx": bool(i.get("fx")), "l": i["l"], "src": i["src"], "d": fd(i["d"])} for o in OUT for L in data[o["key"]] for i in L}
    inner = (f'<div class="top h3"><div class="in"><a class="logo" href="#"><span>ALL</span>NEWS</a><nav class="bar">{bar}</nav>'
             f'<input id="q" type="search" placeholder="CERCA" autocomplete="off" aria-label="Cerca nelle notizie"><span class="d">Aggiornato il {NOW:%d/%m/%Y %H:%M}</span>'
             f'<span class="fzb"><button onclick="fz(-1)" aria-label="Riduci testo">A−</button><button onclick="fz(1)" aria-label="Ingrandisci testo">A+</button></span></div></div>'
             f'<main>{body}<div id="sr"></div></main><footer>ALL NEWS · Aggiornamento automatico ogni ora · Solo articoli gratuiti, testo completo in lingua originale</footer>'
             '<div id="rd" hidden><div class="rin"><button class="rx" onclick="cr()" aria-label="Chiudi">✕ Chiudi</button><article id="ra"></article></div></div>'
             '<button id="up" aria-label="Torna su">↑ Su</button>')
    pw = os.environ.get("ALLNEWS_PASS")
    if not pw: raise SystemExit("ALLNEWS_PASS mancante")
    payload = base64.b64encode(gzip.compress(json.dumps({"html": inner, "items": items, "js": open("site/app.js").read()}, ensure_ascii=False).encode())).decode()
    blob = encrypt(pw, payload)
    shell = open("site/shell.html").read().replace("__BLOB__", blob)
    shutil.rmtree("docs", ignore_errors=True); os.makedirs("docs")
    open("docs/index.html", "w").write(shell); shutil.copy("site/style.css", "docs/style.css"); open("docs/.nojekyll", "w").close()
    stats["fulltext"] = {o["label"]: len(data[o["key"]][0]) + len(data[o["key"]][1]) for o in OUT}
    stats["esclusi"] = excl
    print(json.dumps({"stats": stats, "vuoti": empty, "traduzioni": {"nuove": ntodo, "ok": nok, "cache": len(used)}, "body_tr": tr_stats}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
