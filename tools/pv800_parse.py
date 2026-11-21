#!/usr/bin/env python3
"""Tách “800 phrasal verb tiếng Anh thông dụng” (IELTS Fighter, PDF) thành bảng dữ liệu.

Sách đánh dấu: “*” giữa động từ và tiểu từ = chèn được tân ngữ vào giữa (tách được);
“+” sau cụm = tân ngữ đứng sau tiểu từ. Có cả hai = cả hai vị trí đều được.

Dùng toạ độ chữ (pdftotext -bbox-layout): mỗi ô Định nghĩa / Ví dụ được gán cho ô Phrasal verb
có tâm theo chiều dọc gần nhất (ô trong bảng được căn giữa theo chiều dọc).

    pdftotext -bbox-layout "800 phrase vebs thông dụng - IELTS Fighter.pdf" pv800.html
    python3 tools/pv800_parse.py pv800.html      # -> tools/data/expressions/pv800.json
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "expressions", "pv800.json")
NUM = r'"([\d.]+)"'
PART = set("up down in out on off over away back about around through along across into with to of for from at by after apart forward ahead behind under".split())


def parse(path):
    src = open(path, encoding="utf-8").read()
    pages = []
    for pg in re.findall(r"<page.*?</page>", src, re.S):
        lines = []
        for bi, blk in enumerate(re.findall(r"<block.*?</block>", pg, re.S)):
            for ln in re.findall(r"<line.*?</line>", blk, re.S):
                ws = re.findall(r'<word xMin=%s yMin=%s xMax=%s yMax=%s>(.*?)</word>' % (NUM, NUM, NUM, NUM), ln)
                if not ws:
                    continue
                # tách dòng ở khoảng trống rộng (ô cột kề nhau bị gộp chung 1 dòng)
                segs, cur = [], [ws[0]]
                for a, b in zip(ws, ws[1:]):
                    if float(b[0]) - float(a[2]) > 12:
                        segs.append(cur)
                        cur = []
                    cur.append(b)
                segs.append(cur)
                for sg in segs:
                    x0 = min(float(w[0]) for w in sg)
                    y0 = min(float(w[1]) for w in sg)
                    y1 = max(float(w[3]) for w in sg)
                    lines.append(dict(b=bi, x=x0, y0=y0, y1=y1, t=html.unescape(" ".join(w[4] for w in sg))))
        pages.append(lines)
    return pages


def main(path):
    pages = parse(path)
    out = []
    started = False
    defx, exx = 110.0, 300.0
    for lines in pages:
        hdr = [l for l in lines if l["t"].startswith(("Phrasal Verb", "Phrasal")) or "Definition" in l["t"]]
        for l in lines:
            if re.match(r"Phrasal Verb \( ?[A-Z]", l["t"]):
                started = True
        if not started:
            continue
        body_all = [l for l in lines if l["y0"] > 85 and not re.search(r"IELTS FIGHTER|Website:|Fanpage:|TỔNG HỢP", l["t"])]
        # tách trang thành từng bảng (mỗi chữ cái một bảng) theo dòng “Phrasal Verb ( X )”
        cuts = sorted(l["y0"] for l in body_all if re.match(r"Phrasal Verb \( ?[A-Z]", l["t"]))
        bounds = [0] + cuts + [9999]
        for s0, s1 in zip(bounds, bounds[1:]):
            seg = [l for l in body_all if s0 <= l["y0"] < s1]
            body = [l for l in seg if not re.search(r"^Phrasal|^Verb$|^Definition|^Example$", l["t"])]
            xs = sorted({round(l["x"]) for l in body if l["x"] > 45})
            if len(xs) >= 2:
                gaps = [(xs[i + 1] - xs[i], i) for i in range(len(xs) - 1)]
                g, i = max(gaps)
                if g > 60:
                    defx, exx = xs[0], xs[i + 1]
            for l in seg:
                if l["t"].startswith("Definition"):
                    defx = l["x"]
                if l["t"].startswith("Example"):
                    exx = l["x"]
            out.extend(rows_of(body, defx, exx))
    for e in out:
        if not e["ex"]:  # nghĩa + ví dụ dính chung 1 dòng
            m = re.search(r"\s(?=(?:The|We|I|He|She|They|You|Why|Can|My|Did|When|If)\b.*[.!?]$)", e["def"])
            if m:
                e["def"], e["ex"] = e["def"][:m.start()].strip(), e["def"][m.end():].strip()
        if len(e["pv"].split()) > 4:  # cụm dính chữ của cột nghĩa
            ws = e["pv"].split()
            k = 1
            while k < len(ws) and ws[k] in PART:  # động từ + các tiểu từ liền sau
                k += 1
            e["def"] = " ".join(ws[k:]) + " " + e["def"]
            e["pv"] = " ".join(ws[:k])
            e["mark"] = re.sub(r"^(.*?%s).*?(\s*\+)?$" % re.escape(ws[k - 1]), lambda m: m.group(1) + (m.group(2) or ""), e["mark"])
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(out), "mục →", OUT)
    for e in out[::45]:
        print(" | ".join([e["mark"], e["def"], e["ex"]]))


def rows_of(body, defx, exx):
    out = []
    if True:
        col0 = [l for l in body if l["x"] < 45]
        rest = [l for l in body if l["x"] >= 45]
        # gộp các dòng cột 1 thuộc cùng khối (vd “crack down on +” / “on”)
        cells = []
        for l in sorted(col0, key=lambda l: l["y0"]):
            if cells and cells[-1]["b"] == l["b"] and l["y0"] - cells[-1]["y1"] < 4 and (re.fullmatch(r"[+*]|on|with|to|of|for|in|at|from|about|up|out|off", l["t"]) or len(cells[-1]["t"]) < 3):
                cells[-1]["t"] += " " + l["t"]
                cells[-1]["y1"] = l["y1"]
            else:
                cells.append(dict(l, defs=[], exs=[]))
        if not cells:
            return out
        # gom dòng cột 2/3 thành ô theo khối
        blocks = {}
        for l in rest:
            col = "defs" if l["x"] < exx - 8 else "exs"
            blocks.setdefault((l["b"], col), []).append(l)
        for (b, col), ls in blocks.items():
            ls.sort(key=lambda l: l["y0"])
            centers = [(c["y0"] + c["y1"]) / 2 for c in cells]
            span0, span1 = ls[0]["y0"], ls[-1]["y1"]
            inside = [i for i, c in enumerate(centers) if span0 - 1 < c < span1 + 1]
            if len(inside) <= 1:  # cả khối thuộc 1 hàng
                mid = (span0 + span1) / 2
                i = min(range(len(cells)), key=lambda i: abs(centers[i] - mid))
                cells[i][col].extend(ls)
            else:  # khối dính nhiều hàng → gán từng dòng
                for l in ls:
                    mid = (l["y0"] + l["y1"]) / 2
                    i = min(range(len(cells)), key=lambda i: abs(centers[i] - mid))
                    cells[i][col].append(l)
        for c in cells:
            mark = re.sub(r"\s+", " ", c["t"]).strip()
            d = " ".join(l["t"] for l in sorted(c["defs"], key=lambda l: (l["y0"], l["x"])))
            x = " ".join(l["t"] for l in sorted(c["exs"], key=lambda l: (l["y0"], l["x"])))
            pv = re.sub(r"\s*[*+]\s*", " ", mark).strip()
            if not re.match(r"^[a-z]", pv) or not d:
                continue
            out.append({"pv": re.sub(r"\s+", " ", pv), "mark": mark, "sep": "*" in mark, "obj_after": "+" in mark,
                        "def": d.strip(), "ex": x.strip()})
    return out


if __name__ == "__main__":
    main(sys.argv[1])
