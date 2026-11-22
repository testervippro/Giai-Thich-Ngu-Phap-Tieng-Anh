"""Dò lại mặt sau cho dải thẻ bị hằn (1410–1485): độ phân giải gốc, ứng viên ±8, dịch ±24 px."""
import sys, json, glob, os
sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageFilter
from multiprocessing import Pool
from topcut import story_box
SRC = "/Users/kieuxuanthoai/Giai-Thich-Ngu-Phap-Tieng-Anh/docs/kanji-viewer"
FILES = {int(os.path.basename(f)[:4]): f for f in glob.glob(SRC + "/kanji_p*/*.webp")}
def ink(a): return 1 - a.min(axis=2) / 255.0
def one(n):
    im = Image.open(FILES[n]).convert("RGB"); box = story_box(im)
    if not box: return n, None
    w, h = im.size
    fi = ink(np.asarray(im).astype(np.float32))
    dark = np.asarray(Image.fromarray(((fi > .5) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    faint = np.where(dark, 0, np.clip((fi - .03) / .3, 0, 1))
    x0, y0, x1, y1 = box
    M = np.zeros((h, w), bool); M[y0 + 4:y1 - 4, x0 + 4:x1 - 4] = True
    a = faint[M]; a = a - a.mean(); na = np.sqrt((a * a).sum()) + 1e-6
    per = []
    for m in range(n - 8, n + 9):
        if m == n or m not in FILES: continue
        b0 = ink(np.asarray(Image.open(FILES[m]).convert("RGB").resize((w, h))).astype(np.float32))[:, ::-1]
        best = (0, m, 0, 0)
        for dy in range(-45, 46, 3):
            for dx in range(-15, 16, 3):
                b = np.roll(np.roll(b0, dy, 0), dx, 1)[M]; b = b - b.mean()
                s = float((a * b).sum() / (na * (np.sqrt((b * b).sum()) + 1e-6)))
                if s > best[0]: best = (s, m, dy, dx)
        per.append(best)
    per.sort(reverse=True)
    return n, per[:3]
if __name__ == "__main__":
    with Pool(7) as p:
        res = dict(p.map(one, [n for n in range(1410, 1486) if n in FILES]))
    json.dump(res, open("ghost_scan2.json", "w"))
    for n, v in sorted(res.items()):
        if v and v[0][0] > .25: print(n, [(round(a, 2), m, dy, dx) for a, m, dy, dx in v], end="\n")
