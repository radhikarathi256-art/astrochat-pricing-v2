/* AstroChat · Add Money — interactive prototype (no build step) */

// [amount, bonus]. Wallet credit = amount + bonus; GST = 18% of the amount only.
const AMTS = [[50,0],[100,150],[250,500],[500,300],[1000,500],[2000,800],[3000,1000],[4000,1200],[5000,1500],[10000,2000]];
const GST_RATE = 0.18;
const OFFER_SECONDS = 5 * 60;

const PM = [
  { k:'phonepe', n:'PhonePe', src:'assets/phonepe.png', raw:true },
  { k:'gpay',    n:'Gpay',    src:'assets/gpay.png' },
  { k:'paytm',   n:'Paytm',   src:'assets/paytm.png' },
  { k:'cred',    n:'Cred',    src:'assets/cred.png' },
];

const state = { sel:100, open:false, sumOpen:false, pmOpen:false, pm:'phonepe', shown:null };

const $ = id => document.getElementById(id);
const screen = $('screen');
const fmt = n => String(n);
const bonusFor = v => (AMTS.find(a => a[0] === v) || [0,0])[1];
const gstFor = v => Math.round(v * GST_RATE);
const isGold = () => bonusFor(state.sel) === 0;

/* ---------- tiles ---------- */
const CORNER = `<span class="corner"><svg width="38" height="38" viewBox="0 0 38 38"><path d="M0 0H38V38Z" fill="#EF6939"/><path class="tick" d="M30.2 11.1L24.3 16.2L21.4 13.5L21.9 12.8L24.3 14.9L29.7 10.3L30.2 11.1Z" fill="#fff"/></svg></span>`;
// Coin shower on the hero amount. Tiles are re-rendered from scratch on every tap, so each
// coin gets a negative delay off a single clock — otherwise the shower restarts on each tap.
const COIN_AMT = 100, COIN_CYCLE = 3.6, COIN_OFF = [0, .9, 1.8, 2.7, 3.3];
const coinClock = performance.now();
function coinfall(){
  const el = ((performance.now() - coinClock) / 1000) % COIN_CYCLE;
  return `<span class="coinfall" aria-hidden="true">${
    COIN_OFF.map(o => `<i class="coin" style="animation-delay:${(o - el).toFixed(2)}s"><i class="s"><b class="f"></b><b class="k"></b></i></i>`).join('')}</span>`;
}
function tile([v,b]){
  const on = v === state.sel;
  return `<div class="col">
    <div class="opt" role="radio" tabindex="0" aria-checked="${on}" aria-label="₹${fmt(v)}${b?`, ₹${fmt(b)} extra`:''}" data-amt="${v}">
      <div class="box ${on?'on':''}">${v===COIN_AMT?coinfall():''}<div class="sku"><span class="r">₹</span><span class="n">${v}</span></div>${on?CORNER:''}</div>
    </div>
    ${b?`<div class="chip"><p>+ ₹${fmt(b)}</p></div>`:''}
  </div>`;
}
// Collapsed row: ₹50 · ₹100 · ₹250, or the picked amount in the third slot when it's bigger.
function collapsedSet(){
  const base = AMTS.slice(0,3);
  if (state.sel <= 250) return base;
  return [AMTS[1], AMTS[2], AMTS.find(a => a[0] === state.sel)];
}
function renderTiles(){
  $('skus').innerHTML = collapsedSet().map(tile).join('');
  $('grid').innerHTML = AMTS.map(tile).join('');
}

/* ---------- band (timer; turns gold on ₹50) ---------- */
let remaining = OFFER_SECONDS;
const clock = s => `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
function bandInner(){
  if (isGold()) return `<div class="bandin"><img src="assets/warning.svg" alt=""><div><p class="l1">You're missing out on a bonus</p><p class="l2">Pick ₹100 or more to get extra</p></div></div>`;
  return `<div class="bandin"><img class="tag" src="assets/discount.svg" alt=""><div><p class="l1">Recharge offer valid for <b class="cd">${clock(remaining)}</b></p><p class="l2">Extra credit lands in your wallet instantly</p></div></div>`;
}
function renderBand(){
  const g = isGold();
  for (const el of [$('band'), $('band3')]) { el.className = (el.id === 'band' ? 'banner' : 'band3') + (g ? ' gold' : ''); el.innerHTML = bandInner(); }
}
setInterval(() => {
  remaining = remaining > 0 ? remaining - 1 : OFFER_SECONDS;   // loops for the prototype
  document.querySelectorAll('.cd').forEach(n => n.textContent = clock(remaining));
}, 1000);

/* ---------- card ---------- */
let animToken = 0;
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
function renderCard(animate = true){
  const v = state.sel, b = bonusFor(v), total = v + b, g = isGold();
  $('card').className = 'ac ' + (g ? 'gold' : 'green');
  $('payblock').classList.toggle('gold', g);
  // ₹50 earns no bonus; drop the eyebrow rather than calling that out
  $('cardE').hidden = g;
  const n = $('cardN'), token = ++animToken;
  const setN = x => { state.shown = x; n.textContent = fmt(x); alignCardRupee(); };
  // The reveal replays on every pick, but not on first paint. ₹50 earns no bonus, so it
  // has nothing to add on.
  if (!animate || reduced() || b === 0) { setN(total); return; }
  // Three beats: count up to the recharge amount, fly the bonus chip off its tile and
  // into the card, then count the bonus on from the frame it lands.
  const from = state.shown ?? v;
  const d1 = from === v ? 0 : 360, flight = 640, d2 = 700, t0 = performance.now();
  const ease = p => 1 - Math.pow(1 - p, 3);
  const lerp = (a, z, p) => Math.round(a + (z - a) * ease(p));
  flyBonus(b, d1, flight);
  let landed = false;
  const step = t => {
    if (token !== animToken) return;
    const e = t - t0;
    if (e < d1) setN(lerp(from, v, e / d1));
    else if (e < d1 + flight) setN(v);
    else if (e < d1 + flight + d2) {
      if (!landed) { landed = true; thump(); }
      setN(lerp(v, total, (e - d1 - flight) / d2));
    }
    else { setN(total); return; }
    requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
// pop the amount at the instant the chip arrives
function thump(){
  const a = document.querySelector('.ac .amt'); if (!a) return;
  a.classList.remove('absorb'); void a.offsetWidth; a.classList.add('absorb');
}
// Lift the chosen tile's "+₹X" chip off the tile and arc it into the card. Both ends are
// measured at call time, so it works from the collapsed row and the open grid alike.
function flyBonus(b, delay, dur){
  const root = state.open ? $('grid') : $('skus');
  const chip = root.querySelector(`[data-amt="${state.sel}"]`)?.closest('.col')?.querySelector('.chip');
  const amt = document.querySelector('.ac .amt');
  if (!chip || !amt) return;
  const sr = screen.getBoundingClientRect(), a = chip.getBoundingClientRect(), z = amt.getBoundingClientRect();
  const fly = document.createElement('div');
  fly.className = 'flyer';
  fly.innerHTML = `<p>+ ₹${fmt(b)}</p>`;
  Object.assign(fly.style, {
    left: (a.left - sr.left) + 'px', top: (a.top - sr.top) + 'px',
    width: a.width + 'px', height: a.height + 'px',
  });
  screen.appendChild(fly);
  const dx = (z.left + z.width / 2) - (a.left + a.width / 2);
  const dy = (z.top + z.height / 2) - (a.top + a.height / 2);
  // Each leg carries its own easing and the iteration stays linear, so the chip lands on
  // the last frame of the flight rather than racing ahead of it: lift well clear of the
  // tile and hang at the top, then drop onto the card and squash into the number.
  fly.animate([
    { offset: 0,   opacity: 0, transform: 'translate(0,0) scale(.9) rotate(0deg)', easing: 'cubic-bezier(.12,.75,.3,1)' },
    { offset: .28, opacity: 1, transform: `translate(${dx * .03}px,-50px) scale(1.3) rotate(-9deg)`, easing: 'cubic-bezier(.5,0,.92,.4)' },
    { offset: .66, opacity: 1, transform: `translate(${dx * .45}px,${dy * .36}px) scale(1.14) rotate(8deg)`, easing: 'cubic-bezier(.3,.08,.2,1)' },
    { offset: .9,  opacity: 1, transform: `translate(${dx}px,${dy}px) scale(.85) rotate(-5deg)`, easing: 'ease-out' },
    { offset: 1,   opacity: 0, transform: `translate(${dx}px,${dy}px) scale(.3) rotate(0deg)` },
  ], { duration: dur, delay, easing: 'linear', fill: 'both' })
    .finished.then(() => fly.remove(), () => fly.remove());
}
// Top-align the ₹ with the cap height of the number, using real glyph metrics.
const cx = document.createElement('canvas').getContext('2d');
function alignCardRupee(){
  const a = document.querySelector('.ac .amt'); if (!a) return;
  const r = a.querySelector('.r'), n = a.querySelector('.n');
  const m = (el, t) => { const c = getComputedStyle(el), size = parseFloat(c.fontSize), lh = parseFloat(c.lineHeight) || size;
    cx.font = `${c.fontWeight} ${size}px ${c.fontFamily}`; const mm = cx.measureText(t);
    const asc = mm.fontBoundingBoxAscent ?? size*.97, desc = mm.fontBoundingBoxDescent ?? size*.24;
    return (lh - (asc + desc)) / 2 + asc - mm.actualBoundingBoxAscent; };
  r.style.marginTop = (m(n, n.textContent) - m(r, '₹')).toFixed(2) + 'px';
}

/* ---------- payment summary (original breakdown) ---------- */
function renderSummary(){
  const v = state.sel, gst = gstFor(v), pay = v + gst, b = bonusFor(v), total = v + b;
  $('sumTxt').textContent = `₹${fmt(v)} + ₹${fmt(gst)} GST`;
  const dash = c => `<span class="ps-dash" style="--dc:${c}"></span>`;
  const row = (l, r, cls='') => `<div class="ps-line ${cls}"><span>${l}</span><span>${r}</span></div>`;
  $('psInner').innerHTML = `
    <div class="ps-sec">
      ${dash('#EAECF0')}
      <div class="ps-calc">${row('Recharge amount', `₹${fmt(v)}`, 'r1')}${row('GST (18%)', `₹${fmt(gst)}`, 'r2')}</div>
      ${dash('#EAECF0')}
      ${row('Total payable', `₹${fmt(pay)}`, 'tot')}
      ${dash('#EAECF0')}
    </div>
    <div class="ps-credit">
      <div class="ps-box ${b?'':'plain'}"><span>To be added in your wallet</span><b>₹${fmt(total)}</b></div>
      ${b ? `<div class="ps-panel">
        ${row('Recharge Added', `₹${fmt(v)}`, 'p1')}
        ${row('Extra bonus', `+₹${fmt(b)}`, 'pg')}
        ${dash('#D0D5DD')}
        ${row('Total', `₹${fmt(total)}`, 'pt')}
      </div>` : ''}
    </div>`;
  $('payBtn').innerHTML = `<b>Pay ₹${fmt(pay)}</b><small> (GST incl.)</small>`;
  $('pmPay').innerHTML = `<b>Pay ₹${fmt(pay)}</b><small> (GST incl.)</small>`;
  $('pmCredit').innerHTML = `Pay now &amp; <b class="g">get ₹${fmt(total)} added</b> <span class="w">in your wallet</span>`;
}
function setSumOpen(on){
  state.sumOpen = on;
  screen.classList.toggle('sumopen', on);
  $('sumToggle').setAttribute('aria-expanded', on);
  $('sumChev').classList.toggle('up', on);
  requestAnimationFrame(layoutOpen);
}

/* ---------- payment method sheet ---------- */
const logo = (m, cls) => `<span class="${cls}${m.raw?' raw':''}"><img src="${m.src}" alt=""></span>`;
function renderPM(){
  const cur = PM.find(m => m.k === state.pm);
  $('pp').innerHTML = logo(cur, 'logo') + cur.n;
  const pmRow = m => { const on = m.k === state.pm;
    return `<button class="pm-row" type="button" role="radio" aria-checked="${on}" data-pm="${m.k}">
      <span class="pm-name">${logo(m, 'pm-logo')}<span>${m.n}</span></span>
      <span class="pm-radio"><img src="assets/${on?'radio-on':'radio-off'}.svg" alt=""></span></button>`; };
  $('pmBody').innerHTML = `
    <div class="pm-group"><p class="pm-gt">Suggested</p><div class="pm-card">${pmRow(PM[0])}</div></div>
    <div class="pm-group"><p class="pm-gt">Other UPI app</p><div class="pm-card pm-list">${PM.slice(1).map(pmRow).join('<span class="pm-div"></span>')}</div></div>`;
}
function setPM(on){
  state.pmOpen = on;
  $('pmOverlay').classList.toggle('open', on);
  $('pmOverlay').setAttribute('aria-hidden', !on);
}

/* ---------- open list + scroll indicator ---------- */
let hideTimer;
function layoutOpen(){
  const wrap = $('openwrap'), sc = $('openscroll'), bar = $('sbar'), thumb = $('sthumb');
  const wrapTop = wrap.getBoundingClientRect().top;
  const cardTop = $('card').getBoundingClientRect().top - wrapTop;         // visible height above the card
  // padding so "See Less Options" can scroll clear of the card
  $('scrollpad').style.height = Math.max(0, wrap.clientHeight - cardTop + 16) + 'px';
  bar.style.height = Math.max(40, cardTop - 28) + 'px';
  const view = cardTop, total = sc.scrollHeight - (wrap.clientHeight - cardTop);
  const trackH = bar.clientHeight, h = Math.max(28, Math.round(trackH * Math.min(1, view / total)));
  const max = sc.scrollHeight - sc.clientHeight, p = max > 0 ? sc.scrollTop / max : 0;
  thumb.style.height = h + 'px';
  thumb.style.transform = `translateY(${Math.round((trackH - h) * p)}px)`;
}
function flashBar(ms = 1400){
  const bar = $('sbar'); bar.classList.add('on');
  clearTimeout(hideTimer); hideTimer = setTimeout(() => bar.classList.remove('on'), ms);
}
let switchTimer;
function setOpen(on){
  state.open = on;
  if (on) renderTiles();                       // fill the grid before it animates in
  screen.classList.toggle('open', on);
  screen.classList.add('switching');
  clearTimeout(switchTimer);
  // the layers are mid-transform while switching, so re-measure once they have settled
  switchTimer = setTimeout(() => { screen.classList.remove('switching'); layoutOpen(); }, 400);
  $('openwrap').setAttribute('aria-hidden', !on);
  $('seeMore').setAttribute('aria-expanded', on);
  if (on) { $('openscroll').scrollTop = 0; requestAnimationFrame(() => { layoutOpen(); flashBar(2000); }); }
  else renderTiles();
}
$('openscroll').addEventListener('scroll', () => { layoutOpen(); flashBar(); }, { passive:true });
addEventListener('resize', () => { layoutOpen(); drawRcpt(); });

/* ---------- receipt outline ---------- */
// Drawn at 1:1 so the dashes and the 1px stroke stay undistorted.
// The bottom is a corner and a bow, deliberately kept as two jobs. Trying to do both with
// one curve is what made every earlier version pinch: to swing the tangent from vertical to
// horizontal inside a shallow dip, the curvature has to spike right where the side ends —
// the old elliptical border-radius bottomed out at ry²/rx ≈ 3px there. So BR turns the
// corner on its own generous circular radius, and only then does a very shallow cubic bow
// across the middle, entering and leaving horizontally. Every join is tangent-continuous and
// the tightest curvature anywhere along the bottom is BR itself.
const R = 32, BR = 26, BOW = 14;
function drawRcpt(){
  const el = $('rcpt'), o = .5;                     // half the stroke, so it sits inside the box
  const W = el.clientWidth - o, H = el.clientHeight - o;
  const m = (W + o) / 2, B = H - BOW, c = (W - BR - m) * .55;
  $('rcptLine').setAttribute('viewBox', `0 0 ${el.clientWidth} ${el.clientHeight}`);
  $('rcptPath').setAttribute('d',
    `M${o} ${R}A${R} ${R} 0 0 1 ${o + R} ${o}H${W - R}A${R} ${R} 0 0 1 ${W} ${R}` +
    `V${B - BR}A${BR} ${BR} 0 0 1 ${W - BR} ${B}` +
    `C${W - BR - c} ${B} ${m + c} ${H} ${m} ${H}` +
    `C${m - c} ${H} ${o + BR + c} ${B} ${o + BR} ${B}` +
    `A${BR} ${BR} 0 0 1 ${o} ${B - BR}Z`);
}

/* ---------- selection ---------- */
function select(v){
  // Re-tapping the amount already selected replays the reveal, so rewind the counter to
  // the recharge amount and let the bonus beat run again from there.
  if (v === state.sel) state.shown = v;
  state.sel = v;
  renderTiles(); renderBand(); renderCard(); renderSummary();
  const c = $('card');                          // replay the Z tip on every pick
  c.classList.remove('tilt'); void c.offsetWidth; c.classList.add('tilt');
}

/* ---------- events ---------- */
screen.addEventListener('click', e => {
  const opt = e.target.closest('[data-amt]');
  if (opt) { select(+opt.dataset.amt); return; }
  if (e.target.closest('#seeMore')) { setOpen(true); return; }
  if (e.target.closest('#seeLess')) { setOpen(false); return; }
  if (e.target.closest('#sumToggle')) { setSumOpen(!state.sumOpen); return; }
  if (e.target.closest('#payWith')) { setPM(true); return; }
  if (e.target.closest('[data-pmclose]')) { setPM(false); return; }
  const pm = e.target.closest('[data-pm]');
  if (pm) { state.pm = pm.dataset.pm; renderPM(); setTimeout(() => setPM(false), 180); return; }
  // tap outside an open summary closes it
  if (state.sumOpen && !e.target.closest('.payblock')) setSumOpen(false);
});
screen.addEventListener('keydown', e => {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('[data-amt]')) { e.preventDefault(); select(+e.target.dataset.amt); }
  if (e.key === 'Escape') { if (state.pmOpen) setPM(false); else if (state.sumOpen) setSumOpen(false); }
});

/* ---------- boot ---------- */
renderTiles(); renderBand(); renderCard(false); renderSummary(); renderPM(); drawRcpt();
if (document.fonts) document.fonts.ready.then(() => { alignCardRupee(); layoutOpen(); });
