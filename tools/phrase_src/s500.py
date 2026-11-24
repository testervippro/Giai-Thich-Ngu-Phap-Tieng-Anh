"""Extractor: 500 Spoken English Structures + IELTS Speaking patterns + Part 3."""
import re

SOURCE = {"code": "s500", "name": "500 Spoken English Structures (+ IELTS Speaking patterns)",
          "url": "../500_spoken_english_structures.md"}


def _clean(s):
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = s.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def _rec(t, p, e, g):
    return {"t": t, "p": p, "m": "", "e": e, "ev": "", "g": g, "x": "", "ref": ""}


def extract(root):
    lines = (root / "docs" / "500_spoken_english_structures.md").read_text(encoding="utf-8").splitlines()
    out, seen = [], set()
    part = 0
    group = ""
    cur = None  # current Part 2 pattern: [title, [examples]]

    def add(r):
        k = (r["t"], r["p"], r["e"])
        if r["p"] and k not in seen:
            seen.add(k)
            out.append(r)

    def flush():
        nonlocal cur
        if cur:
            add(_rec("pattern", cur[0], " | ".join(cur[1]), "IELTS Speaking patterns"))
        cur = None

    for ln in lines:
        s = ln.strip()
        m = re.match(r"^## Part (\d)", s)
        if m:
            flush()
            part = int(m.group(1))
            group = ""
            continue
        if s.startswith("### "):
            flush()
            h = _clean(s[4:])
            if part == 2:
                cur = [re.sub(r"^\d+\.\s*", "", h), []]
            else:
                group = h
            continue
        if part == 2 and cur is not None and re.match(r"^[-*]\s+", s):
            ex = _clean(re.sub(r"^[-*]\s+", "", s))
            if ex:
                cur[1].append(ex)
            continue
        if part in (1, 3) and s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 3 or not re.fullmatch(r"\d+", cells[0]):
                continue
            g = "500 Spoken Structures" if part == 1 else (group or "More Structures")
            add(_rec("structure", _clean(cells[1]), _clean(cells[2]), g))
    flush()
    return out
