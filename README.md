# You Are Minecraft (2012)

An archive of **You Are Minecraft**, a 2012 CraftBukkit 1.2.5 server. The world was a flat creative map where every player got a plot along the streets and built a giant statue of their own skin. 87,615 players did.

Live map: https://sybenx.github.io/youareminecraft/map/

This repo holds the landing page, the BlueMap 5.28 web app, and the scripts that turned the original 1.2.5 world into the 3D map. The map tiles themselves (about 5 GB) are served from a separate bucket at `https://yam.syb.lol`.

No Mojang textures or jars are committed here. The build pulls them from the official 1.2.5 client jar on your machine.

## Layout

| Path | What |
| --- | --- |
| `index.html` | Landing page |
| `map/` | BlueMap 5.28 web app. `map/settings.json` points `mapDataRoot` and `liveDataRoot` at `https://yam.syb.lol` with `clientDecompression: true` |
| `tools/build_pack.py` | Builds a resource pack that puts the 1.2.5 `terrain.png` tiles onto the modern block texture names, so the render looks the way the server did in 2012 |
| `tools/scan_ids.py` | Counts `(blockId, data)` pairs in the original world, used to check which textures the pack needs |
| `bluemap/` | BlueMap CLI config (core, webapp, map, file storage) |
| `uploader/` | Temporary Cloudflare Worker plus a batch client for pushing ~105k tiles into R2 without hitting the REST API rate limit |

## Rebuilding the map

You need Java 21, Python 3 with Pillow and numpy, the original server world, and:

- Chunker CLI 1.21.0 (`chunker-cli-1.21.0.jar`) from https://github.com/HiveGamesOSS/Chunker
- BlueMap CLI 5.28 (`bluemap-5.28-cli.jar`) from https://github.com/BlueMap-Minecraft/BlueMap
- The Minecraft 1.2.5 client jar (from the official launcher manifest)

Everything generated goes in `work/`, which is git-ignored.

1. **Check the block ids** (optional):

   ```
   python3 tools/scan_ids.py path/to/world/region 10
   ```

2. **Convert the world** to a modern format with Chunker:

   ```
   java -jar chunker-cli-1.21.0.jar -i path/to/world -o work/conv -f JAVA_1_20_4
   ```

3. **Build the 1.2.5 texture pack.** Pull `terrain.png` and `item/sign.png` out of the 1.2.5 client jar, then:

   ```
   mkdir -p work/tex && unzip -o client-1.2.5.jar terrain.png item/sign.png -d work/tex
   python3 tools/build_pack.py work/tex/terrain.png bluemap/packs/yam-1.2.5 work/tex/item/sign.png
   ```

4. **Render.** Set `accept-download: true` in `bluemap/core.conf` once you accept the Minecraft EULA (BlueMap downloads the current client for the textures the pack doesn't cover). Then:

   ```
   java -jar bluemap-5.28-cli.jar -c bluemap -r
   ```

   The full world is 412,885 chunks. Output lands in `work/web/maps/yam` (about 105k files, 5 GB). Run `java -jar bluemap-5.28-cli.jar -c bluemap -w` to preview it locally on port 8100.

5. **Upload** to an R2 bucket. Deploy `uploader/worker.js` with an R2 binding `B` and a secret `KEY`, put the same key in `uploader/key.txt`, then:

   ```
   PUSH_URL=https://<your-worker>.workers.dev/ PUSH_THREADS=14 PUSH_DONE=work/push.done \
     python3 uploader/push.py work/web/maps ""
   ```

   The upload resumes from `PUSH_DONE` if it stops. Delete the Worker afterwards.

6. **Serve.** Attach a custom domain to the bucket, allow the site's origin in the bucket's CORS policy, and point `map/settings.json` at it.
