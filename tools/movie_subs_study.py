#!/usr/bin/env python3
"""Học tiếng Anh (TOEIC) qua phụ đề phim — từ thư mục phụ đề bạn đã tải về máy.

Đầu vào : ~/remind voca/movies/*.zip (+ .srt/.vtt lẻ). Phụ đề gốc CHỈ dùng trên máy.
Trên máy : movies/_study/  — bản phụ đề đã định dạng để học (mỗi tập 1 trang HTML: lời thoại sạch,
           mốc thời gian, từ TOEIC tô màu + nghĩa). KHÔNG đưa lên git (lời thoại có bản quyền).
Lên web  : không (trang cụm giao tiếp do tools/movie_phrases.py tạo).

    python3 tools/movie_subs_study.py
"""
import html
import io
import json
import os
import re
import sys
import zipfile
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toeic_songs_lrclib as L  # noqa: E402
import toeic_songs_corpus as C  # noqa: E402

SRC = os.path.expanduser("~/remind voca/movies")
STUDY = os.path.join(SRC, "_study")
WEB = os.path.join(L.DOCS, "movie-viewer")
SHOW_NAMES = {"friends": "Friends", "the office": "The Office", "silicon valley": "Silicon Valley",
              "suits la": "Suits LA", "suits": "Suits"}

TIME = re.compile(r"(\d+):(\d\d):(\d\d)[,.](\d+)\s*-->")
TAG = re.compile(r"<[^>]+>|\{[^}]*\}")
HI = re.compile(r"\[[^\]]*\]|\([A-Z][A-Z ,'\-]+\)|♪[^♪]*♪?|^[A-Z][A-Z .'\-]{1,20}:\s*")  # chú thích cho người khiếm thính, tên người nói


def decode(b):
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", "replace")


def parse_subs(text):
    """-> [(giây, dòng thoại)] — gộp các dòng của một khung, bỏ thẻ/ chú thích/ quảng cáo."""
    out = []
    for block in re.split(r"\r?\n\s*\r?\n", text.replace("\r", "")):
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        t = None
        body = []
        for l in lines:
            m = TIME.search(l)
            if m:
                h, mi, s, _ = m.groups()
                t = int(h) * 3600 + int(mi) * 60 + int(s)
                continue
            if t is None or l.isdigit() or l.startswith(("WEBVTT", "NOTE", "Kind:", "Language:")):
                continue
            l = HI.sub("", TAG.sub("", html.unescape(l))).replace(">>", "").replace("\u2019", "'").replace("\u2018", "'").strip()
            if l and not re.search(r"(opensubtitles|subtitles? by|synced|corrected by|addic7ed|www\.|\.com|\.org)", l, re.I):
                body.append(l)
        if t is not None and body:
            for part in re.split(r"(?:^|\s)-\s+", " ".join(body)):  # "- Hey. - Hi." -> 2 lượt thoại
                part = part.strip(" -")
                if re.search(r"[A-Za-z]", part) and not (out and out[-1][1] == part):  # bỏ dòng lặp (phụ đề tự động YouTube)
                    out.append((t, part))
    return out


def ep_key(name):
    """'The Office - 6x01 - Gossip.HDTV.en.srt' -> ('The Office', 6, 1, 'Gossip')"""
    base = os.path.basename(name)
    m = re.match(r"(.+?)\s*-\s*(\d+)x(\d+)\s*-\s*(.+?)(?:\.(?:720p|1080p|HDTV|BluRay|WEB|DVD|en|PSYCHD|[A-Za-z0-9]+)\b.*)?\.(?:en\.)?(?:srt|sub|vtt)$", base, re.I)
    if not m:
        return None
    show = SHOW_NAMES.get(m.group(1).strip().lower().replace("_", " "), m.group(1).strip().replace("_", " "))
    title = re.sub(r"\s*\(\d\)$", "", m.group(4).split(".")[0]).strip()
    return show, int(m.group(2)), int(m.group(3)), title


def load_episodes():
    """Đọc mọi phụ đề, mỗi tập giữ 1 bản (bản có nhiều lượt thoại nhất)."""
    eps = {}
    files = []
    for f in sorted(os.listdir(SRC)):
        p = os.path.join(SRC, f)
        if f.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if n.lower().endswith((".srt", ".vtt")):
                        files.append((n, z.read(n)))
        elif f.lower().endswith((".srt", ".vtt")):
            files.append((f, open(p, "rb").read()))
    for name, raw in files:
        k = ep_key(name)
        lines = parse_subs(decode(raw))
        if len(lines) < 30:
            continue
        if k is None:  # phim lẻ / video
            title = re.sub(r"[._]+", " ", re.sub(r"\.(srt|vtt)$", "", os.path.basename(name)))
            title = re.sub(r"\s+(BluRay|1080p|720p|x264|DTS|track\d+|\[eng\]|eng|en)\b.*", "", title, flags=re.I).strip()
            title = re.sub(r"^\[English \(auto-generated\)\]\s*", "", title)
            k = ("Phim lẻ & video", 0, len([e for e in eps if e[0] == "Phim lẻ & video"]) + 1, title[:80])
        key = k[:3]
        if key not in eps or len(lines) > len(eps[key]["lines"]):
            eps[key] = dict(show=k[0], s=k[1], e=k[2], title=k[3], lines=lines)
    return [eps[k] for k in sorted(eps)]


def code(ep):
    return "S%02dE%02d" % (ep["s"], ep["e"]) if ep["s"] else "#%d" % ep["e"]


def main():
    ets, idx = L.load_ets(), L.load_index()
    for r in ets + idx:
        r["q"] = L.query_of(r["term"])
    rows, _ = L.merged_rows(ets, idx)
    eps = load_episodes()
    print("so tap:", len(eps), {s: sum(1 for e in eps if e["show"] == s) for s in sorted({e["show"] for e in eps})}, flush=True)

    # ---- từ TOEIC trong từng tập ----
    TOK = re.compile(r"[a-z][a-z']*")
    toks = [set(TOK.findall(" ".join(t for _, t in e["lines"]).lower())) for e in eps]
    hits = defaultdict(dict)  # ri -> {ep_i: (giây, dòng, dạng)}
    for ri, r in enumerate(rows):
        q = r["q"]
        if len(q) < 2:
            continue
        ws = q.split()
        exact = re.compile(r"(?<![A-Za-z'])%s(?![A-Za-z'])" % re.escape(q).replace(r"\ ", r"\s+"), re.I)
        rx = C.form_rx(q)
        for ei, e in enumerate(eps):
            if not all(any(f in toks[ei] for f in (C.variants(w) if len(w) >= 4 else {w})) for w in ws if re.fullmatch(r"[a-z']+", w)):
                continue
            best = None
            for t, line in e["lines"]:
                m = exact.search(line) or rx.search(line)
                if m and (best is None or abs(len(line) - 60) < abs(len(best[1]) - 60)):
                    best = (t, line, m.group(0))
            if best:
                hits[ri][ei] = best
    found = [ri for ri in range(len(rows)) if hits[ri]]
    print("tu TOEIC gap trong phim: %d/%d" % (len(found), len(rows)), flush=True)

    write_study(rows, eps, hits)


import movie_phrases as P  # noqa: E402
PH_MEAN = {p: m for p, (m, _) in P.load_gloss().items()}
PH = sorted(((p, P.phrase_rx(p)) for p in PH_MEAN), key=lambda x: -len(x[0]))  # cụm dài trước


def render_line(line, rx_terms, phrases, seen):
    """HTML 1 dòng thoại: cụm giao tiếp gạch chân xanh (cụm dài thắng, không chồng nhau),
    từ TOEIC tô vàng (mỗi từ 1 lần/dòng, không cắt ngang cụm)."""
    ph = []
    for p, rx in phrases:
        for m in rx.finditer(line):
            if all(m.end() <= a or m.start() >= b for a, b, _ in ph):
                ph.append((m.start(), m.end(), p))
                seen.add(p)
    tk = []
    for term, mean, rx in rx_terms:
        m = rx.search(line)
        if m and all(m.end() <= a or m.start() >= b for a, b, _ in tk) \
                and all(m.end() <= a or m.start() >= b or (a <= m.start() and m.end() <= b) for a, b, _ in ph):
            tk.append((m.start(), m.end(), "%s — %s" % (term, mean or "")))
    ev = sorted([(a, 0, '<u class="p" title="%s">' % html.escape("%s — %s" % (P.display(p), PH_MEAN[p]))) for a, b, p in ph]
                + [(b, -1, "</u>") for a, b, p in ph]
                + [(a, 1, '<mark title="%s">' % html.escape(t)) for a, b, t in tk] + [(b, -2, "</mark>") for a, b, t in tk])
    out, pos = [], 0
    for i, _, tag in ev:
        out.append(html.escape(line[pos:i]))
        out.append(tag)
        pos = i
    out.append(html.escape(line[pos:]))
    return "".join(out)


def write_study(rows, eps, hits):
    """Bản phụ đề định dạng để học — CHỈ trên máy (movies/_study)."""
    os.makedirs(STUDY, exist_ok=True)
    by_ep = defaultdict(list)
    for ri, hs in hits.items():
        for ei in hs:
            by_ep[ei].append(ri)
    css = ("body{font:16px/1.6 system-ui,sans-serif;max-width:860px;margin:auto;padding:16px;background:#fafaf7;color:#1d1d1f}"
           "@media(prefers-color-scheme:dark){body{background:#17171a;color:#eee}.t{color:#888}mark{background:#5b4a00;color:#fff}}"
           ".l{display:flex;gap:12px;padding:3px 0;border-bottom:1px solid #8882}.t{color:#999;font:12px monospace;min-width:52px;padding-top:4px}"
           "mark{background:#fff2a8;border-radius:3px;padding:0 2px;cursor:help}"
           "u.p{text-decoration:none;border-bottom:2px solid #2f7de1;cursor:help}@media(prefers-color-scheme:dark){u.p{border-color:#6aa8ff}}a{color:#0a66c2}h1{font-size:22px}.w{font-size:13.5px;color:#666}")
    index = defaultdict(list)
    for ei, e in enumerate(eps):
        rx_terms = [(rows[ri]["term"], rows[ri]["mean"], C.form_rx(rows[ri]["q"])) for ri in by_ep[ei] if len(rows[ri]["q"]) >= 4]
        body, ep_ph = [], set()
        for t, line in e["lines"]:
            h = render_line(line, rx_terms, PH, ep_ph)
            body.append('<div class="l"><span class="t">%d:%02d:%02d</span><span>%s</span></div>' % (t // 3600, t // 60 % 60, t % 60, h))
        fn = re.sub(r"[^\w\-]+", "_", "%s_%s" % (e["show"], code(e))) + ".html"
        wl = sorted({rows[ri]["term"] for ri in by_ep[ei]}, key=str.lower)
        page = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
                "<title>%s %s</title><style>%s</style><p><a href='index.html'>← Danh sách tập</a></p><h1>%s · %s — %s</h1>"
                "<p class=w><b>%d từ TOEIC</b> trong tập (tô vàng, rê chuột xem nghĩa): %s</p>"
                "<p class=w><b>%d cụm giao tiếp</b> (gạch chân xanh): %s</p>%s"
                % (e["show"], code(e), css, html.escape(e["show"]), code(e), html.escape(e["title"]), len(wl),
                   html.escape(", ".join(wl)), len(ep_ph),
                   html.escape(" · ".join("%s (%s)" % (P.display(p), PH_MEAN[p]) for p in sorted(ep_ph))), "".join(body)))
        open(os.path.join(STUDY, fn), "w", encoding="utf-8").write(page)
        index[e["show"]].append((code(e), e["title"], fn, len(wl), len(e["lines"])))
    idx = ["<!doctype html><meta charset=utf-8><title>Phụ đề học tiếng Anh</title><style>%s</style>"
           "<h1>🎬 Phụ đề đã định dạng để học (chỉ trên máy)</h1>" % css]
    for show, lst in index.items():
        idx.append("<h2>%s (%d tập)</h2>" % (html.escape(show), len(lst)))
        idx.append("".join("<div class=l><span class=t>%s</span><span><a href='%s'>%s</a> <span class=w>· %d từ TOEIC · %d câu</span></span></div>"
                           % (c, fn, html.escape(ti), n, nl) for c, ti, fn, n, nl in lst))
    open(os.path.join(STUDY, "index.html"), "w", encoding="utf-8").write("".join(idx))
    print("tren may:", os.path.join(STUDY, "index.html"), "|", len(eps), "tap")


if __name__ == "__main__":
    sys.exit(main())
