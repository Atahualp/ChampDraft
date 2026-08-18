#!/usr/bin/env python3
"""
Draft Room — data build.

Turns whatever CSVs you have into the two blobs the app needs, then injects
them into index.html. The app never knows or cares where the numbers came
from; every label it displays is read from META.

    python3 build-data.py --config etr.json --template app.template.html --out index.html

The config file describes YOUR sources. Nothing here is specific to
FantasyPros, Yahoo, or ETR — see SOURCES.md for the contract.
"""
import argparse, json, os, re, sys
import pandas as pd, numpy as np

# ---------------------------------------------------------------- schema ----
# Raw stat fields the scoring engine understands. Anything not supplied is
# treated as zero, which is correct: a WR has no passing yards.
STAT_FIELDS = [
    'passYds','passTD','passInt','rushYds','rushTD','rec','recYds','recTD',
    'fg','xpt','sack','dint','fr','ff','dtd','safety','pa','ydsAgn'
]
POSITIONS = ['QB','RB','WR','TE','K','DST']
SUFFIX = re.compile(r'\s+(Jr\.?|Sr\.?|II|III|IV|V)$', re.I)


def join_key(name, team, pos):
    """Player identity = name + team + position.

    Name alone is never enough: our own data already contains a J. Love who is
    both an Arizona RB and a Green Bay QB, and a Bijan Robinson who collides
    with Brian Robinson Jr. once the suffix is stripped. So the suffix is kept
    as part of the key, not normalised away.
    """
    n = str(name).strip()
    suf = ''
    m = SUFFIX.search(n)
    if m:
        suf = '+' + m.group(1).replace('.', '')
        n = SUFFIX.sub('', n)
    parts = n.split()
    if not parts:
        return None
    first = parts[0][0]
    last = parts[-1]
    return f"{first}.{last}{suf}|{str(team).strip()}|{pos}".lower()


def load_table(spec, root):
    """Read one CSV and rename its columns to our schema.

    `spec['map']` is {our_name: their_column}. Their column may be given by
    name, or by zero-based index when the header is ambiguous — FantasyPros
    projection exports repeat 'YDS' and 'TDS' for passing and rushing, so
    position is the only thing that distinguishes them.
    """
    path = os.path.join(root, spec['file'])
    df = pd.read_csv(path, skiprows=spec.get('skiprows'))
    df.columns = [str(c).strip() for c in df.columns]
    out = pd.DataFrame()
    for ours, theirs in spec['map'].items():
        if isinstance(theirs, int):
            if theirs >= df.shape[1]:
                raise SystemExit(f"{spec['file']}: column index {theirs} out of range")
            out[ours] = df.iloc[:, theirs]
        else:
            if theirs not in df.columns:
                raise SystemExit(f"{spec['file']}: no column named {theirs!r}. "
                                 f"Available: {list(df.columns)}")
            out[ours] = df[theirs]
    if 'pos' in spec:
        out['pos'] = spec['pos']
    for c in out.columns:
        if c not in ('player', 'team', 'pos'):
            out[c] = pd.to_numeric(out[c], errors='coerce')
    out = out.dropna(subset=['player'])
    out = out[out['player'].astype(str).str.strip() != '']
    out['player'] = out['player'].astype(str).str.strip()
    if 'team' in out:
        out['team'] = out['team'].astype(str).str.strip().str.upper()
    return out


def build(cfg, root):
    frames = [load_table(s, root) for s in cfg['projections']]
    proj = pd.concat(frames, ignore_index=True)
    proj['key'] = [join_key(*r) for r in proj[['player', 'team', 'pos']].values]
    proj = proj.dropna(subset=['key'])

    dupes = proj[proj.key.duplicated(keep=False)]
    if len(dupes):
        print(f"  ! {dupes.key.nunique()} duplicate player keys — keeping the first of each:")
        for k in dupes.key.unique()[:10]:
            print('    ', k)
        proj = proj.drop_duplicates('key', keep='first')

    # Optional extras, each joined on the same key. Missing ones are fine:
    # the app degrades rather than breaks when a column is absent.
    for name, field in (('adp', 'a'), ('rank1', 'r1'), ('rank2', 'r2'), ('bye', 'b')):
        spec = cfg.get(name)
        if not spec:
            continue
        ext = load_table(spec, root)
        ext['key'] = [join_key(*r) for r in ext[['player', 'team', 'pos']].values]
        col = spec['value']
        ext = ext.dropna(subset=['key']).drop_duplicates('key')
        proj = proj.merge(ext[['key', col]].rename(columns={col: field}), on='key', how='left')
        got = proj[field].notna().sum()
        print(f"  {name}: matched {got} of {len(proj)}")

    for c in STAT_FIELDS:
        if c not in proj:
            proj[c] = 0.0
    proj[STAT_FIELDS] = proj[STAT_FIELDS].fillna(0).round(1)

    bad = proj[~proj['pos'].isin(POSITIONS)]
    if len(bad):
        print(f"  ! dropping {len(bad)} rows with unknown positions: {sorted(set(bad['pos']))}")
        proj = proj[proj['pos'].isin(POSITIONS)]

    sort_cols = [c for c in ('a', 'r1', 'r2') if c in proj]
    if sort_cols:
        proj = proj.sort_values(sort_cols, na_position='last')
    proj = proj.reset_index(drop=True)

    players = []
    for i, r in proj.iterrows():
        stats = {c: float(r[c]) for c in STAT_FIELDS if float(r[c])}
        players.append({
            'id': f'p{i}',
            'n': r['player'],
            't': r['team'] if isinstance(r.get('team'), str) else '',
            'p': r['pos'],
            'b': int(r['b']) if pd.notna(r.get('b')) else 0,
            'a': round(float(r['a']), 1) if pd.notna(r.get('a')) else None,
            'r1': int(r['r1']) if pd.notna(r.get('r1')) else None,
            'r2': int(r['r2']) if pd.notna(r.get('r2')) else None,
            's': stats,
        })

    # Depth check: VORP needs players past the replacement baseline, or the
    # engine has nothing to subtract. These minimums assume a 12-team league.
    need = {'QB': 30, 'RB': 60, 'WR': 60, 'TE': 24, 'K': 15, 'DST': 15}
    counts = {p: sum(1 for x in players if x['p'] == p) for p in POSITIONS}
    print('\n  position depth:')
    for p in POSITIONS:
        ok = counts[p] >= need[p]
        print(f"    {p:<4} {counts[p]:>4}  (need {need[p]:>3})  {'ok' if ok else '*** SHORT ***'}")

    scoring_stats = [c for c in STAT_FIELDS if any(c in x['s'] for x in players)]
    print(f"\n  stat fields present: {', '.join(scoring_stats) or '(none — projections missing!)'}")
    if not scoring_stats:
        print('  ! Without raw stats the scoring engine cannot run. Rankings alone')
        print('    cannot be re-scored for league rules — that is the whole point.')

    return players, cfg['meta']


def inject(template, out_path, players, meta):
    src = open(template).read()
    for token in ('/*__PLAYERS__*/[]', '/*__META__*/{}'):
        if token not in src:
            raise SystemExit(f'template is missing the {token} placeholder')
    src = src.replace('/*__PLAYERS__*/[]', json.dumps(players, separators=(',', ':')))
    src = src.replace('/*__META__*/{}', json.dumps(meta, separators=(',', ':')))
    open(out_path, 'w').write(src)
    print(f"\n  wrote {out_path}  ({len(src)//1024} KB, {len(players)} players)")
    print('  remember to bump CACHE in sw.js so installed apps pick it up')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True, help='JSON describing your sources')
    ap.add_argument('--template', default='app.template.html')
    ap.add_argument('--out', default='index.html')
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    root = os.path.dirname(os.path.abspath(a.config))
    print(f'building from {a.config}')
    players, meta = build(cfg, root)
    inject(a.template, a.out, players, meta)
