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

## Build 26 — 8/28 data drop, analyst prose, note repairs

**Projections, ADP, byes and all three rank columns refreshed.** 4for4's 8/28
projections and their standard 6-pt-passing-TD rankings; Winks and Norris from
the 8/28 Yahoo consensus; FantasyPros for kickers and defences, which 4for4 does
not rank at all. 88 stat lines moved, 197 ADPs, 305 4for4 ranks.

**The two analysts barely moved.** Only six players shifted 40 or more spots, and
all six sit between 200 and 300 where the noise is largest — Penix up 93 for
Norris, Cousins down 90. The top 150 is effectively unchanged since 8/24. A
refresh that changes nothing important is still worth doing; it is the only way
to know it changed nothing.

**Two matching faults, both worth remembering.** 4for4 drops generational
suffixes, so their "James Cook" and Yahoo's "J. Cook III" are different strings
for one man, and they spell Jacksonville `JAX` where every other source uses
`JAC`. Together those produced 87 phantom duplicate players on the first run.
The fix keys on initial-plus-surname and keeps the suffix beside the key as a
tiebreaker rather than inside it. One collision needs more than the suffix:
Bijan Robinson and Brian Robinson Jr. are both Atlanta running backs printed as
B. Robinson, and only the first name separates them.

**Analyst prose on the card.** Two pieces, 32 notes across 28 players. The first
is Paulsen's write-up of the same target board the build already carried — every
player and round matches `pt`, so the tiering does not move and the argument is
what is new. The second is a 4for4 piece on weeks 1-6, which is genuinely new
information: the app already models the playoff weeks and had nothing on the
opening month. Summaries are written at build time rather than lifted, because a
phone card has room for the claim and not the essay.

Neither feeds the suggestion engine, for the same reason the news flag does not:
prose argues for a pick, it must not silently reprice one.

**Two defects repaired in the inherited scouting notes.** Eight ran past the end
of their own card into the next one, so the Brock Purdy note finished by
discussing Kyle Pitts and the Isaiah Likely note ended on Michael Pittman. And
Devontez Walker (WR BAL) was holding a note that describes Kenneth Walker III
(RB KC) — the original self-naming check passed it because both men are called
Walker. Surname matching cannot separate those two; only the content can. The
note now sits on the Kansas City back, who previously had none.

**Two things that look like regressions and are not.** The VORP baselines resolve
to RB32 / WR28, not the WR30 written above in this file — v25 already resolved
that way, so the older text is stale rather than the build being wrong. And
Denver's defence surfaces around 20th overall on a raw VORP sort, which is the
same artefact that put the Rams at 24th and the Texans at 27th in v25: DST
scoring still has no per-game brackets. Denver rose because FantasyPros lifted
their sack projection from 48 to 59.8.

**Carried over unchanged:** depth-chart slots, playoff strength of schedule, the
news flags, and Paulsen's tiers. The playoff schedule is unchanged because the
schedule itself is; recomputing it against the new defensive projections would
need an opponent map that none of these files contain, so those numbers still
reflect the 8/24 pull and META says so.

## Build 25 — playoff schedule and Paulsen targets

**Playoff strength of schedule.** The card flags a player whose weeks 14-16
opponents are materially easier or harder than average: "weeks 14-16 his
opponents allow 2.3 points a game fewer than league average. Fine for the
regular season; it bites in the weeks that decide the title."

Opponent quality comes from the app's own DST projections — points allowed per
game — rather than an outside rating, so the yardstick is the same one the board
already trusts. Range runs from the Chargers, Broncos and Cardinals (easiest) to
the Cowboys, Commanders and Eagles (hardest), a spread of about six points a
game between the extremes. Only flagged past +/-1.5 points, since below that it
is noise.

**Paulsen's target board.** All 68 entries from his 8/21 Strategery table, with
his own tiering preserved: autopick, primary target, or a player he likes at that
ADP. Shown on every card, but it only lights up green and puts a star on the
board row when you are actually within a round of his — a round-6 autopick is
information in round 1 and a decision in round 6.

Neither feeds the suggestion engine. Both are context for a human holding the
pick.

## Build 25 — 8/24 data drop (same version, refreshed data)

**Projections, ADP and byes refreshed to the 8/24 4for4 export.** 36 stat lines
genuinely changed: Ashton Jeanty -36 points (the ankle), Kayshon Boutte +37 (the
Houston move), Xavier Hutchinson -33, Mike Washington Jr. +31.

**Analyst notes on the player card.** 62 players carry 4for4's written scouting
note, parsed out of the Notes PDF. This is the "player outlook" the live feeds
could not provide: Sleeper carries status flags only, and ESPN needs a network.
These ship inside the build, so they work on a dead connection and cannot go
stale mid-draft.

Extraction was the whole job. Straight text extraction joins words across line
breaks ("back-to-backseasons"), and matching notes to players by position drifts
whenever a card's prose spills onto the next page — that scored 44 of 96 correct.
Rebuilding each of the three card columns from pdfplumber's word coordinates
recovered the spacing, and matching each note to whichever player's surname
appears in its opening clause removed the ordering dependency entirely. Every
note is verified to name its own subject before it is kept; 62 survive that check
and none are misattributed.

**Dated news flags.** Ten players carry a flag from the 8/24 risers-and-fallers
piece — Jordyn Tyson out roughly two months, Alvin Kamara out a month, Jeremiyah
Love and Isiah Pacheco and Chuba Hubbard to monitor, Tucker Kraft and George
Kittle cleared, Keenan Allen signed with the Colts. Red, amber or green on the
card with a diamond on the board row.

These are deliberately NOT folded into the projections. A flag informs the pick;
silently repricing a player would hide the judgement inside a number.

## Build 25 (cache v25)

**Winks and Norris refreshed to 8/24.** 350 players matched, 283 blends moved.
4for4 ranks, projections, ADP and depth charts are unchanged from the 8/22 pull.

Two roster changes came out of the file rather than a news feed: **Kayshon
Boutte is now Houston**, which moved his expert blend from 233 to 152 — the
Jayden Higgins ACL created that opening — and **Trey Benson has been released**,
so he carries no team. Both had their depth-chart slots cleared, since those
came from the old team's chart and would otherwise be quietly wrong.

**A name collision caught in review, worth recording.** The join key stripped
generational suffixes, so "B. Robinson" (Bijan, ranked 2) and "B. Robinson Jr."
(Brian, ranked 154) collapsed to the same key and Brian's rank landed on Bijan —
the app's second overall player briefly showed an expert blend of 189. The key
now preserves the suffix. A sanity pass over the largest rank moves is what
surfaced it: a top-two player moving 187 places is not a ranking update, it is a
bug, and the size of the move was the tell.

## Build 24 (cache v24)

**Each feed reports for itself in Setup.** The status line covered only injuries,
so a blocked ESPN call and a quiet news day looked identical — no headlines
either way, and no way to tell which. Setup now reads: "Feeds loaded 2h ago.
Injuries: 63 designations · depth chart: 1,412 players. ESPN headlines: 74
articles across 58 players", or names the specific failure. They fail
independently and now they report independently.

**Two badges no longer collide.** The pill beside a player's name was his rank
at his position on OUR board; the badge below was his slot on his TEAM's depth
chart. Both rendered as bare "RB2" / "RB1" inches apart, which is a bad thing to
misread on the clock. They now read "board RB2" and "depth RB1".

## Build 23 (cache v23)

**Depth chart cross-checked against the live feed.** The baked slots come from a
4for4 PDF snapshot; camp battles move after that. Sleeper's player records carry
depth_chart_order, so the card now compares the two and says which way it went:
"the 4for4 snapshot has him RB2, the live feed has him RB1 — a promotion since
the chart was pulled." Green for a promotion, amber for a slip, and a green
triangle on the board row so it is visible while scanning rather than only on a
tap. A player absent from the PDF but present on the live chart gets his live
slot instead. The wording says two sources rather than asserting one is right,
because Sleeper's depth order is itself patchy in the preseason.

**ESPN headlines.** Sleeper carries designations and nothing else, so ESPN's
public news JSON is now a second source: up to three headlines per player, each
linked and timestamped. Articles are pinned to players through their athlete
categories, keyed on name alone — the category rarely carries a team, and a
headline about a player is about him wherever he plays.

Both calls sit outside the main fetch's try block. If ESPN is down the injuries,
depth and trends still land; if Sleeper is down the whole news layer goes quiet
and the board is untouched. Tested both ways.

Neither endpoint could be reached from the machine this was built on, so both
paths remain unverified until someone presses Refresh player news on a real
network.

## Build 22 (cache v22)

**Depth-chart slot on every player.** Parsed from the 4for4 depth-chart PDF and
matched to 360 of 361 skill and kicker players. Board badges read RB1, WR3, TE2
instead of a bare position, and the card carries the same. A player who appears
on no depth chart at all is called out in red — Jake Moody is not on
Washington's, which is exactly the kind of thing worth knowing before you spend
a pick on him.

Matching needed two fixes worth recording. The PDF drops generational suffixes
and breaks hyphenated names across lines, so "Jaxon Smith-Njigba" arrives as
"SmithNjigba" and "James Cook III" as "James Cook" — normalising to letters only
and stripping suffixes recovered 30 players. And the bare "K" row label also
matched the K in "J.K. Dobbins", splitting Denver's backfield in half and losing
three backs; the marker now requires no adjacent letter or period. Three
nickname mismatches (Kenny/Kenneth Gainwell, Chig/Chigoziem Okonkwo,
Andy/Andres Borregales) fell to a surname fallback scoped to the right team and
position.

**Trending adds — the only good news Sleeper has.** The player feed carries
injury designations and nothing else: no outlooks, no analysis, no positive
news. What it does expose is waiver-add velocity, so a player spiking across
leagues now gets a green line on his card with the 24-hour add count. In August
that spike usually means a promotion, a camp report, or the man ahead of him
going down. It is a "look into this" flag and the wording says so rather than
pretending to explain. The trending call sits outside the main fetch's try
block, so if it fails the injury data still lands.

## Build 21 (cache v21)

**Sort cycle is now VORP -> ADP -> AVG -> 4F.** The Norris+Winks blend was
dropped as a sort mode in favour of the three-source average. A session that
saved the old 'trusted' mode falls back to VORP rather than landing on a mode
that no longer exists. The N+W blend still exists internally for the steal
corroboration on the player card.

**Player news on the card.** Injury designations, body part and note from
Sleeper's public player feed — free, no key, and CORS-permissive, which matters
because this is a static page on GitHub Pages with no server to proxy through.
An injured player gets a coloured rule on his card and a dot on his board row:
red for Out/IR/Doubtful, amber for Questionable. Healthy players say so, with
the feed's age, because a blank card is ambiguous between "fine" and "no data".

The feed is fetched once at boot, cached in IndexedDB for six hours, and
refreshable from Setup. It is the only outbound call the app makes besides its
own update check, and every path fails silently: a blocked or offline feed
leaves the board fully usable and simply omits the news lines. Tested both ways.

Three honest limits: designations lag practice reports by hours, so a hit is
confirmation and an absence is never an all-clear; the feed carries status flags
rather than beat-writer copy, so "left practice early" only appears once a team
files it; and the call path could not be verified from the machine this was
built on, so it needs one real test on wifi before draft day.

**Bug found by the news test.** The in-memory storage fallback is shared between
sessions and the new cache store, so a cached feed was being returned by
listSessions and crashed the Setup screen on s.picks.length. Only records that
are actually sessions leave that function now.

## Build 20 (cache v20)

**Reception buckets shown on the player card.** The bucket total is the one
number on that card that is modelled rather than read off a projection, so the
card now shows the working and, more usefully, a claim you can falsify: "115
catches, about 6.7 a game, clears five in about 13.6 of 17 games and ten in 2.5
— 16.2 buckets x 2.5 = 40 pts, 15% of his total." Count the 5-catch games in a
real log and you know whether the model is generous for that player. Catches
that arrive in lumps clear fewer buckets than an even spread, and nothing in the
app used to tell you when that was happening.

**AVG rank.** The mean of Norris, Winks and 4for4, shown beside them on the card
and compactly on board rows. Averaged over whichever sources exist and labelled
"(2 of 3)" when one is missing, which is every kicker and defence since 4for4
ranks skill players only.

Deliberately kept separate from the Norris+Winks blend that drives the sort mode
and the steal corroboration. Those two are the arbitrage signal precisely
because they are NOT the consensus; folding 4for4 into them would blunt the
disagreement worth acting on. AVG is a reference for the eye and feeds no
decision.

## Build 19 (cache v19)

**The new 4for4 file is not new projections.** Every FF Pts change against the
8/22 export is exactly 0.50 per reception, for every player — it is the same
underlying projections re-scored as half-PPR instead of standard. The stat
lines the engine actually scores are unchanged, so nothing needed re-importing.
What did update: the 4for4 rank column (now a half-PPR ranking, which is closer
to this league than standard was) and the composite ADP. FF Pts and 4for4's own
VOR are deliberately ignored — neither can express 2.5 points per five catches,
which is the whole reason this app exists. Half-PPR still overpays receptions
relative to the bucket, which pays about 59% of half-PPR at typical volume, so
the 4for4 rank remains a reference and not a target.

**Stale saved scoring, fixed.** A session writes its own copy of the scoring
when created, and safeScoring only falls back to a default when a saved value is
missing or corrupt — protection against a bad session, but it meant the official
rules shipped in build 18 could never reach an existing draft. Old sessions kept
fumbleLost 0 and the 3/5 game bonuses while picking up the new long-touchdown
keys they had never saved, running on two rulebooks at once and looking entirely
plausible: Taylor 277 and above Gibbs, when the real rules give Gibbs 268 to
Taylor's 267.

Scoring now carries a version. A session built against an older rulebook that
actually differs from the current one gets an amber banner naming what differs,
with one tap to update. It is never applied silently — saved values might be a
deliberate house rule, and overwriting someone's scoring unasked would be worse
than the staleness. The offer fires on load and on session switch, so the
co-owner's and the second household drafts get it too.

## Build 18 — official league scoring

The league's real rules replaced the assumptions the engine was built on.

**Corrections to what was already there.** The 100- and 200-yard game bonuses
were coded as 3 and 5; they are 2 and 4. A lost fumble is -2 and was scored as
0 — fumble projections are now carried for 315 players. A forced fumble is worth
nothing to a defence here and was being paid 1 point.

**Newly modelled.** Long-touchdown bonuses (40+ and 50+ yards, both paid on a
50-yarder), field goals by distance with the miss penalties the make rate
implies, and lost PATs. The projections give counts and not distances, so these
use league rates for how often scores travel that far — modelled, and they move
everyone in the same direction.

**Defences, finally scored properly.** Points- and yards-allowed brackets are
the largest component of a defence's season and were missing entirely, which
compressed all 32 into near-uniformity. A season total cannot be scored against
them directly — a defence allowing 275 points does not allow 16 every week — so
the per-game distribution is modelled and the bracket table integrated over it.
Defences now swing 137 points top to bottom instead of 46, and the best one
carries more VORP than a mid-round receiver.

**That changed when to draft one.** With defences actually worth something,
waiting until the last four rounds costs real points. The K/DST window now opens
seven rounds out: +10.5 points a draft across 300 paired simulations, t = 7.6,
better in 198 of 300. It stays a window rather than a free-for-all so a kicker
can never crowd out a starter mid-draft. The opponent model was deliberately
left at four rounds, since real rooms do wait — if your leaguemates start taking
defences earlier than round 13, this edge shrinks.

**Every rule is now editable in Setup**, including the distance and bracket
values, so a mid-season rule change does not need a rebuild.

## Build 18 (cache v18)

**Reaches were measuring the wrong thing entirely.** The recap compared your
pick number to a player's rank on the full static board. By pick 135 everyone
ranked inside the top 135 is gone, so that comparison is arithmetically
guaranteed to come back hugely negative no matter who you take — it was
measuring how deep into the draft you were and calling it your fault. A real
draft showed picks at 135 and 178 labelled "107 early" and "72 early" when the
median board rank of what the rest of the room took at the same point was 232.

A reach now means what the words mean: better players were sitting there and
you passed them. The count is taken at the moment of the pick, and three tests
must all pass — a crowd of better men left (12+), one of them better by more
than the tie band, and that man actually worth something to your roster. The
last test matters: without it the final round flagged as a reach because a
spare quarterback graded above a sixth running back, which is true and worth
nothing. Validated both directions — a deliberately awful round-3 pick is
caught (112 better available), and a full engine-driven draft flags nothing.

**The recap now grades with the engine's own valuation.** `valueFor` was
hoisted out of `planEnv` to module scope, so the suggestion engine and the
draft-day grade call the identical function. Previously the grade fell back to
raw VORP, which counted players the board would never have taken — a fifth
receiver, a third quarterback — and manufactured reaches out of sensible picks.
They cannot disagree now by construction.

**Fragility assumed you would field an empty slot.** Losing a starter with no
backup was scored as his entire projection, so a 143-point tight end read as
-143. You would stream the position instead. The drop is now measured against
the best replacement you could actually field — your bench, or the waiver level
when that is better — and the row says "would stream" when it applies. Same TE
now reads -55.

**Steals are unchanged and stay valid.** Board fall is self-limiting: to fall
10 picks past your board rank you have to BE a top-N player still sitting
there, which cannot happen once the board is picked over.

## Build 17 (cache v17)

**Ties made explicit.** Scoring 4for4's and FantasyPros' projections through the
identical engine moves a top-100 player's VORP by a standard deviation of 17
points (median 8) — same league, same maths, two credible sources. So gaps
smaller than that are rounding, not ranking. Each player now reports every
other player within that band of him (a symmetric per-player window, not fixed
buckets, which would split two players one point apart purely on where a
boundary fell). Board rows show the range, the pick sheet spells it out, and
the suggestion panel says so when the top three are inside it. At the top of
the current board that means Taylor, Chase, Nacua, Gibbs, Robinson and
Smith-Njigba are one tie group spanning 8 points of VORP.

**Expert gap on the card.** When our board disagrees with the Norris/Winks
average by more than max(5, 30% of board rank) — scaled because six spots of
disagreement at pick 1 is not the same animal as six spots at pick 100 — the
card names both numbers and says which way to read it: this league's scoring
when we are higher, unpriced risk or news when they are.

Nothing about pick logic changed; these are display only.

## Build 17 — engine notes

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
