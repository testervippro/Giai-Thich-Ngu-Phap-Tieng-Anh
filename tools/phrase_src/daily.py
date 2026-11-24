"""700+ câu nói ngắn hàng ngày -> records (t="daily")."""
import re

SOURCE = {"code": "dl", "name": "700+ câu nói ngắn hàng ngày", "url": "../daily-native-expressions.md"}
FILE = "docs/daily-native-expressions.md"


def clean(s):
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = s.replace("`", "")
    s = re.sub(r"\*+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def extract(root):
    out, seen, group = [], set(), None
    for raw in (root / FILE).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            h = re.sub(r"^\d+\.\s*", "", line[3:].strip())
            group = clean(h)
            continue
        if not line.startswith("|") or group is None:
            continue
        cs = [c.strip() for c in line.strip("|").split("|")]
        if len(cs) < 3 or not re.fullmatch(r"\d+", cs[0]):
            continue  # header / separator rows
        p, m = clean(cs[1]), clean(cs[2])
        if not p or not re.search(r"[A-Za-z]", p):
            continue
        key = (p, m)
        if key in seen:
            continue
        seen.add(key)
        out.append({"t": "daily", "p": p, "m": m, "e": "", "ev": "", "g": group, "x": "", "ref": ""})
    return out
