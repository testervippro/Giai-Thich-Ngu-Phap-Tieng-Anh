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
        if sm and not l.startswith("#") and ("|" in t or len(t) > 70 or not re.match(r"[a-z(]", sm.group(2))):
            sm = None                              # không phải tiêu đề nghĩa ("1 short sharp sound")
        if sm:
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
        nb = []
        HW[0] = e["w"].lower()
        for k, t in e["b"]:
            if k == "c":
                nb += restructure(t)
            else:
                nb.append([k, t])
        # nhóm không nhãn đứng sau một nhóm có nhãn = dòng bị ngắt → nối vào
        out = []
        for b in nb:
            if b[0] == "c" and not b[1] and out and out[-1][0] == "c":
                out[-1][2] += b[2]
            elif (b[0] == "c" and out and out[-1][0] == "c" and out[-1][1] == b[1] and out[-1][2] and b[2]
                  and out[-1][2][0][0] == b[2][0][0]):          # OCR lặp nhóm → giữ bản đầy đủ hơn
                if len(json.dumps(b)) > len(json.dumps(out[-1])):
                    out[-1] = b
            else:
                out.append(b)
        e["b"] = out
    return entries


# ---------------------------------------------------------------- định dạng lại nhóm collocation (OCR)
CAT_FIX = {"AD.J.": "ADJ.", "ADJ": "ADJ.", "AD J.": "ADJ.", "PREP": "PREP.", "PREF.": "PREP.", "ADV": "ADV.", "QUANT": "QUANT.",
           "VERB": "VERBS", "PHRASE": "PHRASES"}
BULLET = "☐☑▶•●⊠⊗⊕⊝▸♦♡◦○⌊⌉"
XREF = re.compile(r"\s*[↪⇦⇒⇨➞↔⇔→]?\s*\b(Special pages? at|Note at|See also|Compare|See)\s+((?:[A-Z][A-Z'’-]+(?:,\s*|\s+(?:and|or)\s+|\s+)?)+)")
# nhãn nhóm: ADJ. ADV. VERBS PREP. PHRASES QUANT. PHRASAL VERB, VERB + X, X + VERB/NOUN, NOUN + X…
CAT = re.compile(r"(?<![A-Za-z])((?:VERB|NOUN|ADJ\.?|ADV\.?|PREP\.?)\s?\+\s?[A-Z][A-Z'’-]+(?:\s[A-Z][A-Z'’-]+)?"
                 r"|[A-Z][A-Z'’-]+(?:\s[A-Z][A-Z'’-]+)?\s?\+\s?(?:VERB|NOUN|PREP\.?|ADJ\.?|ADV\.?)"
                 r"|PHRASAL VERBS?|AD\.?\s?J\.|ADJ\.|ADV\.|VERBS|PREP\.|PREF\.|PHRASES|QUANT\.)(?=\s|$)")


HW = [""]   # từ mục đang xử lý (để nhận ra ví dụ dạng cụm viết thường)


def split_example(seg):
    """'big, crucial It was a big decision.' -> [['big, crucial', ['It was a big decision.']]]
    'for They have… approval. to She submitted…' -> [['for', [...]], ['to', [...]]] (nhiều giới từ dính nhau)."""
    seg = seg.strip()
    m = None
    for mm in re.finditer(r"(?<=[a-z0-9~)\]'’,/.!?-])\s+(?=(?:[A-Z‘'\"“]|I\s)[a-z'’ ]?)", seg):
        if seg[:mm.start()] and not seg[:mm.start()].endswith(","):
            m = mm
            break
    if not m:
        # ví dụ dạng cụm viết thường: "difficult, hard, tough the difficult decision of whether…"
        stem = HW[0][:max(3, len(HW[0]) - 2)] if HW[0] else ""
        for mm in re.finditer(r"(?<=[a-z)])\s+(?=(?:the|a|an|his|her|its|their|our|my|your|this|that|these|those|some|no)\s)", seg):
            rest_ = seg[mm.end():]
            if stem and stem in rest_.lower() and len(rest_.split()) >= 3 and stem not in seg[:mm.start()].lower():
                return [[seg[:mm.start()].strip(), [rest_.strip()]]]
        return [[seg, []]]
    coll, ex = seg[:m.start()].strip(), seg[m.end():].strip()
    rest = []
    # sau một câu ví dụ, chữ thường mở đầu = collocate mới ("…approval. to She…", "…stupid. growing, increasing")
    k = re.search(r"(?<=[.!?])\s+(?=(?:~\s?)?[a-z])", ex)
    if k:
        rest = split_example(ex[k.end():])
        ex = ex[:k.start()]
    exs = [x.strip() for x in re.split(r"\s*[◇♢]\s*|(?<=[.!?])\s+(?=[A-Z‘“\"])", ex) if x.strip()]
    return [[coll, exs]] + rest


def restructure(t):
    t = re.sub(r"[⌊⌉]", "", t)
    refs = []
    def keep_ref(m):
        refs.append(m.group(2).strip(" ,"))
        return " "
    t = XREF.sub(keep_ref, t)
    t = re.sub("[%s]" % BULLET, " ¶ ", t)
    t = CAT.sub(lambda m: " ¶ " + m.group(1), t)
    out = []
    for part in [p.strip(" :;") for p in t.split("¶")]:
        if not part:
            continue
        cm = CAT.match(part)
        cat = ""
        if cm:
            cat = re.sub(r"\s?\+\s?", " + ", cm.group(1)).replace("AD J.", "ADJ.")
            cat = CAT_FIX.get(cat, cat)
            part = part[cm.end():].strip()
        segs = []
        for seg in re.split(r"\s+\|\s+|\s\|(?=\s)|\|", part):
            seg = seg.strip()
            if not seg:
                continue
            segs += split_example(seg)
        if cat or segs:
            out.append(["c", cat, segs])
    if refs:
        out.append(["x", ", ".join(dict.fromkeys(r.title() for r in refs))])
    return out


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
