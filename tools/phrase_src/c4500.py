"""4500 English Collocations and Idioms: bảng "| # | Cụm từ | Nghĩa |" trong docs/4500-collocations-idioms.md (OCR từ sách)."""
import re

SOURCE = {"code": "c4500", "name": "4500 English Collocations and Idioms", "url": "../#/4500-collocations-idioms"}

_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*$")


def extract(root):
    out, topic, kind = [], "", "collocation"
    for line in (root / "docs/4500-collocations-idioms.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            topic = re.sub(r"^## (Chủ đề \d+:\s*)?", "", line).strip()
        elif line.startswith("### "):
            kind = "idiom" if "Idiom" in line else "collocation"
        else:
            m = _ROW.match(line)
            if m and re.search(r"[A-Za-z]{2}", m.group(2)):
                out.append({"t": kind, "p": m.group(2), "m": m.group(3), "e": "", "ev": "", "g": topic, "x": "", "ref": ""})
    return out
