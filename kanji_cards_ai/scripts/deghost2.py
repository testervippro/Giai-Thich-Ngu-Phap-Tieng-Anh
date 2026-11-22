"""Xoá hằn mặt sau, căn chỉnh theo từng đoạn ngang của ô câu chuyện (trang sau hơi nghiêng/lệch)."""
import sys, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageFilter
from topcut import story_box
SRC = "/Users/kieuxuanthoai/Giai-Thich-Ngu-Phap-Tieng-Anh/docs/kanji-viewer"

def ink(a): return 1 - a.min(axis=2) / 255.0
def filt(a, f):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(f)).astype(np.float32) / 255

def deghost(front_path, back_path, ai_img, dy0, dx0, tiles=9, real_thr=.68, keep_sat=1.1, STRICT=False):
    im = Image.open(front_path).convert("RGB"); w, h = im.size
    box = story_box(im)
    W, H = ai_img.size; k = W // w
    a = np.asarray(ai_img).astype(np.float32); fi = ink(a)
    back = Image.open(back_path).convert("RGB").resize((W, H), Image.LANCZOS).transpose(Image.FLIP_LEFT_RIGHT)
    b0 = ink(np.asarray(back).astype(np.float32))
    x0, y0, x1, y1 = [v * k for v in box]
    dark = filt(fi > .5, ImageFilter.MaxFilter(5)) > .5
    faint = np.where(dark, 0, np.clip((fi - .03) / .3, 0, 1))
    real = filt(fi > real_thr, ImageFilter.MaxFilter(3)) > .5
    satA = (a.max(axis=2) - a.min(axis=2)) / 255
    real |= satA > keep_sat                                  # màu rõ = nội dung thật
    out = a.copy(); tot = 0
    edges = np.linspace(x0 + 6, x1 - 6, tiles + 1).astype(int)
    for i in range(tiles):
        xa, xb = edges[i], edges[i + 1]
        sl = (slice(y0 + 6, y1 - 6), slice(xa, xb))
        fa = faint[sl]; fa = fa - fa.mean(); nf = np.sqrt((fa * fa).sum()) + 1e-6
        best = (-9, dy0 * k, dx0 * k)
        for dy in range(dy0 * k - 12, dy0 * k + 13, 2):
            for dx in range(dx0 * k - 12, dx0 * k + 13, 2):
                bb = np.roll(np.roll(b0, dy, 0), dx, 1)[sl]; bb = bb - bb.mean()
                s = (fa * bb).sum() / (nf * (np.sqrt((bb * bb).sum()) + 1e-6))
                if s > best[0]: best = (s, dy, dx)
        b = np.roll(np.roll(b0, best[1], 0), best[2], 1)
        b = filt(b, ImageFilter.MaxFilter(5))[sl]
        f = fi[sl]
        g = (b > .12) & (f < .62 * b + .18) & ~real[sl]
        A = a[sl]; sat = (A.max(axis=2) - A.min(axis=2)) / 255
        g |= (b > .45) & (f < .86) & (sat < .13) & (~real[sl] if STRICT else True)              # nét hằn đậm: xám, đúng chỗ nét mặt sau
        g |= f < .1
        o = out[sl]; o[g] = 255; out[sl] = o; tot += g.mean()
    return Image.fromarray(out.astype(np.uint8)), tot / tiles, box
