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
