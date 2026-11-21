#!/usr/bin/env python3
"""Truyện dài Kanji -> lời đọc (12 chương lớn) để làm audiobook.

Bỏ chữ Hán/Kana trong 【】 và (…) để máy đọc trôi như kể chuyện.

    python3 tools/kanji_saga_audio.py                    # -> build/kanji-saga-audio-text/*.txt
    .venv/bin/python tools/audio/tts.py build/kanji-saga-audio-text -o build/kanji-saga-audio --rate +25%
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/kanji-viewer/truyen-data.js"
OUT = ROOT / "build/kanji-saga-audio-text"
CJK = "⺀-⿟々〆ぁ-ゟ゠-ヿㄅ-ㄯ㐀-鿿豈-﫿\U00020000-\U0003FFFF"


def clean(s: str) -> str:
    s = re.sub(rf"\s*【[^】]*】", "", s)
    s = re.sub(rf"\s*[(（][^)）]*[{CJK}][^)）]*[)）]", "", s)
    s = re.sub(r"\s*[(（]\S{1,3}[)）]", "", s)   # mảnh dạng ký hiệu: (E), (#), (ǂ)
    s = re.sub(rf"[{CJK}]", "", s)
    s = re.sub(r"^([^(]*)\)", r"\1", s)            # ")" lẻ còn sót sau khi bỏ "(…"
    s = re.sub(r"\s+([,.!?;:])", r"\1", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def main() -> None:
    txt = SRC.read_text(encoding="utf-8")
    i = re.search(r"window\.SAGA\s*=\s*", txt).end()
    saga = json.JSONDecoder().raw_decode(txt, i)[0]
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.txt"):
        old.unlink()
    for n, ch in enumerate(saga, 1):
        parts = [ch["t"].rstrip(".") + "."]
        for sec in ch["s"]:
            parts.append(sec["t"].rstrip(".") + ".")
            parts += [clean(p) for p in sec["p"]]
        (OUT / f"{n:02d}.txt").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"{len(saga)} chương -> {OUT}")


if __name__ == "__main__":
    main()
