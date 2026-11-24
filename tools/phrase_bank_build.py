#!/usr/bin/env python3
"""Gộp mọi nguồn trong tools/phrase_src/ -> docs/tools/phrase-bank-data.js (trang docs/tools/phrase-bank.html).

    python3 tools/phrase_bank_build.py        # cần node (đọc file dữ liệu JS)
"""
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools/phrase_src"
ORDER = ["ex", "pv800", "pb", "s500", "itp", "e650", "dl", "mv", "cae"]       # nguồn đứng trước giữ nghĩa/ví dụ khi trùng cụm
TYPES = {"idiom": "Thành ngữ (idiom)", "phrasal": "Phrasal verb", "collocation": "Collocation", "fixed": "Cụm cố định",
         "pattern": "Mẫu câu IELTS", "structure": "Cấu trúc nói", "topic": "Câu theo chủ đề", "daily": "Câu hàng ngày",
         "movie": "Cụm trong phim", "situation": "Câu theo tình huống", "it": "Tiếng Anh IT"}


def modules():
    for f in sorted(SRC.glob("*.py")):
        spec = importlib.util.spec_from_file_location(f.stem, f)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        yield m


def clean(s):
    s = unicodedata.normalize("NFC", str(s or ""))
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[*_`]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


PLACEHOLDER = re.compile(r"\b(sb|sth|somebody|someone|something|oneself|noun|verb|adj|adv|pron|v-?ing|ving)\b")


def key(p):
    """Khoá gộp trùng: bỏ chữ trong ngoặc, ký hiệu …/+/dấu câu, từ giữ chỗ (sb, sth, noun…), hoa/thường."""
    p = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", p.lower())
    p = PLACEHOLDER.sub(" ", p.replace("’", "'"))
    return re.sub(r"[^a-z0-9]", "", p.replace("'", ""))


def noise(p):
    """Càng ít ngoặc/ký hiệu/độ dài càng là dạng 'sạch' để hiển thị."""
    return sum(p.count(c) for c in "[](){}…+:") * 10 + len(p) / 100


def filler_example(p):
    """'As far as I know, [nobody else uses that endpoint].' -> câu hoàn chỉnh không còn ngoặc (làm ví dụ nếu cụm chưa có)."""
    return re.sub(r"\s+", " ", re.sub(r"[\[\]]", "", p)).strip() if re.search(r"\[[^\]]{6,}\]", p) else ""


def main():
    sources, recs = {}, []
    for m in modules():
        for attr, fn in (("SOURCE", "extract"), ("SOURCE_PV", "extract_pv")):
            if hasattr(m, attr) and hasattr(m, fn):
                S = getattr(m, attr); sources[S["code"]] = {"name": S["name"], "url": S["url"]}
                got = getattr(m, fn)(ROOT)
                for r in got:
                    r["s"] = S["code"]
                recs += got
                print(f'{S["code"]:6s} {len(got):6d}  {S["name"]}')
    recs.sort(key=lambda r: ORDER.index(r["s"]) if r["s"] in ORDER else 99)
    groups = {}
    for r in recs:
        p = clean(r.get("p"))
        if len(key(p)) < 2:
            continue
        r = {k: clean(r.get(k)) if k not in ("s",) else r["s"] for k in ("t", "p", "m", "d", "e", "ev", "g", "x", "ref", "s")} | {"p": p}
        groups.setdefault(key(p), []).append(r)
    merged = []
    for rs in groups.values():                      # rs đã theo thứ tự ưu tiên nguồn
        best = min(rs, key=lambda r: noise(r["p"]))   # dạng sạch nhất làm tiêu đề
        o = {"p": best["p"]}
        for f in ("m", "d", "e", "ev", "g", "x"):
            o[f] = next((r[f] for r in rs if r[f]), "")
        if not o["e"]:
            o["e"] = next((filler_example(r["p"]) for r in rs if filler_example(r["p"])), "")
        o["ts"] = list(dict.fromkeys(r["t"] for r in rs))
        o["ss"] = list(dict.fromkeys(r["s"] for r in rs))
        o["refs"] = {}
        for r in rs:
            o["refs"][r["s"]] = o["refs"].get(r["s"]) or r["ref"]
        merged.append(o)
    items = [[o["ts"], o["p"], o["m"], o["e"], o["ev"], o["g"], o["x"], o["d"], o["ss"], o["refs"]] for o in merged]
    total = len(recs)
    out = {"types": TYPES, "sources": sources, "items": items}
    dest = ROOT / "docs/tools/phrase-bank-data.js"
    dest.write_text("// Kho cụm từ & mẫu câu — sinh bởi tools/phrase_bank_build.py từ tools/phrase_src/*.py\n"
                    "window.PHRASES=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"gộp {total} bản ghi -> {len(items)} cụm (bỏ trùng {total - len(items)}) | {dest.stat().st_size // 1024} KB")


if __name__ == "__main__":
    sys.exit(main())
