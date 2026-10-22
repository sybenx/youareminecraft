# Turns extract_signs.py output into the two files the map's search and name labels load.
# python build_sign_index.py <signs.json> <out_dir>
#   plots.json: [x, y, z, facing, name, extra]  one per plot sign ("Built by:" and its variants)
#   signs.json: [x, y, z, facing, text]         every other sign with text (lines joined by \n)
import os, re, sys, json

USERNAME = re.compile(r'^[A-Za-z0-9_]{1,16}$')
# First line of a plot sign, as players actually typed it (Notch's own says "Build by:", Mojang's "Skin for:")
PLOT_HEAD = re.compile(r'^(built|build|bulit|made|gebaut|skin)?\s*(by|buy|von|for)\s*:?$', re.I)
INLINE = re.compile(r'^(built|build|bulit|made|gebaut)\s+(by|buy|von)\s*:?\s+([A-Za-z0-9_]{3,16})$', re.I)


def plot_name(lines):
    """(name, remaining lines) for a plot sign, else (None, None). Blank or decorative lines may come first."""
    while lines and not any(c.isalnum() for c in lines[0]):
        lines = lines[1:]
    if not lines:
        return None, None
    m = INLINE.match(lines[0])
    if m:
        return m.group(3), lines[1:]
    if not PLOT_HEAD.match(lines[0]):
        return None, None
    rest = [t for t in lines[1:]]
    while rest and not rest[0]:
        rest = rest[1:]
    if not rest:
        return None, None
    name, rest = rest[0], rest[1:]
    if not any(c.isalnum() for c in name):
        return None, None
    # Sign lines hold 15 characters, so 16-character names wrap onto the next line
    if len(name) >= 15 and rest and rest[0] and USERNAME.match(name + rest[0]):
        name, rest = name + rest[0], rest[1:]
    return name, rest


def on_stand(x, y, z):
    """Plot signs sit on the statue stands: on the 16-block grid (give or take a block) at ground level,
    or in the front row of Mojang and Bukkit statues by spawn."""
    return y <= 8 and ((x + 1) % 16 <= 2 and (z - 11) % 16 <= 2 or z < 0)


def dedupe(plots, r=24):
    """Some players covered their statue in copies of the same sign; keep one per name per spot, preferring the plot-grid sign."""
    on_grid = lambda p: p[0] % 16 == 0 and p[2] % 16 == 12
    kept, seen = [], {}
    for p in sorted(plots, key=lambda p: (not on_grid(p), p[1])):
        near = seen.setdefault(p[4].lower(), [])
        if any(abs(p[0] - q[0]) <= r and abs(p[2] - q[2]) <= r for q in near):
            continue
        near.append(p)
        kept.append(p)
    return sorted(kept, key=lambda p: (p[0], p[2], p[1]))


def main():
    signs, out = json.load(open(sys.argv[1])), sys.argv[2]
    plots, other = [], []
    for x, y, z, f, lines in signs:
        lines = [t.strip() for t in lines]
        name, rest = plot_name(lines)
        if name and on_stand(x, y, z):
            plots.append([x, y, z, f, name, ' '.join(t for t in rest if t.strip('=-*'))])  # skip ===== dividers
        elif any(lines):
            other.append([x, y, z, f, '\n'.join(lines).strip('\n')])
    plots = dedupe(plots)
    os.makedirs(out, exist_ok=True)
    for fn, d in (('plots.json', plots), ('signs.json', other)):
        json.dump(d, open(os.path.join(out, fn), 'w'), separators=(',', ':'), ensure_ascii=False)
    print(len(plots), 'plots,', len(other), 'other signs')


main()
