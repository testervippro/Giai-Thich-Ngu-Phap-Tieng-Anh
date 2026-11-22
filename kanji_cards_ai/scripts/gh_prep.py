"""25 thẻ bị hằn mặt sau: xoá hằn trên ẢNH GỐC (trước AI) -> gh/in/NNNN.png (ô câu chuyện)."""
import sys, json
sys.path.insert(0, '.')
import numpy as np
from collections import deque
from PIL import Image
from deghost2 import deghost
SRC = '/Users/kieuxuanthoai/Giai-Thich-Ngu-Phap-Tieng-Anh/docs/kanji-viewer/kanji_p2/'

def gray_clean(a):
    a = a.astype(np.float32); ink = 1 - a.min(axis=2) / 255.; sat = (a.max(axis=2) - a.min(axis=2)) / 255.
    g = ((sat < .16) & (ink < .33)) | (ink < .13)
    out = a.copy(); out[g] = 255; return out.astype(np.uint8)

def components_clean(a):
    """Xoá cụm nét đứng riêng: nhỏ & nhạt (<=14 px, đậm nhất <.62) hoặc bất kỳ cỡ nào mà đậm nhất <.5."""
    ink = 1 - a.min(axis=2) / 255.; m = ink > .12; h, w = m.shape
    seen = np.zeros_like(m); out = a.copy()
    for y in range(h):
        for x in range(w):
            if not m[y, x] or seen[y, x]: continue
            comp = []; q = deque([(y, x)]); seen[y, x] = True; mx = 0
            while q:
                cy, cx = q.popleft(); comp.append((cy, cx)); mx = max(mx, ink[cy, cx])
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = cy + dy, cx + dx
                        if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not seen[yy, xx]:
                            seen[yy, xx] = True; q.append((yy, xx))
            if (len(comp) <= 14 and mx < .62) or (mx < .58 and len(comp) < 4000):
                for p in comp: out[p] = 255
    return out

if __name__ == "__main__":
    r = json.load(open('ghost_scan2.json')); meta = json.load(open('story_meta.json'))['boxes']
    todo = {int(n): v[0][1:] for n, v in r.items() if v and v[0][0] >= .25}; todo[1431] = [1427, -36, 9]
    prev = []
    for n, (m, dy, dx) in sorted(todo.items()):
        f = SRC + '%04d.webp' % n; im = Image.open(f).convert('RGB')
        o, _, _ = deghost(f, SRC + '%04d.webp' % m, im, dy, dx, real_thr=.45, keep_sat=.34, STRICT=True)
        b = meta['%04d.webp' % n]
        c = components_clean(gray_clean(np.asarray(o.crop(tuple(b)))))
        Image.fromarray(c).save('gh/in/%04d.png' % n)
        if n in (1421, 1431, 1451, 1437, 1474, 1433):
            prev += [Image.fromarray(np.asarray(im.crop(tuple(b)))), Image.fromarray(c)]
    json.dump(sorted(todo), open('gh/list.json', 'w'))
    W = 800; prev = [p.resize((W, int(W * p.height / p.width)), Image.BICUBIC) for p in prev]
    s = Image.new('RGB', (W * 2 + 10, sum(prev[i].height + 8 for i in range(0, len(prev), 2))), (40, 40, 40)); y = 0
    for i in range(0, len(prev), 2):
        s.paste(prev[i], (0, y)); s.paste(prev[i + 1], (W + 10, y)); y += prev[i].height + 8
    s.save('gh_prev5.png')
