# Swapping data sources

The app has no opinion about where its numbers come from. Player data and the
labels describing it live in two blobs at the top of `index.html`, and
`build-data.py` generates both from whatever CSVs you have.

Send me the files, tell me what they are, and you get a new `index.html` back.

---

## What actually matters

The app does three separate jobs with three separate inputs. Losing one doesn't
break the app, but it does turn off the feature that depends on it.

| Input | Feeds | Without it |
|---|---|---|
| **Raw projected stats** | Scoring engine, VORP, cost of waiting, grades | The whole point is gone. Rankings alone cannot be re-scored for your rules. |
| **ADP** | Steal flags, survival, draft board realism | Falls back to published rank order. Steals disappear. |
| **Primary expert rank** | The `W+N` column, third sort mode | Column and sort mode disappear. |
| **Secondary rank** | Disagreement signal against the primary | Arbitrage view collapses to one opinion. |

**The stats are non-negotiable.** Everything else degrades gracefully.

### Stats the engine reads

Only what's relevant to a position is needed. Missing fields are treated as zero,
which is correct — a receiver has no passing yards.

```
passYds passTD passInt          quarterbacks
rushYds rushTD                  quarterbacks, backs, some receivers
rec recYds recTD                backs, receivers, tight ends
fg xpt                          kickers
sack dint fr ff dtd safety      defenses
pa ydsAgn                       defenses (season totals are fine)
```

**Ignore any "FPTS" or "projected points" column the source gives you.** It's
computed under *their* scoring assumptions, not yours. FantasyPros publishes at
4-point passing TDs and −1 interceptions; your league is 6 and −2. That single
difference moves Josh Allen by 55 points. The app recomputes from raw stats
every time, which is why changing a scoring rule in Setup instantly re-ranks the
board.

---

## Before you spend the $50 on ETR

**Check whether their rankings are derived from their own projections.** If they
are, then buying ETR replaces two of your three inputs with one opinion wearing
two hats.

We hit this exact trap early on. Your Underdog rankings turned out to correlate
with their own ADP column at 0.98 — no independent signal at all. Later, the
"independent" analyst list turned out to be the same board as the CSV, differing
on two players out of fifty-three.

ETR is likely better than what you have. But "better single source" and
"multiple independent sources" solve different problems, and the disagreement
between sources is the only thing that can tell you where the market is wrong.

**My suggestion:** use ETR for projections and their rank as primary, and keep
the Yahoo consensus as the secondary. Costs nothing, takes five minutes to
re-scrape, and keeps the arbitrage column alive.

---

## What to send me

1. **Every projection export they offer**, one per position ideally. Include the
   header row exactly as downloaded — don't clean it up. Duplicate column names
   are fine; the build maps by position when names repeat.
2. **ADP**, if it's a separate file.
3. **Rankings**, if separate from projections.
4. **A note on which product it is** and roughly when you downloaded it, so the
   data stamp is accurate.

**Depth matters more than you'd think.** VORP compares each player to the last
starter at his position, so the file has to reach past that line or there's
nothing to subtract. For your 12-team league: roughly 30 QB, 60 RB, 60 WR,
24 TE, 15 K, 15 DST. The first FantasyPros QB export you sent had 10 rows — not
enough to reach the QB12 baseline, so the engine couldn't run at all.

`build-data.py` prints a depth check for every position and warns when one is
short.

---

## Known rough edges in the pipeline

- **Defenses need a team code.** Most sources list them by full name
  ("Houston Texans") with no team column, which doesn't join to anything else.
  Currently handled by a manual normalisation step.
- **Kickers need field-goal distance splits** to be scored properly in your
  league (3 / 4 / 5 points by range, no penalty for missing 40+). No free source
  publishes them. If ETR does, kickers stop being guesswork.
- **Per-game defensive brackets** need a distribution, not a season total. Same
  situation — if ETR publishes weekly projections, this gets much better.
- **Name collisions are real.** Your current data alone contains a J. Love who is
  both an Arizona back and a Green Bay quarterback, plus Bijan Robinson and
  Brian Robinson Jr. on the same team at the same position. Joins key on name
  *plus team plus position*, and keep suffixes — normalising away the "Jr."
  once put Bijan 180th on the board.

---

## Running it yourself

```bash
python3 build-data.py --config etr.json --template app.template.html --out index.html
```

The config describes your files and maps their columns onto the schema. Columns
can be referenced by name or by zero-based index, which you need when a source
repeats a header — FantasyPros exports use `YDS` twice, once for passing and
once for rushing, distinguished only by position.

After rebuilding, bump `CACHE` in `sw.js` so installed apps pick up the change.

Old saved drafts record which dataset they were built against. Open one after a
data swap and the Recap tab says so plainly, rather than quietly showing
different numbers than you saw on the night.
