#!/usr/bin/env python3
"""Từ vựng tiếng Anh trong câu chuyện Kanji bản tiếng Anh (kanji-en.js), để học câu chuyện bằng tiếng Anh.

    .venv/bin/python tools/kanji_en_vocab.py    # -> docs/kanji-viewer/kanji-en-vocab.js

window.KANJI_VOCAB = {w: [[từ gốc, nghĩa Việt, số câu chuyện, "các chữ Kanji"], ...],   # nhiều câu chuyện dùng nhất trước
                      k: {chữ: [chỉ số từ trong w, ...]}}                               # từ của từng câu chuyện, theo thứ tự xuất hiện
Nghĩa: tools/data/kanji_story_vocab_vi.tsv (soạn cho bộ này) > tools/data/en_vi_movie_words.tsv.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import movie_phrases as MP  # noqa: E402

STOP = set("""a an the and or but if of to in on at by for with from into onto as is are was were be been being am
it its this that these those he she him her his hers they them their theirs we us our you your i me my mine who whom
whose which what when where why how not no so too very then than there here do does did done have has had will would
can could should may might must shall up down out off over under again also just only all any some each every both
either neither one two""".split())


def main() -> None:
    # Chỉ lấy nghĩa tự soạn (en_vi_movie_words.tsv); DK / TOEIC cho nghĩa theo chủ đề hẹp
    # (stand = giá đỡ, lead = chì…) nên sai ngữ cảnh câu chuyện — không dùng.
    vi = {}
    for line in (ROOT / "tools/data/en_vi_movie_words.tsv").read_text(encoding="utf-8").splitlines():
        if not line.startswith("#") and "\t" in line:
            w, m = line.split("\t", 1)
            if m != "=tên":
                vi.setdefault(w, m)
    full_vi, _names = MP.load_vi()          # chỉ để lemma() nhận ra từ gốc
    mine, drop = {}, set()
    for line in (ROOT / "tools/data/kanji_story_vocab_vi.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        w, m = line.split("\t", 1)
        (drop.add(w) if m == "=bỏ" else mine.__setitem__(w, m))
    s = (ROOT / "docs/kanji-viewer/kanji-en.js").read_text(encoding="utf-8")
    EN = json.loads(s[s.index("=") + 1:s.rindex(";")])

    # tên riêng: từ chỉ xuất hiện viết hoa giữa câu (Nguyet, Hanoi…)
    cap, low = defaultdict(int), defaultdict(int)
    for _m, st in EN.values():
        for i, w in enumerate(re.findall(r"[A-Za-z]+(?:'[a-z]+)?", st or "")):
            (cap if (w[0].isupper() and i > 0) else low)[w.lower()] += 1
    names = {w for w in cap if not low[w]}

    words, per_k, missing = {}, {}, set()
    for k, (_m, st) in EN.items():
        if not st:
            continue
        seq = []
        for w in re.findall(r"[A-Za-z]+(?:'[a-z]+)?", st):
            w = w.lower().split("'")[0]
            if w in STOP or len(w) < 3 or w in names:
                continue
            lem = MP.lemma(w, full_vi)
            if lem in drop or lem in names or lem in seq:
                continue
            mean = mine.get(lem) or vi.get(lem) or mine.get(w) or vi.get(w)
            if not mean:
                missing.add(lem)
                continue
            seq.append(lem)
            e = words.setdefault(lem, [lem, mean, 0, []])
            e[2] += 1
            e[3].append(k)
        per_k[k] = seq
    W = sorted(words.values(), key=lambda e: (-e[2], e[0]))
    ix = {e[0]: i for i, e in enumerate(W)}
    out = {"w": [[e[0], e[1], e[2], "".join(e[3])] for e in W],
           "k": {k: [ix[w] for w in seq] for k, seq in per_k.items() if seq}}
    dest = ROOT / "docs/kanji-viewer/kanji-en-vocab.js"
    dest.write_text("// tạo bởi tools/kanji_en_vocab.py — từ vựng tiếng Anh trong câu chuyện Kanji\n"
                    "window.KANJI_VOCAB=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n",
                    encoding="utf-8")
    print(f"{dest.relative_to(ROOT)}: {len(W)} từ, {len(out['k'])} câu chuyện, {dest.stat().st_size // 1024} KB")
    if missing:
        print(f"chưa có nghĩa ({len(missing)}):", " ".join(sorted(missing)))
    print("nhiều nhất:", ", ".join(f"{e[0]} ({e[2]})" for e in W[:15]))


if __name__ == "__main__":
    main()
