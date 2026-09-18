# AstroChat · Bonus highlight prototype

Interactive HTML prototype of the Add Money to Wallet flow.

## Open it
Double-click **index.html**. It's one self-contained file (all icons embedded), so it works offline and can be committed or hosted as-is.
- On a phone: full-screen, with a small **Flows ▾** button at the top to jump between paths.
- On desktop: framed phone with a toolbar of paths.
- Deep links: `index.html?start=home | wallet | listingChat | again | history` (add `&view=mobile` to force the phone layout).

## Flows
| Path | Route |
|---|---|
| Wallet | Home → wallet chip → Add Money |
| Insufficient balance | Home → astrologer card → Chat → low balance → Add Money (red warning rises when ₹50 is picked) |
| Coupon | Recent chats → Chat Again → low balance → coupon popup → Add Money (ASTRO50 banner) |
| ₹5/min offer | Recent chats → View History → Continue Chat → low balance → offer popup → Add Money |

## Edit it
- All markup, styles and logic: `src/template.html`
- Icons (exported from Figma): `src/icons/`
- Optional photos (avatars, promo banner, low-wallet art): drop `vippsana`, `hemali`, `chat`, `promo`, `lowWallet` images into `src/photos/`; the stand-ins are replaced automatically.
- Rebuild after editing: `python3 src/build.py` (Python 3, no packages needed) → regenerates `index.html`.

## Key numbers and rules (in `src/template.html`)
- `BASE` — amounts and standard bonuses; `COUPON` — coupon bonuses
- `ASTRO_RATE` — astrologer rate used for the per-minute price (₹25/min)
- GST 18% on the recharge amount; wallet credit = amount + bonus
- Count-up animation plays once per amount per visit; ₹50 (no bonus) never animates
- Rays show at ₹250 and above

Fonts load from Google Fonts (Inter); without internet the page falls back to the system font.
