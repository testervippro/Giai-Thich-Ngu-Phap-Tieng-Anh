#!/bin/bash
# Làm nét 2.097 ảnh thẻ Kanji bằng Real-ESRGAN x4plus-anime.
# Lô 100 ảnh; bước đổi sang WebP chạy song song (nền) trong lúc GPU làm lô kế tiếp.
# Chạy lại được: ảnh đã có trong cards/webp sẽ bỏ qua.
set -e
SP=/private/tmp/claude-501/-Users-kieuxuanthoai-Giai-Thich-Ngu-Phap-Tieng-Anh/82d55789-ce18-4f55-8dbd-4b6a5843e0e4/scratchpad
SRC=/Users/kieuxuanthoai/Giai-Thich-Ngu-Phap-Tieng-Anh/docs/kanji-viewer
ESR=$SP/esr_dl/esr
C=$SP/cards
PY=/opt/homebrew/bin/python3
B=100
cd "$C"
rm -rf in out b_*
cat > conv.py <<'EOF'
import sys, glob, os
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
bd, d = sys.argv[1], sys.argv[2]
def one(f):
    n = os.path.basename(f)[:-4]
    w, h = Image.open("%s/in/%s.png" % (bd, n)).size
    im = Image.open(f).convert("RGB").resize((w * 2, h * 2), Image.LANCZOS)
    im.save("webp/%s/%s.webp" % (d, n), "WEBP", quality=84, method=4)
if __name__ == "__main__":
    with ProcessPoolExecutor(4) as ex:
        list(ex.map(one, glob.glob(bd + "/out/*.png")))
    import shutil; shutil.rmtree(bd)
EOF
for d in kanji_p1 kanji_p2; do
  mkdir -p webp/$d
  files=()
  for f in "$SRC/$d"/*.webp; do
    n=$(basename "$f")
    [ -f "webp/$d/$n" ] || files+=("$f")
  done
  total=${#files[@]}
  echo "$d: còn $total ảnh"
  for ((i=0; i<total; i+=B)); do
    bd=b_${d}_$i
    mkdir -p $bd/in $bd/out
    for f in "${files[@]:i:B}"; do sips -s format png "$f" --out "$bd/in/$(basename "$f" .webp).png" >/dev/null; done
    "$ESR/realesrgan-ncnn-vulkan" -i $bd/in -o $bd/out -n realesrgan-x4plus-anime -m "$ESR/models" -f png -j 2:2:2 >/dev/null 2>&1
    wait                                   # lô WebP trước phải xong (giới hạn ổ đĩa)
    $PY conv.py $bd $d &
    echo "  $d $((i+B < total ? i+B : total))/$total  $(date +%H:%M)"
  done
done
wait
echo "XONG: $(ls webp/kanji_p1 | wc -l) + $(ls webp/kanji_p2 | wc -l) ảnh, $(du -sh webp | cut -f1)"
