# Counts (blockId, data) pairs in a 1.2.x Anvil world: python3 scan_ids.py <world/region> [sample_every]
import os, sys, zlib, struct, collections, json
import numpy as np


def nbt(b, i, t):
    if t == 1: return b[i], i + 1
    if t == 2: return struct.unpack_from('>h', b, i)[0], i + 2
    if t == 3: return struct.unpack_from('>i', b, i)[0], i + 4
    if t == 4: return struct.unpack_from('>q', b, i)[0], i + 8
    if t == 5: return None, i + 4
    if t == 6: return None, i + 8
    if t == 7:
        n = struct.unpack_from('>i', b, i)[0]; return b[i + 4:i + 4 + n], i + 4 + n
    if t == 8:
        n = struct.unpack_from('>H', b, i)[0]; return b[i + 2:i + 2 + n].decode('utf-8', 'replace'), i + 2 + n
    if t == 9:
        et = b[i]; n = struct.unpack_from('>i', b, i + 1)[0]; i += 5; out = []
        for _ in range(n):
            v, i = nbt(b, i, et); out.append(v)
        return out, i
    if t == 10:
        d = {}
        while True:
            tt = b[i]; i += 1
            if tt == 0: return d, i
            n = struct.unpack_from('>H', b, i)[0]; name = b[i + 2:i + 2 + n].decode('utf-8', 'replace'); i += 2 + n
            d[name], i = nbt(b, i, tt)
    if t == 11:
        n = struct.unpack_from('>i', b, i)[0]; return None, i + 4 + 4 * n
    if t == 12:
        n = struct.unpack_from('>i', b, i)[0]; return None, i + 4 + 8 * n
    raise ValueError(t)


def chunks(path):
    f = open(path, 'rb').read()
    for k in range(1024):
        off = int.from_bytes(f[k * 4:k * 4 + 3], 'big') * 4096
        if not off: continue
        ln = struct.unpack_from('>i', f, off)[0]
        data = zlib.decompress(f[off + 5:off + 4 + ln])
        root, _ = nbt(data, 3 + struct.unpack_from('>H', data, 1)[0], 10)
        yield root['Level']


def main():
    rd = sys.argv[1]; every = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    cnt = collections.Counter(); n = 0; ents = collections.Counter()
    for fn in sorted(os.listdir(rd)):
        if not fn.endswith('.mca'): continue
        for j, L in enumerate(chunks(os.path.join(rd, fn))):
            if j % every: continue
            n += 1
            for s in L.get('Sections', []):
                bl = np.frombuffer(s['Blocks'], np.uint8).astype(np.int32)
                dt = np.frombuffer(s['Data'], np.uint8)
                d = np.empty(4096, np.int32); d[0::2] = dt & 15; d[1::2] = dt >> 4
                key = bl * 16 + d
                u, c = np.unique(key[bl != 0], return_counts=True)
                for k, v in zip(u.tolist(), c.tolist()): cnt[(k >> 4, k & 15)] += v
            for te in L.get('TileEntities', []): ents[te.get('id')] += 1
    print('chunks sampled', n)
    print(json.dumps(sorted([[a, b, c] for (a, b), c in cnt.items()], key=lambda x: -x[2])))
    print('tile entities', dict(ents))


main()
