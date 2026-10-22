// Temporary bulk uploader: POST a batch of files, each written to R2 with its own type/encoding.
// Body framing per file: u16 keyLen, key, u16 typeLen, type, u8 gzip, u32 dataLen, data.
export default {
  async fetch(req, env) {
    if (req.method !== 'POST' || req.headers.get('x-key') !== env.KEY) return new Response('no', { status: 403 });
    const b = new Uint8Array(await req.arrayBuffer());
    const dv = new DataView(b.buffer);
    const td = new TextDecoder();
    let i = 0, n = 0;
    const puts = [];
    while (i < b.length) {
      const kl = dv.getUint16(i); i += 2; const key = td.decode(b.subarray(i, i + kl)); i += kl;
      const tl = dv.getUint16(i); i += 2; const type = td.decode(b.subarray(i, i + tl)); i += tl;
      const gz = b[i]; i += 1;
      const dl = dv.getUint32(i); i += 4; const data = b.slice(i, i + dl); i += dl;
      const meta = { contentType: type, cacheControl: 'public, max-age=86400' };
      if (gz) meta.contentEncoding = 'gzip';
      puts.push(env.B.put(key, data, { httpMetadata: meta }));
      n++;
    }
    await Promise.all(puts);
    return new Response(String(n));
  }
};
