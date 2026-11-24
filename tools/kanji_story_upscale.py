#!/usr/bin/env python3
"""Làm nét ảnh câu chuyện Kanji (docs/kanji-viewer/kanji_story/*.webp) bằng Real-ESRGAN bản tranh vẽ (anime_6B).

Phóng x4 bằng AI rồi thu về x2 (LANCZOS) -> nét viền sắc, hết nhòe do nén; hình vẽ giữ nguyên.
Ghi ra thư mục riêng (mặc định build/kanji_story_x2/), KHÔNG đụng ảnh gốc. Chạy lại thì bỏ qua ảnh đã có.

    pip install torch spandrel pillow numpy
    python3 tools/kanji_story_upscale.py                 # cả bộ
    python3 tools/kanji_story_upscale.py 17 542 2095     # vài thẻ
    python3 tools/kanji_story_upscale.py --compare       # chỉ tạo trang so sánh trước/sau
    python3 tools/kanji_story_upscale.py --shard 0/2 & python3 tools/kanji_story_upscale.py --shard 1/2   # 2 tiến trình song song
Chạy trên CUDA / Apple MPS / CPU (MPS ~3 s/ảnh).
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/kanji-viewer/kanji_story"
OUT = ROOT / "build/kanji_story_x2"
MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
MODEL = Path.home() / ".cache/realesrgan/RealESRGAN_x4plus_anime_6B.pth"


def load_model():
    import torch
    from spandrel import ModelLoader
    dev = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    if not MODEL.exists():
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        print("tải model ->", MODEL)
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    m = ModelLoader().load_from_file(str(MODEL)).to(dev).eval()
    half = dev == "cuda" and m.supports_half
    if half:
        m.half()
    return m, dev, half


def upscale(model, dev, half, im, scale=2, tile=512, pad=16):
    """Chia ô (đỡ tốn bộ nhớ), phóng x4 từng ô, ghép lại, thu về x`scale`."""
    import torch
    with torch.no_grad():
        x = torch.from_numpy(np.array(im.convert("RGB"))).permute(2, 0, 1)[None].float().div(255).to(dev)
        if half:
            x = x.half()
        _, _, h, w = x.shape
        s = model.scale
        out = torch.zeros(1, 3, h * s, w * s, device=dev, dtype=x.dtype)
        for y0 in range(0, h, tile):
            for x0 in range(0, w, tile):
                ya, yb = max(y0 - pad, 0), min(y0 + tile + pad, h)
                xa, xb = max(x0 - pad, 0), min(x0 + tile + pad, w)
                o = model(x[:, :, ya:yb, xa:xb])
                ty, tx = min(y0 + tile, h), min(x0 + tile, w)
                out[:, :, y0 * s:ty * s, x0 * s:tx * s] = \
                    o[:, :, (y0 - ya) * s:(ty - ya) * s, (x0 - xa) * s:(tx - xa) * s]
        arr = out[0].float().clamp(0, 1).mul(255).round().byte().permute(1, 2, 0).cpu().numpy()
    big = Image.fromarray(arr)
    return big if scale == s else big.resize((w * scale, h * scale), Image.LANCZOS)


def compare_page(names):
    """build/kanji_story_x2/compare.html: kéo thanh trượt để so trước/sau từng ảnh."""
    rel = Path("../../docs/kanji-viewer/kanji_story")
    items = [[n, f"{rel}/{n}", n] for n in names]
    html = """<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>So sánh làm nét</title>
<style>
body{margin:0;font:15px system-ui,sans-serif;background:#f4f4f2;color:#222}
header{position:sticky;top:0;background:#fff;padding:10px 16px;border-bottom:1px solid #ddd;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:2}
input[type=number]{width:80px}button{padding:4px 10px}
.card{background:#fff;margin:14px auto;max-width:1300px;padding:10px;border-radius:8px;box-shadow:0 1px 3px #0002}
.cmp{position:relative;overflow:hidden;cursor:ew-resize;user-select:none}
.cmp img{display:block;width:100%}
.cmp .after{position:absolute;inset:0;clip-path:inset(0 0 0 50%)}
.cmp .bar{position:absolute;top:0;bottom:0;left:50%;width:2px;background:#e33}
.lab{display:flex;justify-content:space-between;font-size:13px;color:#666;margin-top:4px}
</style>
<header><b>Trái: ảnh gốc · Phải: đã làm nét</b> — kéo/rê chuột trên ảnh để so
<span>Từ thẻ <input id=from type=number min=1 value=1></span><button id=prev>◀ 20</button><button id=next>20 ▶</button>
<label><input id=zoom type=checkbox> phóng to phần tranh</label><span id=info></span></header>
<main id=list></main>
<script>
const ITEMS=__ITEMS__, OUT="./", PAGE=20;
const list=document.getElementById('list'), from=document.getElementById('from');
function render(){
  let i=Math.max(0,ITEMS.findIndex(x=>parseInt(x[0])>=+from.value)); if(i<0)i=0;
  const zoom=document.getElementById('zoom').checked;
  list.innerHTML='';
  ITEMS.slice(i,i+PAGE).forEach(([n,orig])=>{
    const c=document.createElement('div');c.className='card';
    c.innerHTML=`<div class=cmp style="${zoom?'width:250%':''}"><img src="${orig}"><img class=after src="${OUT}${n}"><div class=bar></div></div>
      <div class=lab><span>gốc</span><b>${n}</b><span>làm nét</span></div>`;
    const box=c.querySelector('.cmp'), after=c.querySelector('.after'), bar=c.querySelector('.bar');
    const move=e=>{const r=box.getBoundingClientRect(),x=((e.touches?e.touches[0].clientX:e.clientX)-r.left)/r.width*100;
      const p=Math.min(100,Math.max(0,x));after.style.clipPath=`inset(0 0 0 ${p}%)`;bar.style.left=p+'%'};
    box.addEventListener('mousemove',move);box.addEventListener('touchmove',move,{passive:true});
    if(zoom)c.style.overflowX='auto';
    list.appendChild(c);
  });
  document.getElementById('info').textContent=`${ITEMS.length} ảnh`;
  scrollTo(0,0);
}
const step=d=>{const i=Math.max(0,ITEMS.findIndex(x=>parseInt(x[0])>=+from.value))+d;
  from.value=parseInt(ITEMS[Math.min(Math.max(i,0),ITEMS.length-1)][0]);render()};
document.getElementById('prev').onclick=()=>step(-PAGE);document.getElementById('next').onclick=()=>step(PAGE);
from.onchange=render;document.getElementById('zoom').onchange=render;render();
</script></html>"""
    (OUT / "compare.html").write_text(html.replace("__ITEMS__", json.dumps(items)), encoding="utf-8")
    return OUT / "compare.html"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards", nargs="*", type=int, help="số thẻ (bỏ trống = tất cả)")
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--quality", type=int, default=90, help="chất lượng webp")
    ap.add_argument("--compare", action="store_true", help="chỉ tạo lại trang so sánh")
    ap.add_argument("--shard", default="0/1", help="i/N: tiến trình thứ i trong N tiến trình chạy song song")
    ap.add_argument("--limit", type=int, default=0, help="làm tối đa N ảnh rồi thoát (chạy lặp lại để tránh MPS phình bộ nhớ)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    files = sorted(SRC.glob("*.webp"))
    if a.cards:
        want = {f"{n:04d}.webp" for n in a.cards}
        files = [f for f in files if f.name in want]
    if not a.compare:
        si, sn = map(int, a.shard.split("/"))
        todo = [f for k, f in enumerate(files) if k % sn == si and not (OUT / f.name).exists()]
        if a.limit:
            todo = todo[:a.limit]
        print(f"{len(files)} ảnh, đã có {len(files) - len(todo)}, cần làm {len(todo)} -> {OUT}", flush=True)
        if todo:
            model, dev, half = load_model()
            print("thiết bị:", dev, flush=True)
            t0 = time.time()

            def save(big, f):                         # nén webp (CPU) ở luồng riêng, GPU làm ảnh tiếp theo
                tmp = OUT / (f.stem + ".tmp.webp")
                big.save(tmp, quality=a.quality, method=6)
                tmp.rename(OUT / f.name)              # ghi xong mới đổi tên -> không có ảnh dở
            pool, pend = ThreadPoolExecutor(2), []
            for i, f in enumerate(todo, 1):
                try:
                    pend.append((f, pool.submit(save, upscale(model, dev, half, Image.open(f), a.scale), f)))
                    if dev == "mps":
                        import torch
                        torch.mps.empty_cache()           # MPS giữ bộ nhớ đệm ngày càng lớn -> swap -> chậm dần
                except Exception as e:                # noqa: BLE001 — một ảnh lỗi thì bỏ qua, làm tiếp
                    print(f"⚠️ {f.name}: {e}", flush=True)
                while len(pend) > 4 or (pend and pend[0][1].done()):
                    g, fut = pend.pop(0)
                    if fut.exception():
                        print(f"⚠️ {g.name}: {fut.exception()}", flush=True)
                if i % 25 == 0 or i == len(todo):
                    el = time.time() - t0
                    print(f"[{a.shard}] {i}/{len(todo)}  {el / i:.1f} s/ảnh  còn ≈ {(len(todo) - i) * el / i / 60:.0f} phút", flush=True)
            pool.shutdown(wait=True)
    done = [f.name for f in sorted(SRC.glob("*.webp")) if (OUT / f.name).exists()]
    src_mb = sum((SRC / n).stat().st_size for n in done) / 1e6
    out_mb = sum((OUT / n).stat().st_size for n in done) / 1e6
    print(f"xong {len(done)} ảnh: {src_mb:.0f} MB -> {out_mb:.0f} MB | so sánh: {compare_page(done)}")


if __name__ == "__main__":
    main()
