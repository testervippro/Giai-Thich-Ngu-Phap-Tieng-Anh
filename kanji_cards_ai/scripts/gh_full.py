"""25 thẻ bị hằn: dựng lại THẺ ĐẦY ĐỦ (x2) = thẻ đã làm nét + ô câu chuyện từ AI chạy trên ảnh gốc đã xoá hằn
(gh/out), rồi xoá hằn sau AI (giữ nét thật) + bỏ cụm chấm nhạt trong ô câu chuyện."""
import sys, json
sys.path.insert(0, '.')
import numpy as np
from collections import deque
from PIL import Image
from deghost2 import deghost
SRC = '/Users/kieuxuanthoai/Giai-Thich-Ngu-Phap-Tieng-Anh/docs/kanji-viewer/kanji_p2/'

def comp_clean(a):
    ink = 1 - a.min(axis=2) / 255.
    m = ink > .1; h, w = m.shape; seen = np.zeros_like(m); out = a.copy()
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
            if (len(comp) <= 90 and mx < .72) or (mx < .6 and len(comp) < 8000):
                for p in comp: out[p] = 255
    return out

if __name__ == "__main__":
    ns = json.load(open('gh/list.json'))
    r = json.load(open('ghost_scan2.json')); meta = json.load(open('story_meta.json'))['boxes']
    todo = {int(n): v[0][1:] for n, v in r.items() if v and v[0][0] >= .25}; todo[1431] = [1427, -36, 9]
    for n in ns:
        name = '%04d.webp' % n; b = meta[name]; m, dy, dx = todo[n]
        full = Image.open('webp/kanji_p2/' + name).convert('RGB')
        w, h = Image.open('gh/in/%04d.png' % n).size
        ai = Image.open('gh/out/%04d.png' % n).convert('RGB').resize((w * 2, h * 2), Image.LANCZOS)
        full.paste(ai, (b[0] * 2, b[1] * 2))
        o, _, _ = deghost(SRC + name, SRC + '%04d.webp' % m, full, dy, dx, real_thr=.66, keep_sat=.3, STRICT=True)
        box2 = tuple(v * 2 for v in b)
        inner = (box2[0] + 6, box2[1] + 6, box2[2] - 6, box2[3] - 6)     # chừa đường khung
        from clean_text import clean
        reg = comp_clean(clean(np.asarray(o.crop(inner))))
        o.paste(Image.fromarray(reg), inner[:2])
        o.save('webp/kanji_p2/' + name, 'WEBP', quality=84, method=4)
    print('dựng lại', len(ns), 'thẻ đầy đủ')
