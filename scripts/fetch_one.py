#!/usr/bin/env python3
"""Top-30 per testata: python3 scripts/fetch_one.py <key> [N=40] [extra_feed_or_page ...]
Usa i feed di data/outlets.json + URL extra (RSS o pagine sezione: per le pagine HTML passare 'html:<url>|<regex percorso>').
Stampa titoli e testo completo (trafilatura) in /tmp/one-<key>.txt, salta titoli già presenti in data/src/so-<key>.txt."""
import sys,json,re,importlib.util,concurrent.futures as cf
sys.argv,args=[sys.argv[0]],sys.argv[1:]
spec=importlib.util.spec_from_file_location("fo","scripts/fetch_outlets.py")
src=open("scripts/fetch_outlets.py").read().split("with cf.ThreadPoolExecutor(10) as ex: R=")[0]
g={};exec(src.replace("O=[o for o","O=[];_=[o for o"),g)
key=args[0];N=int(args[1]) if len(args)>1 else 40
o=[x for x in json.load(open("data/outlets.json")) if x["key"]==key][0]
feeds=o.get("news",[]);pages=[]
for a in args[2:]:
    if a.startswith("html:"): u,r=a[5:].split("|",1);pages.append({"url":u,"re":r})
    else: feeds.append(a)
if o.get("html"): pages.append(o["html"])
L=[];seen=set()
for u in feeds:
    try:
        for it in g["items"](u):
            if g["fresh"](it["date"]) and it["link"] not in seen and not g["US"].search(it["title"]+" "+it["desc"]): seen.add(it["link"]);L.append(it)
    except Exception as e: print("KO",u,e,file=sys.stderr)
for p in pages:
    try:
        for it in g["scrape"](p):
            if it["link"] not in seen: seen.add(it["link"]);L.append(it)
    except Exception as e: print("KO",p,e,file=sys.stderr)
L=L[:N]
import trafilatura,subprocess
def tx(u):
    try:
        h=subprocess.run(["curl","-sL","--max-time","20","-A","Mozilla/5.0",u],capture_output=True).stdout.decode("utf8","replace")
        t=trafilatura.extract(h,favor_precision=True) or ""
        if not t: t="\n".join(g["text"](u))
        m=re.search(r'property="og:title"[^>]+content="([^"]+)"',h)
        return t,(m.group(1) if m else "")
    except Exception: return "",""
with cf.ThreadPoolExecutor(10) as ex: T=list(ex.map(lambda i:tx(i["link"]),L))
with open(f"/tmp/one-{key}.txt","w") as f:
    for i,(it,(t,ot)) in enumerate(zip(L,T)):
        f.write(f"### {i} {it['title'] or ot} | {it['date']} | {it['link']}\n{t[:3500]}\n\n")
print(len(L),"items ->",f"/tmp/one-{key}.txt")
