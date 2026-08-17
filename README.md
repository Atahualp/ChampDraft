# Draft Room — v0.1

Live fantasy draft companion. Three files plus two icons, no backend, works offline.

## Deploy

1. Push `index.html`, `manifest.json`, `sw.js`, `icon-192.png`, `icon-512.png` to a GitHub repo.
2. Settings → Pages → deploy from branch, root.
3. Open the URL on your phone → Share → **Add to Home Screen**.

Must be served over HTTPS for the service worker to register. GitHub Pages does this by default. Opening `index.html` from the filesystem works, but without offline caching.

After first load it runs fully offline. When you update the app, bump `CACHE` in `sw.js` or the old shell will keep serving.

## What's in it

**League preset to your rules.** 12 teams, QB/RB/RB/WR/WR/TE/FLEX/K/DST + 7 bench, 16 rounds. Six-point passing TDs, −2 INT, 0.04/passing yard, and the per-game reception buckets. Every value is editable in Setup and the board re-ranks immediately.

**381 players** — FantasyPros projections joined to FantasyPros ADP and bye weeks, plus Yahoo consensus rank and the Winks + Norris blend (`trust` in the row meta).

**Scoring engine.** `computeProjectedPoints()` returns the exact linear part and the modeled bonus part separately. Reception buckets are computed as a per-game floor function with a Poisson distribution over catches; yardage-game bonuses use a Gamma distribution over per-game yards. Rows leaning >18% on modeling are tagged `est`.

**VORP** against baselines derived from league size and lineup, with FLEX resolved by pooling spare RB/WR/TE — currently landing at QB12 / RB30 / WR30 / TE12.

**Suggestions** use cost of waiting: for each position, the best available now versus the expected best survivor at your next pick, given a survival model over ADP with live drift correction. Backups are discounted by expected starts, so it won't hand you four quarterbacks.

**Mock draft.** "Sim to my pick" auto-drafts every other team at roughly one pick per second and stops when you're up. Each bot gets a random style at draft creation — chalk (follows ADP), needs (fills holes), sharp (drafts by VORP), gambler (reaches wildly). Styles show on the League tab.

## Validation

Everything below came from running full 192-pick drafts headlessly against the same engine the app ships.

**Survival calibration.** Predicted survival probability was checked against what actually happened, across 40 drafts. Mean error is 1.9 percentage points, tracking closely from the 10% bucket to the 90% bucket. Two earlier models were thrown out getting here: one biased by kickers and defenses sitting unclaimed in the ADP ordering, and one that assumed teams draft in strict rank order when they actually draft for need.

**Strategy benchmark, 60 drafts with identical bot behaviour:**

| Strategy | Starting lineup points |
|---|---|
| This engine | 1912 |
| Best VORP + roster needs | 1912 |
| Best available by ADP | 1759 |

Read that honestly. **The engine beats ADP-following by about 9%, and ties simple VORP-plus-needs exactly.** The value is in scoring your league correctly — six-point passing TDs, the reception buckets, two WR starters — not in the cost-of-waiting timing layer, which doesn't change the pick when opponents draft near ADP. Against a sharper room it should matter more, and the survival numbers are useful to read even when they don't flip the top suggestion.

**Roster shape.** Averaging around 2.8 QB / 2.9 RB / 4.1 WR / 4.2 TE / 1 K / 1 DST. The tight end count is higher than good practice, and the simulation can't settle it: bench composition barely moves starting points when nobody gets hurt and no bye weeks are modelled. Treat late-round suggestions as advisory and use your own judgement on depth.

## Known gaps

- **Kickers and defenses can't be scored properly.** The projections have no field-goal distance splits, and DST points-allowed and yards-allowed are season totals against per-game brackets. Both are ranked by consensus and marked `est`. Everything else is real.
- **Long-TD bonuses are ignored.** 40+ and 50+ yard TD bonuses need a distribution of touchdown lengths that nothing publishes. Small relative to the reception bucket, but it's a known blind spot.
- **`games` is assumed to be 17** for every player. If FantasyPros bakes expected missed time into season totals, per-game rates are understated for injury-prone players.
- **Fumbles score zero**, matching what the league settings showed. If a fumble category does exist, set `fumbleLost` in Setup.
- **75 of 381 players have no ADP** — mostly deep bench. They sort by consensus rank instead and never trigger steal flags.
- The per-game coefficients of variation (0.70 receiving, 0.55 rushing, 0.28 passing) are reasoned estimates, not fitted. They affect ordering among receivers more than anything else.
- **Bench depth is the weakest part of the engine.** VORP measures value above the last starter, which makes it a poor yardstick for players who'll never start. There's a discount based on effective starting slots, but the simulation can't tell whether it's calibrated.
- No injuries or bye weeks in the mock, so it overstates how little bench quality matters.

## Worth testing before draft night

Run three or four mocks from different draft slots. Specifically check:

- Whether the suggestions feel right in rounds 1–3, where the WR discount is most aggressive.
- What happens when you deliberately ignore the app for six rounds — does it recover sensibly?
- Pick entry speed. Tap a row, tap a team, done. If that's more than two taps in practice, tell me.
- Undo, both from the header and from a drafted player's sheet.
- Airplane mode after first load.

## Not built yet

Cloud sync for your son and co-owner (Phase 3), Sleeper live draft sync (Phase 4), and CSV import — the dataset is currently baked into `index.html`. Rankings lock into a session at creation, so a mid-draft data change can't shift your board.
