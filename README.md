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

**Watchlist.** Star players from the pick sheet. They pin to the top of the board with a live survival percentage against your next pick, sorted most-endangered first, with a count of how many are about to disappear. Players who get taken move to a "Gone" line rather than vanishing.

**Handcuff and stack flags.** `HC` marks a back who shares a backfield with one of yours — injury insurance. `STACK` marks a receiver or tight end catching passes from your quarterback, whose big weeks arrive together with his. Both derived from the team field, no extra data.

**Draft board grid.** The League tab toggles between rosters and a full rounds-by-teams wall, snake order intact, your column highlighted, colour-coded by position. Scrolls sideways.

**Bye-week planner.** A bar strip on My Team showing how many projected starters are off each week, flagging any week with three or more while you can still draft around it. The pick sheet also warns when a player shares a bye with two starters you already have.

**Export.** One button in Recap copies the whole draft — your lineup, bench, league table, and all 192 picks — as plain text for the league chat.

**Post-draft recap and grades.** A fifth tab that fills in as the draft runs. Shows your optimal starting lineup, a letter grade and league rank based on projected starting points, which positions you're strong and weak at versus the rest of the league, your best value picks and biggest reaches against ADP, how far your roster falls if a starter goes down, bye-week collisions among starters, and a full league table. Grades also appear on each team card in the League tab. All computed locally — no network, no API.

**Mock draft.** "Auto-sim" is a mode, not a one-shot. Arm it and the other eleven teams draft themselves at roughly two picks per second, halting the moment you're on the clock and resuming automatically once you make your selection — so a full mock takes about as long as your own decisions. Undo disarms it, so you can rewind without it immediately re-drafting what you just undid. Each bot gets a random style at draft creation — chalk (follows ADP), needs (fills holes), sharp (drafts by VORP), gambler (reaches wildly). Styles show on the League tab.

## Validation

Everything below came from running full 192-pick drafts headlessly against the same engine the app ships.

**Survival calibration.** Predicted survival probability was checked against what actually happened, across 40 drafts. Mean error is 1.9 percentage points, tracking closely from the 10% bucket to the 90% bucket. Two earlier models were thrown out getting here: one biased by kickers and defenses sitting unclaimed in the ADP ordering, and one that assumed teams draft in strict rank order when they actually draft for need.

**Strategy benchmark, 60 drafts with identical bot behaviour:**

| Strategy | Starting lineup points |
|---|---|
| This engine | 1921 |
| Best VORP + roster needs | 1904 |
| Best available by ADP | 1747 |

**The engine beats ADP-following by about 10%, and simple VORP-plus-needs by 17 points.** Most of the value is in scoring your league correctly — six-point passing TDs, the reception buckets, two WR starters — rather than in the timing layer, which only separates from plain VORP once roster construction starts to bind.

**Roster shape.** Averaging 2.0 QB / 4.2 RB / 5.8 WR / 2.0 TE / 1 K / 1 DST. Across 30 drafts, **zero** surplus tight ends were taken.

**How bench depth is handled.** VORP measures value above the last *starter*, so it stops being comparable between positions once you're drafting bench — and below replacement it's actively misleading. Leftover receivers read as −80 because the WR curve collapses past WR30; leftover tight ends read as −30 because the TE curve is shallow past TE12. So tight ends always looked "least bad" even though a third TE can never enter the lineup.

Three corrections work together:

1. A multiplier discounting value above replacement by effective starting slots (this league starts ~2.5 RB but 1 TE)
2. A flat penalty for stacking past those slots — needed because a multiplier does nothing at zero
3. A hard cap at single-start positions: no third QB or TE unless the player is genuinely above replacement

All three use the slot the player *would occupy* once drafted, not the current roster count. Kickers and defenses are never suggested beyond one.

## Reading the grades

Grades are **relative to the eleven other teams in that draft**, not an absolute scale — someone always finishes last, and a D in a sharp room may be a better roster than an A in a weak one. They rest on consensus projections, which are deliberately middle-of-the-road, and kicker and defense totals are incomplete. Treat the grade as a conversation starter and the positional breakdown as the useful part: "your RBs are 22 points above league average, your WRs 7 below" is actionable in a way that a letter isn't.

## Build 14 (cache v14)

**Head-to-head compare.** Open any player's card and tap *⚖ Compare with
another player*, then tap the second player anywhere — board, watchlist,
suggestions, grid. The sheet lays both out side by side (plan value, VORP,
points, our board, Norris / Winks / Consensus, ADP, survival to your next
pick, bye) and gives a verdict: which one to take first, by how many points,
and whether the other is likely to still be there. The verdict uses the exact
two-pick plan machinery behind the suggestions, refactored into a shared
`planEnv`/`planScore` so the two features cannot disagree — verified across
eight full drafts producing byte-identical suggestion output pre- and
post-refactor.

**Steal flag, finalized.** The trigger stays pure league math (12+ picks past
our board, positive VORP). Winks and Norris now layer on top of the player
card: when they also rank the player well above the market, the card says they
agree; when they rank him well below it, the card warns that the projections
may be missing news the analysts have. Experts corroborate or caution — they
never trigger.

## Build 13 (cache v13)

Rankings refreshed to the 2026-08-18 Yahoo consensus. The two trusted analysts
are shown separately — every player line reads **Norris, Winks, Consensus** in
that order — while their blend (`N+W`) remains the sort mode and the arbitrage
signal. Defenses finally join to their ranks (team-name mapping), and Brandon
Aubrey, previously missing from the pool entirely, is restored from his
FantasyPros projection row.

**Tight ends.** The app now encodes the league's actual behavior: one TE, then
stream from waivers. Suggestions never offer a second TE, the two-pick
lookahead never plans one, sim bots carry exactly one (about one team every
other draft grabs a second, late; a third never happens), and the survival
model knows a team holding a TE has near-zero remaining TE demand.

**Steals are league logic, not ADP.** A steal is a player still available 12+
picks past where THIS league's scoring ranks him, with positive VORP — kickers,
defenses, and second tight ends excluded. The recap grades every pick against
our board the same way, with the ADP gap as context only. ADP's one remaining
job is predicting the other eleven teams (survival), which is the only thing
it is actually evidence of.

Known data gap: Keenan Allen (now IND) has no projection row — the FantasyPros
exports predate his move, and the ADP file still lists him on LAC. Re-export
FantasyPros WR projections and ADP before draft night and rebuild.

## Build 17 (cache v17)

**Bench in the Recap.** A card below the starting lineup lists every bench
player with his projection, sorted by points, and tagged with what he is
actually for: `handcuff` behind one of your own backs, `plugs week N` when he
covers a bye your starters leave open, `outprojects a starter`, `same bye as
your starter` when he does not help, or plain `depth`. A closing line names the
weeks no bench player can fill, so waiver weeks are explicit.

**Honest late-round suggestions.** Once your starting slots are full, the panel
stops printing a confident VORP number. It shows each candidate's marginal
value in points over a waiver streamer plus the expected weeks he would spend
in your lineup, and says so in a line above: "Your starters are set — these are
bench picks. The best is worth about 3 points over streaming that spot. Take
the upside you like."

**Valuation: rebuilt, measured, and reverted.** The R8 backup-QB suggestion
prompted a rebuild around option value (expected weeks in lineup x points over
a waiver streamer). It was tested four ways against the existing formula over
300 paired drafts on identical seeds and lost every time: -4.4, -5.1 and -5.7
points per draft, t = -3.4 to -4.3. Slot-by-slot analysis found the loss at
tight end (-9.0 per draft) and WR1 (-4.8) — pricing a STARTER against the
waiver wire understates elite tight ends, because a waiver TE is nearly
startable while a waiver RB is dire, and that skipped the round-2 tight end
this league's reception scoring makes valuable. The engine therefore keeps
VORP; option value survives as the honest display above. The full reasoning is
in the comment block above `adjVal`.

**Opponent model corrected.** Bots could each hoard two quarterbacks, consuming
32 QBs a draft in a one-QB league. They now carry one, with about a third of
teams taking a backup late — 16 QBs a draft, which matches real rooms. This
also fixed the waiver-QB level (was QB33, now QB17) that the option-value work
depended on. Survival was refit against the corrected opponents: band-MAE
1.01pp with +0.08pp bias, out of sample.

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
