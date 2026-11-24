#!/usr/bin/env python3
"""Chữ có trên site nhưng KHÔNG nằm trong danh sách Jōyō 2136.

    python3 tools/kanji_nonjoyo.py     # -> docs/kanji-viewer/kanji-nonjoyo.js  (window.KANJI_NONJOYO = [chữ...])

Nguồn Jōyō: https://en.wikipedia.org/wiki/List_of_j%C5%8Dy%C5%8D_kanji (cột "New", 2136 chữ) -> tools/data/joyo2136_wikipedia.json.
Wikipedia dùng vài dạng chữ khác bản chính thức (𠮟/叱, 剝/剥, 䇳/箋, 篭/籠, 頬/頰) — cùng một chữ nên coi là một (PAIRS).
Gồm: các thẻ trong kanji-game-data.js không thuộc Jōyō + 17 chữ ngoài 2136 (kanji-extra.js). Không tính mảnh ghép / bộ thủ.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KV = ROOT / "docs/kanji-viewer"


def js_value(name, var):
    s = (KV / name).read_text(encoding="utf-8")
    return json.JSONDecoder().raw_decode(s, re.search(rf"window\.{var}\s*=\s*", s).end())[0]


PAIRS = [("𠮟", "叱"), ("剝", "剥"), ("䇳", "箋"), ("篭", "籠"), ("頬", "頰")]
joyo = set(json.loads((ROOT / "tools/data/joyo2136_wikipedia.json").read_text(encoding="utf-8")))
joyo |= {x for pair in PAIRS for x in pair}
cards = [r[1] for r in js_value("kanji-game-data.js", "KANJI")]
extra = [r[0] for r in js_value("kanji-extra.js", "KANJI_EXTRA")]
out = [k for k in dict.fromkeys(cards + extra) if k not in joyo]
(KV / "kanji-nonjoyo.js").write_text(
    "// Chữ không thuộc Jōyō 2136 (Kanshudo) — sinh bởi tools/kanji_nonjoyo.py\n"
    "window.KANJI_NONJOYO = " + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")
print(f"{len(out)} chữ không thuộc Jōyō ({len([k for k in out if k in cards])} thẻ + {len([k for k in out if k in extra])} ngoài 2136):", "".join(out))
