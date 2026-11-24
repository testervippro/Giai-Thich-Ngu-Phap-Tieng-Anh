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
POS = r"(verb|noun|naun|nour|neth|adi\.|adj\.?|adv\.?|prep\.?|pron\.?|conj\.?|exclamation|number|det\.?|phrasal verb|modal verb)"
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
            pos = {"naun": "noun", "nour": "noun", "neth": "noun", "adi.": "adj."}.get(m.group(2), m.group(2)).rstrip(".")
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
            cur["b"].append(["s", sm.group(1) + ". " + fix_text(sm.group(2))])
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
                segs_ = list(b[2])
                if segs_ and segs_[0][0] == "" and out[-1][2]:
                    out[-1][2][-1][1] += segs_.pop(0)[1]
                out[-1][2] += segs_
            elif (b[0] == "c" and out and out[-1][0] == "c" and out[-1][1] == b[1] and out[-1][2] and b[2]
                  and out[-1][2][0][0] == b[2][0][0]):          # OCR lặp nhóm → giữ bản đầy đủ hơn
                if len(json.dumps(b)) > len(json.dumps(out[-1])):
                    out[-1] = b
            else:
                out.append(b)
        # soát tay (tools/data/oxford_fixes_segs.tsv): thay cả mục [cụm, ví dụ] theo (từ mục, nhãn, cụm gốc)
        for b in out:
            if b[0] != "c":
                continue
            new = []
            for c, exs in b[2]:
                rep = SEG_FIX.get((e["w"], b[1], c))
                if rep is not None:
                    SEG_USED.add((e["w"], b[1], c))
                if rep is None:
                    new.append([c, exs])
                    continue
                for r in rep:
                    if r == "DEL":
                        continue
                    new.append([r[0], [x for x in r[1]] + (exs if r[2] else [])])
            b[2] = new
        e["b"] = [b for b in out if b[0] != "c" or b[2] or b[1]]
    return entries


SEG_FIX = {}
SEG_USED = set()
_SF = os.path.join(ROOT, "tools", "data", "oxford_fixes_segs.tsv")
for _l in (open(_SF, encoding="utf-8") if os.path.exists(_SF) else []):
    _p = _l.rstrip("\n").split("\t")
    if len(_p) != 4 or _l.startswith("#"):
        continue
    _rep = []
    for _seg in _p[3].split(" || "):
        if _seg.strip() == "DEL":
            _rep.append("DEL"); continue
        _keep = _seg.endswith(" +EX")
        _seg = _seg[:-4] if _keep else _seg
        _c, _, _x = _seg.partition(" :: ")
        _rep.append([_c.strip(), [x.strip() for x in _x.split(" ◇ ") if x.strip()], _keep])
    SEG_FIX[(_p[0], _p[1], _p[2])] = _rep


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
    seg = seg.strip()
    if re.match(r"^(?:The|A|An|He|She|It|They|We|His|Her|Their|My|Our|This|There)\s+[A-Z]?[a-z]", seg) and re.search(r"[.!?]$|\s[a-z]+\s[a-z]+", seg) and len(seg.split()) >= 4 and not re.match(r"^(?:A|An|The)\s[a-z]+(?:,|\s/|$)", seg):
        return [["", [x for x in re.split(r"\s*[◇♢]\s*", seg) if x]]]       # cả mục là câu ví dụ
    return _split_example(seg)


def _split_example(seg):
    """'big, crucial It was a big decision.' -> [['big, crucial', ['It was a big decision.']]]
    'for They have… approval. to She submitted…' -> [['for', [...]], ['to', [...]]] (nhiều giới từ dính nhau)."""
    seg = seg.strip()
    m = None
    for mm in re.finditer(r"(?<=[a-z0-9~)\]'’,/.!?-])\s+(?=(?:[A-Z‘'\"“]|I\s)[a-z'’ ]?)", seg):
        prevw = seg[:mm.start()].split()[-1].lower() if seg[:mm.start()].split() else ""
        prevraw = seg[:mm.start()].split()[-1] if seg[:mm.start()].split() else ""
        if prevw in ("the", "a", "an") or (prevraw[:1].isupper() and len(seg[:mm.start()].split()) >= 2
                                          and seg[:mm.start()].split()[-2].lower() in ("the", "a", "an") ):        # "the Asian market", "the Queen": tên riêng, không phải đầu câu
            continue
        if seg[:mm.start()] and not seg[:mm.start()].endswith(","):
            m = mm
            break
    if not m:
        # ví dụ dạng cụm viết thường: "difficult, hard, tough the difficult decision of whether…"
        stem = HW[0][:max(3, len(HW[0]) - 2)] if HW[0] else ""
        for mm in re.finditer(r"(?<=[a-z)])\s+(?=(?:the|a|an|his|her|its|their|our|my|your|this|that|these|those|some|no)\s)", seg):
            rest_ = seg[mm.end():]
            lastitem = seg[:mm.start()].split(",")[-1].split()
            if stem and stem in rest_.lower() and len(rest_.split()) >= 3 and stem not in seg[:mm.start()].lower() and len(lastitem) <= 2:
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


PREPS_ALL = ("about above across after against along among amongst around as at before behind below beneath beside besides between beyond by "
             "concerning despite during except for from in inside into like near of off on onto out outside over past per regarding round since "
             "surrounding than through throughout till to toward towards under underneath unlike until up upon via with within without").split()
FIXES = os.path.join(ROOT, "tools", "data", "oxford_fixes.json")
_FX = json.load(open(FIXES, encoding="utf-8")) if os.path.exists(FIXES) else {}
FIX_TEXT = _FX.get("text", {})      # sửa chữ OCR: chuỗi sai -> chuỗi đúng (vd "Heformally" -> "He formally")
_WF = os.path.join(ROOT, "tools", "data", "oxford_fixes_words.tsv")   # soát tay từng từ lạ (OCR, chữ dính, từ bị ngắt dòng)
for _l in (open(_WF, encoding="utf-8") if os.path.exists(_WF) else []):
    if "\t" in _l and not _l.startswith("#"):
        _a, _b = _l.rstrip("\n").split("\t", 1)
        FIX_TEXT[_a] = _b
_FIX_RX = [(re.compile(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])"), b) for a, b in sorted(FIX_TEXT.items(), key=lambda x: -len(x[0]))]


def fix_text(t):
    for rx, b in _FIX_RX:
        if rx.search(t):
            t = rx.sub(lambda m: b, t)
    return t
FIX_SEG = _FX.get("seg", {})        # soát tay: "từ mục|nhãn|cụm gốc" -> [[cụm, [ví dụ…]], …]
PREPS = set("about above across after against along among amongst around as at before behind below beneath beside besides between beyond by "
            "concerning despite during except for from in inside into like near of off on onto out outside over past per regarding round since "
            "surrounding than through throughout till to toward towards under underneath unlike until up upon via with within without".split())
STOP = set("the a an of to in on at for by with and or sb sth one's your his her their its be is are was were that this as from it".split())


def _toks(s):
    """tách từ, phần (…) dính vào từ đứng trước"""
    out = []
    for m in re.finditer(r"\([^)]*\)|\S+", s):
        if m.group(0).startswith("(") and out:
            out[-1] += " " + m.group(0)
        else:
            out.append(m.group(0))
    return out


def _stem(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    return w[:5] if len(w) >= 6 else w


def _exs(ex):
    return [x.strip() for x in re.split(r"\s*[◇♢]\s*", ex) if x.strip()]


def fix_long(coll, exs, cat):
    """Cụm còn dính ví dụ viết thường → tách. Trả về danh sách [cụm, [ví dụ]]."""
    key = "%s|%s|%s" % (HW[0], cat, coll)
    if key in FIX_SEG:
        return [list(x) for x in FIX_SEG[key]]
    if len(coll) <= 40 and "~" not in coll[1:]:
        return [[coll, exs]]
    # A. nhiều giới từ đánh dấu bằng "~": "~ about panic about food ~ among panic among…"
    if "~" in coll[1:] or (coll.startswith("~") and len(coll.split()) > 3):
        parts = [p.strip() for p in re.split(r"(?=~)", coll) if p.strip()]
        # "beyond ~ He was beyond all reason." : "~" là chỗ của từ mục ngay sau giới từ, không mở nhóm mới
        merged = []
        for p in parts:
            if (p.startswith("~") and merged and not merged[-1].startswith("~")
                    and all(x in PREPS for x in re.split(r"[\s/,]+", merged[-1].lower()) if x)
                    and not re.match(r"~\s*(?:%s)\b" % "|".join(PREPS), p)):
                merged[-1] = merged[-1] + " " + p
            else:
                merged.append(p)
        parts = merged
        out = []
        for p in parts:
            if not p.startswith("~"):
                pm = re.match(r"^((?:(?:%s)[\s/,]+)+~)\s+(.*)$" % "|".join(PREPS), p)
                if pm:                                   # "beyond ~ He was beyond all reason."
                    out.append([pm.group(1), _exs(pm.group(2))])
                else:
                    out += fix_long(p, [], cat) if (out == [] and "~" not in p) else [[p, []]]
                continue
            tk = _toks(p[1:].strip())
            k = 0
            while k < len(tk) and all(x in PREPS for x in re.split(r"[/,]", tk[k].lower()) if x):
                k += 1
            if k == 0 and tk and tk[0] in ("s", "'s"):          # "~s from" = số nhiều + giới từ
                k = 1
                while k < len(tk) and all(x in PREPS for x in re.split(r"[/,]", tk[k].lower()) if x):
                    k += 1
            k = max(k, 1) if tk else 0
            c = ("~ " + " ".join(tk[:k])).strip()
            rest = " ".join(tk[k:])
            if len(rest.split()) >= 2:
                out.append([c, _exs(rest)])
            elif out and rest:
                out.append([c + " " + rest, []])
            else:
                out.append([(c + " " + rest).strip(), []])
        if out:
            out[-1][1] += exs
        return out
    # B. danh sách collocate + ví dụ viết thường ở mục cuối
    items = re.split(r",\s+(?![^()]*\))", coll)
    last = items[-1]
    tk = _toks(last)
    if len(tk) < 4:
        return [[coll, exs]]
    head = ", ".join(items[:-1])
    hstem = _stem(HW[0])
    if cat.startswith("PHRASES") and len(tk) <= 6:
        return [[coll, exs]]
    k = 0
    if cat.startswith("PREP") or cat == "PREP.":
        while k < len(tk) - 2 and all(x in PREPS for x in re.split(r"[/]", tk[k].lower()) if x):
            k += 1
    if not k:
        stems_rest = lambda kk: {_stem(x) for x in tk[kk:]}
        for kk in range(min(6, len(tk) - 2), 0, -1):    # cụm dài nhất mà từ cuối được lặp lại trong ví dụ
            lw = tk[kk - 1]
            if _stem(lw) and _stem(lw) not in STOP and re.sub(r"[^a-z]", "", lw.lower()) not in STOP and _stem(lw) in stems_rest(kk):
                k = kk
                break
    if not k:
        rest_has_head = any(_stem(x) == hstem for x in tk[1:]) and tk[0].lower() not in STOP
        others = {_stem(x) for it in items[:-1] for x in _toks(it)} - STOP
        if rest_has_head and (others & {_stem(x) for x in tk[1:]} or not cat.startswith(("PHRASES", "PREP"))):
            k = 1
    if not k:
        return [[coll, exs]]
    c = " ".join(tk[:k])
    ex = " ".join(tk[k:])
    out = []
    # ví dụ kết thúc bằng giới từ trơ trọi (không có dấu câu) → là collocate kế tiếp
    tail = None
    m = re.search(r"\s((?:%s)(?:/(?:%s))*)$" % ("|".join(PREPS), "|".join(PREPS)), ex)
    if m and not re.search(r"[.!?]$", ex):
        tail, ex = m.group(1), ex[:m.start()]
    out.append([(head + ", " + c) if head else c, _exs(ex) + exs])
    if tail:
        out.append([tail, []])
    return out


SENT_START = ("He|She|It|They|We|You|The|A|An|His|Her|Their|My|Our|Your|This|That|These|Those|There|Most|Many|Some|All|"
              "No|Few|Several|Every|Each|Her|Its|In|On|At|After|When|If|As|Don't|I'm|I've|I'll|I'd")


def refine(coll, exs, cat, depth=0):
    """Lỗi OCR còn sót sau khi tách: '|' đọc thành 'I', giới từ viết hoa trôi vào ví dụ, cụm kế tiếp sau dấu phẩy."""
    if depth > 8 or not exs:
        return [[coll, exs]]
    out_ex = []
    tail = []
    for i, x in enumerate(exs):
        # (2) "In, have, meet with She met…" → phần đầu thuộc cụm
        m = re.match(r"^((?:In|Into|On|With|To|At|For|Of|From|By)\b(?:,?\s+[a-z][^A-Z]*?)?)\s+(?=(?:%s)\b|[A-Z][a-z])(.*)$" % SENT_START, x)
        if i == 0 and m and not out_ex and re.search(r"\b(be|put|hand|fall|rise|take part|pale|fade|end up|land|involved|wrapped|collapse|burst|erupt)$", coll):
            coll = coll + " " + m.group(1)[0].lower() + m.group(1)[1:]
            x = m.group(2)
        # (1) "… ◇ I share He shared…" : 'I'/'l' là dấu '|'
        m = re.search(r"(?:^|(?<=[.!?)])\s+)[Il]\s+([a-z][a-z ,/()'’=;-]*?)(?:\.?\s+(?=[A-Z][a-z]|I\s[a-z]|'|‘)|\s*\.?\s*$)", x)
        if m and re.search(r"\b(he|she|it|they|we|you|me|him|her|us|them|that|but|why|what|because|if|was|is|am|are|did|do|can't|don't|'m|the|a|an|my|your|his)\b", re.sub(r"\(=[^)]*\)", "", m.group(1))):
            m = None                                     # là đại từ "I" thật (câu ví dụ), không phải dấu "|"
        if m and any(len(it.split()) > 4 for it in re.sub(r"\(=[^)]*\)", "", m.group(1)).split(",")):
            m = None
        if m and ("," in m.group(1) or len(m.group(1).split()) <= 3):
            before = x[:m.start()].strip()
            after = x[m.end():].strip()
            if before:
                out_ex.append(before)
            tail = refine(m.group(1).strip(" ,"), ([after] if after else []) + exs[i + 1:], cat, depth + 1)
            break
        # (3) cụm kế tiếp sau dấu phẩy / dấu chấm: "…English, on close acquaintance On first…"
        if cat.startswith(("PHRASES", "PREP")):
            m = re.search(r"(?:,|(?<=[.!?]))\s+((?:\(|~\s?)?[a-z][a-z/'’ ()~.-]{2,60}?)\s+(?=(?:%s)\b|[A-Z][a-z])" % SENT_START, x)
            if m and len(m.group(1).split()) <= 9 and not re.search(r"\b(and|but|which|who|that|because|when|while)$", m.group(1)):
                before = x[:m.start()].rstrip(",") + ("" if re.search(r"[.!?]$", x[:m.start()]) else "")
                after = x[m.end():].strip()
                out_ex.append(before.strip())
                tail = refine(m.group(1).strip(), [after] + exs[i + 1:], cat, depth + 1)
                break
        out_ex.append(x)
    return [[coll, out_ex]] + tail


def restructure(t):
    t = re.sub(r"[⌊⌉⌋⌈]", "", t)
    t = re.sub(r"<[^>]*>", " ", t)                       # thẻ HTML lọt vào từ OCR bảng
    t = re.sub(r"\bVER[E8B]\s*\+", "VERB +", t)
    t = fix_text(t)
    t = re.sub(r"\s[\]\[]\s", " | ", t)                   # OCR đọc "|" thành "]" / "["
    t = re.sub(r"(^|\s)[–-]\s?(?=(?:%s)\b)" % "|".join(sorted(PREPS_ALL, key=len, reverse=True)), r"\1~ ", t)
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
            for c_, ex_ in split_example(seg):
                for c2, ex2 in fix_long(c_, ex_, cat):
                    segs += refine(c2, ex2, cat)
        merged = []
        for c_, ex_ in segs:
            if c_ == "" and merged:
                merged[-1][1] += ex_
                continue
            if merged and re.match(r"^(?:%s)\s" % SENT_START, c_) and not ex_ and len(c_.split()) <= 3:
                continue
            merged.append([c_, ex_])
        segs = merged
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
    unused = [k for k in SEG_FIX if k not in SEG_USED]
    if unused:
        with open(os.path.join(ROOT, "build", "oxford_fixes_unused.tsv"), "w", encoding="utf-8") as f_:
            f_.write("\n".join("\t".join(k) for k in unused) + "\n")
    print("soát tay: áp dụng %d / %d mục" % (len(SEG_USED), len(SEG_FIX)))
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
