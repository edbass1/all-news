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
        date=h[3] if len(h)>3 else None
        i=slug(L[1]); o=old.get(i,{})
        out.append({"id":i,"section":sec,"rank":rank,"tag":tag,"source":src,"story":story or i,"title":L[1],"summary":L[2],"body":L[3:],"date":date or o.get("date",today),"first_seen":o.get("first_seen",today)})
json.dump(out,open("data/articles.json","w"),ensure_ascii=False,indent=1); print(len(out),"articoli")
