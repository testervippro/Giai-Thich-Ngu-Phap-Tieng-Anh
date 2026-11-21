#!/usr/bin/env python3
"""Kiểm tra truyện dài (tools/data/kanji_saga/NN.txt): mỗi chương phải có đủ 60 chữ của phần thẻ tương ứng, đánh dấu 【字】.
    .venv/bin/python tools/kanji_saga_check.py [NN ...]"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanji_video as KV  # noqa: E402

D = KV.ROOT / "tools/data/kanji_saga"
K = KV.js_value(KV.KV / "kanji-game-data.js", "KANJI")
N = 60
bad = 0
for f in sorted(D.glob("*.txt")):
    i = int(f.stem)
    if sys.argv[1:] and f.stem not in sys.argv[1:]:
        continue
    want = [r[1] for r in K[(i - 1) * N:i * N]]
    got = re.findall(r"【(.)】", f.read_text(encoding="utf-8"))
    miss = [c for c in want if c not in got]
    extra = [c for c in got if c not in want]
    dup = sorted({c for c in got if got.count(c) > 1})
    ok = not miss and not extra and not dup
    bad += not ok
    print(f"{f.stem}: {len(set(got))}/{len(want)}" + ("" if ok else f"  thiếu {''.join(miss)}  thừa {''.join(extra)}  lặp {''.join(dup)}"))
sys.exit(1 if bad else 0)
