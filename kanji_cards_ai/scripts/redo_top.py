"""900 thẻ đã làm AI cả thẻ -> chỉ giữ AI ở nửa trên (chữ Hán + câu chuyện), nửa dưới phóng to thường."""
import glob, os, sys
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, ".")
SRC = "/Users/kieuxuanthoai/Giai-Thich-Ngu-Phap-Tieng-Anh/docs/kanji-viewer"
from topcut import top_cut
def one(f):
    d, name = f.split("/")[-2], os.path.basename(f)
    orig = Image.open("%s/%s/%s" % (SRC, d, name)).convert("RGB"); w, h = orig.size
    y = top_cut(orig)
    if not y:
        return "full"
    ai = Image.open(f).convert("RGB")
    if ai.size != (w * 2, h * 2):
        return "skip"
    full = orig.resize((w * 2, h * 2), Image.LANCZOS)
    full.paste(ai.crop((0, 0, w * 2, y * 2)), (0, 0))
    full.save(f + ".tmp", "WEBP", quality=84, method=4)
    os.replace(f + ".tmp", f)
    return "top"
if __name__ == "__main__":
    fs = [l.strip() for l in open("redo_list.txt")]
    from collections import Counter
    with ProcessPoolExecutor(6) as ex:
        print(Counter(ex.map(one, fs)))
