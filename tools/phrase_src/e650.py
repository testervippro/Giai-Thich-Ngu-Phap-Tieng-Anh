"""650+ English Phrases for Everyday Speaking -> records (t="topic")."""
import re

SOURCE = {"code": "e650", "name": "650+ English Phrases for Everyday Speaking",
          "url": "../650-english-phrases-everyday-speaking.md"}
FILE = "docs/650-english-phrases-everyday-speaking.md"


def clean(s):
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = s.replace("`", "")
    s = re.sub(r"\*+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def has_alpha(s):
    return bool(re.search(r"[A-Za-z]", s))


def extract(root):
    lines = (root / FILE).read_text(encoding="utf-8").splitlines()
    out, seen = [], set()
    group, header = None, None
    in_toc = False

    def add(p, m="", e="", ev="", x=""):
        p = clean(p)
        if not p or not has_alpha(p) or group is None:
            return
        key = (p, clean(m), clean(e), group)
        if key in seen:
            return
        seen.add(key)
        out.append({"t": "topic", "p": p, "m": clean(m), "e": clean(e), "ev": clean(ev),
                    "g": group, "x": clean(x)[:120], "ref": ""})

    for i, raw in enumerate(lines):
        line = raw.rstrip()
        if line.startswith("## "):
            h = line[3:].strip()
            m = re.match(r"^\d+[a-z]?\.\s*(.+)$", h)
            group = clean(m.group(1)) if m else None
            header = None
            continue
        if group is None:
            continue
        if line.startswith("|"):
            cs = cells(line)
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cs if c) :
                continue
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if nxt.startswith("|") and re.fullmatch(r"[|\s:\-]+", nxt):
                header = [clean(c).lower() for c in cs]
                continue
            if len(cs) < 2 or header is None:
                continue
            p = cs[0]
            rest = cs[1:]
            if not has_alpha(clean(p)) and has_alpha(clean(rest[0])):
                # numeric/time tables: "2:00 | It's two o'clock." -> phrase is the spoken form
                add(rest[0], clean(p), "", "", rest[1] if len(rest) > 1 else "")
                continue
            m = rest[0]
            e = x = ""
            h1 = header[1] if len(header) > 1 else ""
            if h1.startswith("dùng khi") and len(rest) > 1:
                x, m = rest[0], rest[1]
            elif len(rest) > 1:
                h2 = header[2] if len(header) > 2 else ""
                if h2.startswith("ví dụ"):
                    e = rest[1]
                else:
                    x = rest[1]
            add(p, m, e, "", x)
            continue
        # example bullets: - *English* — Vietnamese
        mb = re.match(r"^- \*([^*]+)\*\s*[—–-]\s*(.+)$", line)
        md = re.match(r"^- \*([^*]+)\*\s*→\s*\*([^*]+)\*(?:\s*[—–-]\s*(.+))?\s*$", line)
        if md:
            add(md.group(1).strip() + " → " + md.group(2).strip(), md.group(3) or "", x="Hội thoại mẫu")
            continue
        if mb:
            add(mb.group(1), mb.group(2), x="Câu ví dụ")
            continue
        # inline examples: *Eng* (Viet) · *Eng* (Viet)
        if re.match(r"^\*?Ví dụ:?\*?\s*\*", line) or re.match(r"^\*Ví dụ:\*", line):
            body = re.sub(r"^\*?Ví dụ:\*?\s*", "", line)
            for part in body.split("·"):
                mi = re.match(r"^\s*\*([^*]+)\*\s*(?:\(([^)]*)\))?", part)
                if mi:
                    add(mi.group(1), mi.group(2) or "", x="Câu ví dụ")
    return out
