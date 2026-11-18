#!/usr/bin/env python3
"""Lời đọc tiếng Việt cho thẻ Kanji Tập 1 (thẻ 1–1050) và Tập 2 (1051–…), để đọc thành MP3.

Mỗi thẻ: số thẻ → âm Hán Việt → nghĩa → câu chuyện → câu chuyện con của từng mảnh
mà câu chuyện nhắc tới (giống phần dưới thẻ ở trang Luyện viết). Chữ Hán trong ngoặc
được đổi sang âm Hán Việt để máy đọc được, vd "Cây (木)" → "Cây (Mộc)".

    python3 tools/kanji_audio_text.py                      # -> build/kanji-audio-text/*.txt
    .venv/bin/python tools/audio/tts.py build/kanji-audio-text -o build/kanji-audio -j 6
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KV = ROOT / "docs/kanji-viewer"
OUT = ROOT / "build/kanji-audio-text"
CJK = re.compile(r"[⺀-⿟々゠-ヿ㐀-鿿豈-﫿]")


def js_value(path: Path, name: str):
    s = path.read_text(encoding="utf-8")
    i = s.index(f"window.{name}=") + len(f"window.{name}=")
    return json.JSONDecoder().raw_decode(s, i)[0]


def title(hv: str) -> str:
    """'LẠC, NHẠC' -> 'Lạc, Nhạc' (chữ in hoa toàn bộ dễ bị máy đánh vần)."""
    return ", ".join(w.strip().capitalize() for w in hv.split(",") if w.strip())


def main() -> None:
    kanji = js_value(KV / "kanji-game-data.js", "KANJI")
    radw = js_value(KV / "kanji-roadmap.js", "ROADMAP")["radw"]
    story_of, hv_of, m_of = {}, {}, {}
    for n, k, hv, m, j, s, img in kanji:
        if s and k not in story_of:
            story_of[k] = s
        hv_of.setdefault(k, hv)
        m_of.setdefault(k, m)
    for k, hv, m, _tier in radw:
        hv_of.setdefault(k, hv)
        m_of.setdefault(k, m)

    def speakable(text: str) -> str:
        def rep(mo):
            c = mo.group(0)
            return title(hv_of[c]) if hv_of.get(c) else ""
        t = CJK.sub(rep, text)
        t = re.sub(r"\(\s*\)", "", t)              # ngoặc chỉ còn rỗng (mảnh không có âm)
        # "Yêu (Yêu)": chữ đứng trước đã trùng âm Hán Việt -> bỏ phần ngoặc cho đỡ lặp
        t = re.sub(r"(\w+)\s*\((\w+)\)", lambda mo: mo.group(1) if mo.group(1).lower() == mo.group(2).lower() else mo.group(0), t)
        t = re.sub(r"\s+([,.;:!?])", r"\1", t)
        return re.sub(r"\s{2,}", " ", t).strip()

    def end(t: str) -> str:
        t = t.strip()
        return t if not t or t[-1] in ".!?…" else t + "."

    OUT.mkdir(parents=True, exist_ok=True)
    parts = {"kanji-tap1": [r for r in kanji if r[0] <= 1050],
             "kanji-tap2": [r for r in kanji if r[0] > 1050]}
    for name, rows in parts.items():
        lines = []
        for n, k, hv, m, j, s, img in rows:
            bits = [f"Thẻ {n}. {title(hv)}. Nghĩa: {end(speakable(m))}"]
            if s:
                bits.append("Câu chuyện: " + end(speakable(s)))
                subs, seen = [], {k}
                for c in CJK.findall(s):
                    if c in seen:
                        continue
                    seen.add(c)
                    if c in story_of:
                        subs.append(f"{title(hv_of[c])}, {speakable(m_of[c]).lower()}: " + end(speakable(story_of[c])))
                    elif hv_of.get(c):
                        subs.append(f"{title(hv_of[c])}, {speakable(m_of[c]).lower()}, là mảnh ghép.")
                if subs:
                    bits.append("Câu chuyện con. " + " ".join(subs))
            lines.append(" ".join(bits))
        txt = OUT / f"{name}.txt"
        txt.write_text("\n\n".join(lines) + "\n", encoding="utf-8")
        print(f"{txt.relative_to(ROOT)}: {len(rows)} thẻ, {sum(map(len, lines)):,} ký tự")


if __name__ == "__main__":
    main()
