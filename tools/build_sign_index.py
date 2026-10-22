# Turns extract_signs.py output into the two files the map's search and name labels load.
# python build_sign_index.py <signs.json> <out_dir>
#   plots.json: [x, y, z, facing, name, extra]  one per "Built by:" plot sign
#   signs.json: [x, y, z, facing, text]         every other sign with text (lines joined by \n)
import os, re, sys, json

USERNAME = re.compile(r'^[A-Za-z0-9_]{1,16}$')


def main():
    signs, out = json.load(open(sys.argv[1])), sys.argv[2]
    plots, other = [], []
    for x, y, z, f, lines in signs:
        lines = [t.strip() for t in lines]
        if lines[0].lower().startswith('built by'):
            name, rest = lines[1], lines[2:]
            # Sign lines hold 15 characters, so 16-character names wrap onto line 3
            if len(name) >= 15 and rest[0] and USERNAME.match(name + rest[0]):
                name, rest = name + rest[0], rest[1:]
            if name:
                plots.append([x, y, z, f, name, ' '.join(t for t in rest if t)])
        elif any(lines):
            other.append([x, y, z, f, '\n'.join(lines).strip('\n')])
    os.makedirs(out, exist_ok=True)
    for fn, d in (('plots.json', plots), ('signs.json', other)):
        json.dump(d, open(os.path.join(out, fn), 'w'), separators=(',', ':'), ensure_ascii=False)
    print(len(plots), 'plots,', len(other), 'other signs')


main()
