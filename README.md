# AstroChat · Add Money prototype

Static HTML/CSS/JS. There's no build step.

## Deploy to Vercel
- **Dashboard:** go to vercel.com/new, choose "Deploy" with this folder dragged in, or push it to a GitHub repo and import it. Framework preset: **Other**. Leave the build command empty and the output directory as `.`.
- **CLI:** run `npm i -g vercel`, then `vercel` from inside this folder. Use `vercel --prod` for the production URL.

## Run locally
`npx serve .` or `python3 -m http.server`, then open http://localhost:3000 (or :8000).

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
In `app.js`, change `AMTS = [[amount, bonus], ...]`. GST is `GST_RATE` (18% of the amount only).
