#!/usr/bin/env python3
"""Bản tiếng Anh cho trang Luyện viết Kanji: nghĩa + câu chuyện của mọi thẻ và mảnh ghép (base kanji).

    python3 tools/kanji_en_build.py      # -> docs/kanji-viewer/kanji-en.js  (window.KANJI_EN = {chữ: [nghĩa EN, câu chuyện EN]})

Nguồn:
  - câu chuyện: tools/data/kanji_stories_en.tsv (câu Việt đã bỏ ngoặc \\t câu Anh; chung với app Remind Voca)
  - nghĩa thẻ: KANJIDIC (build/dl-kanjidata/kanji.json), 3 nghĩa đầu
  - mảnh ghép KANJIDIC chỉ ghi "Radical no. x": dịch tay ở RAD_EN
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KV = ROOT / "docs/kanji-viewer"

RAD_EN = {
    "丿": "slash stroke", "亻": "person (side form of 人)", "氺": "water (form of 水)", "⺗": "heart (form of 心)",
    "⺍": "small (form of 小)", "⺌": "small (form of 小)", "亠": "lid", "儿": "human legs", "⻌": "walk (form of 辵)",
    "冂": "border, frontier", "𠂊": "wrap (form of 勹)", "冖": "cover, roof", "禾": "rice plant, grain",
    "⻖": "mound (form of 阜)", "⺕": "pig's head (form of 彐)", "彑": "pig's head (form of 彐)", "广": "slanted roof, eaves",
    "冫": "ice", "⺤": "claw (form of 爪)", "卩": "seal, bamboo joint", "㔾": "seal, bamboo joint (form of 卩)",
    "⺨": "dog (form of 犬)", "罒": "net (form of 网)", "耂": "old (form of 老)", "マ": "the shape マ",
    "⻏": "town (form of 邑)", "匚": "box", "巛": "river", "幺": "short thread, small", "廴": "long stride",
    "爿": "split wood", "⺦": "split wood (form of 爿)", "韋": "tanned leather", "匸": "hiding enclosure",
    "癶": "spread legs", "舛": "opposite, contrary", "𦥑": "mortar (form of 臼)", "尢": "lame, weak",
}


def js_value(path: Path, name: str):
    s = path.read_text(encoding="utf-8")
    return json.JSONDecoder().raw_decode(s, re.search(rf"window\.{name}\s*=\s*", s).end())[0]


def strip(s: str) -> str:
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", s)


def main() -> None:
    en_story = {}
    for line in (ROOT / "tools/data/kanji_stories_en.tsv").read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            vi, en = line.split("\t", 1)
            en_story[vi.strip()] = en.strip()
    dic = json.loads((ROOT / "build/dl-kanjidata/kanji.json").read_text(encoding="utf-8"))

    def meaning(k: str) -> str:
        ms = [m for m in (dic.get(k) or {}).get("meanings", []) if not re.search(r"radical|katakana|no\.", m, re.I)]
        return ", ".join(ms[:3]).lower()

    out, miss_s = {}, 0
    rows = [(r[1], r[5]) for r in js_value(KV / "kanji-game-data.js", "KANJI")]
    rows += [(r[0], r[3]) for r in js_value(KV / "kanji-extra.js", "KANJI_EXTRA")]
    for k, s in rows:
        st = en_story.get(strip(s), "") if s else ""
        miss_s += bool(s and not st)
        prev = out.get(k)
        if prev and prev[1]:
            continue
        out[k] = [meaning(k) or RAD_EN.get(k, ""), st]
    for k, _hv, _m, _t in js_value(KV / "kanji-roadmap.js", "ROADMAP")["radw"]:
        if k not in out:
            out[k] = [RAD_EN.get(k) or meaning(k), ""]
    dest = KV / "kanji-en.js"
    dest.write_text("// tạo bởi tools/kanji_en_build.py — nghĩa + câu chuyện tiếng Anh: {chữ: [nghĩa, câu chuyện]}\n"
                    "window.KANJI_EN=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n",
                    encoding="utf-8")
    print(f"{dest.relative_to(ROOT)}: {len(out)} chữ, thiếu câu chuyện EN: {miss_s}, "
          f"thiếu nghĩa EN: {sum(1 for v in out.values() if not v[0])}, {dest.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
