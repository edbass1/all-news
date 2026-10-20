(function(){
var S=JSON.parse(document.getElementById('S').textContent);
var ZS=[0.9,1,1.1,1.2,1.35,1.5,1.7],ZI=+(localStorage.getItem('anz')||2);
function az(){document.documentElement.style.setProperty('--z',ZS[ZI])}
window.fz=function(d){ZI=Math.min(ZS.length-1,Math.max(0,ZI+d));localStorage.setItem('anz',ZI);az()};az();
function esc(s){return String(s||'').replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function meta(i){return '<div class="mt"><time>'+esc(i.d)+'</time><span class="pill">'+esc(i.src)+'</span></div>'}
function ini(s){return esc(String(s||'').replace(/^(the|il|la|le|el|de|der)\s+/i,'').split(/\s+/).map(function(w){return w[0]}).join('').slice(0,3).toUpperCase())}
var SZ=['xl','tall','w','','','w','',''];
function tile(i,id,s,c){
 if(i.op)return'<a class="t op'+(s?' '+s:'')+'" href="#" data-i="'+id+'"><span class="tag">OPINIONE</span>'+meta(i)+'<h3>«'+esc(i.t)+'»</h3></a>';
 return'<a class="t '+(s||'')+' ni c'+c+'" href="#" data-i="'+id+'"><div class="tx">'+(i.lv?'<span class="tag lv">● LIVE</span>':'')+meta(i)+'<h3>'+esc(i.t)+'</h3>'+(i.s?'<p>'+esc(i.s)+'</p>':'')+'</div></a>'}
function bento(news,ops){var h='',j=0,k=0;
 news.forEach(function(id,x){if(x>=2&&(x-2)%4==0&&ops[j]){h+=tile(IT[ops[j]],ops[j],j==0?'tall':'',0);j++}
  var s=x<SZ.length?SZ[x]:(x%9==4?'w':'');h+=tile(IT[id],id,s,k++%6)});
 while(ops[j]){h+=tile(IT[ops[j]],ops[j],'',0);j++}
 return '<div class="bento">'+h+'</div>'}
var tab='italia',oi=0;
var hd='<header class="hd"><div class="hin"><a class="logo" href="#" onclick="return false"><span>ALL</span>NEWS</a><nav class="tabs">'+S.tabs.map(function(t){return '<button data-t="'+t.k+'">'+esc(t.label)+'</button>'}).join('')+'</nav><input id="q" type="search" placeholder="CERCA" autocomplete="off" aria-label="Cerca nelle notizie"><span class="upd">Aggiornato '+esc(S.upd)+'</span><span class="fz"><button onclick="fz(-1)" aria-label="Riduci testo">A−</button><button onclick="fz(1)" aria-label="Ingrandisci testo">A+</button></span></div></header>'+
'<div class="sel"><button class="ar" data-d="-1" aria-label="Giornale precedente">‹</button><div class="nm"><b></b><small></small></div><button class="ar" data-d="1" aria-label="Giornale successivo">›</button></div><main id="m"></main>'+
'<footer>ALL NEWS · Aggiornamento automatico ogni ora · Solo articoli gratuiti</footer>'+
'<button id="up" aria-label="Torna su">↑ Su</button><div id="rd" hidden><div class="rin"><div class="rbar"><span class="fz"><button onclick="fz(-1)" aria-label="Riduci testo articolo">A−</button><button onclick="fz(1)" aria-label="Ingrandisci testo articolo">A+</button></span><button class="rx" aria-label="Chiudi">✕ Chiudi</button></div><article id="ra"></article></div></div>';
var W=document.createElement('div');W.id='app';W.innerHTML=hd;document.body.appendChild(W);
var M=document.getElementById('m'),Q=document.getElementById('q');
function T(){return S.tabs.filter(function(t){return t.k==tab})[0]||S.tabs[0]}
function draw(push){var t=T(),o=t.outlets[oi]||t.outlets[0];
 document.querySelectorAll('.tabs button').forEach(function(b){b.classList.toggle('on',b.dataset.t==tab)});
 var sel=document.querySelector('.sel');sel.classList.toggle('one',t.outlets.length<2);
 sel.querySelector('b').textContent=o?(o.name||t.label):t.label;sel.querySelector('small').textContent=t.outlets.length>1?(oi+1)+' / '+t.outlets.length:'';
 M.innerHTML=o?bento(o.news,o.ops):'<p class="na">Nessuna notizia al momento.</p>';
 if(push!==false)history.replaceState(null,'','#'+tab+(oi>0&&o?'-'+o.o:''))}
function rh(){var h=location.hash.slice(1),p=h.split('-'),t=p[0];if(!S.tabs.some(function(x){return x.k==t}))t='italia';tab=t;var rest=h.slice(t.length+1);oi=Math.max(0,T().outlets.findIndex(function(o){return o.o==rest}));draw(false)}
document.querySelector('.tabs').onclick=function(e){var b=e.target.closest('button');if(b){tab=b.dataset.t;oi=0;Q.value='';draw();scrollTo(0,0)}};
function st(d){var L=T().outlets.length;if(L<2)return;oi=(oi+d+L)%L;Q.value='';draw();scrollTo(0,0)}
document.querySelectorAll('.sel .ar').forEach(function(b){b.onclick=function(){st(+b.dataset.d)}});
addEventListener('keydown',function(e){if(e.target.tagName=='INPUT'||!RD.hidden)return;if(e.key=='ArrowRight')st(1);if(e.key=='ArrowLeft')st(-1)});
var X0=null,Y0;addEventListener('touchstart',function(e){X0=e.touches[0].clientX;Y0=e.touches[0].clientY},{passive:true});
addEventListener('touchend',function(e){if(X0===null||!RD.hidden)return;var dx=e.changedTouches[0].clientX-X0,dy=e.changedTouches[0].clientY-Y0;X0=null;if(Math.abs(dx)>80&&Math.abs(dx)>2*Math.abs(dy)&&!e.target.closest('.tabs'))st(dx<0?1:-1)});
function nz(s){return String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}
var HX={};for(var k in IT)HX[k]=nz(IT[k].t+' '+IT[k].s+' '+IT[k].x+' '+(IT[k].fx?IT[k].xo:''));
var QT;Q.addEventListener('input',function(){clearTimeout(QT);QT=setTimeout(function(){var q=nz(Q.value.trim());if(!q)return draw();var w=q.split(/\s+/),r=[];for(var k in HX)if(w.every(function(x){return HX[k].indexOf(x)>=0}))r.push(k);
 M.innerHTML='<h2 class="sr">CERCA · '+r.length+' risultati</h2><div class="bento">'+r.slice(0,300).map(function(id,x){return tile(IT[id],id,'',x%6)}).join('')+'</div>'},120)});
var RD=document.getElementById('rd'),RA=document.getElementById('ra'),CUR=null,ORIG=false;
function rr(){var i=IT[CUR],tx=ORIG?i.xo:i.x;RA.innerHTML='<div class="mt"><time>'+esc(i.d)+'</time><span class="pill">'+esc(i.src)+'</span>'+(i.fx?'<button class="otg" onclick="window.tgo()">'+(ORIG?'Italiano':'Originale')+'</button>':'')+'</div><h1>'+esc(i.t)+'</h1>'+(i.s?'<p class="lede">'+esc(i.s)+'</p>':'')+'<div class="rb">'+String(tx||'').split(/\n+/).map(function(p){return'<p>'+esc(p)+'</p>'}).join('')+'</div><p class="org"><a href="'+esc(i.l)+'" target="_blank" rel="noopener">Apri l\'originale ↗</a></p>'}
window.tgo=function(){ORIG=!ORIG;rr()};
document.addEventListener('click',function(e){var a=e.target.closest('[data-i]');if(!a)return;e.preventDefault();if(!IT[a.dataset.i])return;CUR=a.dataset.i;ORIG=false;rr();RD.hidden=false;RD.scrollTop=0;document.body.classList.add('rdo');uu()});
function cr(){RD.hidden=true;document.body.classList.remove('rdo');uu()}
document.querySelector('.rx').onclick=cr;addEventListener('keydown',function(e){if(e.key=='Escape'&&!RD.hidden)cr()});
var U=document.getElementById('up');function sc(){return RD.hidden?(document.scrollingElement||document.documentElement):RD}
function uu(){U.classList.toggle('on',sc().scrollTop>500)}addEventListener('scroll',uu);RD.addEventListener('scroll',uu);
U.onclick=function(){sc().scrollTo({top:0,behavior:'smooth'})};
addEventListener('hashchange',rh);rh();scrollTo(0,0);
})();
