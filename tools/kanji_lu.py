#!/usr/bin/env python3
"""docs/kanji-meo-nho.md (mục 4: chữ 3·LÚ / 2·mơ hồ) -> docs/kanji-viewer/kanji-lu.js

window.KANJI_LU = [[số thẻ, độ lú 3|2, ghi chú html], ...] — dùng cho bộ "🤯 Kanji khó nhớ"
ở trang Luyện viết.   python3 tools/kanji_lu.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
md = (ROOT / "docs/kanji-meo-nho.md").read_text(encoding="utf-8")
rows, level = [], 0
for line in md.splitlines():
    if line.startswith("### 4.1"):
        level = 3
    elif line.startswith("### 4.2"):
        level = 2
    elif line.startswith("## ") and level:
        level = 0
    if not level or not re.match(r"\|\s*\d+\s*\|", line):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    note = html.escape(cells[4], quote=False).replace("&lt;br&gt;", "<br>")
    note = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", note)
    rows.append([int(cells[0]), level, note])
out = ROOT / "docs/kanji-viewer/kanji-lu.js"
out.write_text("// Chữ Kanji nghĩa khác tiếng Việt (3 = LÚ, 2 = mơ hồ) — sinh từ docs/kanji-meo-nho.md bằng tools/kanji_lu.py\n"
               "window.KANJI_LU=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
print(out.relative_to(ROOT), len(rows), sum(r[1] == 3 for r in rows), "LÚ")
