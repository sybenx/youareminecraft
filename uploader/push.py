# Uploads BlueMap map data to R2 through the temporary uploader Worker (uploader/worker.js).
# PUSH_URL=... python push.py <maps_dir> <prefix>   (key in uploader/key.txt, never commit it)
# Files are stored as-is (BlueMap's clientDecompression handles the .gz tiles). Resumable via <web_dir>/../push.done.
import os, sys, struct, urllib.request, concurrent.futures, mimetypes, threading, time

URL = os.environ['PUSH_URL']  # your deployed uploader Worker, e.g. https://yam-upload.<you>.workers.dev/
KEY = open(os.path.join(os.path.dirname(__file__), 'key.txt')).read().strip()
TYPES = {'.prbm': 'application/octet-stream', '.json': 'application/json', '.png': 'image/png', '.html': 'text/html; charset=utf-8',
         '.js': 'application/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff',
         '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json'}
BATCH_FILES, BATCH_BYTES = 80, 2 * 2**20


def entries(web, prefix):
    for root, _, files in os.walk(web):
        for f in files:
            p = os.path.join(root, f); rel = os.path.relpath(p, web).replace(os.sep, '/')
            gz = False; key = prefix + rel  # BlueMap clientDecompression: .gz files are fetched and unpacked by the browser
            ext = os.path.splitext(key)[1].lower()
            yield p, key, TYPES.get(ext) or mimetypes.guess_type(key)[0] or 'application/octet-stream', gz


def send(batch):
    parts = []
    for k, t, g, p in batch:
        d = open(p, 'rb').read()
        parts.append(struct.pack('>H', len(k.encode())) + k.encode() + struct.pack('>H', len(t)) + t.encode() + bytes([g])
                     + struct.pack('>I', len(d)) + d)
    body = b''.join(parts)
    for attempt in range(10):
        try:
            r = urllib.request.urlopen(urllib.request.Request(URL, body, {'x-key': KEY, 'User-Agent': 'yam-push/1.0'}), timeout=120)
            if int(r.read()) == len(batch): return
        except Exception as e:
            err = e
        time.sleep(min(2 ** attempt, 60))
    raise SystemExit(f'batch failed: {err}')


def main():
    web, prefix = sys.argv[1], sys.argv[2]
    done_path = os.environ.get('PUSH_DONE') or os.path.join(web, '..', 'push.done')
    done = set(open(done_path).read().split('\n')) if os.path.exists(done_path) else set()
    lock = threading.Lock(); dl = open(done_path, 'a'); n = [0]
    batches, cur, size = [], [], 0
    for p, key, t, g in entries(web, prefix):
        if key in done: continue
        sz = os.path.getsize(p); cur.append((key, t, g, p)); size += sz
        if len(cur) >= BATCH_FILES or size >= BATCH_BYTES:
            batches.append(cur); cur, size = [], 0
    if cur: batches.append(cur)
    total = sum(len(b) for b in batches); print('to upload', total, 'files in', len(batches), 'batches', flush=True)

    def job(b):
        send(b)
        with lock:
            dl.write('\n'.join(k for k, *_ in b) + '\n'); dl.flush(); n[0] += len(b)
            if n[0] % 5000 < len(b): print(n[0], '/', total, flush=True)

    with concurrent.futures.ThreadPoolExecutor(int(os.environ.get("PUSH_THREADS", 5))) as ex:
        list(ex.map(job, batches))
    print('done', n[0])


main()
