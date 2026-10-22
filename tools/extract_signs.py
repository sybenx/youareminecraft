# Pulls every sign (position, facing, 4 lines) out of the original 1.2.5 world.
# python extract_signs.py <world/region> <out.json>
import os, sys, json, multiprocessing
sys.path.insert(0, os.path.dirname(__file__))
from scan_ids import chunks  # noqa: E402  (scan_ids only runs main() when executed directly)


# Direction a sign's text faces, in 16ths of a turn (0 = south/+z, 4 = west, 8 = north, 12 = east), like standing-sign data.
WALL = {2: 8, 3: 0, 4: 4, 5: 12}


def facing(L, x, y, z):
    for s in L.get('Sections', []):
        if s['Y'] == y >> 4:
            i = (y & 15) * 256 + (z & 15) * 16 + (x & 15)
            block, data = s['Blocks'][i], s['Data'][i >> 1] >> (4 * (i & 1)) & 15
            return data if block == 63 else WALL.get(data, 0) if block == 68 else 0
    return 0


def signs(path):
    out = []
    for L in chunks(path):
        for te in L.get('TileEntities', []):
            if te.get('id') == 'Sign':
                x, y, z = te['x'], te['y'], te['z']
                out.append([x, y, z, facing(L, x, y, z), [te.get(f'Text{i}', '') for i in range(1, 5)]])
    return out


def main():
    rd, dst = sys.argv[1], sys.argv[2]
    files = [os.path.join(rd, f) for f in sorted(os.listdir(rd)) if f.endswith('.mca')]
    with multiprocessing.Pool() as p:
        res = [s for part in p.imap_unordered(signs, files, chunksize=4) for s in part]
    res.sort(key=lambda s: (s[0], s[2], s[1]))
    json.dump(res, open(dst, 'w'), separators=(',', ':'))
    print(len(res), 'signs')


if __name__ == '__main__':
    main()
