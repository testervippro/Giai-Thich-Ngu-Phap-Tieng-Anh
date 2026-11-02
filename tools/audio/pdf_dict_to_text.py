#!/usr/bin/env python3
"""PDF từ điển tranh (DK Illustrated Dictionary) -> văn bản thuần để đọc.

Từ điển tranh có mỗi mục là "<số/icon> <từ>" trỏ vào hình minh hoạ. Đọc thẳng
ra sẽ thành "một brain bảy sinus hai palate..." — vô nghĩa. Script này bóc nhãn
đánh số, gộp dòng bị ngắt, sửa vài lỗi ngắt từ hay gặp, giữ tiêu đề mục, rồi cắt
thành các track ~1 giờ để đưa sang tts.py.

    python3 tools/audio/pdf_dict_to_text.py "…DK.pdf" -o build/dict-audio-text
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

# icon "số khoanh tròn" của DK bị pdftotext map sang các phím này (hàng bàn phím)
ICON = set("qwertyuiopasdfghjklzxcvbnm")

# dòng chỉ là số trang / marker đơn lẻ
PAGE_NUM = re.compile(r"^\d{1,3}$")
# "<marker> <từ>": marker = 1-2 chữ số, HOẶC một chữ cái thường (icon)
LABEL = re.compile(r"^([0-9]{1,2}|[a-z])\s+(.+)$")
# marker icon lọt vào GIỮA dòng khi 2 cột nhãn bị gộp: "... plant w polka dot ..."
# tách ở đây, nhưng chừa " a " (mạo từ thật) để không xé câu.
INLINE = re.compile(r"\s+(?:[0-9]{1,2}|[b-z])\s+(?=[a-z])")


def split_labels(term: str) -> list[str]:
    parts = INLINE.split(" " + term + " ")
    return [p.strip() for p in parts if p.strip()]


def fix_word(s: str) -> str:
    """Sửa vài lỗi ngắt từ hay gặp trong bản trích."""
    s = s.strip()
    # "fatherin-law" / "sister-inlaw" -> "father-in-law" / "sister-in-law"
    s = re.sub(r"([a-z])in-?law\b", r"\1-in-law", s)
    s = s.replace("-inlaw", "-in-law")
    # dấu ngoặc kép cong -> thẳng để TTS đọc ổn
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def clean_page(text: str) -> list[str]:
    """Trả về danh sách 'mục đọc được' của 1 trang."""
    out: list[str] = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if PAGE_NUM.match(line):                 # số trang
            continue
        if line.lower().startswith("see also"):  # tham chiếu chéo -> bỏ khi nghe
            continue
        # tiêu đề mục viết HOA (FAMILY, INTERNAL ORGANS) -> giữ, đổi Title Case
        letters = re.sub(r"[^A-Za-z]", "", line)
        if letters and line.upper() == line and len(letters) >= 3:
            out.append(fix_word(line.title()))
            continue
        m = LABEL.match(line)
        body = m.group(2) if m else line
        # dòng thường (không marker) vẫn giữ nếu có chữ
        if not m and not re.search(r"[A-Za-z]", line):
            continue
        for term in split_labels(fix_word(body)):
            if term and re.search(r"[A-Za-z]", term):
                out.append(term)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("build/dict-audio-text"))
    ap.add_argument("-f", "--first", type=int, default=1, help="Trang bắt đầu")
    ap.add_argument("-l", "--last", type=int, default=0, help="Trang cuối (0 = hết)")
    ap.add_argument("--max-chars", type=int, default=42000, help="Ký tự tối đa mỗi track")
    args = ap.parse_args()

    # đọc từng trang để giữ ranh giới mục
    info = subprocess.run(["pdfinfo", str(args.pdf)], capture_output=True, text=True).stdout
    total = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    last = args.last or total

    items: list[str] = []
    for pg in range(args.first, last + 1):
        raw = subprocess.run(
            ["pdftotext", "-f", str(pg), "-l", str(pg), str(args.pdf), "-"],
            capture_output=True, text=True,
        ).stdout
        page_items = clean_page(raw)
        if page_items:
            items.extend(page_items)

    # khử lặp liên tiếp (nhiều trang lặp tiêu đề)
    dedup: list[str] = []
    for it in items:
        if not dedup or dedup[-1] != it:
            dedup.append(it)

    # cắt thành track ~max-chars, mỗi mục 1 dòng (tts.py cắt theo đoạn/câu)
    args.out.mkdir(parents=True, exist_ok=True)
    tracks: list[list[str]] = [[]]
    size = 0
    for it in dedup:
        if size + len(it) + 1 > args.max_chars and tracks[-1]:
            tracks.append([])
            size = 0
        tracks[-1].append(it)
        size += len(it) + 1

    for i, tk in enumerate(tracks, 1):
        # mỗi mục thành 1 câu (thêm dấu chấm) để TTS ngắt nhịp rõ ràng
        body = "\n\n".join(x if x.endswith((".", "!", "?")) else x + "." for x in tk)
        (args.out / f"{i:02d}-dictionary.txt").write_text(body, encoding="utf-8")

    chars = sum(len(x) for x in dedup)
    print(f"{len(dedup):,} mục, {chars:,} ký tự -> {len(tracks)} track trong {args.out}/")


if __name__ == "__main__":
    main()
