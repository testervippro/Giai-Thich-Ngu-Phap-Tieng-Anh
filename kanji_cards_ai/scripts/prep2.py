import sys, os, json, glob
from PIL import Image
SRC = "/Users/kieuxuanthoai/Giai-Thich-Ngu-Phap-Tieng-Anh/docs/kanji-viewer"
B = 150
def top_cut(im):
    g = im.convert("L"); w, h = g.size; px = g.load()
    def dark_row(y): return sum(1 for x in range(int(w * .3), int(w * .98), 2) if px[x, y] < 110) / ((w * .68) / 2)
    ys = range(int(h * .45), int(h * .75))
    y = max(ys, key=dark_row)
    return y if dark_row(y) > .6 else None
todo = []
for d in ("kanji_p1", "kanji_p2"):
    os.makedirs("webp/" + d, exist_ok=True)
    for f in sorted(glob.glob("%s/%s/*.webp" % (SRC, d))):
        if not os.path.exists("webp/%s/%s" % (d, os.path.basename(f))):
            todo.append((d, f))
print("còn", len(todo), "thẻ", flush=True)
for bi in range(0, len(todo), B):
    bd = "b2_%04d" % bi
    os.makedirs(bd + "/in"); os.makedirs(bd + "/out")
    meta = {}
    for d, f in todo[bi:bi + B]:
        im = Image.open(f).convert("RGB")
        y = top_cut(im)
        n = d + "__" + os.path.basename(f)[:-5]
        (im.crop((0, 0, im.width, y)) if y else im).save("%s/in/%s.png" % (bd, n))
        meta[n] = [f, y]
    json.dump(meta, open(bd + "/meta.json", "w"))
