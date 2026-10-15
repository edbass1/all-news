function cur(){return document.querySelector('.tab.on')}
function og(T){return T.querySelector('.og.on')||T.querySelector('.og')}
function sh(t,v,o){v=v||'n';o=o||(document.querySelector('.tab[data-k="'+t+'"] .og')||{dataset:{}}).dataset.o;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x.dataset.k==t));document.querySelectorAll('.bar button').forEach(x=>x.classList.toggle('on',x.dataset.t==t));var T=cur();if(!T.querySelector('.og[data-o="'+o+'"]'))o=T.querySelector('.og').dataset.o;T.querySelectorAll('.og').forEach(x=>x.classList.toggle('on',x.dataset.o==o));var B=[...T.querySelectorAll('.ol button')];B.forEach((x,i)=>{x.classList.toggle('on',x.dataset.o==o);if(x.dataset.o==o){T.querySelector('.onm').textContent=x.dataset.n;T.querySelector('.oi').textContent=i+1}});T.classList.remove('lo');var G=og(T);if(!G.querySelector('.sb button[data-v="'+v+'"]'))v='n';G.querySelectorAll('.sv').forEach(x=>x.classList.toggle('on',x.dataset.v==v));G.querySelectorAll('.sb button').forEach(x=>x.classList.toggle('on',x.dataset.v==v));history.replaceState(null,'','#'+t+(o!='all'&&o!=T.querySelector('.og').dataset.o?'-'+o:'')+(v=='o'?'-opinioni':''))}
function sv(v){sh(cur().dataset.k,v,og(cur()).dataset.o);scrollTo(0,0)}
function tl(){cur().classList.toggle('lo')}
function st(d){var T=cur(),B=[...T.querySelectorAll('.ol button')];if(!B.length)return;var i=B.findIndex(x=>x.classList.contains('on'));so(B[(i+d+B.length)%B.length].dataset.o)}
var X0=null,Y0;addEventListener('touchstart',function(e){X0=e.touches[0].clientX;Y0=e.touches[0].clientY},{passive:true});addEventListener('touchend',function(e){if(X0===null)return;var dx=e.changedTouches[0].clientX-X0,dy=e.changedTouches[0].clientY-Y0;X0=null;if(Math.abs(dx)>70&&Math.abs(dx)>2*Math.abs(dy)&&!e.target.closest('.ol'))st(dx<0?1:-1)});
addEventListener('keydown',function(e){if(e.target.tagName=='INPUT')return;if(e.key=='ArrowRight')st(1);if(e.key=='ArrowLeft')st(-1)});
function so(o){sh(cur().dataset.k,'n',o);scrollTo(0,0)}
function rh(){var h=location.hash.slice(1),op=/-opinioni$/.test(h);h=h.replace(/-opinioni$/,'');var t=h.split('-')[0];if(!['italia','mondo','sport','torino'].includes(t))t='italia';var o=h.slice(t.length+1)||null;sh(t,op?'o':'n',o)}rh();addEventListener('hashchange',rh);scrollTo(0,0)
var U=document.getElementById('up');
var ZS=[0.9,1,1.1,1.2,1.35,1.5,1.7],ZI=+(localStorage.getItem('anz')||2);function az(){document.documentElement.style.setProperty('--z',ZS[ZI])}function fz(d){ZI=Math.min(ZS.length-1,Math.max(0,ZI+d));localStorage.setItem('anz',ZI);az()}az()
// ---- lettore interno, ricerca, torna su ----
var RD=document.getElementById('rd'),RA=document.getElementById('ra');
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
var CUR=null,ORIG=false;
function body(i){var t=ORIG?i.xo:i.x;return t.split(/\n+/).map(p=>'<p>'+esc(p)+'</p>').join('')}
function rr(){var i=IT[CUR];RA.innerHTML='<div class="meta">'+esc(i.d)+'<span class="srcb">'+esc(i.src)+'</span>'+(i.fx?'<button class="otg" onclick="ORIG=!ORIG;rr()">'+(ORIG?'Italiano':'Originale')+'</button>':'')+'</div><h1>'+esc(i.t)+'</h1>'+(i.s?'<p class="lede">'+esc(i.s)+'</p>':'')+'<div class="rb">'+body(i)+'</div><p class="org"><a href="'+esc(i.l)+'" target="_blank" rel="noopener">Apri l\'originale ↗</a></p>'}
function or(id){if(!IT[id])return;CUR=id;ORIG=false;rr();RD.hidden=false;RD.scrollTop=0;document.body.classList.add('rdo');UU()}
function cr(){RD.hidden=true;document.body.classList.remove('rdo');UU()}
document.addEventListener('click',function(e){var a=e.target.closest('[data-i]');if(a){e.preventDefault();or(a.dataset.i)}});
addEventListener('keydown',function(e){if(e.key=='Escape'&&!RD.hidden)cr()});
function nz(s){return String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}
var HX={};for(var k in IT)HX[k]=nz(IT[k].t+' '+IT[k].s+' '+IT[k].x+' '+(IT[k].fx?IT[k].xo:''));
var Q=document.getElementById('q'),SR=document.getElementById('sr'),QT;
function srch(){var q=nz(Q.value.trim());document.body.classList.toggle('srch',!!q);if(!q){SR.innerHTML='';return}var w=q.split(/\s+/),r=[];for(var k in HX)if(w.every(x=>HX[k].includes(x)))r.push(k);SR.innerHTML='<h2 class="sec"><span>CERCA</span> '+r.length+' risultati</h2><div class="bg">'+r.slice(0,300).map(k=>{var i=IT[k];return '<a class="card" href="#" data-i="'+k+'"><div class="meta">'+esc(i.d)+'<span class="srcb">'+esc(i.src)+'</span></div><h3>'+esc(i.t)+'</h3>'+(i.s?'<p>'+esc(i.s)+'</p>':'')+'</a>'}).join('')+'</div>'}
Q.addEventListener('input',function(){clearTimeout(QT);QT=setTimeout(srch,120)});
function sc(){return RD.hidden?(document.scrollingElement||document.documentElement):RD}
function UU(){U.classList.toggle('on',sc().scrollTop>600)}
U.onclick=function(){sc().scrollTo({top:0,behavior:'smooth'})};
RD.addEventListener('scroll',UU);addEventListener('scroll',UU);
