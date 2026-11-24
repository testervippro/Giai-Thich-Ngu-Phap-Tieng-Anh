#!/usr/bin/env python3
"""Dựng docs/toeic-vocabulary-index.md — danh sách từ vựng gộp, BỎ TRÙNG, sắp A–Z.

Nguồn:
  - Hackers TOEIC Vocabulary (Index, OCR)    : tools/data/toeic_hackers_index.json
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
    # TOEIC (Hackers): bản gốc lưu riêng (không đọc lại từ md để khỏi cộng dồn ghi chú mỗi lần dựng)
    rows = [dict(term=r["term"], ipa="", vi=r["vi"], src="TOEIC (Hackers)")
            for r in json.load(open(os.path.join(DATA, "toeic_hackers_index.json"), encoding="utf-8"))]
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
    # gộp mục gần trùng: khác cách viết (film-maker/filmmaker), có/không "the", ghi chú trong ngoặc, hoa/thường.
    # Giữ riêng động từ cụm và danh từ ghép (break up ≠ break-up, take over ≠ takeover).
    PART = r"(up|down|out|over|in|off|ahead|back|away|on|through|round|about|by)"
    def k3(t):
        t = t.lower().replace("’", "'")
        t = re.sub(r"\(.*?\)", "", t).strip()
        t = re.sub(r"^the\s+", "", t)
        form = ""
        m = re.fullmatch(r"([a-z]+)([ -]?)" + PART, t)
        if m:
            form = "pv" if m.group(2) == " " else "n"
        return re.sub(r"[^a-z0-9]", "", t) + form
    groups = {}
    for k, e in list(merged.items()):
        kk = k3(e["term"])
        if not kk.strip("pvn"):
            continue
        if kk in groups and groups[kk] is not e:
            g = groups[kk]
            # tên hiển thị: ưu tiên dạng không ngoặc, không "the", có nhiều nguồn hơn
            score = lambda x: ("(" in x["term"], x["term"].lower().startswith("the "), -len(x["srcs"]), len(x["term"]))
            keep, drop = (g, e) if score(g) <= score(e) else (e, g)
            for v in drop["vis"]:
                if v.lower() not in (x.lower() for x in keep["vis"]):
                    keep["vis"].append(v)
            for x in drop["srcs"]:
                if x not in keep["srcs"]:
                    keep["srcs"].append(x)
            m_ = re.search(r"\((.*?)\)", drop["term"])
            if m_ and m_.group(1) not in keep["notes"] and len(m_.group(1).split()) >= 2:
                keep["notes"].append(m_.group(1))
            if not keep["ipa"]:
                keep["ipa"] = drop["ipa"]
            for kk2, v2 in list(merged.items()):
                if v2 is drop:
                    del merged[kk2]
            groups[kk] = keep
        else:
            groups[kk] = e
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
         "> 🔎 **[Mở bản tra cứu có bộ lọc](tools/vocab-index.html)** — lọc theo nguồn (TOEIC / IELTS / Word Skills / Oxford 3000–5000), cấp CEFR, chủ đề IELTS.\n",
         "> Tổng cộng: **%s mục** (đã bỏ trùng), A–Z — TOEIC %s · IELTS %s · Word Skills %s · Oxford 3000/5000 %s.\n"
         % tuple("{:,}".format(x).replace(",", ".") for x in (len(items), cnt("TOEIC"), cnt("IELTS"), cnt("Word Skills"), cnt("Oxford 3000") + cnt("Oxford 5000"))),
         "---\n",
         "| # | Từ / Cụm từ | Nghĩa tiếng Việt | Phiên âm | Nguồn |",
         "|---|---|---|---|---|"]
    for i, e in enumerate(items, 1):
        vi = "; ".join(e["vis"])
        if e["notes"]:
            notes = []
            for n in e["notes"]:
                n = re.sub(r"\bofthe\b", "of the", re.sub(r"\bofa\b", "of a", n)).strip()
                if n.lower() not in (x.lower() for x in notes):
                    notes.append(n)
            # ghi chú ngữ cảnh "(of a train)" giữ nguyên, ghi chú định nghĩa "(= colour of hair)" có dấu "="
            vi = (vi + " " if vi else "") + " ".join(("(%s)" if re.match(r"(of|in|on|for|used|with)\b", n) else "(= %s)") % n for n in notes)
        term = e["term"]
        L.append("| %d | %s | %s | %s | %s |" % (i, esc(term), esc(vi), esc(e["ipa"]), esc(", ".join(e["srcs"]))))
    open(MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    # dữ liệu cho trang tra cứu có bộ lọc (docs/tools/vocab-index.html)
    SRC = ["TOEIC", "IELTS", "Basic", "Intermediate", "Advanced", "Oxford 3000", "Oxford 5000"]
    topics, data = [], []
    for e in items:
        flags, lv, tp = 0, "", []
        for x in e["srcs"]:
            if x.startswith("TOEIC"): flags |= 1
            if x.startswith("IELTS"):
                flags |= 2
                t = x.split("·", 1)[1].strip() if "·" in x else ""
                if t:
                    if t not in topics: topics.append(t)
                    tp.append(topics.index(t))
            if x.startswith("Word Skills"):
                for i, b in ((2, "Basic"), (3, "Intermediate"), (4, "Advanced")):
                    if b in x: flags |= 1 << i
            m = re.match(r"Oxford (3000|5000)(?: \(Mỹ\))? · (A1|A2|B1|B2|C1)", x)
            if m:
                flags |= 1 << (5 if m.group(1) == "3000" else 6)
                lv = lv or m.group(2)
        vi = "; ".join(e["vis"])
        data.append([e["term"], vi, e["ipa"], flags, lv, tp] if tp else [e["term"], vi, e["ipa"], flags, lv])
    js = "// Sinh bởi tools/vocab_index_build.py — từ vựng TOEIC + IELTS + Oxford Word Skills + Oxford 3000/5000 (đã bỏ trùng)\n"
    js += "window.VOCAB_INDEX=" + json.dumps({"src": SRC, "topics": topics, "rows": data}, ensure_ascii=False, separators=(",", ":")) + ";\n"
    open(os.path.join(ROOT, "docs", "tools", "vocab-index-data.js"), "w", encoding="utf-8").write(js)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    open(os.path.join(ROOT, "build", "vocab_vi_missing.txt"), "w", encoding="utf-8").write("\n".join(missing) + "\n")
    print("mục", len(items), "| thiếu nghĩa", len(missing))


if __name__ == "__main__":
    main()
