#!/usr/bin/env python3
"""Lấy 2136 Kanji Jōyō theo thứ tự + câu chuyện của bộ *Remembering the Kanji* (Heisig, 3 tập)
trong books/jp/ -> docs/kanji-viewer/rtk-data.js (bộ "📘 Heisig RTK" của trang Xem thẻ Kanji).

- Vol 1 (bản 4, 2042 frame, 56 bài): chữ Kanji in bằng font riêng không có Unicode, nên đọc theo
  font/toạ độ bằng PyMuPDF: số frame (cỡ 12), keyword (cỡ 18), câu chuyện (cỡ 10.2; nghiêng =
  thành phần, đậm = keyword), ghi chú "* As a primitive…".
- Vol 2 + Vol 3: có Unicode -> dùng index (Vol 3 Index vi: keyword–chữ–frame; Vol 2 Index v:
  frame–chữ) để biết frame nào là chữ nào. Vol 3 Part One cho chữ mới (frame 2043–3000).
- Danh sách Jōyō 2136 chính thức: tools/data/joyo2136.json (KANJIDIC: grade 1–8).
Chữ Jōyō không có trong 3 sách (23 chữ) để cuối, không có câu chuyện Heisig.
Chạy: python3 tools/rtk_kanji.py
"""
import collections
import json
import os
import re
import subprocess
import sys

import fitz  # PyMuPDF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, "books", "jp")
V1 = os.path.join(BOOKS, "Remembering the Kanji, Vol. 1 - James W. Heisig (1).pdf")
V2 = os.path.join(BOOKS, "Remembering the Kanji, Vol. 2 - James W. Heisig.pdf")
V3 = os.path.join(BOOKS, "Remembering the Kanji, Vol. 3 - James W. Heisig.pdf")
JOYO = os.path.join(ROOT, "tools", "data", "joyo2136.json")
OUT = os.path.join(ROOT, "docs", "kanji-viewer", "rtk-data.js")
K = r"[㐀-鿿豈-﫿\U00020000-\U0002ffff]"
LIGS = [("ﬀ", "ff"), ("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬃ", "ffi"), ("ﬄ", "ffl")]
# Jōyō 2010 viết khác dạng chữ trong sách
VAR = {"頰": "頬", "籠": "篭", "剝": "剥", "𠮟": "叱", "塡": "填"}


def raw(pdf):
    out = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True, check=True).stdout
    for a, b in LIGS:
        out = out.replace(a, b)
    return out


def frame_map(t2, t3):
    """frame -> [chữ, keyword] từ Index vi (Vol 3) + Index v (Vol 2)."""
    s = t3[t3.index("Index vi contains a cumulative"):]
    pat = re.compile(r"([A-Za-z][A-Za-z0-9 ,'’\-\.\(\)\[\]/!&]*?) (%s) (?<![\d.])(\d{1,4})(?![\d.])" % K)
    F = {}
    for line in s.split("\n"):
        for m in pat.finditer(line):
            F.setdefault(int(m.group(3)), [m.group(2), m.group(1).strip()])
    L = t2.split("\n")
    st = next(i for i, l in enumerate(L) if l.startswith("2 r-1 "))
    v2, pend = {}, None
    for line in L[st - 3:]:
        m = re.match(r"^\s*(\d{1,4}) r-\d+(?: (%s))?" % K, line)
        if m:
            if m.group(2):
                v2.setdefault(int(m.group(1)), m.group(2)); pend = None
            else:
                pend = int(m.group(1))
        elif pend:
            m2 = re.match(r"^\s*(%s)" % K, line)
            if m2:
                v2.setdefault(pend, m2.group(1))
            pend = None
    for n, k in v2.items():
        if n <= 2042 and n not in F:
            F[n] = [k, ""]
    # lỗi in trong index của sách (đối chiếu chéo Vol 2 / Vol 3)
    F[1] = ["一", "one"]; F[578] = ["曰", "sayeth"]; F[1529] = ["壌", "lot"]; F[2029] = ["箇", "item"]
    return F


def parse_v1(F):
    d = fitz.open(V1)
    LIG = {"³": "fi", "µ": "fl"}
    fix = lambda t: "".join(LIG.get(c, c) for c in t)
    frames, cur, les = {}, None, 0
    for pno in range(len(d)):
        spans = [s for b in d[pno].get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
        spans.sort(key=lambda s: s["origin"][1])
        grp, gy = [], None
        for s in spans:  # gom theo dòng (chân chữ lệch <= 4pt)
            if gy is None or s["origin"][1] - gy > 3.5:
                grp.append([]); gy = s["origin"][1]
            grp[-1].append(s)
        spans = []
        for g in grp:
            g.sort(key=lambda s: s["bbox"][0])
            for s in g:
                s["gy"] = g[0]["origin"][1]; spans.append(s)
        xs = collections.Counter(round(s["bbox"][0]) for s in spans if abs(s["size"] - 10.2) < .5 and s["font"].startswith("Minion"))
        nx = [s["bbox"][0] for s in spans if s["font"].startswith("Minion-Regular") and abs(s["size"] - 12) < .5
              and s["text"].strip().isdigit() and s["bbox"][1] > 45]
        if nx:  # trang chẵn/lẻ lệch lề 35pt
            off = 35 if min(nx) > 150 else 0
        else:
            off = 35 if xs.get(196, 0) + xs.get(203, 0) > xs.get(161, 0) + xs.get(168, 0) else 0
        for s in spans:
            x, y, f, sz, t = s["bbox"][0] - off, s["bbox"][1], s["font"], s["size"], s["text"]
            if y < 45:
                continue
            mm = re.match(r"^\s*Lesson (\d+)\s*$", t)
            if mm and sz > 14:
                les = int(mm.group(1)); cur = None; continue
            if f.startswith("Minion-Regular") and abs(sz - 12) < .5 and t.strip().isdigit() and x < 160:
                n = int(t.strip())
                if 1 <= n <= 2042 and n not in frames:
                    cur = {"n": n, "kw": "", "body": [], "les": les}; frames[n] = cur; continue
            if abs(sz - 18) < .5 and t.strip() == "*":
                cur = None; continue
            if cur is None:
                continue
            if f.startswith("Minion-Regular") and abs(sz - 18) < .5 and x > 250:
                if not cur["body"]:
                    cur["kw"] = (cur["kw"] + " " + fix(t.strip())).strip()
                continue
            if x < 150:
                if not f.startswith("Minion") and sz > 20:
                    continue  # chữ Kanji to của frame
                if abs(sz - 10.2) < .5:
                    cur = None  # chữ dẫn bài ngoài frame
                continue
            if sz > 15:
                continue  # thứ tự nét
            if f.startswith("Minion"):
                tt = fix(t)
                if "Italic" in f and "Expert" not in f:
                    tt = "\x01" + tt + "\x02"
                elif "Semibold" in f:
                    tt = "\x03" + tt + "\x04"
                cur["body"].append((round(s["gy"]), tt))
            else:
                cur["body"].append((round(s["gy"]), "◆"))  # chữ/bộ in bằng font hình
    out = {}
    for n, c in frames.items():
        txt, lasty = "", None
        for y, t in c["body"]:
            if lasty is not None and y != lasty:
                if txt.endswith("-") and not txt.endswith(" -"):
                    txt = txt[:-1]
                elif not txt.endswith(" "):
                    txt += " "
            txt += t; lasty = y
        txt = re.sub(r"\x02\s*\x01", " ", txt); txt = re.sub(r"\x04\s*\x03", " ", txt)
        txt = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        txt = txt.replace("\x01", "<i>").replace("\x02", "</i>").replace("\x03", "<b>").replace("\x04", "</b>")
        txt = re.sub(r"◆(\s*)\((frames?)\s+(\d+)", lambda m: (F.get(int(m.group(3))) or ["?"])[0] + m.group(1) + "(" + m.group(2) + " " + m.group(3), txt)
        txt = re.sub(r"\s*◆+", "", txt)
        txt = re.sub(r"(?<![\u3400-\u9fff] )\((frames?) (\d+)\)", lambda m: "(" + ((F.get(int(m.group(2))) or [""])[0] + " " if (F.get(int(m.group(2))) or [""])[0] else "") + m.group(1) + " " + m.group(2) + ")", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        txt = re.sub(r"<i>\s*</i>|<b>\s*</b>", "", txt)
        txt = re.sub(r"\s+([,.;:])", r"\1", txt)
        m = re.search(r"\[(\d+)\]", txt)
        story, prim = txt, ""
        i = txt.find("* ")
        if i >= 0:
            story, prim = txt[:i].strip(), txt[i + 2:].strip()
        if n == 2042:
            story = re.sub(r"<i>Valeant.*", "", story).strip()
        out[n] = {"les": c["les"], "kw": c["kw"] or (F.get(n) or ["", ""])[1], "story": story, "prim": prim,
                  "strokes": int(m.group(1)) if m else None}
    return out


def parse_v3(t3, tp):
    """Vol 3 Part One. Dò frame trong bản -raw (chắc chắn đúng thứ tự), lấy câu chữ từ bản thường (giữ dấu cách)."""
    st = t3.index("\n2043 ")
    pos, hits = st, {}
    for n in range(2043, 3001):
        m = re.compile(r"%d ([^\n]{1,60}?) (%s) r-\d+" % (n, K)).search(t3, pos, pos + 20000)
        if m:
            hits[n] = (m.start(), m.end(), m.group(1).strip(), m.group(2)); pos = m.end()
    ns, out = sorted(hits), {}
    tp = re.sub(r"\n\d+ \| remembering the kanji 3[^\n]*", "\n", tp)
    tp = re.sub(r"\n[^\n]*\| \d+\n", "\n", tp)
    tp = re.sub(r"\n[^\n]*major primitive elements[^\n]*", "\n", tp)
    tp = tp.replace("\x0c", "\n")
    ppos = tp.index("\n2043\n")
    for i, n in enumerate(ns):
        s, e, kw, k = hits[n]
        body = None
        m = re.compile(r"\n%d\n" % n).search(tp, ppos, ppos + 8000)
        if m:
            m2 = re.compile(r"\n%d\n" % (n + 1)).search(tp, m.end(), m.end() + 8000)
            block = tp[m.end():m2.start() if m2 else m.end() + 1500]
            # đoạn (ngăn bởi dòng trống) có "[số nét]" chính là câu chuyện
            for para in re.split(r"\n\s*\n", block):
                if re.search(r"\[\d+\]", para):
                    lines = [l for l in para.split("\n") if l.strip() and not re.fullmatch(r"r-\d+", l.strip())
                             and l.strip() not in (k, kw) and "【" not in l]
                    body = "\n".join(lines); break
            if body is not None:
                ppos = m.end()
        if body is None:  # dự phòng: bản -raw
            body = t3[e:hits[ns[i + 1]][0] if i + 1 < len(ns) else e + 600]
            body = re.split(r"\s*\d+ \| remembering the kanji 3|\n[^\n]*\| \d+|\s\d{4} r-\d+", body)[0]
        for a_, b_ in LIGS:
            body = body.replace(a_, b_)
        body = body.split("\n\n\n")[0] if body.count("\n\n\n") else body
        body = re.sub(r"-\n", "", body); body = re.sub(r"\s+", " ", body).strip()
        body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        m = re.search(r"\[(\d+)\]", body)
        if m:  # "car . . . axe. [11]" -> thành phần in nghiêng
            head = re.sub(r"\s*\.\s*\.\s*\.\s*", " . . . ", body[:m.start()]).strip().rstrip(".").strip()
            tail = body[m.end():].strip()
            if " . . . " in head and len(head) < 120 or len(head) < 40:
                head = "<i>" + head + "</i>"
            body = head + ". [" + m.group(1) + "]" + (" " + tail if tail else "")
        out[n] = {"k": k, "kw": kw, "story": body, "strokes": int(m.group(1)) if m else None}
    return out


def main():
    t2, t3 = raw(V2), raw(V3)
    F = frame_map(t2, t3)
    v1 = parse_v1(F)
    tp = subprocess.run(["pdftotext", V3, "-"], capture_output=True, text=True, check=True).stdout
    v3 = parse_v3(t3, tp)
    joyo = json.load(open(JOYO, encoding="utf-8"))
    J = set(joyo)
    inv = {}
    for n in sorted(F):
        if n <= 2042 and F[n][0]:
            inv.setdefault(F[n][0], n)
    for n in sorted(v3):
        inv.setdefault(v3[n]["k"], n)
    rows, used = [], set()
    for n in range(1, 2043):  # Vol 1 theo đúng thứ tự frame
        k = F[n][0]
        c = next((j for j in J if VAR.get(j, j) == k), None)
        if c and c not in used:
            f = v1[n]
            rows.append([c, n, f["kw"], 1, f["les"], f["story"], f["prim"], f["strokes"]]); used.add(c)
    for n in sorted(v3):  # Vol 3: chữ Jōyō thêm năm 2010
        c = next((j for j in J if VAR.get(j, j) == v3[n]["k"]), None)
        if c and c not in used:
            f = v3[n]
            rows.append([c, n, f["kw"], 3, 0, f["story"], "", f["strokes"]]); used.add(c)
    rest = [c for c in joyo if c not in used]
    for c in rest:
        rows.append([c, 0, "", 0, 0, "", "", None])
    assert len(rows) == 2136, len(rows)
    with open(OUT, "w", encoding="utf-8") as fo:
        fo.write("// 2136 Kanji Jōyō theo thứ tự 3 sách Remembering the Kanji (Heisig) — sinh bởi tools/rtk_kanji.py\n"
                 "// [chữ, frame, keyword, tập (1/3; 0 = không có trong sách), bài (Vol 1), câu chuyện, ghi chú thành phần, số nét]\n")
        fo.write("window.RTK=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("Vol1 %d · Vol3 %d · ngoài sách %d: %s" % (sum(r[3] == 1 for r in rows), sum(r[3] == 3 for r in rows), len(rest), "".join(rest)))


if __name__ == "__main__":
    sys.exit(main())
