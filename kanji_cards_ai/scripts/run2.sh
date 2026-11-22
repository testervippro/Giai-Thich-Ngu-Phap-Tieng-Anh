#!/bin/bash
# Thẻ còn lại: AI chỉ làm NỬA TRÊN thẻ (chữ Hán + tranh + câu chuyện, cắt ở đường kẻ ngang),
# nửa dưới phóng to thường; không dò được đường kẻ -> AI cả thẻ. Chạy lại được (bỏ qua ảnh đã có).
set -e
SP=/private/tmp/claude-501/-Users-kieuxuanthoai-Giai-Thich-Ngu-Phap-Tieng-Anh/82d55789-ce18-4f55-8dbd-4b6a5843e0e4/scratchpad
ESR=$SP/esr_dl/esr
C=$SP/cards
PY=/opt/homebrew/bin/python3
cd "$C"
rm -rf b2_*
cat > prep2.py <<'EOF'
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
EOF
cat > conv2.py <<'EOF'
import sys, os, json
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
bd = sys.argv[1]
meta = json.load(open(bd + "/meta.json"))
def one(n):
    f, y = meta[n]
    d, name = n.split("__")
    orig = Image.open(f).convert("RGB"); w, h = orig.size
    ai = Image.open("%s/out/%s.png" % (bd, n)).convert("RGB")
    if y:
        full = orig.resize((w * 2, h * 2), Image.LANCZOS)
        full.paste(ai.resize((w * 2, y * 2), Image.LANCZOS), (0, 0))
    else:
        full = ai.resize((w * 2, h * 2), Image.LANCZOS)
    full.save("webp/%s/%s.webp" % (d, name), "WEBP", quality=84, method=4)
if __name__ == "__main__":
    with ProcessPoolExecutor(4) as ex:
        list(ex.map(one, list(meta)))
    import shutil; shutil.rmtree(bd)
EOF
$PY prep2.py
for bd in b2_*; do
  "$ESR/realesrgan-ncnn-vulkan" -i $bd/in -o $bd/out -n realesrgan-x4plus-anime -m "$ESR/models" -f png -j 2:2:2 >/dev/null 2>&1
  wait
  $PY conv2.py $bd &
  echo "  lô $bd xong  $(date +%H:%M)"
done
wait
echo "XONG: $(ls webp/kanji_p1 | wc -l) + $(ls webp/kanji_p2 | wc -l) ảnh, $(du -sh webp | cut -f1)"
