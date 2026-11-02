#!/usr/bin/env python3
"""Markdown (kèm bảng HTML) -> văn bản thuần để đọc thành audio.

Việc chính:
  * Bảng <table> -> câu đọc được ("Giới từ: during. Ý nghĩa: ... Ví dụ: ...")
  * Bỏ ký hiệu markdown / emoji / đường kẻ ngang
  * Chèn dấu chấm để TTS ngắt nghỉ đúng chỗ
  * Cắt thành nhiều "track" theo tiêu đề, mỗi track ~1 giờ audio

Dùng:
    python3 tools/audio/md_to_speech.py docs/MindMap-Full.md -o build/audio-text
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------- bảng HTML


class _TableParser(HTMLParser):
    """Gom <table> thành list[list[str]]."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            if self._row is not None:
                self._row.append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def _end_sentence(text: str) -> str:
    text = text.strip().rstrip(",;")
    if not text:
        return ""
    return text if text[-1] in ".!?:…" else text + "."


def table_to_speech(html: str) -> str:
    """Bảng -> đoạn văn. Hàng đầu được coi là tiêu đề cột nếu nó ngắn."""
    p = _TableParser()
    p.feed(html)
    rows = [r for r in p.rows if any(c.strip() for c in r)]
    if not rows:
        return ""

    header = rows[0]
    body = rows[1:]
    # Hàng đầu chỉ là tiêu đề khi mọi ô đều ngắn và không phải câu.
    looks_like_header = body and all(len(c) <= 40 and not c.endswith(".") for c in header)
    if not looks_like_header:
        header, body = [], rows

    out: list[str] = []
    for row in body:
        bits: list[str] = []
        for idx, cell in enumerate(row):
            cell = cell.strip()
            if not cell:
                continue
            label = header[idx].strip() if idx < len(header) else ""
            bits.append(f"{label}: {cell}" if label else cell)
        if bits:
            out.append(" ".join(_end_sentence(b) for b in bits))
    return "\n".join(out)


# ------------------------------------------------------------- làm sạch text

EMOJI = re.compile(
    "[\U0001f300-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff️•]"
)
BULLET = re.compile(r"^\s*(?:[-*+•▪◦–—]|\d+[.)]|[a-zA-Z][.)]|[IVXivx]+[.)])\s+")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
MD_TABLE_ROW = re.compile(r"^\s*\|")
HR = re.compile(r"^\s*([-*_])\1{2,}\s*$")

# Đo thực tế với vi-VN-HoaiMyNeural ở tốc độ mặc định: ~740 ký tự/phút.
CPM = 740


def clean_inline(text: str) -> str:
    # Gỡ thẻ HTML TRƯỚC khi đụng tới ký hiệu markdown, nếu không dấu ">"
    # của blockquote sẽ cắt nát thuộc tính thẻ.
    text = re.sub(r"<[^<>]*>", " ", text)                       # thẻ HTML lẻ
    text = re.sub(r"</?[a-zA-Z][^<>]*", " ", text)              # thẻ hở
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)           # ảnh
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)        # link
    text = re.sub(r"^\s*>+\s*", "", text)                       # blockquote
    text = re.sub(r"[*_`]+", " ", text)                         # nhấn mạnh / code
    text = EMOJI.sub(" ", text)
    text = text.replace("→", " thành ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def md_table_to_speech(lines: list[str]) -> str:
    cells = [
        [c.strip() for c in ln.strip().strip("|").split("|")]
        for ln in lines
        if not re.match(r"^\s*\|[\s:|-]+\|?\s*$", ln)
    ]
    if not cells:
        return ""
    header, body = (cells[0], cells[1:]) if len(cells) > 1 else ([], cells)
    out = []
    for row in body:
        bits = []
        for i, c in enumerate(row):
            if not c:
                continue
            label = header[i] if i < len(header) else ""
            bits.append(f"{label}: {c}" if label else c)
        if bits:
            out.append(" ".join(_end_sentence(b) for b in bits))
    return "\n".join(out)


# ----------------------------------------------------------------- cấu trúc


class Block:
    __slots__ = ("level", "title", "lines")

    def __init__(self, level: int, title: str) -> None:
        self.level = level          # 0 = phần mở đầu, 1..6 = cấp tiêu đề
        self.title = title
        self.lines: list[str] = []

    @property
    def size(self) -> int:
        return sum(len(x) + 1 for x in self.lines) + len(self.title)


def parse(md: str) -> list[Block]:
    # Bảng HTML nằm gọn trên một dòng trong file này, nhưng vẫn xử lý cả
    # trường hợp trải nhiều dòng.
    md = re.sub(
        r"<table\b.*?</table>",
        lambda m: "\n" + table_to_speech(m.group(0)) + "\n",
        md,
        flags=re.S | re.I,
    )

    blocks = [Block(0, "")]
    raw = md.splitlines()
    i = 0
    while i < len(raw):
        line = raw[i]

        if MD_TABLE_ROW.match(line):
            group = []
            while i < len(raw) and MD_TABLE_ROW.match(raw[i]):
                group.append(raw[i])
                i += 1
            spoken = md_table_to_speech(group)
            if spoken:
                blocks[-1].lines.extend(spoken.splitlines())
            continue

        i += 1

        if HR.match(line):
            continue

        m = HEADING.match(line)
        if m:
            title = clean_inline(m.group(2))
            if title:
                blocks.append(Block(len(m.group(1)), title))
            continue

        line = BULLET.sub("", line)
        line = clean_inline(line)
        if line:
            blocks[-1].lines.append(_end_sentence(line))

    return [b for b in blocks if b.title or b.lines]


def slug(text: str, limit: int = 48) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("đ", "d")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:limit].strip("-") or "phan"


def render(block: Block) -> str:
    out = []
    if block.title:
        # Dấu chấm + dòng trống -> TTS nghỉ rõ giữa các mục.
        out.append(_end_sentence(block.title))
        out.append("")
    out.extend(block.lines)
    out.append("")
    return "\n".join(out)


def pack(blocks: list[Block], max_chars: int) -> list[tuple[str, str]]:
    """Gộp block thành track, chỉ cắt ở tiêu đề cấp 1-2."""
    tracks: list[tuple[str, str]] = []
    cur: list[Block] = []
    size = 0

    def flush() -> None:
        nonlocal cur, size
        if not cur:
            return
        # Đặt tên track theo tiêu đề cấp cao nhất trong track, không phải
        # block đầu tiên (block đầu thường là tiêu đề con bị cắt sang).
        headed = [b for b in cur if b.title]
        title = min(headed, key=lambda b: b.level).title if headed else "Phần"
        tracks.append((title, "\n".join(render(b) for b in cur)))
        cur, size = [], 0

    for b in blocks:
        over = size + b.size > max_chars
        # Ưu tiên cắt ở tiêu đề cấp 1; chỉ chấp nhận cấp 2 khi đã quá dài.
        if cur and over and (b.level == 1 or (b.level == 2 and size > max_chars * 1.4)):
            flush()
        cur.append(b)
        size += b.size
    flush()
    return tracks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("build/audio-text"))
    ap.add_argument(
        "--max-chars",
        type=int,
        default=45_000,
        help="Kích thước tối đa mỗi track (~45k ký tự ≈ 1 giờ audio)",
    )
    ap.add_argument("--single", action="store_true", help="Xuất 1 file duy nhất")
    args = ap.parse_args()

    md = args.input.read_text(encoding="utf-8")
    blocks = parse(md)
    tracks = (
        [(args.input.stem, "\n".join(render(b) for b in blocks))]
        if args.single
        else pack(blocks, args.max_chars)
    )

    args.out.mkdir(parents=True, exist_ok=True)
    index = []
    for n, (title, text) in enumerate(tracks, 1):
        text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
        path = args.out / f"{n:02d}-{slug(title)}.txt"
        path.write_text(text, encoding="utf-8")
        mins = len(text) / CPM
        index.append(f"{path.name}\t{len(text):>7,} ký tự\t~{mins:5.1f} phút\t{title}")
        print(index[-1])

    (args.out / "index.tsv").write_text("\n".join(index) + "\n", encoding="utf-8")
    total = sum(len(t) for _, t in tracks)
    print(f"\n{len(tracks)} track, {total:,} ký tự, ước tính ~{total / CPM / 60:.1f} giờ audio")
    print(f"Đã ghi vào {args.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
