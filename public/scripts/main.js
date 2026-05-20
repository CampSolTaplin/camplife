// Nav scroll state
const nav=document.getElementById('nav'),sp=document.getElementById('scrollProgress');
function onScroll(){
  nav.classList.toggle('scrolled',scrollY>40);
  const max=document.documentElement.scrollHeight-innerHeight;
  sp.style.width=(max>0?scrollY/max*100:0)+'%';
}
addEventListener('scroll',onScroll,{passive:true});onScroll();

// Reveal
const io=new IntersectionObserver((es)=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}}),{threshold:.12,rootMargin:'0px 0px -50px 0px'});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

// Carpool tabs
document.querySelectorAll('.cp-tab').forEach(t=>t.addEventListener('click',()=>{
  const id=t.dataset.loc;
  document.querySelectorAll('.cp-tab').forEach(x=>x.classList.toggle('active',x===t));
  document.querySelectorAll('.cp-detail').forEach(d=>d.classList.toggle('active',d.dataset.loc===id));
}));

// Accordions
document.querySelectorAll('.acc-head').forEach(h=>h.addEventListener('click',()=>{
  const it=h.parentElement,wasOpen=it.classList.contains('open');
  // only close siblings within same list
  it.closest('.acc-list').querySelectorAll('.acc-item').forEach(i=>i.classList.remove('open'));
  if(!wasOpen)it.classList.add('open');
}));

// Activity filter
document.querySelectorAll('.fpill').forEach(p=>p.addEventListener('click',()=>{
  const f=p.dataset.f;
  document.querySelectorAll('.fpill').forEach(x=>x.classList.toggle('active',x===p));
  document.querySelectorAll('.acard').forEach(c=>c.classList.toggle('hide',!(f==='all'||c.dataset.c===f)));
}));

// Pack list + localStorage
(function(){
  const KEY='camplife_pack_v1',boxes=document.querySelectorAll('#bringList input'),fill=document.getElementById('bFill'),pct=document.getElementById('bPct');
  try{const s=JSON.parse(localStorage.getItem(KEY)||'{}');boxes.forEach(b=>{if(s[b.id])b.checked=true;});}catch(e){}
  function upd(){let c=0;const s={};boxes.forEach(b=>{if(b.checked){c++;s[b.id]=true;}});const p=Math.round(c/boxes.length*100);fill.style.width=p+'%';pct.textContent=p+'%';try{localStorage.setItem(KEY,JSON.stringify(s));}catch(e){}}
  boxes.forEach(b=>b.addEventListener('change',upd));upd();
})();

// Mobile menu (basic toggle - scroll to anchor via native)
document.querySelector('.nav-toggle')?.addEventListener('click',()=>{
  document.querySelector('.nav-links').style.display=
    getComputedStyle(document.querySelector('.nav-links')).display==='none'?'flex':'none';
});