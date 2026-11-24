#!/usr/bin/env python3
"""OCR từng trang PDF sách "Hack Não Kanji" (macOS Vision) để tìm trang chứa một số chữ Hán.

    python3 tools/book_ocr_scan.py "<file.pdf>" <thư mục ra> [trang đầu] [trang cuối]

Mỗi trang -> <ra>/pNNN.json: [{"t": chuỗi, "c": độ tin cậy, "box": [x, y, w, h] (0..1, gốc dưới-trái)}]
và <ra>/pNNN.png (ảnh trang 170 dpi). Cần: pip install ocrmac ; poppler (pdftoppm).
"""
import json
import subprocess
import sys
from pathlib import Path

from ocrmac import ocrmac

pdf, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
n = int(subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])
a = int(sys.argv[3]) if len(sys.argv) > 3 else 1
b = int(sys.argv[4]) if len(sys.argv) > 4 else n
for p in range(a, b + 1):
    js = out / f"p{p:03d}.json"
    if js.exists():
        continue
    base = out / f"p{p:03d}"
    subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", "170", "-png", "-singlefile", pdf, str(base)], check=True)
    res = ocrmac.OCR(str(base) + ".png", language_preference=["ja-JP", "vi-VT", "en-US"],
                     recognition_level="accurate").recognize()
    js.write_text(json.dumps([{"t": t, "c": round(c, 3), "box": [round(x, 4) for x in bb]} for t, c, bb in res],
                             ensure_ascii=False), encoding="utf-8")
    print(p, len(res), flush=True)
