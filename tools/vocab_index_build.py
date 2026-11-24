#!/usr/bin/env python3
"""Dựng docs/toeic-vocabulary-index.md — danh sách từ vựng gộp, BỎ TRÙNG, sắp A–Z.

Nguồn:
  - Hackers TOEIC Vocabulary (Index, OCR)    : các dòng có Nguồn "TOEIC (Hackers)" trong chính file md (giữ nguyên)
  - 5000 từ vựng IELTS thông dụng (flyer.vn)  : tools/data/ielts_flyer_5000.json   (tools/ielts_flyer_vocab.py)
  - Oxford Word Skills Basic/Intermediate/Advanced (Word list / Index ở cuối sách, OCR theo cột)
                                              : tools/data/oxford_word_skills_index.json
  - The Oxford 3000 / 5000 by CEFR level (+ bản American), oxfordlearnersdictionaries.com
                                              : tools/data/oxford_3000_5000.json
Nghĩa tiếng Việt: lấy từ mục đã có; thiếu thì tra các bộ dữ liệu sẵn có trong repo (DK Dictionary,
Kho cụm từ, Phrasal verbs, 4500 Collocations, từ trong phim) và tools/data/vocab_vi_extra.tsv (dịch bổ sung).

    python3 tools/vocab_index_build.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import ielts_flyer_vocab as F  # noqa: E402  (key(), load_md())

DATA = os.path.join(ROOT, "tools", "data")
MD = os.path.join(ROOT, "docs", "toeic-vocabulary-index.md")
key = F.key


def js_obj(path, name):
    s = open(path, encoding="utf-8").read()
    i = s.index("window." + name)
    return json.JSONDecoder().raw_decode(s[s.index("=", i) + 1:].lstrip())[0]


def vi_lookup():
    lk = {}
    add = lambda k, v: (k and v and key(k) not in lk) and lk.__setitem__(key(k), str(v).strip())
    p = os.path.join(DATA, "vocab_vi_extra.tsv")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            if "\t" in l and not l.startswith("#"):
                a, b = l.rstrip("\n").split("\t")[:2]
                add(a, b)
    T = os.path.join(ROOT, "docs", "tools")
    for r in js_obj(os.path.join(T, "vocab-3d-data.js"), "DK_VOCAB")["words"]:
        for w in str(r[0]).split(","):
            add(w.strip(), r[2])
    for r in js_obj(os.path.join(T, "phrase-bank-data.js"), "PHRASES")["items"]:
        add(r[1], r[2])
    for d in js_obj(os.path.join(T, "pv-ciu-data.js"), "PVCIU"):
        add(d["pv"], d["vi"])
    for r in js_obj(os.path.join(T, "colloc", "index.js"), "COLLOC")["c45"]:
        add(r[0], r[1])
    for f in ("en_vi_movie_words.tsv", "movie_phrases_vi.tsv"):
        for l in open(os.path.join(DATA, f), encoding="utf-8"):
            if "\t" in l and not l.startswith("#"):
                a, b = l.rstrip("\n").split("\t")[:2]
                if not b.startswith("="):
                    add(a, b)
    return lk


def find_vi(k, lk):
    for c in (k, k[:-1] if k.endswith("s") else None, k[:-2] if k.endswith("es") else None,
              k[:-3] + "y" if k.endswith("ies") else None, re.sub(r"\s*\(.*?\)", "", k).strip()):
        if c and c in lk:
            return lk[c]
    return ""


def main():
    rows = F.load_md()                                     # TOEIC (Hackers)
    for r in json.load(open(os.path.join(DATA, "ielts_flyer_5000.json"), encoding="utf-8")):
        rows.append(dict(term=r["term"], ipa=r["ipa"], vi=r["vi"], src=r["src"]))
    for r in json.load(open(os.path.join(DATA, "oxford_word_skills_index.json"), encoding="utf-8")):
        t = r["w"] + (")" * (r["w"].count("(") - r["w"].count(")")))
        note = r.get("note", "") if len((r.get("note") or "").split()) >= 2 else ""      # ghi chú OCR 1 chữ thường là rác
        rows.append(dict(term=t, ipa="", vi="", src="Word Skills " + "/".join(r["books"]), note=note))
    for r in json.load(open(os.path.join(DATA, "oxford_3000_5000.json"), encoding="utf-8")):
        name = "Oxford 3000" if any(s.endswith("3000") for s in r["src"]) else "Oxford 5000"
        if all(s.startswith("American") for s in r["src"]):
            name += " (Mỹ)"
        rows.append(dict(term=r["w"], ipa="", vi="", src="%s · %s · %s" % (name, r["lv"], r["pos"])))
    merged = {}
    for r in rows:
        k = key(r["term"])
        if not k:
            continue
        e = merged.setdefault(k, dict(term=r["term"], ipa="", vis=[], srcs=[], notes=[], pos=""))
        if not e["ipa"] and r.get("ipa"):
            e["ipa"] = r["ipa"]
        for v in re.split(r"\s*;\s*", r.get("vi") or ""):
            if v and v.lower() not in (x.lower() for x in e["vis"]):
                e["vis"].append(v)
        if r["src"] not in e["srcs"]:
            e["srcs"].append(r["src"])
        if r.get("note") and r["note"] not in e["notes"]:
            e["notes"].append(r["note"])
        if r.get("pos") and not e["pos"]:
            e["pos"] = r["pos"]
    lk = vi_lookup()
    # "-" trong vocab_vi_extra.tsv = rác OCR (chỉ bỏ khi mục chỉ đến từ Word Skills)
    for k in [k for k, e in merged.items() if lk.get(k) == "-" and all(x.startswith("Word Skills") for x in e["srcs"])]:
        del merged[k]
    missing = []
    for k, e in merged.items():
        if not e["vis"]:
            v = find_vi(k, lk)
            if v and v != "-":
                e["vis"].append(v)
            else:
                missing.append(e["term"])
    items = sorted(merged.values(), key=lambda e: (key(e["term"]).lstrip("('\"-0123456789 "), key(e["term"])))
    cnt = lambda s: sum(1 for e in items if any(s in x for x in e["srcs"]))
    esc = lambda s: s.replace("|", "/")
    L = ["# Danh sách từ vựng TOEIC + IELTS + Oxford (Index đầy đủ)\n",
         "> Gộp và **bỏ trùng** 4 nguồn: *Hackers TOEIC Vocabulary* (Index, OCR); **5000 từ vựng IELTS thông dụng** "
         "theo 33 chủ đề ([flyer.vn](https://flyer.vn/5000-tu-vung-ielts-thong-dung/), có phiên âm); **Oxford Word Skills** "
         "Basic / Intermediate / Advanced (Word list ở cuối sách, OCR); **The Oxford 3000 & 5000** theo cấp CEFR "
         "([oxfordlearnersdictionaries.com](https://www.oxfordlearnersdictionaries.com/wordlists/oxford3000-5000), gộp bản Anh và Mỹ). "
         "Nghĩa tiếng Việt: theo nguồn nếu có, còn lại dịch bổ sung — có thể chưa sát ngữ cảnh. Dùng `Ctrl+F` để tra nhanh.\n",
         "> Tổng cộng: **%s mục** (đã bỏ trùng), A–Z — TOEIC %s · IELTS %s · Word Skills %s · Oxford 3000/5000 %s.\n"
         % tuple("{:,}".format(x).replace(",", ".") for x in (len(items), cnt("TOEIC"), cnt("IELTS"), cnt("Word Skills"), cnt("Oxford 3000") + cnt("Oxford 5000"))),
         "---\n",
         "| # | Từ / Cụm từ | Nghĩa tiếng Việt | Phiên âm | Nguồn |",
         "|---|---|---|---|---|"]
    for i, e in enumerate(items, 1):
        vi = "; ".join(e["vis"])
        if e["notes"]:
            vi = (vi + " " if vi else "") + " ".join("(= %s)" % n for n in e["notes"])
        term = e["term"]
        L.append("| %d | %s | %s | %s | %s |" % (i, esc(term), esc(vi), esc(e["ipa"]), esc(", ".join(e["srcs"]))))
    open(MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    open(os.path.join(ROOT, "build", "vocab_vi_missing.txt"), "w", encoding="utf-8").write("\n".join(missing) + "\n")
    print("mục", len(items), "| thiếu nghĩa", len(missing))


if __name__ == "__main__":
    main()
