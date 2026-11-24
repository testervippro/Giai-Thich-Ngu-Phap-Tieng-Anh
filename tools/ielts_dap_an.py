#!/usr/bin/env python3
"""Phân tích câu hỏi + đáp án IELTS Reading (Cambridge 10–21).

- Đề: ~/Ielts-Reading/cleaned_camNN_testN.html (bài đọc + câu hỏi)
- Đáp án: tools/data/ielts_answers.json (lấy từ ieltstrainingonline.com — trang bên thứ ba,
  không phải đáp án chính thức của Cambridge)

Với mỗi câu hỏi:
  - dạng câu hỏi (nhận từ lời hướng dẫn: TRUE/FALSE/NOT GIVEN, YES/NO/NOT GIVEN, chọn heading,
    nối thông tin với đoạn, nối đặc điểm, nối nửa câu, trắc nghiệm, chọn 2 đáp án, điền từ…)
  - đáp án (+ nội dung lựa chọn nếu đáp án là chữ cái / số La Mã)
  - câu DẪN CHỨNG trong bài đọc: so khớp từ khoá (lemma spaCy, trọng số idf) giữa câu hỏi
    (+ đáp án với dạng điền từ) và từng câu của bài; đáp án là chữ cái đoạn văn thì chỉ tìm
    trong đoạn đó. Tự động nên có thể chỉ sai chỗ.

Ra docs/: ielts-dap-an-tong-quan.md + ielts-dap-an-cam-NN.md

    ~/Ielts-Reading/.venv-nlp/bin/python tools/ielts_dap_an.py
"""
import html
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import spacy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ielts_ngu_phap as ng  # noqa: E402  (trích bài đọc)

SRC = ng.SRC
DOCS = ng.DOCS
ANS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ielts_answers.json")

TYPES = [
    # key, tên, nhận dạng (regex trên lời hướng dẫn)
    ("tfng", "TRUE / FALSE / NOT GIVEN", r"agree with the information|TRUE\s+if"),
    ("ynng", "YES / NO / NOT GIVEN", r"agree with the (views|claims)|YES\s+if"),
    ("head", "Chọn tiêu đề cho đoạn (Matching headings)", r"list of headings|correct heading"),
    ("info", "Nối thông tin với đoạn (Matching information)", r"which (paragraph|section) contains|contains the following information"),
    ("end", "Nối nửa câu (Sentence endings)", r"correct ending"),
    ("feat", "Nối đặc điểm / người (Matching features)", r"match each|with the correct (person|researcher|scientist|name|date|period|group|place|country|company|feature|type|category)|list of (people|researchers|scientists|findings|statements)"),
    ("mcq2", "Chọn 2–3 đáp án (Multiple choice – nhiều đáp án)", r"choose (two|three) (letters|correct)"),
    ("mcq", "Trắc nghiệm 1 đáp án (Multiple choice)", r"choose the correct letter"),
    ("sumopt", "Điền tóm tắt từ danh sách cho sẵn (Summary – word list)", r"(summary|notes|sentences).*(using the list|from the box|list of words|words, A)|using the list of (words|phrases)|from the list (below|of)"),
    ("diag", "Điền sơ đồ / lưu đồ (Diagram / flow-chart)", r"(diagram|flow-?chart|label)"),
    ("table", "Điền bảng (Table completion)", r"complete the table"),
    ("notes", "Điền ghi chú (Note completion)", r"complete the notes"),
    ("summ", "Điền tóm tắt (Summary completion)", r"complete the summary"),
    ("sent", "Điền câu (Sentence completion)", r"complete the (following )?sentences|complete each sentence"),
    ("short", "Trả lời ngắn (Short answer)", r"answer the questions"),
]
TYPE_NAME = {k: n for k, n, _ in TYPES}
TIPS = {
    "tfng": "Tìm đúng câu chứa thông tin (từ khoá ít đổi: tên riêng, số, năm), rồi so **ý**: cùng ý → TRUE; ngược ý "
            "(phủ định, đổi số/so sánh, all↔some) → FALSE; bài không nói tới điểm mấu chốt → NOT GIVEN. Thứ tự câu hỏi "
            "đi theo thứ tự bài.",
    "ynng": "Như TRUE/FALSE/NOT GIVEN nhưng so với **quan điểm / nhận định của tác giả** (chú ý từ thể hiện thái độ: "
            "surprisingly, unfortunately, it is clear that…). Thứ tự câu hỏi đi theo thứ tự bài.",
    "head": "Đọc câu chủ đề (thường câu 1–2) và câu kết của đoạn, tìm **ý chính cả đoạn**, không chọn heading chỉ khớp "
            "một chi tiết. Làm đoạn dễ trước, loại dần heading đã dùng.",
    "info": "Thông tin cần tìm thường là **chi tiết** (một ví dụ, một lý do, một con số…) nằm ở bất kỳ đoạn nào, không "
            "theo thứ tự. Gạch từ khoá dạng danh từ của câu hỏi rồi quét từng đoạn; một đoạn có thể dùng nhiều lần.",
    "end": "Đọc nửa đầu, tìm vị trí trong bài (theo thứ tự), rồi chọn kết thúc vừa **đúng ý** vừa **đúng ngữ pháp**.",
    "feat": "Tìm **tên người / mốc thời gian** trong bài trước (dễ quét), đọc quanh tên đó rồi so với các nhận định. "
            "Không theo thứ tự; một lựa chọn có thể dùng nhiều lần.",
    "mcq2": "Mỗi phương án đúng phải có dẫn chứng riêng trong bài; loại phương án đúng một nửa hoặc bài không nhắc. "
            "Thứ tự 2 đáp án không quan trọng.",
    "mcq": "Tìm vị trí bằng từ khoá ở thân câu hỏi (theo thứ tự bài), đọc kỹ 2–3 câu quanh đó; phương án đúng thường "
           "**paraphrase**, phương án bẫy lặp nguyên từ của bài nhưng sai ý.",
    "sumopt": "Đoán **từ loại** cần điền (danh từ/tính từ/động từ) trước, rồi chọn từ trong danh sách mang **cùng nghĩa** "
              "với bài (đáp án hầu như luôn là từ đồng nghĩa, không trùng nguyên văn).",
    "diag": "Quét tên các bộ phận / bước trong bài; điền đúng số chữ cho phép, chép **nguyên văn** từ bài.",
    "table": "Xác định cột/hàng → biết cần loại thông tin gì (năm, tên, số…); chép **nguyên văn**, đúng giới hạn số từ.",
    "notes": "Ghi chú đi theo thứ tự bài; đoán từ loại trước, chép **nguyên văn** và đúng giới hạn số từ.",
    "summ": "Tóm tắt thường chỉ bao một phần bài, theo thứ tự; đoán từ loại, tìm câu paraphrase rồi chép **nguyên văn**.",
    "sent": "Câu hỏi theo thứ tự bài; tìm câu paraphrase, chép **nguyên văn**, đúng giới hạn số từ và đúng ngữ pháp.",
    "short": "Câu hỏi Wh- theo thứ tự bài; xác định cần **ai / cái gì / bao nhiêu**, chép nguyên văn từ bài.",
    "other": "Đọc kỹ lời hướng dẫn để biết cách trả lời.",
}


ORDERED = {"tfng", "ynng", "mcq", "end", "sent", "summ", "notes", "short", "table", "diag"}


def detect_type(instr):
    for k, _, rx in TYPES:
        if re.search(rx, instr, re.I):
            return k
    return "other"


# ---------------------------------------------------------------- tách câu hỏi
def lines_of(path):
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<ins.*?</ins>", " ", s, flags=re.S)
    s = re.sub(r"<(br|/p|/li|/h\d|/tr|/td|/th|/div)[^>]*>", "\n", s)
    t = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return [re.sub(r"[ \t\u00a0]+", " ", l).strip() for l in t.split("\n") if l.strip()]


QHEAD = re.compile(r"^Questions?\s+(\d{1,2})\s*(?:[–\-—]|to|and)\s*(\d{1,2})\b", re.I)
GAP = re.compile(r"(?<!\d)(\d{1,2})\s*(?:…|_{2,}|\.{3,}|\u2026)+")
ROMAN = re.compile(r"^(i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii)\s+(.+)$")
OPT = re.compile(r"^([A-L])\s+(.{2,})$")


MULTI_OPT = re.compile(r"(?:^|\s)([A-L])\s+(?=\S)")


def split_options(ln):
    """'A pressure B satisfaction C intuition' -> [('A','pressure'), ...] (chữ cái tăng dần)."""
    ms = list(MULTI_OPT.finditer(ln))
    if len(ms) < 2 or ms[0].start() > 0:
        return None
    letters = [m.group(1) for m in ms]
    if any(ord(b) != ord(a) + 1 for a, b in zip(letters, letters[1:])):
        return None
    out = []
    for k, m in enumerate(ms):
        e = ms[k + 1].start() if k + 1 < len(ms) else len(ln)
        out.append((m.group(1), ln[m.end():e].strip()))
    return out


def parse_questions(path):
    """-> list of groups: dict(lo, hi, type, instr, items{n: text}, options{key: text}, item_opts{n:{k:v}})"""
    L = lines_of(path)
    heads = [(i, int(m.group(1)), int(m.group(2))) for i, l in enumerate(L) for m in [QHEAD.match(l)] if m]
    heads = [h for h in heads if 1 <= h[1] <= h[2] <= 40]
    # bỏ tiêu đề lặp (cùng khoảng số liền nhau), sửa khoảng số bị ghi sai (vd "Questions 1-8" cho câu 14-21)
    fixed, prev_hi = [], 0
    for i, lo, hi in heads:
        if fixed and (lo, hi) == fixed[-1][1:]:
            fixed[-1] = (i, lo, hi)
            continue
        if lo <= prev_hi:
            shift = prev_hi + 1 - lo
            lo, hi = lo + shift, hi + shift
        fixed.append((i, lo, hi))
        prev_hi = hi
    groups = []
    for gi, (i, lo, hi) in enumerate(fixed):
        stop = fixed[gi + 1][0] if gi + 1 < len(fixed) else len(L)
        g = dict(lo=lo, hi=hi, instr="", items={}, options={}, item_opts=defaultdict(dict))
        instr, cur = [], None
        # số in trên trang có thể bị lệch (vd 1-8 thay vì 14-21): nhận cả số gốc
        raw_lo = int(QHEAD.match(L[i]).group(1))
        off = lo - raw_lo
        for ln in L[i + 1:stop]:
            if re.match(r"READING PASSAGE \d", ln) or ln in ("Save", "Cancel", "Delete"):
                break
            mi = re.match(r"^(\d{1,2})\s*[.)]?\s+(.+)$", ln)
            num = int(mi.group(1)) if mi else None
            if num is not None and not (lo <= num <= hi) and lo <= num + off <= hi:
                num += off
            so = split_options(ln)
            if mi and lo <= num <= hi and not re.match(r"^\d{1,2}\s*(…|_|\.{3})", ln):
                cur = num
                g["items"][cur] = mi.group(2)
            elif GAP.search(ln) and any(lo <= int(x) <= hi for x in GAP.findall(ln)):
                for x in GAP.findall(ln):
                    if lo <= int(x) <= hi:
                        g["items"].setdefault(int(x), ln)
                cur = None
            elif so:
                for k, v in so:
                    g["options"].setdefault(k, v)
            elif ROMAN.match(ln) and len(ln) < 160:
                r = ROMAN.match(ln)
                g["options"][r.group(1)] = r.group(2)
            elif OPT.match(ln) and len(ln) < 220:
                o = OPT.match(ln)
                if cur is not None:
                    g["item_opts"][cur][o.group(1)] = o.group(2)
                g["options"].setdefault(o.group(1), o.group(2))
            elif not g["items"]:
                instr.append(ln)
            elif cur is not None and len(ln) < 200 and not re.match(r"^[A-Z ]{12,}$", ln):
                g["items"][cur] += " " + ln
        g["instr"] = " ".join(instr)
        g["type"] = detect_type(g["instr"])
        if g["type"] == "mcq2" and not g["items"]:
            stem = [x for x in re.split(r"(?<=[.?])\s+", g["instr"]) if x.endswith("?") or x.lower().startswith("which")]
            for n in range(lo, hi + 1):
                g["items"][n] = stem[-1] if stem else g["instr"]
        groups.append(g)
    return groups


# ---------------------------------------------------------------- dẫn chứng
class Finder:
    def __init__(self, nlp):
        self.nlp = nlp

    def prep_passage(self, paras):
        """paras: [(label, text)] -> list of sentences dict(label, text, lem set)"""
        out = []
        for lab, txt in paras:
            for s in self.nlp(txt).sents:
                st = s.text.strip()
                if len(st.split()) < 3:
                    continue
                lem = {t.lemma_.lower() for t in s if t.is_alpha and not t.is_stop and len(t) > 2}
                lem |= {t.text for t in s if t.like_num}
                out.append(dict(label=lab, text=st, lem=lem))
        return out

    def keywords(self, text):
        d = self.nlp(text)
        k = {t.lemma_.lower() for t in d if t.is_alpha and not t.is_stop and len(t) > 2}
        k |= {t.text for t in d if t.like_num}
        return k - {"paragraph", "section", "passage", "reading", "statement", "information", "writer", "author",
                    "following", "mention", "mentioned", "reference", "description", "example", "true", "false"}

    def best(self, sents, kw, bonus=(), only_label=None, df=None, min_idx=0):
        N = len(sents) or 1
        best, bs, bm = None, 0.0, set()
        for i, s in enumerate(sents):
            if i < min_idx:
                continue
            if only_label and s["label"] != only_label:
                continue
            m = kw & s["lem"]
            sc = sum(math.log(1 + N / (1 + df[w])) for w in m)
            bm_ = set(m)
            for b in bonus:
                if b and b.lower() in s["text"].lower():
                    sc += 6
                    bm_.add(b)
            if sc > bs:
                best, bs, bm = i, sc, bm_
        return best, bs, bm


def mark(text, words):
    """In đậm các từ khoá khớp (theo dạng gốc gần đúng)."""
    out = text
    for w in sorted(words, key=len, reverse=True):
        if len(w) < 3 and not w.isdigit():
            continue
        stem = re.escape(w[:-1] if len(w) > 4 and w.endswith("e") else w)
        out = re.sub(r"(?<![\w*])(%s\w*)" % stem, r"**\1**", out, flags=re.I, count=2)
    return out.replace("****", "")


def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")


# ---------------------------------------------------------------- passage có nhãn đoạn
def labelled_paras(path):
    L = lines_of(path)
    res = {}
    for no, title, paras in ng.extract_test(path):
        lab_paras = []
        for k, p in enumerate(paras):
            lab = ""
            key = p[:40]
            for idx, ln in enumerate(L):
                if key in ln:
                    if re.match(r"^[A-H]\s", ln):
                        lab = ln[0]
                    elif idx > 0 and re.fullmatch(r"[A-H]", L[idx - 1]):
                        lab = L[idx - 1]
                    break
            lab_paras.append((lab, p))
        res[no] = (title, lab_paras)
    return res


def passage_of(n):
    return 1 if n <= 13 else 2 if n <= 26 else 3


def main():
    nlp = spacy.load("en_core_web_sm")
    F = Finder(nlp)
    answers = json.load(open(ANS, encoding="utf-8"))
    A = answers["answers"]
    type_count = Counter()
    tf_count = Counter()
    found_stats = Counter()
    pages = defaultdict(list)       # cam -> lines
    per_type_examples = defaultdict(list)
    for c in range(10, 22):
        for t in range(1, 5):
            path = os.path.join(SRC, "cleaned_cam%d_test%d.html" % (c, t))
            key = "%d-%d" % (c, t)
            P = pages[c]
            P.append("\n## 📝 Test %d\n" % t)
            if key not in A:
                P.append("> ⚠️ Chưa có đáp án cho đề này (trang nguồn không có). Xem đề trên "
                         "[site luyện đề](https://testervippro.github.io/Ielts-Reading/).\n")
                continue
            ans = {int(k): v for k, v in A[key].items()}
            passages = labelled_paras(path)
            sents = {no: F.prep_passage(ps) for no, (title, ps) in passages.items()}
            dfs = {no: Counter(w for s in ss for w in s["lem"]) for no, ss in sents.items()}
            groups = parse_questions(path)
            covered = set()
            for g in groups:
                pno = passage_of(g["lo"])
                if g["lo"] in (1, 14, 27) or not any(passage_of(x["lo"]) == pno for x in groups if x["lo"] < g["lo"]):
                    title = passages.get(pno, ("", []))[0]
                    P.append("\n### 📖 Passage %d%s\n" % (pno, (": " + title) if title else ""))
                typ = g["type"]
                P.append("#### Câu %d–%d · %s\n" % (g["lo"], g["hi"], TYPE_NAME.get(typ, "Dạng khác")))
                P.append("> 💡 **Cách làm:** %s · [xem mẹo dạng này](ielts-dap-an-tong-quan.md?id=%s)\n" % (TIPS[typ], typ))
                if g["options"] and typ in ("head", "feat", "end", "sumopt", "info", "mcq2"):
                    opts = " · ".join("**%s** %s" % (k, esc(v)) for k, v in list(g["options"].items())[:14])
                    P.append("> 📋 Lựa chọn: %s\n" % opts)
                ss = sents.get(pno, [])
                df = dfs.get(pno, Counter())
                last_idx = None
                for n in range(g["lo"], g["hi"] + 1):
                    if n in covered:
                        continue
                    covered.add(n)
                    q = g["items"].get(n, "")
                    a = ans.get(n, "?")
                    type_count[typ] += 1
                    if typ in ("tfng", "ynng"):
                        tf_count[(typ, a.upper())] += 1
                    # nội dung đáp án nếu là chữ cái / La Mã
                    a_text = ""
                    keys = [x.strip() for x in re.split(r"[,/&]| and ", a) if x.strip()]
                    src_opts = g["item_opts"].get(n) or g["options"]
                    opt_txt = [src_opts.get(k) or src_opts.get(k.lower()) for k in keys]
                    if any(opt_txt) and typ != "info":
                        a_text = "; ".join(o for o in opt_txt if o)
                    # tìm dẫn chứng
                    kw = F.keywords(q) if q else set()
                    bonus = ()
                    only = None
                    if typ in ("table", "notes", "summ", "sent", "short", "diag"):
                        bonus = tuple(x.strip(" ()") for x in re.split(r"/|\bor\b", re.sub(r"\(.*?\)", "", a)) if x.strip())
                    elif typ in ("head",):
                        mlab = re.search(r"\b(?:Paragraph|Section)\s+([A-H])\b", q)
                        only = mlab.group(1) if mlab else None
                        kw = F.keywords(a_text) if a_text else kw
                    elif typ == "info" and re.fullmatch(r"[A-H]", a.strip()):
                        only = a.strip()
                    elif typ in ("feat", "end", "sumopt", "mcq", "mcq2") and a_text:
                        kw = kw | F.keywords(a_text)
                    # dạng theo thứ tự bài: dẫn chứng câu sau nằm sau câu trước (lùi tối đa 1 câu)
                    ordered = typ in ORDERED
                    mi = max(0, last_idx - 1) if ordered and last_idx is not None else 0
                    bi, sc, words = F.best(ss, kw, bonus, only, df, mi) if ss else (None, 0, set())
                    if (bi is None or sc < 3) and mi:
                        bi2, sc2, w2 = F.best(ss, kw, bonus, only, df)
                        if bi2 is not None and sc2 > sc + 3:
                            bi, sc, words = bi2, sc2, w2
                    if bi is None and only:
                        bi, sc, words = F.best(ss, kw, bonus, None, df)
                    if ordered and bi is not None and sc >= 3:
                        last_idx = bi
                    found_stats["co" if bi is not None and sc >= 3 else "yeu"] += 1
                    q_show = re.sub(r"\s+[A-D]\s+.*$", "", q) if typ == "mcq" and g["item_opts"].get(n) else q
                    line = "**%d.** %s" % (n, esc(q_show) if q_show else "_(xem đề)_")
                    line += "\n  → ✅ **%s**%s" % (esc(a), (" — " + esc(a_text)) if a_text else "")
                    if bi is not None and sc >= 2:
                        s = ss[bi]
                        loc = ("đoạn %s" % s["label"]) if s["label"] else "câu %d của bài" % (bi + 1)
                        conf = "" if sc >= 5 else " · độ tin cậy thấp"
                        line += "\n  > 📍 *Dẫn chứng (%s%s):* %s" % (loc, conf, mark(esc(s["text"]), words))
                        if len(per_type_examples[typ]) < 3 and sc >= 6 and q:
                            per_type_examples[typ].append((c, t, n, q, a, a_text, s["text"], words))
                    else:
                        line += "\n  > 📍 *Không tự tìm được câu dẫn chứng chắc chắn — đọc lại bài để xác định.*"
                    P.append("- " + line)
                P.append("")

    # ---- trang theo cuốn
    for c, P in pages.items():
        head = ["# ✅ Cam %d — Đáp án & phân tích câu hỏi IELTS Reading\n" % c,
                "> Mỗi câu: **dạng câu hỏi** → **đáp án** → **câu dẫn chứng** trong bài (từ khoá khớp với câu hỏi được "
                "**in đậm**, chỉ rõ đoạn A, B, C… nếu bài có nhãn đoạn). Mỗi nhóm câu có **cách làm** cho dạng đó.\n>\n"
                "> ⚠️ Đáp án lấy từ ieltstrainingonline.com (bên thứ ba, không phải đáp án chính thức của Cambridge). Câu "
                "dẫn chứng do máy tìm bằng so khớp từ khoá nên **có thể chỉ sai chỗ** — với TRUE/FALSE/NOT GIVEN và "
                "câu paraphrase mạnh, hãy đọc thêm câu trước/sau. NOT GIVEN thì câu dẫn chứng chỉ là chỗ gần nhất bài nói tới.\n",
                "**Các cuốn:** " + " · ".join(("**Cam %d**" % x) if x == c else "[Cam %d](ielts-dap-an-cam-%d.md)" % (x, x)
                                             for x in range(10, 22)) +
                " · [📊 Tổng quan dạng câu hỏi](ielts-dap-an-tong-quan.md) · [🗺️ Ngữ pháp Cam %d](ielts-ngu-phap-cam-%d.md)\n" % (c, c)]
        open(os.path.join(DOCS, "ielts-dap-an-cam-%d.md" % c), "w", encoding="utf-8").write("\n".join(head + P) + "\n")

    # ---- tổng quan
    tot = sum(type_count.values())
    T = ["# 📊 IELTS Reading — Tổng quan dạng câu hỏi & cách làm (Cambridge 10–21)\n",
         "> Thống kê **%s câu hỏi** trong **%d đề** Cambridge IELTS 10–21 (47 đề có đáp án; Cam 17 Test 3 chưa có). Bấm vào "
         "từng cuốn để xem **đáp án + câu dẫn chứng** cho từng câu.\n>\n> ⚠️ Đáp án lấy từ ieltstrainingonline.com (bên thứ "
         "ba, không phải đáp án chính thức của Cambridge); dạng câu hỏi và câu dẫn chứng do máy nhận diện.\n"
         % ("{:,}".format(tot), len(A)),
         "**Đáp án & phân tích theo cuốn:** " + " · ".join("[Cam %d](ielts-dap-an-cam-%d.md)" % (x, x) for x in range(10, 22)) + "\n",
         "## 📈 Dạng câu hỏi nào gặp nhiều nhất\n", "| # | Dạng câu hỏi | Số câu | Tỉ lệ |\n|---|---|---|---|"]
    for i, (k, v) in enumerate(type_count.most_common(), 1):
        T.append("| %d | [%s](#%s) | %d | %.1f%% |" % (i, TYPE_NAME.get(k, "Dạng khác"), k, v, 100 * v / tot))
    T.append("\n## ⚖️ Phân bố đáp án TRUE / FALSE / NOT GIVEN và YES / NO / NOT GIVEN\n")
    T.append("| Dạng | TRUE / YES | FALSE / NO | NOT GIVEN |\n|---|---|---|---|")
    for k, yes, no in (("tfng", "TRUE", "FALSE"), ("ynng", "YES", "NO")):
        T.append("| %s | %d | %d | %d |" % (TYPE_NAME[k], tf_count[(k, yes)], tf_count[(k, no)], tf_count[(k, "NOT GIVEN")]))
    T.append("\n> Ba đáp án xuất hiện gần đều nhau → **đừng đoán theo cảm giác** \"chắc là NOT GIVEN\"; luôn tìm câu dẫn chứng.\n")
    T.append("## 🧭 Cách làm từng dạng (kèm ví dụ thật từ đề)\n")
    for k, n, _ in TYPES + [("other", "Dạng khác", "")]:
        if not type_count.get(k):
            continue
        T.append('<a id="%s"></a>\n\n### %s <small>(%d câu)</small>\n' % (k, n, type_count[k]))
        T.append("💡 %s\n" % TIPS[k])
        for c, t, nn, q, a, at, ev, words in per_type_examples[k]:
            T.append("- *(Cam %d · Test %d · câu %d)* %s → ✅ **%s**%s\n  > 📍 %s" % (
                c, t, nn, esc(q), esc(a), (" — " + esc(at)) if at else "", mark(esc(ev), words)))
        T.append("")
    open(os.path.join(DOCS, "ielts-dap-an-tong-quan.md"), "w", encoding="utf-8").write("\n".join(T) + "\n")
    print("cau hoi:", tot, "| dang:", dict(type_count), "| dan chung:", dict(found_stats))


if __name__ == "__main__":
    sys.exit(main())
