#!/usr/bin/env python3
"""Điền nghĩa tiếng Việt vào cạnh mỗi nhãn tiếng Anh trong PDF từ điển tranh.

- Đọc vị trí từng nhãn "<số/icon> <từ>" trên trang (PyMuPDF).
- Tra nghĩa tiếng Việt trong glossary (JSON: {"english term": "nghĩa"}).
- Chèn nghĩa tiếng Việt ngay dưới từ tiếng Anh, chữ xanh, font Unicode có dấu.
- KHÔNG ghi đè bản gốc: xuất ra một file PDF mới.

    python3 tools/audio/pdf_annotate_vi.py IN.pdf -g glossary.json -o OUT.pdf -p 14
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import fitz  # PyMuPDF

FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
MARKER = re.compile(r"^([0-9]{1,2}|[a-z])$")


def reconstruct_labels(page) -> list[dict]:
    """Trả về [{term, x0, y1, x1}] cho từng nhãn.

    Gom theo (block, line) mà PyMuPDF trả về — mỗi dòng gốc là một nhãn
    "<marker> <từ>", khớp với cách pdftotext tách dòng nên đáng tin hơn là
    gom theo toạ độ y (dễ dính 2 cột trái/phải cùng hàng).
    """
    words = page.get_text("words")  # (x0,y0,x1,y1, word, block,line,wno)
    lines: dict[tuple[int, int], list] = {}
    for w in words:
        lines.setdefault((w[5], w[6]), []).append(w)

    labels = []
    open_label = None       # nhãn đang mở, có thể nhận thêm dòng nối tiếp
    open_line = None        # (block, line) của dòng cuối trong nhãn đang mở
    for key in sorted(lines):
        row = sorted(lines[key], key=lambda w: w[7])  # theo thứ tự từ
        toks = [w[4] for w in row]
        has_marker = bool(toks) and MARKER.match(toks[0])
        term_words = row[1:] if has_marker else row
        if not term_words:
            continue
        term = " ".join(w[4] for w in term_words)
        if not re.search(r"[A-Za-z]", term):
            continue
        x0, x1 = term_words[0][0], max(w[2] for w in term_words)
        y1 = max(w[3] for w in term_words)

        # cụm bị ngắt dòng, vd "to hold" / "your breath" (cùng block, dòng kế
        # tiếp, không có marker riêng): nối vào nhãn trước thay vì tạo mới.
        is_continuation = (
            not has_marker and open_label is not None
            and open_line == (key[0], key[1] - 1)
            and abs(x0 - open_label["x0"]) < 20
        )
        if is_continuation:
            open_label["term"] += " " + term
            open_label["x1"] = max(open_label["x1"], x1)
            open_label["y1"] = y1
        else:
            open_label = {"term": term, "x0": x0, "x1": x1, "y1": y1}
            labels.append(open_label)
        open_line = key
    return labels


def norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower()).strip()


def annotate(pdf: Path, glossary: dict, out: Path, pages: list[int]) -> None:
    doc = fitz.open(pdf)
    gl = {norm(k): v for k, v in glossary.items()}
    total = missing = 0
    miss_terms: set[str] = set()
    for pno in pages:
        page = doc[pno - 1]
        page.insert_font(fontname="viet", fontfile=FONT)
        labels = reconstruct_labels(page)
        # Khoảng cách tới nhãn kế tiếp GẦN NHẤT theo chiều dọc, để nhãn dày đặc
        # (hai dòng cách nhau ~11pt như "gray (US)" / "grey (UK)") không bị đè.
        ys = sorted({lab["y1"] for lab in labels})
        for lab in labels:
            vi = gl.get(norm(lab["term"]))
            total += 1
            if not vi:
                missing += 1
                miss_terms.add(lab["term"])
                continue
            nexts = [y for y in ys if y > lab["y1"] + 0.5]
            gap = (nexts[0] - lab["y1"]) if nexts else 20.0
            offset = max(5.0, min(9.0, gap * 0.55))
            fontsize = 7.0 if gap >= 15 else 5.5
            page.insert_text(
                fitz.Point(lab["x0"], lab["y1"] + offset),
                vi, fontname="viet", fontsize=fontsize, color=(0, 0.2, 0.75),
            )
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    print(f"Đã điền {total - missing}/{total} nhãn. Thiếu nghĩa: {missing}")
    if miss_terms:
        print("Chưa có trong glossary:", ", ".join(sorted(miss_terms)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-g", "--glossary", type=Path, required=True)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("-p", "--pages", default="14",
                    help="Trang cần điền, vd '14' hoặc '14-40' hoặc '14,15,20'")
    args = ap.parse_args()

    pages: list[int] = []
    for part in args.pages.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))

    glossary = json.loads(args.glossary.read_text(encoding="utf-8"))
    annotate(args.pdf, glossary, args.out, pages)


if __name__ == "__main__":
    main()
