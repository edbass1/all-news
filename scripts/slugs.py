#!/usr/bin/env python3
"""Mappa slug stabili: data/slugs.json = {"published":[...tutti gli slug mai pubblicati], "redirects":{vecchio:nuovo}}.
Uso: python3 scripts/slugs.py [--history]  (--history recupera slug e articoli dalla storia git)"""
import json,os,re,sys,subprocess,glob
P="data/slugs.json"
def tok(s): return {w for w in re.findall(r"[a-zà-ù0-9]{4,}",s.lower())}
def jac(a,b): return len(a&b)/max(1,len(a|b))
def load(): return json.load(open(P)) if os.path.exists(P) else {"published":[],"redirects":{}}
def best(old,cur):
    """old: dict con section/title/summary (o solo slug). Ritorna id corrente più simile o None."""
    ot=tok(old.get("title","")+" "+old.get("summary","")) or tok(old["id"].replace("-"," "))
    c=[(jac(ot,tok(a["title"]+" "+a["summary"]))+(.1 if a["section"]==old.get("section") else 0),a["id"]) for a in cur]
    s,i=max(c) if c else (0,None); return i if s>=.25 else None
def update(cur,known_old=()):
    m=load(); ids={a["id"] for a in cur}; olds={o["id"]:o for o in known_old}
    pub=set(m["published"])|ids|set(olds)
    for s in sorted(pub-ids):
        r=m["redirects"].get(s)
        if r in ids: continue
        m["redirects"][s]=best(olds.get(s,{"id":s}),cur) or ""
    for s in list(m["redirects"]):
        if s in ids: del m["redirects"][s]
    m["published"]=sorted(pub); json.dump(m,open(P,"w"),ensure_ascii=False,indent=1); return m
if __name__=="__main__":
    cur=json.load(open("data/articles.json")); old=[]
    if "--history" in sys.argv:
        for c in subprocess.run(["git","log","--all","--pretty=%h","--","data/articles.json"],capture_output=True,text=True).stdout.split():
            try: old+=json.loads(subprocess.run(["git","show",c+":data/articles.json"],capture_output=True,text=True).stdout)
            except Exception: pass
        names=subprocess.run(["git","log","--all","--pretty=format:","--name-only","--","docs/a"],capture_output=True,text=True).stdout.split()
        seen={o["id"] for o in old}; old+=[{"id":n[7:-5]} for n in names if n.startswith("docs/a/") and n[7:-5] not in seen]
    m=update(cur,old); print(len(m["published"]),"pubblicati,",len(m["redirects"]),"redirect,",sum(1 for v in m["redirects"].values() if not v),"senza corrispondenza")
