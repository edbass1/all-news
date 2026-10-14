#!/usr/bin/env python3
"""SPORT per testata: legge data/outlets.json, scarica i feed (news/op) e il testo completo dei primi articoli.
Output: data/outlet_candidates.json = {key:{"news":[...],"op":[...],"ok":bool}} con title, desc, link, date, text (paragrafi letti dalla pagina).
Esclude sport americani (NFL, NBA, MLB, NHL, college). Uso: python3 scripts/fetch_outlets.py [N=12]"""
import json,re,sys,html,gzip,urllib.request,concurrent.futures as cf,xml.etree.ElementTree as ET
N=int(sys.argv[1]) if len(sys.argv)>1 else 12
O=[o for o in json.load(open("data/outlets.json")) if len(sys.argv)<3 or o.get("tab")==sys.argv[2]]
US=re.compile(r"\b(nfl|nba|mlb|nhl|wnba|ncaa|college|super bowl|touchdown|quarterback|baseball|basketball|hockey|playoffs? (nfl|nba)|yankees|dodgers|lakers|celtics|knicks|warriors|cowboys|chiefs|eagles|patriots|packers|49ers|steelers|ravens|jets|giants|mets|cubs|red sox|nba finals|world series|stanley cup|march madness|fantasy football|heisman|draft pick|nba draft|nfl draft)\b",re.I)
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) Chrome/120","Accept-Language":"it,en;q=0.8"}
def raw(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20).read()
    return gzip.decompress(r) if r[:2]==b"\x1f\x8b" else r
def items(u):
    b=raw(u).decode("utf8","replace"); out=[]
    for m in re.finditer(r"<(item|entry)\b.*?</\1>",b,re.S):
        x=m.group(0)
        def g(t):
            mm=re.search(rf"<{t}\b[^>]*>(.*?)</{t}>",x,re.S); v=mm.group(1) if mm else ""
            return html.unescape(re.sub(r"<!\[CDATA\[|\]\]>","",v)).strip()
        link=g("link") or (re.search(r'<link[^>]+href="([^"]+)"',x) or [None,""])[1]
        out.append({"title":re.sub("<[^>]+>","",g("title")),"desc":re.sub(r"\s+"," ",re.sub("<[^>]+>"," ",g("description") or g("summary")))[:600],"link":link.strip(),"date":g("pubDate") or g("updated") or g("published")})
    return out
def text(u):
    try:
        b=raw(u).decode("utf8","replace")
        b=re.sub(r"<(script|style|aside|nav|footer|figure)\b.*?</\1>","",b,flags=re.S)
        ps=[re.sub(r"\s+"," ",html.unescape(re.sub("<[^>]+>","",p))).strip() for p in re.findall(r"<p\b[^>]*>(.*?)</p>",b,re.S)]
        return [p for p in ps if len(p)>60][:40]
    except Exception: return []
def scrape(cfg):
    """Pagina HTML senza RSS: estrae link articolo che rispettano la regex cfg['re'] (percorso relativo)."""
    from urllib.parse import urljoin,urlparse
    b=raw(cfg["url"]).decode("utf8","replace"); out=[];seen=set()
    for m in re.finditer(r'<a\b[^>]*href="([^"#?]+)"[^>]*>(.*?)</a>',b,re.S):
        p=urlparse(urljoin(cfg["url"],m.group(1))).path.rstrip("/")
        if p in seen or not re.match(cfg["re"],p): continue
        t=re.sub(r"\s+"," ",html.unescape(re.sub("<[^>]+>"," ",m.group(2)))).strip()
        seen.add(p); out.append({"title":t,"desc":"","link":urljoin(cfg["url"],p),"date":""})
    return out
def ptitle(u):
    try:
        b=raw(u).decode("utf8","replace"); m=re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',b) or re.search(r"<title>(.*?)</title>",b,re.S)
        return html.unescape(m.group(1)).strip() if m else ""
    except Exception: return ""
def outlet(o):
    res={"ok":False}
    for k in("news","op"):
        L=[];seen=set()
        src=[("rss",u) for u in o.get(k,[])]+([("html",o["html"])] if k=="news" and o.get("html") else [])+([("html",o["html_op"])] if k=="op" and o.get("html_op") else [])
        if k=="op" and o.get("op_match"): src+=[("rss",u) for u in o.get("news",[])]
        for typ,u in src:
            try:
                for it in (items(u) if typ=="rss" else scrape(u)):
                    if not it["title"]: it["title"]=ptitle(it["link"])
                    if k=="op" and o.get("op_match") and typ=="rss" and u in o.get("news",[]) and not re.search(o["op_match"],it["link"]): continue
                    if k=="news" and o.get("op_match") and re.search(o["op_match"],it["link"]): continue
                    if it["title"] in seen or US.search(it["title"]+" "+it["desc"]): continue
                    seen.add(it["title"]);L.append(it)
            except Exception as ex: print("KO",o["key"],u,str(ex)[:50],file=sys.stderr)
        L=L[:N if k=="news" else 5]
        with cf.ThreadPoolExecutor(8) as ex:
            for it,t in zip(L,ex.map(lambda i:text(i["link"]),L)): it["text"]=t
        res[k]=L; res["ok"]|=bool(L)
    return o["key"],res
with cf.ThreadPoolExecutor(10) as ex: R=dict(ex.map(outlet,O))
import os; R0=json.load(open("data/outlet_candidates.json")) if os.path.exists("data/outlet_candidates.json") else {}; R0.update(R); R=R0
json.dump(R,open("data/outlet_candidates.json","w"),ensure_ascii=False,indent=1)
for o in O: r=R[o["key"]]; print(o["key"],"news",len(r.get("news",[])),"op",len(r.get("op",[])),"testo",sum(1 for i in r.get("news",[])+r.get("op",[]) if len(i["text"])>=3))
