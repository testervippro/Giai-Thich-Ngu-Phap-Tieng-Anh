#!/usr/bin/env python3
"""Vùng tranh (bên trái) của từng ảnh docs/kanji-viewer/kanji_story/NNNN.webp -> docs/kanji-viewer/kanji-anim-crop.js
cho trang anim.html (hoạt hình câu chuyện chạy ngay trên trình duyệt, không cần file GIF).

    python3 tools/kanji_anim_crop.py
"""
import json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kanji_story_gif as G   # picture(): tách tranh + bỏ đường viền mảnh

ROOT = G.ROOT
D = os.path.join(ROOT, 'docs/kanji-viewer/kanji_story')


def crop_box(n):
    im = Image.open(G.STORY % n).convert('RGB')
    a = np.asarray(im).astype(int)
    x1 = G.R.split_picture(a)
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
    out = {}
    for f in sorted(os.listdir(D)):
        if f.endswith('.webp') and f[:4].isdigit() and len(f) == 9:
            b = crop_box(int(f[:4]))
            if b:
                out[int(f[:4])] = b
    js = ('// Vùng tranh [x0, y0, x1, y1] trong ảnh kanji_story/NNNN.webp (sinh bởi tools/kanji_anim_crop.py)\n'
          'window.KANJI_ANIM_CROP=' + json.dumps(out, separators=(',', ':')) + ';\n')
    open(os.path.join(ROOT, 'docs/kanji-viewer/kanji-anim-crop.js'), 'w').write(js)
    print(len(out), 'thẻ có tranh')
