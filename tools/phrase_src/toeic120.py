"""120 Thành ngữ & Cụm từ cố định TOEIC (Hackers TOEIC Vocabulary) -> records.

Câu ví dụ: câu trích đề ETS 2026 đã dò sẵn trong tools/colloc_hub_build.py (docs/tools/colloc/index.js, chủ đề 📕 120…).
Loại: động từ + tiểu từ (back out, build up…) = phrasal; còn lại = idiom.
"""
import json
import re

SOURCE = {"code": "t120", "name": "120 Thành ngữ & cụm cố định TOEIC (Hackers)", "url": "../#/120-thanh-ngu-cum-tu-toeic"}
FILE = "docs/120-thanh-ngu-cum-tu-toeic.md"
PART = r"(up|out|off|in|on|over|down|away|back|around|along|into|for|with|ahead|behind|under|within|through|against|to)"


def ets_examples(root):
    p = root / "docs/tools/colloc/index.js"
    if not p.exists():
        return {}
    s = p.read_text(encoding="utf-8")
    d = json.loads(s[s.index("{"):s.rindex("}") + 1])
    t = next((i for i, x in enumerate(d["topics"]) if x.startswith("📕 120")), None)
    return {r[0]: r[5] for r in d["c45"] if r[2] == t and r[5]}


def extract(root):
    ex = ets_examples(root)
    out = []
    for l in (root / FILE).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (\d+) \| (.+?) \| (.+?) \|\s*$", l)
        if not m:
            continue
        n, p, vi = m.group(1), m.group(2).strip(), m.group(3).strip()
        t = "phrasal" if re.fullmatch(r"[a-z]+(\s+A)?\s+" + PART + r"(\s+" + PART + r")?", p) else "idiom"
        e, x = "", ""
        if p in ex:
            mm = re.match(r"^(\S+)\s+\*\(Test (\d+)\)\*\s*(.+)$", ex[p])
            if mm:
                e = mm.group(3)
                x = f"{'🎧 Listening' if mm.group(1) == '🎧' else '📖 Reading'} — đề ETS 2026 Test {mm.group(2)}"
        out.append({"t": t, "p": p, "m": vi, "e": e, "ev": "", "g": "TOEIC (Hackers)", "x": x, "ref": ""})
    return out
