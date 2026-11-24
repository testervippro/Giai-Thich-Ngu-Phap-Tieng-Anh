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


def key(p):
    return re.sub(r"[^a-z0-9]", "", p.lower())


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
    merged, byk = [], {}
    for r in recs:
        p = clean(r.get("p"))
        if len(key(p)) < 2:
            continue
        r = {k: clean(r.get(k)) if k not in ("s",) else r["s"] for k in ("t", "p", "m", "d", "e", "ev", "g", "x", "ref", "s")} | {"p": p}
        k = key(p)
        if k in byk:
            o = byk[k]
            for f in ("m", "d", "e", "ev", "g", "x"):
                if not o[f] and r[f]:
                    o[f] = r[f]
            if r["t"] not in o["ts"]:
                o["ts"].append(r["t"])
            if r["s"] not in o["ss"]:
                o["ss"].append(r["s"])
            o["refs"][r["s"]] = o["refs"].get(r["s"]) or r["ref"]
        else:
            o = dict(r, ts=[r["t"]], ss=[r["s"]], refs={r["s"]: r["ref"]})
            byk[k] = o; merged.append(o)
    items = [[o["ts"], o["p"], o["m"], o["e"], o["ev"], o["g"], o["x"], o["d"], o["ss"], o["refs"]] for o in merged]
    total = len(recs)
    out = {"types": TYPES, "sources": sources, "items": items}
    dest = ROOT / "docs/tools/phrase-bank-data.js"
    dest.write_text("// Kho cụm từ & mẫu câu — sinh bởi tools/phrase_bank_build.py từ tools/phrase_src/*.py\n"
                    "window.PHRASES=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"gộp {total} bản ghi -> {len(items)} cụm (bỏ trùng {total - len(items)}) | {dest.stat().st_size // 1024} KB")


if __name__ == "__main__":
    sys.exit(main())
