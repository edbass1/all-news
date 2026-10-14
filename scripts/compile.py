#!/usr/bin/env python3
"""data/src/<sezione>.txt -> data/articles.json. ID stabili (slug titolo), conserva first_seen."""
import json, re, os, glob, datetime, unicodedata
today=datetime.date.today().isoformat()
old={a["id"]:a for a in json.load(open("data/articles.json"))} if os.path.exists("data/articles.json") else {}
def slug(s): s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower(); return re.sub(r"[^a-z0-9]+","-",s).strip("-")[:70]
out=[]
for f in sorted(glob.glob("data/src/*.txt")):
    sec=os.path.basename(f)[:-4]
    for rank,blk in enumerate(x for x in open(f).read().split("\n\n") if x.strip()):
        L=blk.strip().split("\n"); h=L[0][1:].split("|")
        tag,src=h[0],h[1]; story=h[2] if len(h)>2 else ""
        date=(h[3] if len(h)>3 else "") or None; live=h[4] if len(h)>4 else ""
        i=slug(L[1]); o=old.get(i,{})
        out.append({"id":i,"section":sec,"rank":rank,"tag":tag,"source":src,"story":story or i,"title":L[1],"summary":L[2],"body":L[3:],"date":date or o.get("date",today),"first_seen":o.get("first_seen",today),"live":live})
# slug stabili: se un titolo cambia, l'articolo mantiene il vecchio ID (URL) pubblicato
import sys; sys.path.insert(0,"scripts"); from slugs import best
newids={a["id"] for a in out}; gone=[o for i,o in old.items() if i not in newids]
for a in out:
    if a["id"] in old or not gone: continue
    m=best(a,[dict(g,section=g["section"]) for g in gone if g["section"]==a["section"]])
    if m and m not in {x["id"] for x in out}:
        a["id"]=m; a["first_seen"]=old[m]["first_seen"]; gone=[g for g in gone if g["id"]!=m]
json.dump(out,open("data/articles.json","w"),ensure_ascii=False,indent=1); print(len(out),"articoli")
