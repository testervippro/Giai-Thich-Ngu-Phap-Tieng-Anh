#!/usr/bin/env python3
"""Cắt ô câu chuyện (khung tranh + câu gợi nhớ) từ thẻ Hán tự docs/hanzi-viewer/tap*/NNNN.webp (784×~250)
-> docs/hanzi-viewer/story/NNNN.webp: tranh bên trái, câu chuyện bên phải (bỏ huy hiệu số + bảng từ vựng),
giống ảnh câu chuyện Kanji (docs/kanji-viewer/kanji_story).

    python3 tools/hanzi_story_crop.py            # cắt tất cả
    python3 tools/hanzi_story_crop.py 0138 1723  # chỉ vài thẻ
"""
import sys, numpy as np
from PIL import Image

def ink(a, thr=200):
    return a.min(axis=2) < thr

def colored(a):
    mx, mn = a.max(axis=2), a.min(axis=2)
    return ((mx - mn) > 60) | (mn < 120)

def frame(a):
    """Khung tranh: hai cột / hai hàng có nhiều điểm màu nhất trong vùng giữa thẻ."""
    H, W, _ = a.shape
    top = a[:int(H * .7)]
    c = colored(top)
    xs = c[:, 200:520].mean(axis=0)
    # cột trái/phải của khung: mật độ cao
    cand = [i + 200 for i, v in enumerate(xs) if v > .45]
    if not cand:
        return None
    L = min(cand)
    R = max(x for x in cand if x - L < 260)
    if R - L < 80:
        return None
    ys = colored(a[:, L:R + 1]).mean(axis=1)
    rows = [i for i, v in enumerate(ys) if v > .6]
    rows = [r for r in rows if r < H * .75]
    if not rows:
        return None
    T, B = min(rows), max(rows)
    return L, T, R, B

def text_box(a, R, T, B):
    H, W, _ = a.shape
    x0, x1 = R + 8, W - 4
    ylim = B + 6
    reg = ink(a[:ylim, x0:x1], 170)
    # che các vạch dọc (ngoặc khung bên phải, mép bảng) — chạy gần suốt chiều cao
    vc = reg[T:ylim].mean(axis=0) > .7
    lines = np.where(vc)[0]
    for c in lines:
        reg[:, max(0, c - 3):c + 4] = False
    rows = reg.mean(axis=1) > .004
    bands, s = [], None
    for y, v in enumerate(list(rows) + [False]):
        if v and s is None: s = y
        if not v and s is not None:
            if y - s >= 4: bands.append([s, y])
            s = None
    # gộp các band sát nhau
    m = []
    for b in bands:
        if m and b[0] - m[-1][1] <= 3: m[-1][1] = b[1]
        else: m.append(b)
    # bỏ hàng huy hiệu số ở đầu (nằm trong ~50px trên cùng); band dính cả huy hiệu lẫn chữ thì tách ở hàng ít mực nhất
    prof = reg.mean(axis=1)
    out = []
    for k, (s0, s1) in enumerate(m):
        if s1 <= 52 and s0 < 40:
            continue
        if s0 < 70 and s1 - s0 <= 34 and not out:            # hàng huy hiệu: viên thuốc màu đậm
            band = a[s0:s1, x0:x1]
            if ((band.max(axis=2) - band.min(axis=2)) > 80).mean() > .06:
                continue
        if s0 < 40 < s1 and s1 - s0 > 45:
            cut = 32 + int(np.argmin(prof[32:min(62, s1)]))
            s0 = cut + 1
        out.append([s0, s1])
    m = [x for x in out if x[1] - x[0] >= 6]
    if len(m) > 1 and m[-1][0] >= B - 6:        # band bắt đầu ngay đáy khung = mép bảng từ vựng
        m = m[:-1]
    if not m:
        return None
    ty0, ty1 = m[0][0], m[-1][1]
    if ty1 >= ylim - 1 and m[-1][0] < B - 12:                         # dòng cuối tràn qua đáy khung: kéo xuống tới hàng trắng đầu tiên
        y = ty1
        while y < min(H, B + 40) and ink(a[y:y + 1, x0:x1], 170).mean() > .004:
            y += 1
        ty1 = y
    cm = ink(a[ty0:ty1, x0:x1], 170).mean(axis=0)
    for c in lines:                             # vạch dọc của khung (đã dò trên cả chiều cao khung tranh)
        cm[max(0, c - 4):c + 5] = 0
    cols = np.where(cm > .01)[0]
    if len(cols) == 0:
        return None
    # cụm chữ liền nhau; khoảng trắng > 28px => phần sau là vạch khung / vật lạ -> bỏ
    segs = [[cols[0], cols[0]]]
    for c in cols[1:]:
        if c - segs[-1][1] > 28: segs.append([c, c])
        else: segs[-1][1] = c
    segs = [g for g in segs if not (g[1] - g[0] <= 8 and cm[g[0]:g[1] + 1].max() > .5)]   # vạch dọc mảnh
    if not segs:
        return None
    best = max(segs, key=lambda g: g[1] - g[0])
    i = segs.index(best)
    lo, hi = best
    j = i - 1
    while j >= 0 and lo - segs[j][1] <= 60: lo = segs[j][0]; j -= 1
    j = i + 1
    while j < len(segs) and segs[j][0] - hi <= 60: hi = segs[j][1]; j += 1
    # nối các cụm sát bên (chữ ngắn đầu/cuối dòng) nếu cách < 28px đã gộp ở trên; giữ cụm lớn nhất
    return x0 + lo, ty0, x0 + hi + 1, ty1

def crop(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    f = frame(a)
    if f and (f[3] - f[1] < 100 or f[2] - f[0] < 120):
        f = None                                # nhận nhầm một vạch ngang -> dùng vị trí chuẩn
    if not f:
        H, W, _ = a.shape
        if W != 784 or not (220 <= H <= 290): return None, "no frame"
        f = (285, 8, 456, 141)                  # khung mờ / không viền: lấy vị trí chuẩn của thẻ
    L, T, R, B = f
    tb = text_box(a, R, T, B)
    if not tb: return None, "no text"
    tx0, ty0, tx1, ty1 = tb
    pic = im.crop((L, T, R + 1, B + 1))
    txt = im.crop((tx0, ty0, tx1, ty1))
    pad = 14
    Hh = max(pic.height, txt.height)
    out = Image.new("RGB", (pic.width + pad * 3 + txt.width + pad, Hh), "white")
    out.paste(pic, (0, (Hh - pic.height) // 2))
    out.paste(txt, (pic.width + pad * 3, (Hh - txt.height) // 2))
    return out, (L, T, R, B, tx0, ty0, tx1, ty1)

if __name__ == "__main__":
    import glob, os
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs/hanzi-viewer"
    out = root / "story"
    out.mkdir(exist_ok=True)
    want = set(sys.argv[1:])
    fail = []
    files = sorted(glob.glob(str(root / "tap*/*.webp")))
    for p in files:
        no = os.path.basename(p)[:-5]
        if want and no not in want:
            continue
        try:
            o, info = crop(p)
        except Exception as e:                  # thẻ lạ (trang sách lẫn vào…)
            o, info = None, f"lỗi {e}"
        if o is None:
            fail.append((no, info))
            continue
        o.save(out / f"{no}.webp", "WEBP", quality=90)
    print(f"xong {len(files) - len(fail) if not want else len(want) - len(fail)} ảnh; không cắt được {len(fail)}:", fail)
