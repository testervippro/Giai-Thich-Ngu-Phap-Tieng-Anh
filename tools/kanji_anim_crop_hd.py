#!/usr/bin/env python3
"""Toạ độ vùng TRANH [x0, y0, x1, y1] (pixel của ảnh kanji_story/NNNN.webp) cho trang Kanji chuyển động.

    python3 tools/kanji_anim_crop_hd.py     # -> docs/kanji-viewer/kanji-anim-crop.js

Dùng cho bộ ảnh dựng lại (build/kanji_story_hd -> docs/kanji-viewer/kanji_story): phần tranh nằm bên trái, chiếm trọn
chiều cao, kết thúc ở ranh giới dò bởi tools/kanji_story_redraw.picture_right_edge. Hộp lấy theo vùng khác nền trắng.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import kanji_story_redraw as R  # noqa: E402

SRC = ROOT / "docs/kanji-viewer/kanji_story"
story = R.load_story()
out, bad = {}, []
for n in sorted(story):
    f = SRC / f"{n:04d}.webp"
    if not f.exists():
        continue
    im = Image.open(f).convert("RGB")
    W, H = im.size
    px1 = R.picture_right_edge(im)
    a = np.asarray(im.crop((0, 0, px1, H))).astype(int)
    ink = (a.min(2) < 236) | ((a.max(2) - a.min(2)) > 16)
    # bỏ nhiễu rải rác: chỉ tính cột/hàng có đủ điểm mực (tránh vệt mờ ở mép làm khung phình ra)
    cols = np.where(ink.sum(0) >= max(4, 0.012 * H))[0]
    rows = np.where(ink.sum(1) >= max(4, 0.012 * px1))[0]
    if len(cols) == 0 or len(rows) == 0:
        bad.append(n); continue
    x0, x1, y0, y1 = max(0, cols.min() - 3), min(px1, cols.max() + 4), max(0, rows.min() - 3), min(H, rows.max() + 4)
    if x1 - x0 < 60 or y1 - y0 < 40:
        bad.append(n); continue
    out[str(n)] = [int(x0), int(y0), int(x1), int(y1)]
(ROOT / "docs/kanji-viewer/kanji-anim-crop.js").write_text(
    "// Vùng tranh [x0, y0, x1, y1] trong ảnh kanji_story/NNNN.webp (sinh bởi tools/kanji_anim_crop_hd.py)\n"
    "window.KANJI_ANIM_CROP=" + json.dumps(out, separators=(",", ":")) + ";\n", encoding="utf-8")
print(f"{len(out)} thẻ có toạ độ | không tính được: {len(bad)} {bad[:10]}")
