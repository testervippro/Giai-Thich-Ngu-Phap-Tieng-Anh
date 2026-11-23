#!/usr/bin/env python3
"""Vùng tranh (bên trái) của từng ảnh câu chuyện -> file .js cho trang anim.html
(hoạt hình câu chuyện chạy ngay trên trình duyệt, không cần file GIF).

    python3 tools/kanji_anim_crop.py           # Kanji: kanji_story/  -> docs/kanji-viewer/kanji-anim-crop.js
    python3 tools/kanji_anim_crop.py --hanzi   # Hán tự: story/        -> docs/hanzi-viewer/hanzi-anim-crop.js
"""
import json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kanji_story_gif as G   # picture(): tách tranh + bỏ đường viền mảnh

ROOT = G.ROOT


def crop_box(path, text_only=False):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(int)
    x1 = None if text_only else G.R.split_picture(a)
    if x1 is None:
        return None
    pic = im.crop((0, 0, x1 + 8, im.height))
    g = np.asarray(pic.convert('L')) < 235
    rows = g.mean(1)
    r = np.where(rows > 0.01)[0]
    if len(r) > 2:   # bỏ đường kẻ mảnh ở mép trên / dưới (viền ảnh gốc)
        top = r[0]
        if len(r[r < top + 6]) <= 4 and not (rows[top + 6:top + 20] > 0.01).any():
            g[:top + 6] = False
        bot = r[-1]
        if len(r[r > bot - 6]) <= 4 and not (rows[max(bot - 20, 0):bot - 6] > 0.01).any():
            g[bot - 5:] = False
    ys, xs = np.where(g)
    if not len(xs):
        return None
    return [int(max(xs.min() - 6, 0)), int(max(ys.min() - 6, 0)),
            int(min(xs.max() + 7, pic.width)), int(min(ys.max() + 7, pic.height))]


if __name__ == '__main__':
    hanzi = '--hanzi' in sys.argv
    D = os.path.join(ROOT, 'docs/hanzi-viewer/story' if hanzi else 'docs/kanji-viewer/kanji_story')
    dst = os.path.join(ROOT, 'docs/hanzi-viewer/hanzi-anim-crop.js' if hanzi else 'docs/kanji-viewer/kanji-anim-crop.js')
    var = 'HANZI_ANIM_CROP' if hanzi else 'KANJI_ANIM_CROP'
    out = {}
    for f in sorted(os.listdir(D)):
        if f.endswith('.webp') and f[:4].isdigit() and len(f) == 9:
            n = int(f[:4])
            b = crop_box(os.path.join(D, f), hanzi and n in G.R.TEXT_ONLY)
            if b:
                out[n] = b
    js = ('// Vùng tranh [x0, y0, x1, y1] trong ảnh câu chuyện NNNN.webp (sinh bởi tools/kanji_anim_crop.py)\n'
          'window.' + var + '=' + json.dumps(out, separators=(',', ':')) + ';\n')
    open(dst, 'w').write(js)
    print(len(out), 'thẻ có tranh ->', dst)
