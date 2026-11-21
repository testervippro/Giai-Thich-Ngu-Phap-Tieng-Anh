#!/usr/bin/env python3
"""Truyện dài "Hành trình của cậu Nhân" (tools/data/kanji_saga/NN.txt) -> docs/kanji-viewer/truyen-data.js
37 phần nguồn (mỗi phần ~60 thẻ theo thứ tự thẻ) gom thành 12 chương lớn; phần nguồn thành đề mục nhỏ (có ảnh truyen-img/NN.webp).
Chữ đang học đánh dấu 【字】, mảnh ghép trong ngoặc (木).
    .venv/bin/python tools/kanji_saga_check.py && .venv/bin/python tools/kanji_saga_build.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanji_video as KV  # noqa: E402

D = KV.ROOT / "tools/data/kanji_saga"
# (tên chương lớn, các phần nguồn)
GROUPS = [
    ("Lên đường", [1, 2, 3]),
    ("Mưa sấm và làng ông Lí", [4, 5, 6]),
    ("Kinh đô và biển cả", [7, 8, 9]),
    ("Phường dệt, thủ lĩnh và chiếc ghế phi phàm", [10, 11, 12]),
    ("Ân nhân, đám cưới và đồng ruộng tự do", [13, 14, 15]),
    ("Vườn ngự uyển, rừng chim và cung điện", [16, 17, 18]),
    ("Thầy phép trên đèo, quần đảo và nước Tề", [19, 20, 21]),
    ("Đảo chim, võ đường và tay thiện xạ", [22, 23, 24]),
    ("Hải cảng, quan giả và vở kịch con hổ", [25, 26, 27]),
    ("Rồng, hươu và phía đông", [28, 29, 30]),
    ("Đại thần, cô Tấm và chiến dịch ngày Tết", [31, 32, 33]),
    ("Thác rồng và ngày trở về", [34, 35, 36, 37]),
]


def part(i):
    lines = [l.strip() for l in (D / f"{i:02d}.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    t = lines[0].lstrip("# ").strip()
    return {"t": t.split(". ", 1)[-1], "img": f"{i:02d}", "p": lines[1:]}


srcs = sorted(int(f.stem) for f in D.glob("*.txt"))
assert sorted(i for _, g in GROUPS for i in g) == srcs, "GROUPS phải phủ đúng mọi phần nguồn"
out = [{"t": f"Chương {n}. {t}", "s": [part(i) for i in g]} for n, (t, g) in enumerate(GROUPS, 1)]
dest = KV.KV / "truyen-data.js"
dest.write_text("// tạo bởi tools/kanji_saga_build.py — sửa ở tools/data/kanji_saga/*.txt\nwindow.SAGA = "
                + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
print(dest, len(out), "chương,", len(srcs), "phần")
