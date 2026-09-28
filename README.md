# AstroChat · Add Money prototype

Live: https://astrochat-pricing-v2.vercel.app/

## How to edit it
`index.html` is **generated**. Edit `src/template.html`, then run `python3 src/build.py`, which
inlines the fonts, icons and photos from `src/` and rewrites `index.html`. Pushing to `main`
redeploys Vercel automatically. `app.js` / `styles.css` are leftovers from an older build and
are not loaded by the page.

## Deploy to Vercel
- **Dashboard:** go to vercel.com/new and import the GitHub repo. Framework preset: **Other**. Leave the build command empty and the output directory as `.`.
- **CLI:** run `npm i -g vercel`, then `vercel` from inside this folder. Use `vercel --prod` for the production URL.

## Run locally
`npx serve .`, then open http://localhost:3000.

## What works
- **₹50, ₹100 and ₹250 amounts:** the selected tile gets the orange corner and tick.
  - **₹50:** gold card ("NO BONUS ON ₹50"), gold "You're missing out on a bonus" band, and the arc without the green line.
  - **₹100 and up:** green card showing amount + bonus, with a count-up. The band shows the live timer "Recharge offer valid for m:ss".
- **See More Options:** all 10 amounts in a scrollable list that runs under the card, with a mint or gold fade behind it and a custom scroll indicator. The indicator appears on open and while scrolling. See Less Options returns to 3 amounts; if a bigger amount was picked, it takes the third slot.
- **Payment Summary:** tap to expand the original breakdown:
  - Recharge amount, GST 18%, Total payable
  - "To be added in your wallet"
  - Recharge Added, Extra bonus, Total

  The card and arc stay mounted on top.
- **Pay with:** opens the original Select Payment Method sheet.

## Edit amounts and bonuses
In `src/template.html`: `BASE = [[amount, bonus], ...]` is the ₹ ladder and `USD` is the NRI one.
GST is `gstFor()` (18% of the amount only, and zero on NRI). The ASTRO50 coupon is `COUPON_FLAT`,
and it is itemised at checkout rather than folded into the bonus — anything showing a wallet
**total** must call `creditFor()`, which adds both, or the coupon goes missing from the total.

---

# Motion tokens

Everything below is measured off the running prototype (`src/template.html`), not redrawn from
a spec. The CSS column is the source of truth; the Compose column is the translation used by the
Android rebuild. Durations are milliseconds.

## Curves

| Token | cubic-bezier | Compose | Used by |
|---|---|---|---|
| `curve/standard` | `.2, .8, .2, 1` | `CubicBezierEasing(0.2f, 0.8f, 0.2f, 1f)` | selection border, payment-summary open/close |
| `curve/settle` | `.22, .9, .28, 1` | `CubicBezierEasing(0.22f, 0.9f, 0.28f, 1f)` | card tilt |
| `curve/snap` | `.3, 1.5, .5, 1` | `CubicBezierEasing(0.3f, 1.5f, 0.5f, 1f)` | corner tick spin |
| `curve/absorb` | `.24, 1.6, .36, 1` | `CubicBezierEasing(0.24f, 1.6f, 0.36f, 1f)` | number taking the hit |
| `curve/launch` | `.12, .8, .25, 1` | `CubicBezierEasing(0.12f, 0.8f, 0.25f, 1f)` | badge leaving the tile |
| `curve/hang` | `.45, 0, .55, 1` | `CubicBezierEasing(0.45f, 0f, 0.55f, 1f)` | badge at the top of its arc |
| `curve/fall` | `.4, 0, .8, .7` | `CubicBezierEasing(0.4f, 0f, 0.8f, 0.7f)` | badge falling into the card |
| `curve/count` | — (JS) | `EaseOutCubic` | every counting number |

`curve/snap`, `curve/absorb` and `curve/settle` overshoot on purpose (y > 1). Do not "fix" them.

## Durations

| Token | ms | Used by |
|---|---|---|
| `dur/press` | 120 | tile and chip press-down |
| `dur/fade` | 200 | summary content fading out |
| `dur/mark-in` | 280 | selection border |
| `dur/pop` | 300 | tile pop |
| `dur/box` | 350 | summary card padding + radius |
| `dur/expand` | 400 | summary height |
| `dur/tick` | 500 | corner tick |
| `dur/absorb` | 520 | number hit |
| `dur/tilt` | 620 | card tilt |
| `dur/flight` | 640 | badge drop |
| `dur/count-in` | 360 | counting to the recharge amount |
| `dur/count-bonus` | 700 | counting the bonus on |

---

## 1 · Light sweep

A pale diagonal highlight that crosses a surface, waits, and crosses again. Three places use it
with different rhythms. In all three the highlight travels on `transform`, never on `left` or
`background-position` of a laid-out box — animating position re-runs layout every frame and the
sweep visibly stutters.

**a. Discount band** (`.sweep`) — the ASTRO50 coupon band only. The offer band deliberately has none.

```css
/* the travelling highlight is 40% of the band's width, skewed 18 degrees */
width: 40%; left: -60%;
background: linear-gradient(100deg, transparent, rgba(255,255,255,.55), transparent);
animation: sweep 2.8s ease-in-out infinite;

@keyframes sweep {
  0%, 40%   { transform: translateX(0)    skewX(-18deg) }   /* 1120ms still */
  80%, 100% { transform: translateX(475%) skewX(-18deg) }   /* 1120ms travel, 560ms still */
}
```

`475%` is derived, not chosen: the travel is 190% of the *band's* width, and a translateX
percentage resolves against the *element's* own width, which is 40% of the band. 190 / 40 = 475.
If the highlight's width changes, this number has to be recomputed.

**b. SKU bonus badge** (`.chip::after`) — the "+₹150 more" pill on the collapsed row only. Nine of
these at once in the open grid reads as noise, so the grid has none.

```css
width: 38%;
background: linear-gradient(100deg, rgba(255,255,255,0), rgba(255,255,255,.4) 50%, rgba(255,255,255,0));
animation: chipSweep 3.2s linear infinite;
animation-delay: var(--sd);   /* negative, see below */

@keyframes chipSweep {
  0%        { transform: translateX(-120%) }   /* 1344ms travel */
  42%, 100% { transform: translateX(300%)  }   /* 1856ms still */
}
```

Two rules the badge sweep obeys, and both are product decisions rather than polish:

- **Staggered, and phase-stable across re-renders.** Badge *i* gets `animation-delay` of
  `-(((now - clockStart)/1000 + i * 0.38) % 3.2)` seconds. The 0.38s offset fans the row out; the
  negative delay means a badge that gets re-rendered resumes mid-cycle instead of restarting, so
  re-selecting an amount doesn't make the whole row flash in unison.
- **It stands down when it has nothing to sell.** The sweep is bait for a bonus you are *not*
  taking, so it runs only while the selected amount earns nothing. Pick ₹100 or more and the
  badges go still. It is also dropped whenever a live countdown is on the band — the clock should
  be the only moving thing. In both cases the rule is `display: none`, **not**
  `animation-play-state: paused`; a paused sweep freezes mid-pill as a visible pale streak.

**c. Loading skeleton** (`.strip::after`) — `shimmer 4.2s ease-in-out infinite`, background-position
`150% 0` → `-60% 0` over the first 60%, then still.

---

## 2 · Card movement on SKU change

Every tap on an amount replays a single tip of the congratulations card — it catches the light,
rocks back, and settles. It is one animation on the card's own transform; nothing inside it moves
independently.

```css
.ac.tilt { animation: cardTilt 620ms cubic-bezier(.22, .9, .28, 1) }

@keyframes cardTilt {
  0%   { transform: none }
  30%  { transform: rotateX(9deg)    rotateY(-6deg)   scale(1.03)  }
  62%  { transform: rotateX(-3.5deg) rotateY(2.5deg)  scale(1.006) }
  100% { transform: none }
}
```

Replay on **every** pick, including re-picking the amount already selected. In CSS that needs the
class removed, a forced reflow, then the class added again; in Compose, bump a key on the
`LaunchedEffect` that drives it.

The tile being tapped runs its own three, all starting together:

| Element | Spec |
|---|---|
| Tile press | `transform: scale(.96)`, `transition: transform 120ms ease` — on press only |
| Tile pop | `tilePop 300ms ease-out` — `scale(1) → 1.02 at 45% → 1` |
| Orange border + corner | `selin 280ms curve/standard` — `opacity 0, translate(3px, -3px) → opacity 1, none` |
| Corner tick | `tickSpin 500ms curve/snap, 50ms delay` — `opacity 0, rotate(-120deg) scale(.3) → opacity 1, none` |

The 50ms delay on the tick is what makes the corner read as arriving first and the tick as landing
into it. The border, corner and tick are also published together as a standalone Lottie on a
transparent background (`assets/sku-selected.json`), so they can be dropped onto any tile.

---

## 3 · Number animation

The figure on the card counts up. It is **three phases back to back**, not one count, because the
bonus is not supposed to be believable until the badge has physically arrived.

```
phase A   0 → 360ms     count from the previous figure to the recharge amount     (dur/count-in)
phase B   360 → 1000ms  figure holds at the recharge amount while the badge flies (dur/flight)
phase C   1000 → 1700ms count the bonus on, up to the new total                   (dur/count-bonus)
```

- Easing for both counts is `easeOutCubic` — `p => 1 - (1 - p)³`. Applied to the **value**, then
  rounded, so the digits themselves decelerate.
- If the figure is already at the recharge amount (the usual case on first entry), phase A is
  **0ms** and the sequence starts at phase B.
- At the exact frame phase C begins, the figure takes the hit — see §4.
- Set the figure in `font-variant-numeric: tabular-nums` (Compose: a monospaced-digit font
  feature). Without it the number's width changes every frame and the whole block jitters.

**When it does *not* run**, all three of which matter:

1. `prefers-reduced-motion: reduce` → jump straight to the total.
2. Bonus is zero (₹50) → there is nothing to count on, so no animation at all.
3. **Once per amount per visit.** Picking ₹100 drops its badge and counts; picking ₹100 again
   later just refreshes the number. Re-entering the screen resets the set and replays them all.

---

## 4 · Badge drop

The selected tile's "+₹150 more" pill lifts off the tile, arcs over, and is absorbed by the card.
Both endpoints are measured at call time from the two elements' bounding boxes, so it works
identically from the collapsed row and the open grid. `dx`/`dy` below are centre-to-centre.

```js
element.animate([
  {offset: 0,   opacity: 0, transform: `translate(0,0) scale(1) rotate(0deg)`,
                easing: 'cubic-bezier(.12,.8,.25,1)'},                                  // curve/launch
  {offset: .22, opacity: 1, transform: `translate(${dx*.03}px,-76px) scale(.92) rotate(-9deg)`,
                easing: 'cubic-bezier(.45,0,.55,1)'},                                   // curve/hang
  {offset: .34,             transform: `translate(${dx*.12}px,-68px) scale(.86) rotate(-3deg)`,
                easing: 'cubic-bezier(.4,0,.8,.7)'},                                    // curve/fall
  {offset: .86, opacity: 1},
  {offset: 1,   opacity: 0, transform: `translate(${dx}px,${dy}px) scale(.34) rotate(5deg)`},
], {duration: 640, delay: <phase A>, easing: 'linear', fill: 'both'});
```

Five things here are load-bearing:

1. **The velocity profile is the whole brief: fast → almost stopped → fastest on impact.**
   `0 → .26` leaves the tile hard and decelerates into the apex; `.26 → .40` is the direction
   change, 4px of travel over 14% of the flight, so it hangs; `.40 → 1` falls away accelerating
   the whole way, with no tail.
2. **Iteration easing must stay `linear`, with the easing carried per keyframe.** A single
   front-loaded curve over the whole animation remaps progress and the pill arrives long before
   the count starts.
3. **The fall is one keyframe interval.** Every extra waypoint restarts its own easing from zero
   velocity — a mid-flight waypoint measured as a drop from 2840 px/s to 70 px/s, a visible hitch
   just before the card. The `.86` keyframe carries opacity only, which does not split the
   transform interval.
4. **`curve/fall` is near free fall** (distance ∝ t²). It covers 8 / 30 / 62 / 85% of the drop at
   quarter / half / three-quarter / nine-tenths time, against free fall's 6 / 25 / 56 / 81. A
   steeper ease-in reads as hovering and then teleporting.
5. **Scale only ever decreases. Keep every value ≤ 1.** It used to balloon to 1.3 at the apex and
   shrink back; starting at full size and shrinking the whole way reads as the card absorbing the
   pill rather than the pill popping at the user.

The flying pill must use the **same** fill as the badge it left (`linear-gradient(180deg, …)` on
white) — any drift between the two reads as a colour change mid-flight.

Landing on offset `1` rather than `.9` puts arrival on the same frame as the number's hit:

```css
.amt.absorb { animation: absorb 520ms cubic-bezier(.24, 1.6, .36, 1) }
@keyframes absorb { 0% {transform:none} 24% {scale(1.14)} 58% {scale(.975)} 100% {transform:none} }
```

---

## 5 · Payment summary

Expand and collapse of the breakdown card. Four properties animate, on three different clocks, and
the staggering is what stops it looking like a box being stretched.

```css
/* the card itself — it loosens as it opens */
.ps-card          { padding: 8px 4px; border-radius: 12px;
                    transition: padding 350ms cubic-bezier(.2,.8,.2,1), border-radius 350ms }
.ps-card.open     { padding: 12px;    border-radius: 16px }

/* height, without measuring anything */
.ps-details       { display: grid; grid-template-rows: 0fr;
                    transition: grid-template-rows 400ms cubic-bezier(.2,.8,.2,1) }
.ps-card.open .ps-details { grid-template-rows: 1fr }
.ps-inner         { min-height: 0; overflow: hidden }

/* contents, held back so they arrive into an already-opening box */
.ps-inner         { opacity: 0; transition: opacity 200ms ease }
.ps-card.open .ps-inner { opacity: 1; transition: opacity 300ms ease 100ms; padding-top: 12px }

/* the collapsed row's "you get ₹250" gives up its space to the expanded version */
.ps-get           { transition: opacity 200ms }
.ps-card.open .ps-get { opacity: 0; width: 0; overflow: hidden }
```

- The `0fr → 1fr` grid trick animates to the content's natural height with no JS measurement and
  no `max-height` guess. Compose equivalent: `animateContentSize(tween(400, easing = curve/standard))`.
- The content fade is **asymmetric on purpose**: 300ms with a 100ms delay opening, 200ms with no
  delay closing. Opening, the box starts moving before the text appears; closing, the text is gone
  before the box finishes collapsing. Symmetric timings make the text visibly collide with the
  card edge on the way down.
- The chevron flips `rotate(180deg)` over **400ms** on `curve/standard` — slightly slower than the
  height, so the arrow is still turning as the box finishes. The collapsed "GST" label swaps its
  short form for its long form at the same moment, as a straight `display` swap with no crossfade.
