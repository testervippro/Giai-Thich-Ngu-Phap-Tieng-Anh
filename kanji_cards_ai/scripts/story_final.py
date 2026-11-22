"""Cắt ô câu chuyện từ thẻ đã làm nét (x2) + BỎ VIỀN ĐEN (khung trên/phải/dưới/trái, góc bo) + bỏ dải bảng dưới.
Khung dò trên ảnh gốc (topcut.story_box, mép trên theo đoạn tối liền mạch); dò hụt -> tỉ lệ của ~30 thẻ gần nhất."""
import glob, os, sys, statistics, json
from collections import deque
import numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")
from topcut import story_box, top_cut
SRC = "/Users/kieuxuanthoai/Giai-Thich-Ngu-Phap-Tieng-Anh/docs/kanji-viewer"
GHOST = {"%04d" % n for n in json.load(open("deghosted.json"))}


def detect(f):
    im = Image.open(f).convert("RGB")
    return f, im.size, story_box(im), top_cut(im)


def longest_run(mask):
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def trim(a):
    """Cắt bỏ đường kẻ đen sát mép (kể cả hơi nghiêng: xét dải 10 hàng/cột) và dải màu của bảng bên dưới."""
    a0 = a
    dark = (a.max(axis=2) < 200) & ((a.max(axis=2).astype(int) - a.min(axis=2)) < 60)   # nét đen/xám, không tính mảng màu
    h, w = dark.shape
    B = 10
    def band_rows(y0, y1, x0, x1):  # cột nào có điểm tối trong dải hàng y0..y1
        return dark[max(0, y0):y1, x0:x1].any(axis=0)
    def band_cols(x0, x1, y0, y1):
        return dark[y0:y1, max(0, x0):x1].any(axis=1)
    t, b, l, r = 0, h, 0, w
    # chỉ cắt đường kẻ SÁT MÉP: đi từ mép vào, gặp dải không còn đường kẻ thì dừng
    seen = False
    for y in range(0, int(h * .14)):                    # mép trên
        if longest_run(band_rows(y, y + B, 0, w)) > .55 * w: t = y + B; seen = True
        elif seen or y > B: break
    seen = False
    for y in range(h, int(h * .84), -1):                # mép dưới
        if longest_run(band_rows(y - B, y, 0, w)) > .55 * w: b = min(b, y - B); seen = True
        elif seen or y < h - B: break
    seen = False
    for x in range(w, int(w * .93), -1):                # mép phải
        if longest_run(band_cols(x - B, x, t, b)) > .55 * (b - t): r = min(r, x - B); seen = True
        elif seen or x < w - B: break
    seen = False
    for x in range(0, int(w * .07)):                    # mép trái
        if longest_run(band_cols(x, x + B, t, b)) > .55 * (b - t): l = x + B; seen = True
        elif seen or x > B: break
    if (b - t) < .85 * h or (r - l) < .85 * w:       # chốt an toàn: cắt quá nhiều -> bỏ qua
        t, b, l, r = 0, h, 0, w
    a = a[t:b, l:r]
    h, w, _ = a.shape
    rm = a[:, w // 2:].min(axis=2).mean(axis=1)
    y = h - 1
    while y > h * .8 and rm[y] < 225: y -= 1
    return a[:y + 1]


def clean_corners(a):
    """Góc bo tròn: tô trắng nét đen nối với mép ảnh, chỉ trong 4 ô góc."""
    a = a.copy(); h, w, _ = a.shape
    R = int(min(h, w) * .22)
    dark = a.min(axis=2) < 170
    for ys, xs in ((range(0, R), range(w - R, w)), (range(0, R), range(0, R)),
                   (range(h - R, h), range(w - R, w)), (range(h - R, h), range(0, R))):
        y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
        seen = np.zeros((h, w), bool); q = deque()
        for y in (y0, y1 - 1):
            for x in range(x0, x1):
                if dark[y, x] and (y in (0, h - 1)): q.append((y, x)); seen[y, x] = True
        for x in (x0, x1 - 1):
            for y in range(y0, y1):
                if dark[y, x] and (x in (0, w - 1)): q.append((y, x)); seen[y, x] = True
        while q:
            y, x = q.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if y0 <= yy < y1 and x0 <= xx < x1 and not seen[yy, xx] and dark[yy, xx]:
                        seen[yy, xx] = True; q.append((yy, xx))
        # chỉ xoá nếu là nét mảnh dạng cung (không phải mảng tranh lớn chạm mép)
        if 0 < seen.sum() < R * 6:
            m = seen.copy()
            for _ in range(2):                           # nới 2 px để xoá viền răng cưa
                m[1:, :] |= m[:-1, :]; m[:-1, :] |= m[1:, :]; m[:, 1:] |= m[:, :-1]; m[:, :-1] |= m[:, 1:]
            sub = np.zeros((h, w), bool); sub[y0:y1, x0:x1] = True
            a[m & sub & (a.min(axis=2) < 235)] = 255
    return a


def erase_edge_lines(a):
    """Nét kẻ mảnh, dài, chạy dọc theo mép (đường khung nghiêng còn sót) trong dải sát mép -> trắng."""
    a = a.copy(); h, w, _ = a.shape
    mx = a.max(axis=2).astype(int); mn = a.min(axis=2).astype(int)
    line = (mx < 215) & (mx - mn < 70)
    kh, kw = max(6, int(h * .12)), max(6, int(w * .10))
    bands = [((0, kh), (0, w), "h"), ((h - kh, h), (0, w), "h"), ((0, h), (w - kw, w), "v"), ((0, h), (0, kw), "v")]
    for (y0, y1), (x0, x1), o in bands:
        sub = line[y0:y1, x0:x1].copy(); H, W = sub.shape
        seen = np.zeros_like(sub)
        for sy in range(H):
            for sx in range(W):
                if not sub[sy, sx] or seen[sy, sx]: continue
                comp = []; q = deque([(sy, sx)]); seen[sy, sx] = True
                while q:
                    y, x = q.popleft(); comp.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < H and 0 <= xx < W and sub[yy, xx] and not seen[yy, xx]:
                                seen[yy, xx] = True; q.append((yy, xx))
                ys = [c[0] for c in comp]; xs = [c[1] for c in comp]
                L = (max(xs) - min(xs) + 1) if o == "h" else (max(ys) - min(ys) + 1)
                T = (max(ys) - min(ys) + 1) if o == "h" else (max(xs) - min(xs) + 1)
                edge = W if o == "h" else H
                if L > .2 * edge and len(comp) < L * 6 and T < (H if o == "h" else W) * .9 + 1:
                    for y, x in comp:
                        a[y0 + y, x0 + x] = 255
                        for dy in (-1, 0, 1):          # cả viền răng cưa 1 px
                            for dx in (-1, 0, 1):
                                yy, xx = y0 + y + dy, x0 + x + dx
                                if 0 <= yy < h and 0 <= xx < w and a[yy, xx].min() > 150: a[yy, xx] = 255
    return a


def cut(args):
    f, b = args
    d, name = f.split("/")[-2], os.path.basename(f)
    up = "webp/%s/%s" % (d, name)
    a = np.asarray(Image.open(up).convert("RGB").crop(tuple(v * 2 for v in b)))
    a = erase_edge_lines(clean_corners(trim(a)))
    if name[:4] in GHOST:                               # thẻ bị hằn mặt sau: xoá vệt xám ở vùng chữ
        from clean_text import clean
        a = clean(a)
    Image.fromarray(a).save("story/" + name, "WEBP", quality=85, method=4)


def main():
    fs = sorted(glob.glob(SRC + "/kanji_p*/*.webp"))
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(detect, fs, chunksize=20))
    boxes, guessed = {}, []
    for i, (f, (w, h), b, y) in enumerate(res):
        if not b:
            near = [r for r in res[max(0, i - 15):i + 16] if r[2] and r[0].split("/")[-2] == f.split("/")[-2]]
            nx = statistics.median(r[2][0] / r[1][0] for r in near)
            ny = statistics.median(r[2][3] / r[1][1] for r in near)
            b = (int(w * nx) + 2, 0, w, y or int(h * ny))
            guessed.append(os.path.basename(f))
        boxes[f] = b
    os.makedirs("story", exist_ok=True)
    only = set(sys.argv[1:])
    items = [kv for kv in boxes.items() if not only or os.path.basename(kv[0])[:4] in only]
    with ProcessPoolExecutor(6) as ex:
        list(ex.map(cut, items, chunksize=20))
    json.dump({"guessed": guessed, "boxes": {os.path.basename(k): v for k, v in boxes.items()}}, open("story_meta.json", "w"))
    print("cắt %d ảnh; %d thẻ đoán khung" % (len(boxes), len(guessed)))


if __name__ == "__main__":
    main()
