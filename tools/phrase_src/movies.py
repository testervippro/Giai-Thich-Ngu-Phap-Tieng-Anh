"""Cụm giao tiếp trong phim: docs/movie-viewer/cum-giao-tiep.html (JS: const D = {...})."""
import html
import json
import re

SOURCE = {"code": "mv", "name": "Cụm giao tiếp trong phim", "url": "../movie-viewer/cum-giao-tiep.html"}

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _c(s):
    if s is None:
        return ""
    return _WS.sub(" ", html.unescape(_TAG.sub("", str(s)))).strip()


def _short(name):
    name = _c(name)
    name = re.sub(r"\s+(19|20)\d\d$", "", name)
    name = re.sub(r"^The ", "", name)
    return name if len(name) <= 24 else name[:22].rstrip() + "…"


def extract(root):
    text = (root / "docs/movie-viewer/cum-giao-tiep.html").read_text(encoding="utf-8")
    m = re.search(r"const D = (\{.*\});\s*\n", text)
    if not m:
        raise RuntimeError("movie data object not found")
    D = json.loads(m.group(1))
    names = [_short(s["name"]) for s in D["shows"]]
    groups = D.get("groups", {})
    out, seen = [], set()
    for r in D.get("all") or D.get("daily") or []:
        p = _c(r[1])
        if not p or p in seen:
            continue
        seen.add(p)
        secs = [_c(s) for s in (r[3] or []) if _c(s)]
        secs = [groups.get(s, s) for s in secs]
        per = r[5] or []
        x = " · ".join("%s %d" % (names[i], n) for i, n in per[:4] if i < len(names))
        if not x and not r[4]:
            x = "chưa gặp trong phụ đề"
        x = x[:120]
        e = _c(r[6])
        out.append({"t": "movie", "p": p, "m": _c(r[2]), "e": e, "ev": "",
                    "g": " · ".join(secs), "x": x, "ref": p})
    return out
