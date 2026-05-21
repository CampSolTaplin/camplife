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

// Carpool route animation — one cycle per .carpool-anim instance
document.querySelectorAll('.carpool-anim').forEach((wrap)=>{
  const entry = wrap.querySelector('.route-entry');
  const exit  = wrap.querySelector('.route-exit');
  const car   = wrap.querySelector('.car');
  const drop  = wrap.querySelector('.point-dropoff');
  const gate  = wrap.querySelector('.point-gate');
  const lDrop = wrap.querySelector('.label-dropoff');
  const lGate = wrap.querySelector('.label-gate');
  if(!entry || !exit || !car) return;

  const lenIn  = entry.getTotalLength();
  const lenOut = exit.getTotalLength();
  entry.style.strokeDasharray  = lenIn;
  exit.style.strokeDasharray   = lenOut;
  entry.style.strokeDashoffset = lenIn;
  exit.style.strokeDashoffset  = lenOut;

  // Constant-speed: longer segment => longer duration. ~140 px/sec.
  const PX_PER_SEC = 140;
  const DUR_IN  = Math.max(4000, Math.min(14000, Math.round(lenIn  / PX_PER_SEC * 1000)));
  const DUR_OUT = Math.max(4000, Math.min(14000, Math.round(lenOut / PX_PER_SEC * 1000)));
  const PAUSE_DROP=1800, PAUSE_GATE=1800, GAP=600;
  const CYCLE = DUR_IN + PAUSE_DROP + DUR_OUT + PAUSE_GATE + GAP;

  function ease(t){ return t; }  // linear — constant speed
  function setCar(path, prog){
    const L = path.getTotalLength();
    const p = path.getPointAtLength(prog * L);
    car.setAttribute('transform', 'translate('+p.x.toFixed(1)+' '+p.y.toFixed(1)+')');
  }

  setCar(entry, 0);

  let start = null;
  let running = false;
  function loop(ts){
    if(!running) return;
    if(!start) start = ts;
    const e = (ts - start) % CYCLE;

    if(e < DUR_IN){
      const t = ease(e / DUR_IN);
      entry.style.strokeDashoffset = String(lenIn * (1 - t));
      exit.style.strokeDashoffset = String(lenOut);
      car.classList.add('visible');
      drop.classList.remove('visible');
      gate.classList.remove('visible');
      lDrop.classList.remove('visible');
      lGate.classList.remove('visible');
      setCar(entry, t);
    } else if(e < DUR_IN + PAUSE_DROP){
      entry.style.strokeDashoffset = '0';
      drop.classList.add('visible');
      lDrop.classList.add('visible');
      setCar(entry, 1);
    } else if(e < DUR_IN + PAUSE_DROP + DUR_OUT){
      const t = ease((e - DUR_IN - PAUSE_DROP) / DUR_OUT);
      entry.style.strokeDashoffset = '0';
      exit.style.strokeDashoffset = String(lenOut * (1 - t));
      drop.classList.add('visible');
      lDrop.classList.add('visible');
      setCar(exit, t);
    } else if(e < DUR_IN + PAUSE_DROP + DUR_OUT + PAUSE_GATE){
      exit.style.strokeDashoffset = '0';
      gate.classList.add('visible');
      lGate.classList.add('visible');
      setCar(exit, 1);
    } else {
      entry.style.strokeDashoffset = String(lenIn);
      exit.style.strokeDashoffset = String(lenOut);
      drop.classList.remove('visible');
      gate.classList.remove('visible');
      lDrop.classList.remove('visible');
      lGate.classList.remove('visible');
      car.classList.remove('visible');
    }
    requestAnimationFrame(loop);
  }

  const obs = new IntersectionObserver((entries)=>{
    entries.forEach(en=>{
      if(en.isIntersecting && !running){
        running = true; start = null;
        requestAnimationFrame(loop);
      } else if(!en.isIntersecting){
        running = false;
      }
    });
  }, { threshold: 0.15 });
  obs.observe(wrap);
});