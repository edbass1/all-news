#!/usr/bin/env python3
"""Genera docs/ da data/articles.json (sito ALL NEWS)."""
import json, html, os, shutil, datetime
e=html.escape
M=["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"]
def d(s): y,m,g=s.split("-"); return f"{int(g)} {M[int(m)-1]} {y}"
A=json.load(open("data/articles.json"))
TABS=[("italia","Italia",[("it-news","Prima pagina"),("it-op","Editoriali e opinioni"),("it-sport","Sport"),("it-opsport","Sport · Commenti")]),
      ("mondo","Mondo",[("wo-news","Notizie dal mondo"),("wo-op","Editoriali e opinioni")]),
      ("sport","Sport",[("wo-sport","Sport internazionale"),("wo-opsport","Commenti e analisi")])]
SECN={k:n for _,_,s in TABS for k,n in s}
now=datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
CSS=""".top{background:#111114;border-bottom:1px solid #26262b}.top .in{max-width:1200px;margin:auto;display:flex;align-items:stretch;padding:0 24px;height:60px}
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
JS="""function sh(t){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x.id==t));document.querySelectorAll('.bar button').forEach(x=>x.classList.toggle('on',x.dataset.t==t));history.replaceState(null,'','#'+t)}
var h=location.hash.slice(1);sh(['italia','mondo','sport'].includes(h)?h:'italia')"""
def head(t,root,bar=True):
    b="".join(f'<button data-t="{k}" onclick="sh(\'{k}\')">{n}</button>' for k,n,_ in TABS) if bar else "".join(f'<button onclick="location.href=\'{root}index.html#{k}\'">{n}</button>' for k,n,_ in TABS)
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t}</title><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap"><link rel="stylesheet" href="{root}style.css"></head><body>
<div class="top h3"><div class="in"><a class="logo" href="{root}index.html"><span>ALL</span>NEWS</a><nav class="bar">{b}</nav><span class="d">Aggiornato il {now}</span></div></div><main>"""
FOOT="""</main><footer>ALL NEWS · Aggiornamento automatico ogni ora · Tutti gli articoli sono sintesi originali, riscritte e tradotte in italiano dalla redazione · Le testate di origine sono citate in calce</footer>"""
def card(a,cls="",rel=()):
    r="".join(f'<div><b>›</b> {e(x["title"])}</div>' for x in rel)
    return f'<a class="card {cls}" href="a/{a["id"]}.html"><div class="meta"><span class="tag">{e(a["tag"])}</span>{e(a["source"].split(",")[0])}</div><h3>{e(a["title"])}</h3><p>{e(a["summary"])}</p>{"<div class=rel>"+r+"</div>" if r else ""}</a>'
shutil.rmtree("docs",ignore_errors=True); os.makedirs("docs/a")
open("docs/style.css","w").write(CSS); open("docs/.nojekyll","w").close()
body=""
for k,n,secs in TABS:
    body+=f'<div class="tab" id="{k}">'
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
            i=len(cards); cls=("lead small" if lv=="live-big" else "lead" if i==0 else "big" if i<3 else "")+(" op" if "op" in s else "")
            cards.append(card(a,cls,rel))
        body+=f'<h2 class="sec"><span>{sn}</span></h2><div class="grid">'+"".join(cards)+"</div>"
        if briefs: body+='<div class="briefs"><h4>Risultati e dirette in breve</h4>'+"".join(briefs)+"</div>"
    body+="</div>"
open("docs/index.html","w").write(head("ALL NEWS – Italia, Mondo, Sport","")+body+FOOT+f"<script>{JS}</script></body></html>")
for a in A:
    p="".join(f"<p>{e(x)}</p>" for x in a["body"])
    rel=[x for x in A if x["story"]==a["story"] and x["id"]!=a["id"] and x["section"]==a["section"]]
    rl="".join(f'<div><b>›</b> <a href="{x["id"]}.html">{e(x["title"])}</a></div>' for x in rel)
    open(f"docs/a/{a['id']}.html","w").write(head(e(a["title"])+" – ALL NEWS","../",False)+f"""<article><div class="meta"><span class="tag">{e(a['tag'])}</span>{SECN[a['section']]} · {d(a['date'])}</div><h1>{e(a['title'])}</h1><p class="lede">{e(a['summary'])}</p>{p}{'<div class="rel"><b>Sullo stesso tema</b>'+rl+'</div>' if rl else ''}<div class="src">Fonti: {e(a['source'])} · {d(a['date'])}<br>Sintesi originale riscritta{' e tradotta' if not a['section'].startswith('it') else ''} in italiano dalla redazione di ALL NEWS.</div></article>"""+FOOT+"</body></html>")
print(len(A),"articoli")
