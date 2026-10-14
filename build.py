#!/usr/bin/env python3
"""Genera docs/ da data/articles.json (sito ALL NEWS)."""
import json, html, os, shutil, datetime
e=html.escape
M=["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"]
def d(s): y,m,g=s.split("-"); return f"{int(g)} {M[int(m)-1]} {y}"
A=json.load(open("data/articles.json"))
TABS=[("italia","Italia",[("it-news","Prima pagina"),("it-op","Editoriali e opinioni"),("it-sport","Sport"),("it-opsport","Sport · Commenti")]),
      ("mondo","Mondo",[("wo-news","Notizie dal mondo"),("wo-op","Editoriali e opinioni")]),
      ("sport","Sport",[("wo-sport","Sport internazionale"),("wo-opsport","Commenti e analisi")]),
      ("torino","Torino",[("to-news","Torino e Piemonte"),("to-op","Opinioni")])]
SECN={k:n for _,_,s in TABS for k,n in s}
OUT=json.load(open("data/outlets.json"))
for o in OUT: P="Sport · " if o.get("tab","sport")=="sport" else ""; SECN[f"so-{o['key']}"]=f"{P}{o['label']}"; SECN[f"so-{o['key']}-op"]=f"{P}Opinioni · {o['label']}"
COLS={"it-news":"#ff2d55","it-op":"#ff9f0a","it-sport":"#30d158","it-opsport":"#64d2ff","wo-news":"#0a84ff","wo-op":"#bf5af2","wo-sport":"#30d158","wo-opsport":"#64d2ff","to-news":"#ffd60a","to-op":"#ff9f0a"}
now=datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
FZ="var Z=+localStorage.getItem('anfs')||17;function ap(){document.querySelector('article').style.setProperty('--fs',Z+'px')}function fz(d){Z=Math.min(26,Math.max(13,Z+d*2));localStorage.setItem('anfs',Z);ap()}ap()"
CSS="""
.og{display:none}.og.on{display:block}
.ob{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 4px}.ob button{background:#18181c;border:1px solid #2c2c32;color:#cfcfd4;border-radius:999px;padding:5px 12px;font:600 12.5px Arial,sans-serif;cursor:pointer;line-height:1.2}
.ob button small{display:block;font-size:9.5px;color:#888;font-weight:400;text-transform:uppercase;letter-spacing:.6px}.ob button:hover{border-color:#30d158}.ob button.on{background:#30d158;border-color:#30d158;color:#000}.ob button.on small{color:#033}
.na{color:#999;font:15px Arial,sans-serif;padding:24px 0}
@media(max-width:560px){.ob{flex-wrap:nowrap;overflow-x:auto;padding-bottom:6px}.ob button{flex:0 0 auto}}

.sb{display:flex;justify-content:space-between;align-items:stretch;border-bottom:1px solid #26262b;margin:6px 0 4px}
.sb button{background:none;border:0;border-bottom:4px solid transparent;color:#8a8a92;cursor:pointer;font:800 20px Arial,sans-serif;padding:10px 4px 8px;letter-spacing:.3px}
.sb button.on{color:var(--k);border-bottom-color:var(--k)}.sb button:hover{color:#fff}
.sv{display:none}.sv.on{display:block}
#up{position:fixed;right:20px;bottom:20px;z-index:50;background:#ff2d55;color:#fff;border:0;border-radius:999px;padding:10px 16px;font:700 14px Arial,sans-serif;cursor:pointer;box-shadow:0 4px 14px #0008;opacity:0;pointer-events:none;transform:translateY(10px);transition:.2s}
#up.on{opacity:1;pointer-events:auto;transform:none}
@media(max-width:560px){.sb button{font-size:16px}#up{right:12px;bottom:12px;padding:9px 14px}}

.blk{display:grid;grid-template-columns:170px 1fr;gap:20px;border-top:4px solid var(--k);padding:12px 0 26px}.bh{margin:0;font:800 22px/1.15 Arial,sans-serif;color:var(--k)}
.bg{display:grid;grid-template-columns:repeat(4,1fr);grid-auto-flow:dense;gap:1px;background:#222;border:1px solid #222}
.bg .card{background:#121215;border:0;border-top:2px solid var(--k);border-radius:0;padding:12px 14px;grid-column:auto}.bg .card:hover{background:#18181c;border-color:var(--k)}
.bg .card h3{font-size:16.5px}.bg .card p{font-size:14px;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.bg .card.q{grid-column:span 2;grid-row:span 2;padding:20px}.bg .card.q h3{font-size:28px;line-height:1.15}.bg .card.q p{font-size:15.5px;-webkit-line-clamp:6}.bg .card.q.small h3{font-size:22px}
.blk .tag{color:var(--k)}.blk .meta .tag{margin-right:6px}.blk .rel b{color:var(--k)}.blk .briefs{margin-top:12px}
@media(max-width:900px){.blk{grid-template-columns:1fr;gap:10px}.bg{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.bg{grid-template-columns:1fr}.bg .card.q{grid-column:auto;grid-row:auto}.bg .card.q h3{font-size:22px}}
.srcb{display:inline-block;margin-left:8px;padding:2px 8px;border:0;border-radius:4px;background:#2a2a2a;color:#e0e0e4;font:600 10.5px/1.4 Arial,sans-serif;letter-spacing:.4px;text-transform:none;vertical-align:middle}
.fs{float:right;display:flex;gap:6px}.fs button{background:#18181c;color:#ddd;border:1px solid #333;border-radius:4px;padding:3px 9px;font:600 13px Arial,sans-serif;cursor:pointer}.fs button:hover{color:#fff;border-color:#ff2d55}article>p{font-size:var(--fs,17px)}
.top{background:#111114;border-bottom:1px solid #26262b}.top .in{max-width:1200px;margin:auto;display:flex;align-items:stretch;padding:0 24px;height:60px}
.top .logo{display:flex;align-items:center;gap:6px;font:700 22px 'Space Grotesk',Arial,sans-serif;color:#fff;letter-spacing:1px;padding-right:28px;border-right:1px solid #26262b}.top .logo span{background:#ff2d55;color:#fff;padding:2px 7px;border-radius:3px}
.top .bar{display:flex;margin-left:8px}.top .bar button{display:flex;align-items:center;background:none;border:0;border-bottom:3px solid transparent;cursor:pointer;padding:0 22px;font:500 13px 'Space Grotesk',Arial,sans-serif;letter-spacing:2px;text-transform:uppercase;color:#9a9aa2}.top .bar button.on{color:#fff;border-bottom-color:#ff2d55;background:#18181c}.top .bar button:hover{color:#fff}
.top .d{margin-left:auto;align-self:center;font:500 12px 'Space Grotesk',Arial,sans-serif;color:#666}
@media(max-width:640px){.top .in{padding:0 10px;height:auto;flex-wrap:wrap}.top .logo{border:0;padding:10px 0;font-size:19px}.top .d{display:none}.top .bar{margin:0;width:100%}.top .bar button{flex:1;justify-content:center;padding:10px 4px;font-size:12px;letter-spacing:1px}}
*{box-sizing:border-box}body{margin:0;background:#0a0a0c;color:#e4e4e7;font:16px/1.55 Georgia,'Times New Roman',serif}
a{color:inherit;text-decoration:none}
main{max-width:1200px;margin:auto;padding:20px}.tab{display:none}.tab.on{display:block}
h2.sec{font:900 22px Arial,sans-serif;color:#fff;text-transform:uppercase;border-bottom:2px solid #333;padding-bottom:6px;margin:34px 0 16px}
h2.sec span{background:#ff2d55;padding:3px 10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}
.card{background:#131316;border:1px solid #232327;padding:16px;border-radius:6px;transition:.15s;display:block}.card:hover{border-color:#ff9f0a}
.card.lead{grid-column:1/-1;padding:26px;background:linear-gradient(135deg,#1a1a1f,#101013)}.card.lead h3{font-size:32px}
.card.lead.small{padding:16px}.card.lead.small h3{font-size:21px}.briefs{margin:14px 0 0;border:1px solid #232327;border-radius:6px;padding:10px 16px;font:14px Arial,sans-serif}.briefs h4{margin:0 0 6px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#888}.brief{display:block;padding:5px 0;border-top:1px solid #1d1d21;color:#ddd}.brief:hover{color:#fff}.brief .tag{margin-right:8px}.card.big{grid-column:span 2}.card.big h3{font-size:24px}
.card h3{color:#fff;margin:6px 0;font:700 19px/1.25 Arial,sans-serif}.card p{margin:0;color:#aaa;font-size:15px}
.meta{font:11px Arial,sans-serif;color:#888;text-transform:uppercase;letter-spacing:.5px}
.tag{color:#ff9f0a;font-weight:800;margin-right:8px}
.rel{margin-top:12px;border-top:1px solid #2a2a2e;padding-top:8px;font:13px Arial,sans-serif}.rel div{color:#ddd;padding:3px 0}.rel b{color:#ff2d55}
.op h3{font-style:italic;font-family:Georgia,serif}
article{max-width:760px;margin:30px auto}article h1{color:#fff;font:800 38px/1.15 Arial,sans-serif}.lede{font-size:20px;color:#bbb;font-style:italic}
.src{margin-top:36px;border-top:1px solid #333;padding-top:12px;font:13px Arial,sans-serif;color:#888}
footer{text-align:center;color:#666;font:12px Arial,sans-serif;padding:30px;border-top:1px solid #222}
@media(max-width:640px){.card.big{grid-column:auto}}"""
JS="""function cur(){return document.querySelector('.tab.on')}
function og(T){return T.querySelector('.og.on')||T.querySelector('.og')}
function sh(t,v,o){v=v||'n';o=o||(document.querySelector('.tab[data-k="'+t+'"] .og')||{dataset:{}}).dataset.o;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x.dataset.k==t));document.querySelectorAll('.bar button').forEach(x=>x.classList.toggle('on',x.dataset.t==t));var T=cur();if(!T.querySelector('.og[data-o="'+o+'"]'))o=T.querySelector('.og').dataset.o;T.querySelectorAll('.og').forEach(x=>x.classList.toggle('on',x.dataset.o==o));T.querySelectorAll('.ob button').forEach(x=>x.classList.toggle('on',x.dataset.o==o));var G=og(T);if(!G.querySelector('.sb button[data-v="'+v+'"]'))v='n';G.querySelectorAll('.sv').forEach(x=>x.classList.toggle('on',x.dataset.v==v));G.querySelectorAll('.sb button').forEach(x=>x.classList.toggle('on',x.dataset.v==v));history.replaceState(null,'','#'+t+(o!='all'&&o!=T.querySelector('.og').dataset.o?'-'+o:'')+(v=='o'?'-opinioni':''))}
function sv(v){sh(cur().dataset.k,v,og(cur()).dataset.o);scrollTo(0,0)}
function so(o){sh(cur().dataset.k,'n',o);scrollTo(0,0)}
var h=location.hash.slice(1).split('-');sh(['italia','mondo','sport','torino'].includes(h[0])?h[0]:'italia',h.includes('opinioni')?'o':'n',h[1]&&h[1]!='opinioni'?h[1]:null);scrollTo(0,0)
var U=document.getElementById('up');addEventListener('scroll',function(){U.classList.toggle('on',scrollY>600)})"""
def head(t,root,bar=True):
    b="".join(f'<button data-t="{k}" onclick="sh(\'{k}\')">{n}</button>' for k,n,_ in TABS) if bar else "".join(f'<button onclick="location.href=\'{root}index.html#{k}\'">{n}</button>' for k,n,_ in TABS)
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t}</title><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap"><link rel="stylesheet" href="{root}style.css"></head><body>
<div class="top h3"><div class="in"><a class="logo" href="{root}index.html"><span>ALL</span>NEWS</a><nav class="bar">{b}</nav><span class="d">Aggiornato il {now}</span></div></div><main>"""
FOOT="""</main><footer>ALL NEWS · Aggiornamento automatico ogni ora · Tutti gli articoli sono sintesi originali, riscritte e tradotte in italiano dalla redazione · Le testate di origine sono citate in calce</footer>"""
def card(a,cls="",rel=()):
    r="".join(f'<div><b>›</b> {e(x["title"])}</div>' for x in rel)
    return f'<a class="card {cls}" href="a/{a["id"]}.html"><div class="meta"><span class="tag">{e(a["tag"])}</span>{d(a["date"])}<span class="srcb">{e(a["source"].split(",")[0])}</span></div><h3>{e(a["title"])}</h3><p>{e(a["summary"])}</p>{"<div class=rel>"+r+"</div>" if r else ""}</a>'
shutil.rmtree("docs",ignore_errors=True); os.makedirs("docs/a")
open("docs/style.css","w").write(CSS); open("docs/.nojekyll","w").close()
body=""
def isop(s): return s.endswith("-op") or "-op" in s
def render(secs):
    V={'n':'','o':''}
    for s,sn in secs:
        L=sorted([a for a in A if a["section"]==s],key=lambda a:a["rank"])
        if not L: continue
        seen=set(); cards=[]; briefs=[]
        for a in L:
            if a["id"] in seen: continue
            rel=[x for x in L if x["story"]==a["story"] and x["id"]!=a["id"]]; seen|={x["id"] for x in rel}
            lv=a.get("live","")
            if lv=="live" or (lv=="live-big" and cards):
                briefs.append(f'<a class="brief" href="a/{a["id"]}.html"><span class="tag">{e(a["tag"])}</span>{e(a["title"])}</a>'); continue
            i=len(cards); cls=("q small" if lv=="live-big" else "q" if i==0 else "")+(" op" if isop(s) else "")
            cards.append(card(a,cls,rel))
        bx='<div class="briefs"><h4>Risultati e dirette in breve</h4>'+"".join(briefs)+"</div>" if briefs else ""
        V['o' if isop(s) else 'n']+=f'<section class="blk" style="--k:{COLS.get(s,"#30d158")}"><h2 class="bh">{sn}</h2><div><div class="bg">'+"".join(cards)+f"</div>{bx}</div></section>"
    return V
def group(gk,secs,label,note=""):
    V=render(secs); ns=next(s for s,_ in secs if not isop(s)); os_=next((s for s,_ in secs if isop(s)),None)
    if not V['n']: V['n']=f'<p class="na">{note or "Contenuti non disponibili al momento."}</p>'
    ob=f'<button data-v="o" onclick="sv(\'o\')" style="--k:{COLS.get(os_,"#64d2ff")}">Opinioni</button>' if V['o'] else ''
    return f'<div class="og" data-o="{gk}"><div class="sb" style="--k:{COLS.get(ns,"#30d158")}"><button data-v="n" onclick="sv(\'n\')">{label}</button>{ob}</div><div class="sv" data-v="n">{V["n"]}</div><div class="sv" data-v="o">{V["o"]}</div></div>'
for k,n,secs in TABS:
    body+=f'<div class="tab" data-k="{k}">'
    OK=[o for o in OUT if o.get("tab","sport")==k and not o.get("pool")]
    if OK:
        body+='<div class="ob">'+"".join(f'<button data-o="{o["key"]}" onclick="so(\'{o["key"]}\')" title="{e(o["country"])}">{e(o["label"])}<small>{e(o["country"])}</small></button>' for o in OK)+'</div>'
        for o in OK: body+=group(o["key"],[(f"so-{o['key']}",f"Notizie · {o['label']}"),(f"so-{o['key']}-op",f"Opinioni · {o['label']}")],o["label"],o.get("note",""))
    else: body+=group("all",secs,secs[0][1])
    body+='</div>'
open("docs/index.html","w").write(head("ALL NEWS – Italia, Mondo, Sport","")+body+FOOT+'<button id="up" onclick="scrollTo({top:0,behavior:\'smooth\'})" aria-label="Torna su">↑ Su</button>'+f"<script>{JS}</script></body></html>")
for a in A:
    p="".join(f"<p>{e(x)}</p>" for x in a["body"])
    rel=[x for x in A if x["story"]==a["story"] and x["id"]!=a["id"] and x["section"]==a["section"]]
    rl="".join(f'<div><b>›</b> <a href="{x["id"]}.html">{e(x["title"])}</a></div>' for x in rel)
    open(f"docs/a/{a['id']}.html","w").write(head(e(a["title"])+" – ALL NEWS","../",False)+f"""<article><div class="fs"><button onclick="fz(-1)" aria-label="Riduci testo">A−</button><button onclick="fz(1)" aria-label="Ingrandisci testo">A+</button></div><div class="meta"><span class="tag">{e(a['tag'])}</span>{SECN[a['section']]} · {d(a['date'])}<span class="srcb">{e(a['source'])}</span></div><h1>{e(a['title'])}</h1><p class="lede">{e(a['summary'])}</p>{p}{'<div class="rel"><b>Sullo stesso tema</b>'+rl+'</div>' if rl else ''}<div class="src">Fonti: {e(a['source'])} · {d(a['date'])}<br>Sintesi originale riscritta{' e tradotta' if not a['section'].startswith('it') else ''} in italiano dalla redazione di ALL NEWS.</div></article>"""+FOOT+"<script>"+FZ+"</script></body></html>")
import sys; sys.path.insert(0,"scripts"); from slugs import update
SM=update(A)
for s,t in SM["redirects"].items():
    u=f"{t}.html" if t else "../index.html"
    open(f"docs/a/{s}.html","w").write(f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={u}"><link rel="canonical" href="{u}"><title>ALL NEWS</title></head><body style="background:#0a0a0c;color:#ccc;font-family:Arial"><p>Questo articolo è stato spostato: <a href="{u}">continua qui</a>.</p></body></html>')
print(len(A),"articoli,",len(SM["redirects"]),"redirect")
