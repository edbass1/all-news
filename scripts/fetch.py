#!/usr/bin/env python3
"""Scarica i feed RSS e produce data/candidates.json con cluster ordinati per prominenza cross-fonte."""
import json, re, sys, urllib.request, concurrent.futures as cf, xml.etree.ElementTree as ET, html
from email.utils import parsedate_to_datetime
FEEDS=json.load(open("data/feeds.json"))
STOP=set("il lo la i gli le un una di da in con su per tra fra e o che del della dei delle al alla ai nel nella è a the of to and in on for at by with from as is are was be has have after over its it an new says de la le les des el los las en y der die das und".split())
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=15).read()
        root=ET.fromstring(r); out=[]
        for it in root.iter():
            t=it.tag.split('}')[-1]
            if t not in("item","entry"): continue
            g=lambda n:next((c.text or "" for c in it if c.tag.split('}')[-1]==n),"")
            d=g("pubDate") or g("updated") or g("published") or g("date")
            desc=re.sub("<[^>]+>"," ",html.unescape(g("description") or g("summary") or g("encoded")))
            out.append({"title":html.unescape(g("title")).strip(),"desc":re.sub(r"\s+"," ",desc).strip()[:700],"date":d})
        return out[:40]
    except Exception as ex: return None
def toks(s): return {w for w in re.findall(r"[a-zà-ÿ0-9]{4,}",s.lower()) if w not in STOP}
res={}
with cf.ThreadPoolExecutor(32) as ex:
    jobs={(grp,src,u):ex.submit(get,u) for grp,srcs in FEEDS.items() for src,u in srcs.items()}
    for (grp,src,u),f in jobs.items():
        r=f.result(); print(("OK " if r else "KO ")+grp,src,len(r or []),file=sys.stderr)
        for i,it in enumerate(r or []): res.setdefault(grp,[]).append(dict(it,src=src,rank=i))
out={}
for grp,items in res.items():
    cl=[]
    for it in items:
        tk=toks(it["title"]+" "+it["desc"][:150])
        for c in cl:
            if len(tk&c["tk"])>=3: c["items"].append(it); c["tk"]|=tk; break
        else: cl.append({"tk":tk,"items":[it]})
    for c in cl:
        c["sources"]=sorted({i["src"] for i in c["items"]}); c["score"]=len(c["sources"])*10-min(i["rank"] for i in c["items"])*0.3
        del c["tk"]
    out[grp]=sorted(cl,key=lambda c:-c["score"])
json.dump(out,open("data/candidates.json","w"),ensure_ascii=False,indent=1)
