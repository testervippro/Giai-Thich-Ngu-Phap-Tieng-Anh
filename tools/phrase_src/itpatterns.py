"""Extractor: IT English Patterns - Speaking & Writing."""
import re

SOURCE = {"code": "itp", "name": "IT English Patterns — Speaking & Writing",
          "url": "../IT%20English%20Patterns.md"}

_MARKS = {"🟢": "thân mật", "🟣": "trang trọng"}


def _clean(s):
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"[\1]", s)
    s = s.replace("**", "").replace("`", "")
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?!\w)", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def _split_marks(s):
    reg = [v for k, v in _MARKS.items() if k in s]
    star = "⭐" in s
    for k in list(_MARKS) + ["⭐"]:
        s = s.replace(k, "")
    return s.strip(), reg, star


def extract(root):
    lines = (root / "docs" / "IT English Patterns.md").read_text(encoding="utf-8").splitlines()
    out, seen = [], set()
    group = ""
    mode = None  # "pat" or "err"
    for ln in lines:
        s = ln.strip()
        if s.startswith("## "):
            group = re.sub(r"^\d+\.\s*", "", _clean(s[3:]))
            mode = None
            continue
        if s.startswith("# PHẦN 3"):
            group = "Lỗi thường gặp của người Việt trong môi trường IT"
            mode = None
            continue
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells and cells[0] == "#":
            mode = "err" if len(cells) >= 4 else "pat"
            continue
        if not re.fullmatch(r"\d+", cells[0] if cells else ""):
            continue
        if mode == "pat" and len(cells) >= 3:
            p, reg1, star1 = _split_marks(cells[1])
            note, reg2, star2 = _split_marks(cells[2])
            reg = reg1 or reg2
            x = _clean(note)
            if reg:
                x = (x + " · " if x else "") + reg[0]
            if star1 or star2:
                x = (x + " · " if x else "") + "nên học trước"
            p = _clean(p)
            rec = {"t": "it", "p": p, "m": "", "e": "", "ev": "", "g": group,
                   "x": x[:120], "ref": ""}
            # note column is a Vietnamese explanation of the pattern
            rec["m"] = _clean(note)
            rec["x"] = ("; ".join(reg) + ("; nên học trước" if (star1 or star2) else "")).strip("; ")[:120]
        elif mode == "err" and len(cells) >= 4:
            bad, good, note = _clean(cells[1]), _clean(cells[2]), _clean(cells[3])
            p = good
            x = ("Tránh: " + bad)[:120]
            rec = {"t": "it", "p": p, "m": note, "e": "", "ev": "", "g": group, "x": x, "ref": ""}
        else:
            continue
        if rec["p"] and (rec["g"], rec["p"]) not in seen:
            seen.add((rec["g"], rec["p"]))
            out.append(rec)
    return out
