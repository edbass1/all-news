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

def gather(urls, sport):
    seen, res = set(), []
    with ThreadPoolExecutor(4) as ex:
        for L in ex.map(fetch, urls):
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

def fd(dt): return f"{dt.day} {M[dt.month-1]} · {dt:%H:%M}"

def card(i, src, first, op):
    cls = ("q" if first else "") + (" op" if op else "")
    s = f"<p>{e(i['s'])}</p>" if i["s"] else ""
    return (f'<a class="card {cls}" href="{e(i["l"])}" target="_blank" rel="noopener"><div class="meta">{fd(i["d"])}<span class="srcb">{e(src)}</span></div>'
            f'<h3>{e(i["t"])}</h3>{s}<span class="ext">Leggi su {e(src)} ↗</span></a>')

def block(items, op, color):
    cards, briefs = [], []
    for i in items:
        if LIVE.search(i["t"]):
            briefs.append(f'<a class="brief" href="{e(i["l"])}" target="_blank" rel="noopener"><span class="tag">{i["d"]:%H:%M}</span>{e(i["t"])}<span class="srcb">{e(i["src"])}</span></a>')
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
        n = gather(o.get("news", []), sp); p = gather(o.get("op", []), sp)
        for i in n + p: i["src"] = o["label"]
        data[o["key"]] = (n, p)
    foreign = [o for o in OUT if o["tab"] in ("mondo", "sport")]
    strs = [s for o in foreign for L in data[o["key"]] for i in L for s in (i["t"], i["s"])]
    ntodo, nok = translate(strs)
    for o in foreign:
        for L in data[o["key"]]:
            for i in L:
                i["t"] = TR.get(key(i["t"]), i["t"]); i["s"] = TR.get(key(i["s"]), i["s"]) if i["s"] else ""
    # prune cache
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
    page = (f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ALL NEWS – Italia, Mondo, Sport, Torino</title>'
            f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap"><link rel="stylesheet" href="style.css"></head><body>'
            f'<div class="top h3"><div class="in"><a class="logo" href="index.html"><span>ALL</span>NEWS</a><nav class="bar">{bar}</nav><span class="d">Aggiornato il {NOW:%d/%m/%Y %H:%M}</span></div></div><main>'
            + body + '</main><footer>ALL NEWS · Aggiornamento automatico ogni ora · Titoli e sommari dai feed delle testate, tradotti automaticamente · Ogni notizia rimanda all\'articolo originale</footer>'
            '<button id="up" onclick="scrollTo({top:0,behavior:\'smooth\'})" aria-label="Torna su">↑ Su</button><script>' + open("site/app.js").read() + "</script></body></html>")
    shutil.rmtree("docs", ignore_errors=True); os.makedirs("docs")
    open("docs/index.html", "w").write(page); shutil.copy("site/style.css", "docs/style.css"); open("docs/.nojekyll", "w").close()
    print(json.dumps({"stats": stats, "vuoti": empty, "traduzioni": {"nuove": ntodo, "ok": nok, "cache": len(used)}}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
