#!/usr/bin/env python3
"""Dữ liệu cho trang tra chung Collocations & Idioms (docs/tools/phrasal-verbs-collocations-in-use.html).

Gộp (bỏ trùng) các nguồn đang nằm rải ở nhiều trang:
  - Oxford Collocations Dictionary (docs/Oxford Collocations Dictionary.md) — bản đầy đủ có ví dụ.
    Các trang "Collocations (dạng cụm)", "— 5000 từ", "— ngoài 5000 từ" đều trích từ đây, nên chỉ giữ
    1 bản Oxford + nhãn ★5000 (từ mục nằm trong Collocations5000.md).
  - 4500 English Collocations and Idioms (docs/4500-collocations-idioms.md) — theo chủ đề.
  - Bản lọc TOEIC 990 (docs/4500-collocations-toeic-990.md) — thành nhãn 🎯/📘/⭐ + câu đề ETS trên cụm 4500.
  - Phrasal verbs trong Collocations in Use (docs/tools/pv-ciu-data.js) — giữ nguyên file.

Ra docs/tools/colloc/:
  index.js      từ mục Oxford [từ, từ loại, có trong 5000 (0/1), chữ cái] + dữ liệu 4500/TOEIC (nhỏ, tải ngay)
  ox-<x>.js     nội dung Oxford theo chữ cái đầu (tải khi cần)

    python3 tools/colloc_hub_build.py
"""
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(DOCS, "tools", "colloc")
POS = r"(verb|noun|adj\.?|adv\.?|prep\.?|pron\.?|conj\.?|exclamation|number|det\.?|phrasal verb|modal verb)"
HEAD = re.compile(r"^#{1,6}\s+(?:•\s*)?([A-Za-zà-ÿ][^#|]*?)\s+" + POS + r"(?=$|[\s,.;])(.*)$")


def letter(w):
    c = w[:1].lower()
    return c if "a" <= c <= "z" else "0"


def clean(t):
    t = t.replace("$ ^{1} $", "¹").replace("$ ^{2} $", "²")
    t = re.sub(r"\$[^$]*\$", "", t)
    return re.sub(r"\s+", " ", t).strip()


def oxford():
    words5000 = {l[3:].strip().lower() for l in open(os.path.join(DOCS, "Collocations5000.md"), encoding="utf-8") if l.startswith("## ")}
    known = {re.sub(r"\s*\(.*", "", l[3:].strip().lower()) for l in open(os.path.join(DOCS, "Collocations.md"), encoding="utf-8") if l.startswith("## ")}
    entries = []   # dict(w, pos, b=[[kind, text]])  kind: s = nghĩa (sense), c = nhóm collocation
    cur, skip = None, False
    for raw in open(os.path.join(DOCS, "Oxford Collocations Dictionary.md"), encoding="utf-8"):
        l = raw.rstrip("\n")
        if not l.strip() or re.match(r"^#{1,6}\s+[A-Z][a-z]$", l.strip()) or l.startswith("# Oxford"):
            continue
        m = HEAD.match(l)
        if m and m.group(1)[0].isupper() and clean(re.sub(r"\(.*?\)", "", m.group(1))).strip(" ,").lower() not in known:
            m = None
        if m:
            skip = False
            w = clean(re.sub(r"\(.*?\)", "", m.group(1))).strip(" ,")
            w = {"z00": "zoo"}.get(w, w)
            pos = m.group(2).rstrip(".")
            if cur and cur["w"] == w:          # cùng từ, từ loại khác → gộp vào 1 mục
                cur["pos"].append(pos)
                cur["b"].append(["p", pos])
            else:
                cur = dict(w=w, pos=[pos], b=[])
                entries.append(cur)
            continue
        if cur is None:
            continue
        t = clean(re.sub(r"^#{1,6}\s*", "", l))
        if not t:
            continue
        if "KEY TO THE STUDY PAGES" in t:         # hết từ điển, sau đây là phụ lục "study pages"
            t = t.split("KEY TO THE STUDY PAGES")[0].strip()
            t = re.sub(r"\s+zoology naun Note at SUBJECT$", "", t)
            if t and cur["b"]:
                cur["b"][-1][1] += " " + t
            skip = True                            # bỏ phụ lục tới từ mục kế tiếp
            continue
        if skip:
            continue
        sm = re.match(r"^(\d+)\s+(.*)$", t)
        if l.startswith("#") and sm:
            cur["b"].append(["s", sm.group(1) + ". " + sm.group(2)])
        elif t.startswith("•"):
            cur["b"].append(["c", t.lstrip("• ").strip()])
        elif cur["b"] and cur["b"][-1][0] == "c":   # dòng bị ngắt (OCR) → nối vào nhóm trước
            prev = cur["b"][-1][1]
            cur["b"][-1][1] = prev[:-1] + t if prev.endswith("-") else prev + " " + t
        else:
            cur["b"].append(["c", t])
    for e in entries:
        e["f"] = 1 if e["w"].lower() in words5000 else 0
    return entries


def four500():
    rows, topic, kind = [], "", ""
    for l in open(os.path.join(DOCS, "4500-collocations-idioms.md"), encoding="utf-8"):
        m = re.match(r"^## (Chủ đề \d+: .*)", l)
        if m:
            topic = m.group(1).strip(); continue
        if l.startswith("### A."):
            kind = "c"; continue
        if l.startswith("### B."):
            kind = "i"; continue
        m = re.match(r"^\| (\d+) \| (.+?) \| (.*?) \|\s*$", l)
        if m and topic:
            rows.append(dict(p=m.group(2).strip(), vi=m.group(3).strip(), t=topic, k=kind))
    return rows


def toeic():
    out, topic = [], ""
    LV = {"🎯": "ets", "📘": "hackers", "⭐": "topic"}
    for l in open(os.path.join(DOCS, "4500-collocations-toeic-990.md"), encoding="utf-8"):
        m = re.match(r"^## (Chủ đề \d+: .*)", l)
        if m:
            topic = m.group(1).strip(); continue
        m = re.match(r"^\| \d+ \| (\S+) \| \*\*(.+?)\*\* \| (.*?) \| (.*?) \|\s*$", l)
        if m:
            out.append(dict(lv=LV.get(m.group(1), "topic"), p=m.group(2).strip(), vi=m.group(3).strip(), ets=m.group(4).strip(), t=topic))
    return out


def key(p):
    return re.sub(r"[^a-z/ ]", "", p.lower()).strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    ox = oxford()
    by_letter = defaultdict(list)
    for i, e in enumerate(ox):
        by_letter[letter(e["w"])].append(e)
    idx = []
    for L in sorted(by_letter):
        data = {e["w"] + "\t" + str(j): e["b"] for j, e in enumerate(by_letter[L])}
        with open(os.path.join(OUT, "ox-%s.js" % L), "w", encoding="utf-8") as f:
            f.write("window.OXC=window.OXC||{};OXC[%s]=%s;\n" % (json.dumps(L), json.dumps([e["b"] for e in by_letter[L]], ensure_ascii=False, separators=(",", ":"))))
        for j, e in enumerate(by_letter[L]):
            idx.append([e["w"], "/".join(e["pos"]), e["f"], L, j])
    rows = four500()
    tk = {key(r["p"]): r for r in rows}
    extra = 0
    for r in toeic():
        x = tk.get(key(r["p"]))
        if x is None:                  # bản lọc đã sửa chính tả → khớp lỏng theo nghĩa + chủ đề
            x = next((y for y in rows if y["t"] == r["t"] and y["vi"].lower() == r["vi"].lower()), None)
        if x is None:
            x = dict(p=r["p"], vi=r["vi"], t=r["t"], k="c"); rows.append(x); extra += 1
        x["p"] = r["p"]                # dùng bản đã sửa chính tả
        x["lv"] = r["lv"]
        if r["ets"]:
            x["ets"] = r["ets"]
    topics = list(dict.fromkeys(r["t"] for r in rows))
    small = dict(ox=idx, c45=[[r["p"], r["vi"], topics.index(r["t"]), r["k"], r.get("lv", ""), r.get("ets", "")] for r in rows], topics=topics)
    with open(os.path.join(OUT, "index.js"), "w", encoding="utf-8") as f:
        f.write("window.COLLOC=%s;\n" % json.dumps(small, ensure_ascii=False, separators=(",", ":")))
    sizes = {L: os.path.getsize(os.path.join(OUT, "ox-%s.js" % L)) // 1024 for L in by_letter}
    print("oxford", len(ox), "mục (5000:", sum(e["f"] for e in ox), ") | 4500:", len(rows), "(toeic", sum(1 for r in rows if r.get("lv")), ", thêm", extra, ")",
          "| index", os.path.getsize(os.path.join(OUT, "index.js")) // 1024, "KB | ox KB", sizes)


if __name__ == "__main__":
    main()
