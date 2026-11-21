#!/usr/bin/env python3
"""Ảnh minh hoạ mỗi chương truyện dài -> docs/kanji-viewer/truyen-img/NN.webp
Ghép từ thư viện sẵn có: phông cảnh hay nhắc nhất trong chương + các nhân vật xuất hiện nhiều nhất
+ vài đồ vật (danh từ) hay nhắc nhất.
    .venv/bin/python tools/kanji_saga_art.py"""
import collections
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanji_shorts as KS  # noqa: E402
import kanji_assets as KA  # noqa: E402

OUT = KS.ROOT / "docs/kanji-viewer/truyen-img"
W, H = 900, 420


def plain(t):
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)|【.】", "", t)).lower()


def chapter_art(i, title, paras):
    low = plain(" ".join(paras))
    # phông: từ khoá bối cảnh được nhắc nhiều nhất
    best = max(KS.BG_KEYS, key=lambda kv: len(re.findall(kv[0], low)))
    prompt = best[1] if re.search(best[0], low) else KS.BG_DEFAULT[i % len(KS.BG_DEFAULT)]
    bg = Image.open(KS.ASSETS / "bc" / f"{KA.slug(prompt)}.png").convert("RGB")
    sc = W / bg.width
    bg = bg.resize((W, int(bg.height * sc)), Image.LANCZOS)
    top = max(0, (bg.height - H) // 2)
    im = bg.crop((0, top, W, top + H)).convert("RGBA")
    # nhân vật hay xuất hiện
    cnt = collections.Counter({cid: len(re.findall(rx, low)) for cid, rx in KS.TEXT_RX.items()})
    cnt["nhan"] += 99                                       # cậu Nhân luôn có mặt
    cast = [c for c, n in cnt.most_common(4) if n > 0]
    # đồ vật hay nhắc
    objs = collections.Counter()
    for rx, e, kind in KS.LEX:
        if kind in "GF" and e != "💧":
            n = len(rx.findall(low))
            if n:
                objs[e] += n
    d = ImageDraw.Draw(im)
    xs = [0.16, 0.38, 0.6, 0.82][:len(cast)]
    for cid, x in zip(cast, xs):
        sp = Image.open(KS.CAST / f"{cid}.png").convert("RGBA")
        h = int(H * (KS.SIZE.get(cid, 0.44) + 0.18))
        sp = sp.resize((max(1, int(sp.width * h / sp.height)), h), Image.LANCZOS)
        cx, gy = int(W * x), H - 12
        d.ellipse([cx - sp.width * 0.35, gy - 10, cx + sp.width * 0.35, gy + 8], fill=(0, 0, 0, 55))
        im.alpha_composite(sp, (cx - sp.width // 2, gy - sp.height))
    for j, (e, _) in enumerate(objs.most_common(4)):
        ei = Image.open(KS.emoji_png(e)).convert("RGBA")
        s = 78
        ei = ei.resize((s, max(1, int(ei.height * s / ei.width))), Image.LANCZOS)
        x = int(W * (0.1 + 0.27 * j)) + 40
        im.alpha_composite(ei, (x, 26 + (j % 2) * 34))
    OUT.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(OUT / f"{i:02d}.webp", quality=72, method=6)


def main():
    import kanji_saga_shorts as SS
    for i, (t, ps) in enumerate(SS.chapters(), 1):
        chapter_art(i, t, ps)
    print(len(list(OUT.glob("*.webp"))), "ảnh ->", OUT)


if __name__ == "__main__":
    main()
