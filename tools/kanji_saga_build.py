#!/usr/bin/env python3
"""Truyện dài "Hành trình của cậu Nhân" (tools/data/kanji_saga/NN.txt) -> docs/kanji-viewer/truyen-data.js
Mỗi chương 60 thẻ theo thứ tự thẻ; chữ đang học đánh dấu 【字】, mảnh ghép trong ngoặc (木).
    .venv/bin/python tools/kanji_saga_check.py && .venv/bin/python tools/kanji_saga_build.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanji_video as KV  # noqa: E402

D = KV.ROOT / "tools/data/kanji_saga"
out = []
for f in sorted(D.glob("*.txt")):
    lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    title = lines[0].lstrip("# ").strip()
    out.append({"t": title, "p": lines[1:]})
dest = KV.KV / "truyen-data.js"
dest.write_text("// tạo bởi tools/kanji_saga_build.py — sửa ở tools/data/kanji_saga/*.txt\nwindow.SAGA = "
                + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
print(dest, len(out), "chương")
