#!/usr/bin/env python3
"""Bản đồ ngữ pháp IELTS Reading (Cambridge 10–21) — giống bộ "Bản đồ ngữ pháp ETS 2026".

Nguồn: ~/Ielts-Reading/cleaned_camNN_testN.html (48 đề, 3 bài đọc/đề). Chỉ lấy đoạn văn
của bài đọc (bỏ câu hỏi). Mỗi câu được spaCy (en_core_web_sm) phân tích cú pháp rồi gắn
nhãn điểm ngữ pháp theo đúng 19 chương của trang "Xem Tất Cả" (tên điểm ngữ pháp dùng
lại của bộ ETS để 2 bộ khớp nhau, thêm vài điểm hay gặp trong văn học thuật).

Ra (trong docs/):
  ielts-ngu-phap-ban-do.md          bản đồ: chương nào / điểm nào gặp nhiều nhất + ví dụ
  ielts-ngu-phap-full-<chuong>.md   toàn bộ câu của từng điểm ngữ pháp (tối đa CAP câu/điểm)
  ielts-ngu-phap-cam-NN.md          phân tích từng câu của Cam NN (4 test × 3 passage)

Chạy (cần venv có spaCy):
  ~/Ielts-Reading/.venv-nlp/bin/python tools/ielts_ngu_phap.py
"""
import html
import os
import re
import sys
from collections import Counter, defaultdict
from urllib.parse import quote

import spacy

SRC = os.path.expanduser("~/Ielts-Reading")
DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
CAP = 150          # số câu tối đa mỗi điểm ngữ pháp trên trang full
EX = 3             # số ví dụ mỗi điểm trên bản đồ

# ---------------------------------------------------------------- chương (khớp bộ ETS)
CHAPTERS = [
    ("noun", "🔤", "Danh từ", "DANH TỪ", "Danh Từ.md"),
    ("pron", "👤", "Đại từ", "ĐẠI TỪ", "Đại Từ.md"),
    ("sva", "🤝", "Hòa hợp S-V", "SỰ HÒA HỢP GIỮA CHỦ NGỮ VÀ ĐỘNG TỪ", "Sự Tương Tự Giữa Chủ Ngữ Và Động Từ.md"),
    ("adj", "🎨", "Tính từ", "TÍNH TỪ", "Tính Từ.md"),
    ("adv", "⚡", "Trạng từ", "TRẠNG TỪ", "Trạng Từ.md"),
    ("comp", "📊", "So sánh", "SO SÁNH CỦA TÍNH TỪ VÀ TRẠNG TỪ", "Các Phép So Sánh Của Tính Từ Và Trạng Từ.md"),
    ("verb", "🏃", "Động từ", "ĐỘNG TỪ", "Động Từ.md"),
    ("phr", "🧷", "Cụm động từ", "CỤM ĐỘNG TỪ", "Cụm Động Từ.md"),
    ("pass", "🔁", "Bị động", "CÂU BỊ ĐỘNG", "Câu Bị Động.md"),
    ("inf", "✳️", "To V / V-ing", "ĐỘNG TỪ NGUYÊN MẪU VÀ DANH ĐỘNG TỪ", "Động Từ Nguyên Mẫu Và Danh Động Từ.md"),
    ("prep", "📍", "Giới từ", "GIỚI TỪ", "Giới Từ.md"),
    ("conj", "🧩", "Liên từ", "LIÊN TỪ", "Liên Từ.md"),
    ("art", "🅰️", "Mạo từ", "MẠO TỪ", "Mạo Từ.md"),
    ("quant", "🔢", "Lượng từ", "LƯỢNG TỪ", "Lượng Từ.md"),
    ("tense", "⏱️", "Thì", "CÁC THÌ ĐỘNG TỪ", "TENSES.md"),
    ("clause", "🔗", "Mệnh đề", "MỆNH ĐỀ", "Menh De.md"),
    ("sent", "📝", "Câu", "CÂU", "SENTENCES.md"),
    ("seq", "⏩", "Phối hợp thì", "PHỐI HỢP THÌ", "SEQUENCE OF TENSES.md"),
    ("inv", "🔄", "Đảo ngữ", "ĐẢO NGỮ", "Đảo Ngữ.md"),
]
CH = {c[0]: c for c in CHAPTERS}


def link(fn):
    return quote(fn)


# ---------------------------------------------------------------- trích bài đọc
QUESTION_RX = re.compile(r"^(questions?\b|choose|write|complete|do the following|answer|look at|"
                         r"which paragraph|reading passage \d|you should spend|NB\b|TRUE|FALSE|NOT GIVEN|YES\b|NO\b|"
                         r"[A-H]\s|[ivx]+\s|\d+\s)", re.I)


def text_of(fragment):
    t = re.sub(r"<br\s*/?>", " ", fragment)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t).strip()


def extract_test(path):
    """-> [(passage_no, title, [paragraph, ...])]"""
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<ins.*?</ins>", " ", s, flags=re.S)
    parts = re.split(r"READING PASSAGE\s*(\d)", s)
    out = {}
    for i in range(1, len(parts) - 1, 2):
        no = int(parts[i])
        body = parts[i + 1]
        m = re.search(r"<h2[^>]*>(.*?)</h2>", body, flags=re.S)
        title = text_of(m.group(1)) if m else ""
        paras = []
        for p in re.findall(r"<p[^>]*>(.*?)</p>", body, flags=re.S):
            t = text_of(p)
            t = re.sub(r"^[A-H]\s+(?=[A-Z\u2018\u2019\u201c\"\'])", "", t)          # "A  Paragraph text" (đoạn có nhãn)
            if len(t.split()) < 18 or QUESTION_RX.match(t):
                continue
            if re.search(r"NO MORE THAN|ONE WORD|Write the correct letter|Choose the correct", t):
                continue
            if re.search(r"_{3,}|…{2,}|\.{4,}|…\s*\.|\b\d{1,2}\s*(…|_{2,}|\.{3,})", t):   # đoạn tóm tắt điền chỗ trống
                continue
            paras.append(t)
        if paras:
            prev = out.get(no)
            if not prev or len(" ".join(paras)) > len(" ".join(prev[1])):
                out[no] = (title, paras)
    if not out:
        out = extract_by_questions(s)
    return [(no, out[no][0], out[no][1]) for no in sorted(out)]


def good_para(t):
    t = re.sub(r"^[A-H]\s+(?=[A-Z\u2018\u2019\u201c\"\'])", "", t)
    if len(t.split()) < 18 or QUESTION_RX.match(t):
        return None
    if re.search(r"NO MORE THAN|ONE WORD|Write the correct letter|Choose the correct", t):
        return None
    if re.search(r"_{3,}|…{2,}|\.{4,}|…\s*\.|\b\d{1,2}\s*(…|_{2,}|\.{3,})", t):
        return None
    return t


def extract_by_questions(s):
    """Đề không có dòng "READING PASSAGE n" (vd Cam 17 Test 3): xếp đoạn văn vào passage theo
    số câu hỏi của tiêu đề "Questions X…" kế tiếp (1–13 → P1, 14–26 → P2, 27–40 → P3)."""
    out = {}
    events = [(m.start(), "h", text_of(m.group(1))) for m in re.finditer(r"<h[23][^>]*>(.*?)</h[23]>", s, flags=re.S)]
    events += [(m.start(), "p", text_of(m.group(1))) for m in re.finditer(r"<p[^>]*>(.*?)</p>", s, flags=re.S)]
    events.sort()
    qstarts = [(pos, int(re.match(r"Questions?\s*(\d+)", t).group(1))) for pos, k, t in events
               if k == "h" and re.match(r"Questions?\s*\d+", t)]
    title, short = "", ""
    last_q = qstarts[-1][0] if qstarts else len(s)
    for pos, kind, t in events:
        if kind == "h":
            if not re.match(r"(Questions?|Reading Passage)", t, re.I):
                title = t
            continue
        if pos > last_q:               # sau tiêu đề câu hỏi cuối: đoạn tóm tắt của câu hỏi
            continue
        if 2 <= len(t.split()) <= 15 and not QUESTION_RX.match(t) and not re.search(r"[A-D]\s", t[:2]):
            short = t
        t = good_para(t)
        if not t:
            continue
        nxt = next((q for qp, q in qstarts if qp > pos), 41)
        no = 1 if nxt <= 13 else 2 if nxt <= 26 else 3
        if no not in out:
            out[no] = (title or short, [])
            title, short = "", ""
        out[no][1].append(t)
    return out


# ---------------------------------------------------------------- bộ gắn nhãn
UNCOUNT = set("""information research evidence equipment advice knowledge furniture luggage news progress
water air energy traffic pollution damage software data money work homework weather music behaviour behavior
transport transportation agriculture technology education health accommodation access feedback assistance
machinery equipment vegetation wildlife soil oxygen heat light rain snow ice sand gold silver oil food
literature poetry evidence knowledge awareness intelligence creativity productivity employment unemployment
safety security happiness fun luck patience nutrition sugar salt salt rice""".split())
INDEF_PRON = set("someone somebody something anyone anybody anything everyone everybody everything no one nobody nothing".split())
REFLEX = set("myself yourself himself herself itself ourselves yourselves themselves oneself".split())
POSS_PRON = set("mine yours hers ours theirs".split())
COLLECTIVE = set("staff team committee government public family audience crew company population "
                 "group council board jury class police majority minority".split())
LINKING = set("become remain seem appear look sound stay grow prove feel turn get".split())
FEEL_ED = set("interested surprised excited bored tired worried pleased satisfied disappointed amazed shocked "
              "confused frustrated embarrassed annoyed impressed concerned exhausted fascinated frightened "
              "astonished delighted alarmed relieved puzzled".split())
FEEL_ING = set("interesting surprising exciting boring tiring worrying pleasing satisfying disappointing "
               "amazing shocking confusing frustrating embarrassing annoying impressive concerning "
               "exhausting fascinating frightening astonishing alarming puzzling challenging".split())
TIME_ADV = set("already recently soon yet still now then later lately currently previously eventually "
               "finally formerly once today tomorrow yesterday nowadays initially subsequently afterwards "
               "immediately shortly ultimately".split())
FREQ_ADV = set("always usually often frequently sometimes occasionally rarely seldom never generally "
               "normally typically regularly constantly repeatedly continually".split())
DEGREE_ADV = set("very extremely highly quite rather fairly too so really particularly especially "
                 "relatively considerably significantly increasingly incredibly remarkably entirely "
                 "completely totally fully largely slightly somewhat deeply strongly reasonably".split())
APPROX_ADV = set("nearly almost approximately roughly around virtually practically".split())
CONJ_ADV = ["however", "moreover", "therefore", "furthermore", "nevertheless", "nonetheless", "consequently",
            "thus", "hence", "meanwhile", "instead", "otherwise", "indeed", "similarly", "likewise",
            "in addition", "in contrast", "as a result", "for example", "for instance", "in fact",
            "on the other hand", "in other words", "by contrast", "besides", "accordingly", "conversely"]
COMPOUND_PREP = ["according to", "due to", "because of", "instead of", "in addition to", "in terms of",
                 "prior to", "apart from", "along with", "in spite of", "regardless of", "on behalf of",
                 "in front of", "as a result of", "by means of", "thanks to", "in relation to", "compared with",
                 "compared to", "with regard to", "in response to", "in favour of", "in favor of",
                 "as opposed to", "in place of", "on top of", "out of", "together with", "owing to",
                 "in the case of", "in charge of", "in accordance with", "with respect to", "as for",
                 "close to", "next to", "away from", "up to", "as part of", "in light of"]
VOP = {("provide", "with"), ("supply", "with"), ("thank", "for"), ("prevent", "from"), ("protect", "from"),
       ("stop", "from"), ("blame", "for"), ("accuse", "of"), ("remind", "of"), ("inform", "of"),
       ("convert", "into"), ("turn", "into"), ("divide", "into"), ("compare", "with"), ("compare", "to"),
       ("distinguish", "from"), ("associate", "with"), ("attribute", "to"), ("apply", "to"),
       ("expose", "to"), ("translate", "into"), ("transform", "into"), ("charge", "with"),
       ("separate", "from"), ("derive", "from"), ("link", "to"), ("connect", "to"), ("connect", "with"),
       ("relate", "to"), ("add", "to"), ("spend", "on"), ("base", "on"), ("focus", "on")}
TIME_WORDS = set("year years month months week weeks day days century centuries decade decades hour hours "
                 "minute minutes morning afternoon evening night time period era age past future summer "
                 "winter spring autumn season moment beginning end january february march april may june july "
                 "august september october november december monday tuesday wednesday thursday friday "
                 "saturday sunday weekend 1900s 1980s".split())
PLACE_PREPS = {"in", "at", "on", "into", "between", "throughout", "near", "under", "among", "along",
               "across", "behind", "outside", "onto", "toward", "towards", "above", "beyond", "opposite",
               "below", "beneath", "inside", "around", "within", "over"}
TIME_PREPS = {"in", "at", "on", "for", "by", "from", "during", "within", "over", "before", "after",
              "through", "until", "between", "throughout", "since"}
QUANT_DET = {"all": "all + N", "some": "some + N", "any": "any + N", "several": "several + N số nhiều",
             "other": "other + N (số nhiều/không đếm được)", "each": "each + N số ít/không đếm được",
             "many": "many + N số nhiều", "no": "no + N", "another": "another + N (số ít)",
             "every": "every + N số ít/không đếm được", "various": "various + N số nhiều",
             "multiple": "multiple + N số nhiều", "both": "both + N số nhiều", "enough": "enough + N",
             "much": "much + N số ít/không đếm được", "either": "either + N số ít/không đếm được",
             "most": "most + N (hầu hết)", "few": "few + N số nhiều", "little": "little + N số ít/không đếm được",
             "numerous": "numerous + N số nhiều", "half": "half + N số ít/không đếm được"}
QUANT_OF = ["one", "some", "most", "many", "all", "any", "none", "much", "thousands", "hundreds", "dozens",
            "millions", "each", "both", "several", "few", "half", "a couple", "a range", "a wide range",
            "a number", "the majority", "a variety", "a series", "a group"]
SUB_TIME = {"when", "while", "before", "after", "until", "till", "since", "once", "whenever", "as soon as"}
SUB_CAUSE = {"because", "since", "as"}
SUB_CONC = {"although", "though", "even though", "whereas", "even if", "while"}
SUB_PURP = {"so that", "in order that"}
REPORT = set("say tell report claim argue suggest believe think find show reveal state explain note "
             "discover realise realize conclude know feel assume announce indicate admit estimate".split())
NEG_INV = ["not only", "never", "rarely", "seldom", "hardly", "scarcely", "no sooner", "little",
           "only when", "only after", "only by", "only then", "only if", "only in", "not until", "nor",
           "neither", "under no circumstances", "at no time", "in no way", "nowhere", "on no account"]


class Tagger:
    def __init__(self, nlp):
        self.nlp = nlp

    def tags(self, sent):
        d = sent
        T = []

        def add(ch, label, a, b=None):
            add_tok(T, d, a, a if b is None else b, ch, label)

        toks = list(d)
        low = d.text.lower()
        first = next((t for t in toks if not t.is_punct), None)

        # ---------- tenses / passive / modals (theo từng động từ chính)
        for t in toks:
            if t.pos_ not in ("VERB", "AUX") or t.dep_ in ("aux", "auxpass"):
                continue
            auxs = [c for c in t.children if c.dep_ in ("aux", "auxpass")]
            al = [a.lower_ for a in auxs]
            alem = [a.lemma_ for a in auxs]
            passive = any(c.dep_ == "auxpass" for c in t.children) or (t.tag_ == "VBN" and "be" in alem)
            agent = any(c.dep_ == "agent" for c in t.children)
            mod = next((a for a in auxs if a.tag_ == "MD"), None)
            span_a = auxs[0] if auxs else t
            if mod is not None and mod.lower_ not in ("will", "shall", "'ll", "’ll"):
                if passive:
                    pass
                elif "have" in alem and t.tag_ == "VBN":
                    add("verb", "Modal + have + V3 (may have done)", mod, t)
                else:
                    add("verb", "Động từ khuyết thiếu %s + V nguyên mẫu" % mod.lower_.replace("’", "'"), mod, t)
            # thì
            tense = None
            if t.tag_ in ("VBZ", "VBP") and not auxs:
                tense = "Hiện tại đơn"
            elif t.tag_ == "VBD" and not auxs:
                tense = "Quá khứ đơn"
            elif auxs:
                if any(x in ("will", "shall", "'ll", "’ll") for x in al):
                    tense = ("Tương lai tiếp diễn" if t.tag_ == "VBG" else
                             "Tương lai hoàn thành" if "have" in alem and t.tag_ == "VBN" and not passive else
                             "Tương lai đơn")
                elif mod is not None:
                    tense = None
                elif "have" in alem:
                    hv = next(a for a in auxs if a.lemma_ == "have")
                    past = hv.tag_ == "VBD"
                    if t.tag_ == "VBG":
                        tense = "Quá khứ hoàn thành tiếp diễn" if past else "Hiện tại hoàn thành tiếp diễn"
                    else:
                        tense = "Quá khứ hoàn thành" if past else "Hiện tại hoàn thành"
                elif "be" in alem:
                    be = [a for a in auxs if a.lemma_ == "be"][0]
                    if be.lower_ == "to" or be.tag_ in ("VB", "VBN", "VBG"):
                        tense = None
                    else:
                        past = be.tag_ == "VBD"
                        if t.tag_ == "VBG" and not passive:
                            if t.lower_ == "going" and any(c.dep_ == "xcomp" for c in t.children):
                                tense = "Quá khứ tiếp diễn (was going to)" if past else "Tương lai gần (be going to)"
                            else:
                                tense = "Quá khứ tiếp diễn" if past else "Hiện tại tiếp diễn"
                        elif passive:
                            being = any(a.lower_ == "being" for a in auxs)
                            tense = ("Quá khứ tiếp diễn" if past else "Hiện tại tiếp diễn") if being else \
                                    ("Quá khứ đơn" if past else "Hiện tại đơn")
                elif "do" in alem:
                    dd = next(a for a in auxs if a.lemma_ == "do")
                    tense = "Quá khứ đơn" if dd.tag_ == "VBD" else "Hiện tại đơn"
            if tense:
                add("tense", tense, span_a, t)
            if passive:
                if mod is not None and mod.lower_ not in ("will", "shall", "'ll"):
                    pl = "Bị động với động từ khuyết thiếu (modal + be + V3)"
                elif any(a.lower_ == "to" for a in auxs) or any(a.lower_ == "be" and a.tag_ == "VB" and
                                                              any(x.lower_ == "to" for x in auxs) for a in auxs):
                    pl = "Bị động dạng nguyên mẫu (to be + V3)"
                elif tense in ("Hiện tại đơn", "Quá khứ đơn", "Tương lai đơn", "Hiện tại hoàn thành",
                               "Quá khứ hoàn thành", "Hiện tại tiếp diễn", "Quá khứ tiếp diễn"):
                    pl = "Bị động – " + tense[0].lower() + tense[1:]
                elif t.dep_ in ("xcomp",) and t.head.lemma_ in ("be", "get"):
                    pl = "Bị động"
                else:
                    pl = "Bị động"
                add("pass", pl + (" + by tác nhân" if agent else ""), span_a, t)
                if any(c.dep_ == "xcomp" and any(x.lower_ == "to" for x in c.children) for c in t.children):
                    add("pass", "Bị động + to V (be asked/required/expected to V)", span_a, t)

        # ---------- từng token
        for t in toks:
            l, lem, tag, dep, h = t.lower_, t.lemma_.lower(), t.tag_, t.dep_, t.head
            # Danh từ
            if dep == "compound" and tag.startswith("NN") and h.tag_.startswith("NN"):
                add("noun", "Danh từ ghép (N + N)", t, h)
            if tag == "VBG" and dep in ("compound", "amod") and h.tag_.startswith("NN") and t.i == h.i - 1 \
                    and l not in FEEL_ING:
                add("noun", "Danh từ ghép V-ing + N (danh động từ bổ nghĩa)", t, h)
            if tag == "POS":
                add("noun", "Sở hữu cách ('s)", d.doc[t.i - 1], h if h.i > t.i else t)
            if dep == "appos":
                add("noun", "Đồng vị ngữ (N, N bổ sung)", h, t)
            if tag == "NN" and lem in UNCOUNT and not any(c.lower_ in ("a", "an") for c in t.children):
                add("noun", "Danh từ không đếm được (không thêm -s, không dùng a/an)", t)
            # Đại từ
            if tag == "PRP$" and h.pos_ in ("NOUN", "PROPN"):
                add("pron", "Tính từ sở hữu + N", t, h)
            if l in ("this", "that", "these", "those") and dep in ("nsubj", "dobj", "pobj", "nsubjpass") \
                    and tag == "DT":
                add("pron", "Đại từ chỉ định (this/that/these/those)", t)
            if l in INDEF_PRON:
                add("pron", "Đại từ bất định", t)
            if l in REFLEX:
                add("pron", "Đại từ phản thân", t)
            if l in POSS_PRON and tag == "PRP":
                add("pron", "Đại từ sở hữu", t)
            if l in ("one", "ones") and tag in ("NN", "NNS", "PRP") and dep not in ("nummod",) and \
                    any(c.dep_ in ("det", "amod") for c in t.children):
                add("pron", "one/ones thay cho danh từ", t)
            if l == "those" and any(c.dep_ == "relcl" and any(x.lower_ == "who" for x in c.children) for c in t.children):
                add("pron", "those who … (những người mà)", t)
            if l in ("that", "those") and d.doc[t.i + 1:t.i + 2].text.lower() == "of" and dep != "det":
                add("pron", "that/those of (thay cho danh từ đã nhắc)", t, d.doc[t.i + 1])
            # Tính từ
            if t.pos_ == "ADJ" and dep == "acomp":
                if h.lemma_ == "be":
                    add("adj", "Tính từ làm bổ ngữ sau be", h, t)
                elif h.lemma_ in LINKING:
                    add("adj", "Tính từ sau động từ nối (become/remain/seem…)", h, t)
                    add("verb", "Liên động từ (linking verb) + bổ ngữ", h, t)
            if t.pos_ == "ADJ" and dep in ("acomp", "amod", "oprd") and \
                    any(c.dep_ == "prep" and c.i == t.i + 1 for c in t.children):
                add("adj", "Tính từ + giới từ", t, d.doc[t.i + 1])
            if tag == "VBN" and dep == "amod":
                add("adj", "Tính từ dạng V3/-ed (phân từ quá khứ)", t)
            if l in FEEL_ED and t.pos_ in ("ADJ", "VERB") and dep in ("acomp", "amod"):
                add("adj", "Tính từ đuôi -ed (cảm nhận / bị tác động)", t)
            if l in FEEL_ING and t.pos_ in ("ADJ", "VERB") and dep in ("acomp", "amod"):
                add("adj", "Tính từ đuôi -ing (tính chất / gây ra)", t)
            elif tag == "VBG" and dep == "amod" and l not in FEEL_ING:
                add("adj", "Tính từ dạng V-ing (phân từ hiện tại)", t)
            if t.text == "-" and t.i > 0 and t.i + 1 < len(d.doc) and d.doc[t.i + 1].dep_ in ("amod",) or \
                    (t.text == "-" and h.dep_ == "amod"):
                add("adj", "Tính từ ghép có gạch nối", d.doc[t.i - 1], d.doc[min(t.i + 1, len(d.doc) - 1)])
            if dep in ("oprd", "ccomp", "xcomp") and t.pos_ == "ADJ" and h.lemma_ in ("make", "keep", "find", "leave", "render", "consider"):
                add("adj", "Tính từ sau tân ngữ (make/keep/find + O + adj)", h, t)
            # Trạng từ
            if t.pos_ == "ADV" and dep == "advmod":
                if l in TIME_ADV:
                    add("adv", "Trạng từ chỉ thời gian (already/recently/soon…)", t)
                if l in FREQ_ADV:
                    add("adv", "Trạng từ tần suất", t)
                if l == "also":
                    add("adv", "also (vị trí: sau be/trợ động từ, trước động từ thường)", t)
                if l == "only":
                    add("adv", "Trạng từ nhấn mạnh only", t)
                if l == "even" and h.tag_ not in ("JJR", "RBR"):
                    add("adv", "Trạng từ nhấn mạnh even", t)
                if l in APPROX_ADV:
                    add("adv", "Trạng từ chỉ mức độ xấp xỉ (nearly/almost/approximately)", t)
                if h.pos_ == "ADJ":
                    if l in DEGREE_ADV:
                        add("adv", "Trạng từ chỉ mức độ + tính từ/trạng từ", t, h)
                    elif l.endswith("ly"):
                        add("adv", "Trạng từ bổ nghĩa cho tính từ", t, h)
                elif h.pos_ == "ADV" and l.endswith("ly"):
                    add("adv", "Trạng từ bổ nghĩa cho trạng từ", t, h)
                elif h.pos_ == "VERB" and l.endswith("ly"):
                    auxs = [c for c in h.children if c.dep_ in ("aux", "auxpass")]
                    if auxs and auxs[0].i < t.i < h.i:
                        add("adv", "Trạng từ đứng giữa trợ động từ và động từ chính", auxs[0], h)
                    elif t.i < h.i and t.i != (first.i if first else -1):
                        add("adv", "Trạng từ đứng trước động từ", t, h)
                    elif t.i > h.i:
                        add("adv", "Trạng từ đứng sau động từ/tân ngữ", h, t)
                if first is not None and t.i == first.i and l.endswith("ly") and \
                        d.doc[t.i + 1:t.i + 2].text == ",":
                    add("adv", "Trạng từ đầu câu bổ nghĩa cả câu", t)
            # So sánh
            if tag in ("JJS", "RBS") or (l == "most" and h.pos_ in ("ADJ", "ADV") and dep == "advmod"):
                if l == "most" and h.pos_ not in ("ADJ", "ADV"):
                    pass
                else:
                    tgt = h if l == "most" else t
                    add("comp", "So sánh nhất (the … -est / the most …)", t, tgt)
                    prev = d.doc[max(t.i - 3, 0):t.i].text.lower()
                    if "one of the" in prev:
                        add("comp", "one of the + so sánh nhất + N số nhiều", d.doc[t.i - 3], t)
                    if "by far" in prev:
                        add("comp", "by far + so sánh nhất", d.doc[t.i - 2], t)
            if tag in ("JJR", "RBR"):
                after = d.doc[t.i + 1:min(t.i + 8, d.end)]
                if l in ("more", "fewer", "less") and t.i + 1 < d.end and d.doc[t.i + 1].tag_ in ("NN", "NNS"):
                    add("comp", "So sánh hơn với danh từ (more/fewer/less + N)", t, d.doc[t.i + 1])
                elif l in ("more", "less", "fewer") and t.i + 2 < d.end and d.doc[t.i + 1].lower_ == "than" \
                        and d.doc[t.i + 2].like_num:
                    add("comp", "more/less than + số lượng", t, d.doc[t.i + 2])
                elif any(x.lower_ == "than" for x in after):
                    add("comp", "So sánh hơn (… than)", t, next(x for x in after if x.lower_ == "than"))
                elif not (l in ("more", "less") and h.pos_ in ("ADJ", "ADV") and dep == "advmod" and False):
                    if not (l == "more" and dep == "advmod" and h.pos_ in ("ADJ", "ADV")) or True:
                        add("comp", "So sánh hơn (không có than)", t)
                if t.i > d.start and d.doc[t.i - 1].lower_ in ("much", "even", "far", "significantly",
                                                                "considerably", "slightly", "a lot", "substantially"):
                    add("comp", "Từ nhấn mạnh so sánh hơn (much/even/far/significantly)", d.doc[t.i - 1], t)
            # Cụm động từ
            if dep == "prt":
                add("phr", "Cụm động từ (V + tiểu từ)", h, t)
            # Động từ
            if dep == "dative" and h.pos_ == "VERB" and any(c.dep_ == "dobj" for c in h.children):
                add("verb", "Động từ + 2 tân ngữ (V + IO + DO)", h, max((c for c in h.children if c.dep_ == "dobj"), key=lambda c: c.i))
            if h.lemma_ in ("have", "get") and tag == "VBN" and dep in ("ccomp", "xcomp", "oprd") and \
                    any(c.dep_ in ("dobj", "nsubj", "nsubjpass") for c in t.children):
                add("verb", "Thể sai khiến have/get + O + V3", h, t)
            if lem in ("suggest", "recommend", "require", "insist", "demand", "propose", "ask", "urge"):
                cc = [c for c in t.children if c.dep_ == "ccomp" and c.tag_ == "VB"
                      and any(x.dep_ == "nsubj" for x in c.children)]
                if cc:
                    add("verb", "Câu giả định (suggest/require that + S + V nguyên mẫu)", t, cc[0])
            # To V / V-ing
            to_child = lambda x: any(c.lower_ == "to" and c.dep_ == "aux" for c in x.children)
            if dep == "xcomp" and tag == "VB" and to_child(t):
                if h.pos_ == "ADJ":
                    pre = d.doc[h.i - 1] if h.i > d.start else None
                    if pre is not None and pre.lower_ == "too" or d.doc[h.i + 1:h.i + 2].text.lower() == "enough":
                        add("inf", "too/enough + to V", h, t)
                    else:
                        add("inf", "Tính từ + to V", h, t)
                elif h.lemma_ == "be":
                    add("inf", "be + to V", h, t)
                elif h.pos_ == "VERB":
                    if any(c.dep_ == "dobj" for c in h.children):
                        add("inf", "Động từ + O + to V", h, t)
                    else:
                        add("inf", "Động từ + to V", h, t)
            if dep == "ccomp" and tag == "VB" and to_child(t) and h.pos_ == "VERB" and \
                    any(c.dep_ in ("nsubj",) for c in t.children):
                add("inf", "Động từ + O + to V", h, t)
            if dep == "advcl" and tag == "VB" and to_child(t):
                pre = d.doc[t.i - 3:t.i].text.lower()
                if "in order to" in pre or "so as to" in pre:
                    add("inf", "In order to / so as to + V (mục đích)", d.doc[t.i - 3], t)
                else:
                    add("inf", "To V chỉ mục đích", d.doc[t.i - 1], t)
            if dep in ("acl", "relcl") and tag == "VB" and to_child(t) and h.pos_ in ("NOUN", "PRON", "PROPN"):
                add("inf", "Danh từ/đại từ + to V (bổ nghĩa)", h, t)
            if tag == "VB" and to_child(t) and t.i >= 2 and d.doc[t.i - 2].lower_ in ("how", "what", "where", "which", "whether", "when"):
                add("inf", "Từ để hỏi + to V (how/what/where/which to V)", d.doc[t.i - 2], t)
            if dep == "pcomp" and tag == "VBG":
                if h.lower_ == "to":
                    add("inf", "To (giới từ) + V-ing (look forward to / committed to…)", h, t)
                else:
                    add("inf", "Giới từ + V-ing", h, t)
            if dep in ("xcomp", "ccomp") and tag == "VBG" and h.pos_ == "VERB" and h.lemma_ not in ("be", "go", "keep") \
                    and not to_child(t):
                add("inf", "Động từ + V-ing", h, t)
            if dep in ("csubj", "nsubj", "nsubjpass") and tag == "VBG":
                add("inf", "V-ing (danh động từ) làm chủ ngữ", t, h)
                add("sva", "V-ing làm chủ ngữ → động từ số ít", t, h)
            if dep in ("ccomp", "xcomp") and tag == "VB" and not to_child(t) and h.lemma_ in ("let", "help", "make", "have", "see", "watch", "hear"):
                add("inf", "%s + O + V nguyên mẫu (không to)" % h.lemma_, h, t)
            # Giới từ
            if dep == "prep" and t.pos_ == "ADP":
                pobj = next((c for c in t.children if c.dep_ == "pobj"), None)
                if pobj is not None:
                    is_time = pobj.ent_type_ in ("DATE", "TIME") or pobj.lemma_.lower() in TIME_WORDS or pobj.like_num and len(pobj.text) == 4
                    two = d.doc[t.i:t.i + 2].text.lower(); three = d.doc[t.i - 1:t.i + 1].text.lower() if t.i > 0 else ""
                    if is_time and l in TIME_PREPS:
                        add("prep", "Giới từ chỉ thời gian (%s)" % l, t, pobj)
                    elif l in PLACE_PREPS and (pobj.ent_type_ in ("GPE", "LOC", "FAC", "ORG") or
                                               pobj.lemma_.lower() in ("area", "region", "city", "country",
                                               "world", "place", "room", "building", "field", "site", "town",
                                               "village", "sea", "ocean", "river", "land", "ground", "air",
                                               "water", "forest", "street", "home", "school", "office",
                                               "laboratory", "lab", "island", "coast", "desert", "europe",
                                               "earth", "environment", "space", "surface", "museum", "wall",
                                               "garden", "soil", "cave", "valley", "mountain", "park")):
                        add("prep", "Giới từ chỉ nơi chốn (%s)" % l, t, pobj)
                    elif h.pos_ == "VERB" and l not in ("of",) and (h.lemma_, l) not in VOP and h.i < t.i and \
                            not any(c.dep_ == "dobj" and c.i < t.i for c in h.children):
                        add("prep", "Động từ + giới từ (collocation)", h, t)
                    elif h.pos_ == "NOUN" and l not in ("of", "in", "at", "on") and h.i == t.i - 1:
                        add("prep", "Danh từ + giới từ (collocation)", h, t)
                    if h.pos_ == "VERB" and (h.lemma_, l) in VOP and any(c.dep_ == "dobj" and c.i < t.i for c in h.children):
                        add("prep", "Động từ + tân ngữ + giới từ (thank sb for, provide sb with…)", h, t)
            # Mạo từ
            if l == "an" and t.i + 1 < len(d.doc):
                nx = d.doc[t.i + 1].lower_
                if nx.startswith(("hour", "honest", "honour", "honor", "heir")):
                    add("art", "an + h câm (an hour/an honor)", t, d.doc[t.i + 1])
                else:
                    add("art", "an + nguyên âm", t, d.doc[t.i + 1])
            if l == "a" and t.i + 1 < len(d.doc) and re.match(r"(uni|use|usu|eu|one\b|one-|once|ubiq|uti)", d.doc[t.i + 1].lower_):
                add("art", "a + âm /j/ hoặc /w/ (a unique/a university/a one-)", t, d.doc[t.i + 1])
            if l == "the" and t.i + 1 < len(d.doc):
                nx = d.doc[t.i + 1]
                if nx.tag_ in ("JJS", "RBS") or nx.lower_ in ("only", "same", "following", "first", "second",
                                                               "third", "last", "next", "most") or \
                        (nx.ent_type_ == "ORDINAL"):
                    add("art", "the + so sánh nhất / số thứ tự / only / same / following", t, nx)
            # Lượng từ
            if dep in ("det", "amod", "nummod") and l in QUANT_DET and h.pos_ in ("NOUN", "PROPN"):
                if not (l == "no" and h.lower_ == "one"):
                    add("quant", QUANT_DET[l], t, h)
            if l in ("whole", "entire") and t.i > 0 and d.doc[t.i - 1].lower_ == "the":
                add("quant", "the whole/entire + N", d.doc[t.i - 1], h)
            if l == "enough" and dep == "advmod" and h.pos_ in ("ADJ", "ADV"):
                add("quant", "adj/adv + enough", h, t)
            if l in ("some", "many", "all", "most", "both", "several", "few") and dep in ("nsubj", "dobj", "pobj", "nsubjpass") \
                    and not any(c.dep_ == "prep" for c in t.children):
                add("quant", "%s dùng như đại từ" % l, t)
        # cụm từ cố định / nhiều từ
        for q in QUANT_OF:
            for m in re.finditer(r"\b%s of (the|my|your|his|her|its|our|their|these|those|this|that)\b" % re.escape(q), low):
                add_span(T, d, m.start(), m.end(), "quant", "%s of + the/tính từ sở hữu + N" % q)
        for pat, lab in ((r"\ba lot of\b", "a lot of + N"), (r"\blots of\b", "lots of + N"),
                         (r"\bplenty of\b", "plenty of + N"), (r"\ba few\b", "a few + N"), (r"\ba little\b", "a little + N")):
            for m in re.finditer(pat, low):
                add_span(T, d, m.start(), m.end(), "quant", lab)
        for cp in COMPOUND_PREP:
            for m in re.finditer(r"\b%s\b" % re.escape(cp), low):
                add_span(T, d, m.start(), m.end(), "prep", "Giới từ kép / cụm giới từ")
        for m in re.finditer(r"\bsuch as\b", low):
            add_span(T, d, m.start(), m.end(), "prep", "such as (ví dụ như) + N")
        for m in re.finditer(r"\bby (car|bus|train|plane|air|sea|road|rail|email|post|phone|hand|foot|boat|ship)\b", low):
            add_span(T, d, m.start(), m.end(), "prep", "by + phương tiện/cách thức (không mạo từ)")
            add_span(T, d, m.start(), m.end(), "art", "Không dùng mạo từ: by + phương tiện")
        for pat, lab in ((r"\bas well as\b", "as well as (cũng như)"), (r"\brather than\b", "rather than (thay vì)"),
                         (r"\bboth\b.+?\band\b", "Liên từ tương quan both … and"),
                         (r"\beither\b.+?\bor\b", "Liên từ tương quan either … or"),
                         (r"\bneither\b.+?\bnor\b", "Liên từ tương quan neither … nor"),
                         (r"\bwhether\b.+?\bor\b", "Liên từ tương quan whether … or"),
                         (r"\bnot only\b.+?\bbut( also)?\b", "Liên từ tương quan not only … but (also)")):
            for m in re.finditer(pat, low):
                if len(m.group(0)) < 120:
                    add_span(T, d, m.start(), m.end(), "conj", lab)
        for pat, lab in ((r"\bas (\w+ )?(much|many) \w+ as\b", "as many/much + N + as"),
                         (r"\bnot (as|so) \w+ as\b", "So sánh không bằng (not as … as)"),
                         (r"\bas \w+(ly)? as\b", "So sánh ngang bằng (as … as)"),
                         (r"\bthe same( \w+)? as\b", "the same (N) as"),
                         (r"\b(similar to|different from|compared (with|to)|identical to|superior to|inferior to)\b",
                          "Cấu trúc so sánh khác (similar to/different from…)")):
            for m in re.finditer(pat, low):
                add_span(T, d, m.start(), m.end(), "comp", lab)
                if lab.startswith("So sánh không"):
                    break
        # liên từ / trạng từ liên kết
        for ca in CONJ_ADV:
            if re.match(r"%s\b" % re.escape(ca), low):
                add_span(T, d, 0, len(ca), "conj", "Trạng từ liên kết đầu câu")
            else:
                for m in re.finditer(r"[;,] %s\b" % re.escape(ca), low):
                    add_span(T, d, m.start() + 2, m.end(), "conj", "Trạng từ liên kết giữa câu")
        for t in toks:
            if t.dep_ == "cc" and t.lower_ in ("and", "but", "or"):
                conj = next((c for c in t.head.children if c.dep_ == "conj" and c.i > t.i), None)
                if conj is None:
                    continue
                if conj.pos_ in ("VERB", "AUX") and t.head.pos_ in ("VERB", "AUX"):
                    if any(c.dep_ in ("nsubj", "nsubjpass", "expl") for c in conj.children):
                        add_tok(T, d, t, conj, "conj", "Liên từ đẳng lập nối 2 mệnh đề (%s)" % t.lower_)
                    elif t.lower_ == "and":
                        add_tok(T, d, t.head, conj, "conj", "and nối 2 động từ/cụm động từ song song")
                    else:
                        add_tok(T, d, t, conj, "conj", "Liên từ đẳng lập (%s)" % t.lower_)
                elif t.lower_ in ("but", "or"):
                    add_tok(T, d, t, conj, "conj", "Liên từ đẳng lập (%s)" % t.lower_)
            if t.dep_ == "mark" and t.lower_ not in ("that", "to", "whether", "if") and t.head.dep_ == "advcl":
                add_tok(T, d, t, t, "conj", "Liên từ phụ thuộc")

        # ---------- mệnh đề
        n_sub = 0
        for t in toks:
            dep, h = t.dep_, t.head
            kids = list(t.children)
            mark = next((c for c in kids if c.dep_ == "mark"), None)
            mk = mark.lower_ if mark is not None else ""
            if mark is not None and t.i + 1 > mark.i and d.doc[mark.i + 1:mark.i + 2].text.lower() in ("though", "if", "that", "as") \
                    and mk in ("even", "so", "as", "in"):
                mk = mk + " " + d.doc[mark.i + 1].lower_
            has_subj = any(c.dep_ in ("nsubj", "nsubjpass", "expl") for c in kids)
            if dep == "acl" and t.tag_ == "VBN" and h.pos_ in ("NOUN", "PROPN", "PRON"):
                add_tok(T, d, h, t, "clause", "Rút gọn MĐQH bị động (N + V3)")
            elif dep == "acl" and t.tag_ == "VBG" and h.pos_ in ("NOUN", "PROPN", "PRON"):
                add_tok(T, d, h, t, "clause", "Rút gọn MĐQH chủ động (N + V-ing)")
            elif dep == "relcl":
                n_sub += 1
                rel = next((c for c in t.subtree if c.tag_ in ("WDT", "WP", "WP$", "WRB") or
                            (c.lower_ == "that" and c.dep_ in ("nsubj", "dobj", "nsubjpass", "pobj"))), None)
                start = min(c.i for c in t.subtree)
                comma = start > d.start and d.doc[start - 1].text == ","
                if rel is None:
                    add_tok(T, d, h, t, "clause", "MĐQH lược bỏ đại từ quan hệ (tân ngữ)")
                else:
                    r = rel.lower_
                    if rel.head.dep_ == "prep" or (rel.dep_ == "pobj"):
                        prep = rel.head
                        add_tok(T, d, prep, t, "clause", "MĐQH giới từ + which" if r == "which" else "MĐQH giới từ + %s" % r)
                    elif r in ("who", "whom", "which", "where", "whose", "when", "that", "why"):
                        lab = "MĐQH với %s" % r
                        if comma and r != "that":
                            lab += " (không xác định, có dấu phẩy)"
                        add_tok(T, d, rel, t, "clause", lab)
                    elif r.startswith("wh") and r.endswith("ever"):
                        add_tok(T, d, rel, t, "clause", "Đại từ/trạng từ quan hệ kép (%s)" % r)
            elif dep in ("ccomp", "csubj", "pcomp", "dobj", "nsubj", "attr", "pobj") and t.pos_ in ("VERB", "AUX") and \
                    (has_subj or dep == "ccomp") and t.tag_ not in ("VBG",) and not (t.tag_ == "VB" and any(c.lower_ == "to" for c in kids)):
                wh = next((c for c in t.subtree if c.tag_ in ("WP", "WRB", "WDT") and c.i < t.i), None)
                if dep == "ccomp" and h.pos_ not in ("VERB", "AUX", "ADJ", "NOUN"):
                    continue
                n_sub += 1
                if mk == "that":
                    add_tok(T, d, mark, t, "clause", "Mệnh đề danh từ với that")
                elif mk in ("if", "whether"):
                    add_tok(T, d, mark, t, "clause", "Mệnh đề danh từ với %s" % mk)
                elif wh is not None and wh.lower_ in ("what", "when", "how", "why", "where", "who", "which"):
                    add_tok(T, d, wh, t, "clause", "Mệnh đề danh từ với từ để hỏi (%s)" % wh.lower_)
                elif wh is not None and wh.lower_.endswith("ever"):
                    add_tok(T, d, wh, t, "clause", "Đại từ/trạng từ quan hệ kép (%s)" % wh.lower_)
                elif dep == "ccomp" and h.lemma_ in REPORT and has_subj:
                    add_tok(T, d, h, t, "clause", "Mệnh đề danh từ (lược that)")
                if dep == "pcomp" or (dep == "pobj" and h.dep_ == "prep"):
                    add_tok(T, d, h, t, "clause", "Mệnh đề danh từ sau giới từ")
                if dep == "csubj":
                    add_tok(T, d, t, h, "clause", "Mệnh đề danh từ làm chủ ngữ")
            elif dep == "advcl":
                n_sub += 1 if (has_subj or mark is not None) else 0
                if not has_subj and t.tag_ == "VBG":
                    if mark is not None:
                        add_tok(T, d, mark, t, "clause", "Rút gọn MĐ trạng ngữ (liên từ + V-ing)")
                    else:
                        add_tok(T, d, t, t, "clause", "Rút gọn MĐ trạng ngữ bằng V-ing (phân từ hiện tại)")
                elif not has_subj and t.tag_ == "VBN" and mark is None:
                    add_tok(T, d, t, t, "clause", "Rút gọn MĐ trạng ngữ bằng V3 (phân từ quá khứ)")
                elif mark is not None and has_subj:
                    if mk in ("if", "unless", "provided", "providing", "as long as"):
                        pass
                    elif mk == "as":
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ với as (vì/khi/như)")
                    elif mk == "while":
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ với while (trong khi/mặc dù)")
                    elif mk in SUB_TIME:
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ chỉ thời gian")
                    elif mk == "since":
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ chỉ nguyên nhân/thời gian")
                    elif mk in SUB_CAUSE:
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ chỉ nguyên nhân")
                    elif mk in SUB_CONC or mk == "even though":
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ chỉ nhượng bộ")
                    elif mk in SUB_PURP or mk == "so that":
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ chỉ mục đích")
                    elif mk in ("so", "such"):
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ chỉ kết quả (so/such … that)")
                    elif mk == "whether":
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ với whether (dù... hay không)")
                    elif mk in ("as if", "as though"):
                        add_tok(T, d, mark, t, "clause", "MĐ trạng ngữ chỉ thể cách")
        for m in re.finditer(r"\b(so|such)\b[^.;]{1,40}?\bthat\b", low):
            add_span(T, d, m.start(), m.end(), "clause", "MĐ trạng ngữ chỉ kết quả (so/such … that)")
        for m in re.finditer(r"\bin case\b", low):
            add_span(T, d, m.start(), m.end(), "clause", "MĐ trạng ngữ chỉ điều kiện (phòng khi)")

        # ---------- câu
        root = d.root
        indep = [t for t in toks if t.dep_ == "conj" and t.pos_ in ("VERB", "AUX") and t.head == root
                 and any(c.dep_ in ("nsubj", "nsubjpass", "expl") for c in t.children)]
        semi = ";" in d.text
        compound = bool(indep) or semi
        if compound and n_sub:
            add_tok(T, d, root, root, "sent", "Câu phức hợp (ghép + phức)")
        elif compound:
            add_tok(T, d, root, root, "sent", "Câu ghép (2 mệnh đề độc lập)")
        elif n_sub:
            add_tok(T, d, root, root, "sent", "Câu phức (mệnh đề chính + mệnh đề phụ)")
        else:
            add_tok(T, d, root, root, "sent", "Câu đơn")
        if d.text.strip().endswith("?"):
            add_tok(T, d, root, root, "sent", "Câu hỏi (trong bài đọc)")
            aux = next((c for c in root.children if c.dep_ in ("aux", "auxpass")), None)
            subj = next((c for c in root.children if c.dep_ in ("nsubj", "nsubjpass")), None)
            if aux is not None and subj is not None and aux.i < subj.i:
                add_tok(T, d, aux, subj, "inv", "Đảo ngữ trong câu hỏi (trợ động từ + S)")
        # điều kiện
        for t in toks:
            if t.dep_ == "advcl":
                mk = next((c.lower_ for c in t.children if c.dep_ == "mark"), "")
                if mk in ("if", "unless"):
                    add_tok(T, d, next(c for c in t.children if c.dep_ == "mark"), t, "sent", "Câu điều kiện")
                    main = t.head
                    ma = [c for c in main.children if c.dep_ in ("aux", "auxpass")]
                    ia = [c for c in t.children if c.dep_ in ("aux", "auxpass")]
                    mal = [a.lower_ for a in ma]
                    if any(a.lemma_ == "have" and a.tag_ == "VBD" for a in ia) and any(x in ("would", "could", "might") for x in mal) and "have" in mal:
                        lab = "Câu điều kiện loại 3 (If + had V3, would have V3)"
                    elif (t.tag_ == "VBD" or any(a.tag_ == "VBD" for a in ia) or t.lower_ == "were") and any(x in ("would", "could", "might") for x in mal):
                        lab = "Câu điều kiện loại 2 (If + quá khứ, would/could + V)"
                    elif t.tag_ in ("VBZ", "VBP") and any(x in ("will", "can", "may", "'ll") for x in mal):
                        lab = "Câu điều kiện loại 1 (If + hiện tại, will/can/mệnh lệnh)"
                    elif t.tag_ in ("VBZ", "VBP") and main.tag_ in ("VBZ", "VBP") and not ma:
                        lab = "Câu điều kiện loại 0 (sự thật hiển nhiên)"
                    else:
                        lab = None
                    if lab:
                        add_tok(T, d, t, main, "sent", lab)
        if re.match(r"it (is|was|has been|seems|seemed|appears|would be|may be|might be|can be|will be) ", low):
            add_span(T, d, 0, len(low.split(" ")[0]) + 1 + len(low.split(" ")[1]), "sent",
                     "Chủ ngữ giả It (It is + adj/N + to V/that)")
        if re.match(r"(it is|it was) [^,]{1,40}? (that|who) ", low) and not re.match(r"it (is|was) (\w+ly )?\w+ (that|to) ", low):
            add_span(T, d, 0, 10, "sent", "Câu chẻ (It is … that/who — nhấn mạnh)")
        for t in toks:
            if t.dep_ == "expl" and t.lower_ == "there" and t.head.lemma_ == "be":
                subj = next((c for c in t.head.children if c.dep_ in ("attr", "nsubj")), None)
                if subj is not None:
                    add_tok(T, d, t, subj, "sva", "There + be + N (động từ chia theo danh từ phía sau)")
        # Hòa hợp chủ ngữ – động từ
        for t in toks:
            if t.dep_ not in ("nsubj", "nsubjpass") or t.head.tag_ not in ("VBZ", "VBP") and \
                    not any(a.tag_ in ("VBZ", "VBP") for a in t.head.children if a.dep_ in ("aux", "auxpass")):
                continue
            v = t.head
            kids = list(t.children)
            if any(c.dep_ == "prep" for c in kids) and t.pos_ in ("NOUN", "PROPN"):
                if t.lower_ in ("most", "all", "half", "majority", "some", "rest", "none", "proportion", "percentage"):
                    add_tok(T, d, t, v, "sva", "most/all/half/majority of + N → động từ chia theo N sau of" if t.lower_ != "none"
                            else "none of + N → động từ (thường) số ít")
                else:
                    add_tok(T, d, t, v, "sva", "Chủ ngữ chính đứng trước cụm giới từ xen giữa → chia theo chủ ngữ chính")
            elif any(c.dep_ in ("relcl", "acl") for c in kids):
                add_tok(T, d, t, v, "sva", "Chủ ngữ chính đứng trước mệnh đề/cụm phân từ xen giữa → chia theo chủ ngữ chính")
            if any(c.dep_ == "conj" for c in kids) and any(c.lower_ == "and" for c in kids):
                add_tok(T, d, t, v, "sva", "Chủ ngữ ghép A and B → động từ số nhiều")
            if t.lemma_.lower() in COLLECTIVE:
                add_tok(T, d, t, v, "sva", "Danh từ tập hợp làm chủ ngữ (staff/team/committee…)")
            if t.lower_ in INDEF_PRON:
                add_tok(T, d, t, v, "sva", "Đại từ bất định làm chủ ngữ → động từ số ít")
            if any(c.lower_ in ("each", "every") and c.dep_ == "det" for c in kids):
                add_tok(T, d, t, v, "sva", "Each/Every + N số ít → động từ số ít")
        # Đảo ngữ (câu khẳng định)
        for p in NEG_INV:
            if re.match(r"%s\b" % re.escape(p), low):
                aux = next((x for x in toks[1:8] if x.tag_ in ("MD", "VBZ", "VBP", "VBD") and x.lemma_ in
                            ("be", "have", "do", "can", "could", "will", "would", "should", "may", "might", "must")), None)
                subj = next((x for x in toks if x.dep_ in ("nsubj", "nsubjpass")), None)
                if aux is not None and subj is not None and aux.i < subj.i:
                    add_tok(T, d, toks[0], subj, "inv", "Đảo ngữ với trạng từ phủ định/hạn chế đầu câu (Never/Rarely/Not only…)")
                break
        if re.match(r"(had|were|should) \w+", low) and not d.text.strip().endswith("?"):
            subj = next((x for x in toks if x.dep_ in ("nsubj", "nsubjpass")), None)
            if subj is not None and subj.i == toks[1].i:
                add_tok(T, d, toks[0], subj, "inv", "Đảo ngữ câu điều kiện (Had/Were/Should + S…)")
        if re.match(r"(here|there) (is|are|comes|come|was|were) ", low) and toks[0].dep_ != "expl":
            add_span(T, d, 0, 8, "inv", "Đảo ngữ Here is/are + N")
        for t in toks:
            if t.dep_ in ("nsubj", "nsubjpass") and t.head.i < t.i and t.head.pos_ in ("VERB", "AUX") and \
                    not d.text.strip().endswith("?") and t.head.lemma_ in ("be", "come", "lie", "stand", "remain") and \
                    toks[0].dep_ in ("advmod", "prep", "acomp", "attr") and toks[0].lower_ not in ("there", "here"):
                add_tok(T, d, toks[0], t, "inv", "Đảo ngữ trạng ngữ/bổ ngữ đầu câu (đảo động từ chính)")
                break
        # Phối hợp thì
        for t in toks:
            if t.lemma_ in REPORT and t.tag_ == "VBD":
                cc = next((c for c in t.children if c.dep_ == "ccomp"), None)
                if cc is None:
                    continue
                aux = [c for c in cc.children if c.dep_ in ("aux", "auxpass")]
                if cc.tag_ == "VBD" or any(a.tag_ in ("VBD", "MD") and a.lower_ in ("was", "were", "had", "would", "could", "might", "should", "did") for a in aux):
                    add_tok(T, d, t, cc, "seq", "Lùi thì sau động từ tường thuật ở quá khứ")
                elif cc.tag_ in ("VBZ", "VBP") or any(a.tag_ in ("VBZ", "VBP") or a.lower_ in ("will", "can") for a in aux):
                    add_tok(T, d, t, cc, "seq", "Không lùi thì (sự việc vẫn đúng/chưa xảy ra)")
        for t in toks:
            if t.tag_ == "VBN" and any(a.lower_ == "had" for a in t.children if a.dep_ == "aux"):
                other = [x for x in toks if x.tag_ == "VBD" and x.dep_ in ("advcl", "ROOT", "conj", "ccomp") and x != t]
                if other:
                    add_tok(T, d, t, other[0], "seq", "Quá khứ hoàn thành (xảy ra trước) + quá khứ đơn")
                    break
        for t in toks:
            if t.dep_ == "advcl":
                mk = next((c.lower_ for c in t.children if c.dep_ == "mark"), "")
                ma = [c.lower_ for c in t.head.children if c.dep_ == "aux"]
                if mk in ("when", "before", "after", "until", "once", "as soon as") and t.tag_ in ("VBZ", "VBP") and \
                        any(x in ("will", "'ll") for x in ma):
                    add_tok(T, d, t, t.head, "seq", "MĐ thời gian dùng hiện tại thay cho tương lai")
        return T


def add_tok(T, d, a, b, ch, label):
    lo, hi = (a, b) if a.i <= b.i else (b, a)
    T.append((ch, label, lo.idx - d.start_char, hi.idx + len(hi.text) - d.start_char))


def add_span(T, d, s, e, ch, label):
    T.append((ch, label, s, e))


# ---------------------------------------------------------------- render
def bold(text, s, e):
    s = max(0, min(s, len(text))); e = max(s, min(e, len(text)))
    if e - s > 160:
        e = s + 160
    return text[:s] + "**" + text[s:e].strip() + "**" + text[e:] if text[s:e].strip() else text


def mdesc(text):
    return text.replace("*", "\\*").replace("_", "\\_").replace("|", "\\|")


def main():
    nlp = spacy.load("en_core_web_sm")
    tagger = Tagger(nlp)
    files = sorted(f for f in os.listdir(SRC) if re.fullmatch(r"cleaned_cam(\d+)_test(\d)\.html", f))
    sents = []           # dict(cam, test, p, title, text, tags)
    for f in files:
        cam, test = map(int, re.fullmatch(r"cleaned_cam(\d+)_test(\d)\.html", f).groups())
        for no, title, paras in extract_test(os.path.join(SRC, f)):
            for para in paras:
                for s in nlp(para).sents:
                    txt = s.text.strip()
                    if len(txt.split()) < 4:
                        continue
                    tags = tagger.tags(s)
                    lead = len(s.text) - len(s.text.lstrip())
                    tags = [(c, l, a - lead, b - lead) for c, l, a, b in tags]
                    sents.append(dict(cam=cam, test=test, p=no, title=title, text=txt, tags=tags))
        print(f, len(sents), flush=True)

    # gom theo chương / điểm
    by = defaultdict(lambda: defaultdict(list))     # ch -> label -> [(sent, s, e)]
    for st in sents:
        seen = set()
        for ch, lab, a, b in st["tags"]:
            if (ch, lab) in seen:
                continue
            seen.add((ch, lab))
            by[ch][lab].append((st, a, b))
    order = {c[0]: i for i, c in enumerate(CHAPTERS)}
    labels = {ch: sorted(by[ch], key=lambda l: -len(by[ch][l])) for ch in by}
    lid = {(ch, l): "p%d" % (i + 1) for ch in labels for i, l in enumerate(labels[ch])}
    src = lambda st: "Cam %d · T%d · P%d" % (st["cam"], st["test"], st["p"])
    cams = sorted({st["cam"] for st in sents})
    ntests = len({(st["cam"], st["test"]) for st in sents})

    # ---- bản đồ
    L = []
    L.append("# 🗺️ Bản đồ ngữ pháp IELTS Reading — Cambridge %d–%d, map vào 19 chương\n" % (cams[0], cams[-1]))
    L.append("> Mình đã cho máy phân tích **%s câu** trong **%d đề** IELTS Reading (Cambridge %d–%d, mỗi đề 3 passage — chỉ lấy "
             "bài đọc, không lấy câu hỏi) và gắn nhãn từng điểm ngữ pháp. Sau đó gom các câu theo **đúng thứ tự 19 chương** "
             "của trang [📖 Xem Tất Cả](all.md) — cùng cách làm với [🗺️ Bản đồ ngữ pháp ETS](ets-ngu-phap-ban-do.md).\n>\n"
             "> **Cách học để master:** ① đọc lý thuyết một chương trong Xem Tất Cả → ② mở bảng của chương đó bên dưới, thấy "
             "điểm nào **xuất hiện nhiều nhất** trong bài đọc IELTS thật → ③ đọc ví dụ ngay dưới mỗi điểm, tự giải thích phần "
             "**in đậm** → ④ vào trang phân tích **từng câu** của từng cuốn Cam để luyện nhận diện mọi điểm ngữ pháp trong một câu "
             "học thuật dài.\n>\n"
             "> ⚠️ Nhãn được gắn tự động bằng bộ phân tích cú pháp (spaCy) nên có thể sai khoảng 5–10%%, nhất là với câu rất "
             "dài nhiều mệnh đề.\n" % ("{:,}".format(len(sents)), ntests, cams[0], cams[-1]))
    L.append("**Phân tích từng câu theo cuốn:** " + " · ".join("[Cam %d](ielts-ngu-phap-cam-%d.md)" % (c, c) for c in cams) + "\n")
    L.append("## 📊 Tổng quan: chương nào xuất hiện nhiều nhất trong bài đọc IELTS\n")
    L.append("| # | Chương (bấm để học lý thuyết) | Số lần xuất hiện | Số điểm ngữ pháp con |\n|---|---|---|---|")
    for i, (cid, emo, short, full, th) in enumerate(CHAPTERS, 1):
        n = sum(len(v) for v in by[cid].values())
        L.append("| %d | %s [%s](#%s) · [lý thuyết](%s) | %s | %d |" % (i, emo, short, cid, link(th), "{:,}".format(n), len(by[cid])))
    L.append("\n---\n")
    for i, (cid, emo, short, full, th) in enumerate(CHAPTERS, 1):
        n = sum(len(v) for v in by[cid].values())
        L.append('<a id="%s"></a>\n\n## %d. %s %s\n' % (cid, i, emo, full))
        L.append("> 📚 Lý thuyết: [%s](%s) · %s lần xuất hiện trong %d đề · 📋 [**Xem FULL câu của chương**](ielts-ngu-phap-full-%s.md)\n"
                 % (full, link(th), "{:,}".format(n), ntests, cid))
        if not by[cid]:
            L.append("_Không gặp trong bài đọc._\n\n---\n")
            continue
        L.append("| Điểm ngữ pháp (bấm để xem full câu) | Số câu |\n|---|---|")
        for lab in labels[cid]:
            L.append("| [%s](ielts-ngu-phap-full-%s.md?id=%s) | %d |" % (mdesc(lab), cid, lid[(cid, lab)], len(by[cid][lab])))
        L.append("\n### 📌 Ví dụ cho từng điểm ngữ pháp\n")
        for lab in labels[cid]:
            items = by[cid][lab]
            L.append("**▸ %s** <small>(%d câu)</small>\n" % (mdesc(lab), len(items)))
            step = max(1, len(items) // EX)
            for st, a, b in items[::step][:EX]:
                L.append("- 📖 *(%s)* %s" % (src(st), bold(st["text"], a, b)))
            L.append("\n> 👉 [**Xem FULL %d câu** của mẫu này](ielts-ngu-phap-full-%s.md?id=%s)\n"
                     % (len(items), cid, lid[(cid, lab)]))
        L.append("---\n")
    open(os.path.join(DOCS, "ielts-ngu-phap-ban-do.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    # ---- full theo chương
    for i, (cid, emo, short, full, th) in enumerate(CHAPTERS, 1):
        F = ["# %s %d. %s — full câu ví dụ IELTS Reading (Cam %d–%d)\n" % (emo, i, full, cams[0], cams[-1]),
             "> Câu trong bài đọc IELTS có chứa điểm ngữ pháp của chương này, phần ngữ pháp được **in đậm**. Lý thuyết: "
             "[%s](%s) · quay lại [🗺️ Bản đồ ngữ pháp IELTS](ielts-ngu-phap-ban-do.md?id=%s). Mỗi điểm hiện tối đa %d câu "
             "(trải đều các cuốn).\n>\n> ⚠️ Nhãn gắn tự động (spaCy), có thể sai khoảng 5–10%%.\n" % (full, link(th), cid, CAP),
             "## Mục lục\n"]
        for k, lab in enumerate(labels.get(cid, []), 1):
            F.append("%d. [%s](ielts-ngu-phap-full-%s.md?id=%s) — %d câu" % (k, mdesc(lab), cid, lid[(cid, lab)], len(by[cid][lab])))
        F.append("\n---\n")
        for k, lab in enumerate(labels.get(cid, []), 1):
            items = by[cid][lab]
            F.append('<a id="%s"></a>\n\n### %d. %s\n' % (lid[(cid, lab)], k, mdesc(lab)))
            shown = items if len(items) <= CAP else items[::max(1, len(items) // CAP)][:CAP]
            F.append("<small>%d câu%s</small>\n" % (len(items), (" · hiện %d" % len(shown)) if len(shown) < len(items) else ""))
            for st, a, b in shown:
                F.append("- *(%s)* %s" % (src(st), bold(st["text"], a, b)))
            F.append("")
        open(os.path.join(DOCS, "ielts-ngu-phap-full-%s.md" % cid), "w", encoding="utf-8").write("\n".join(F) + "\n")

    # ---- từng câu theo cuốn
    for cam in cams:
        S = [st for st in sents if st["cam"] == cam]
        P = ["# 🧭 Cam %d — Phân tích ngữ pháp từng câu (IELTS Reading)\n" % cam,
             "> Mỗi câu trong 4 test của Cambridge IELTS %d (3 passage/test) được **map vào đúng chương** trong "
             "[📖 Xem Tất Cả](all.md). Bấm tên chương để xem lý thuyết. Tổng: **%d câu**.\n>\n"
             "> ⚠️ Nhãn gắn tự động bằng spaCy nên có thể sai ~5–10%%.\n" % (cam, len(S)),
             "**Các cuốn:** " + " · ".join(("**Cam %d**" % c) if c == cam else "[Cam %d](ielts-ngu-phap-cam-%d.md)" % (c, c)
                                          for c in cams) + " · [🗺️ Bản đồ ngữ pháp tổng hợp](ielts-ngu-phap-ban-do.md)\n"]
        cur = None
        k = 0
        for st in S:
            key = (st["test"], st["p"])
            if key != cur:
                cur = key
                k = 0
                P.append("\n## 📖 Test %d — Passage %d%s\n" % (st["test"], st["p"], (": " + st["title"]) if st["title"] else ""))
            k += 1
            P.append("**Câu %d.** %s\n" % (k, mdesc(st["text"])))
            grp = defaultdict(list)
            for ch, lab, a, b in st["tags"]:
                frag = st["text"][max(0, a):max(a, b)].strip()
                if len(frag) > 70:
                    frag = frag[:67] + "…"
                item = "%s *%s*" % (mdesc(lab), mdesc(frag)) if frag else mdesc(lab)
                if item not in grp[ch]:
                    grp[ch].append(item)
            lines = []
            for cid in sorted(grp, key=lambda c: order[c]):
                c = CH[cid]
                lines.append("> %s [%s](%s): %s" % (c[1], c[2], link(c[4]), " · ".join(grp[cid][:6])))
            P.append("\n>\n".join(lines) + "\n")
        open(os.path.join(DOCS, "ielts-ngu-phap-cam-%d.md" % cam), "w", encoding="utf-8").write("\n".join(P) + "\n")

    tot = Counter(ch for st in sents for ch, *_ in st["tags"])
    print("cau:", len(sents), "| de:", ntests, "| nhan theo chuong:", dict(tot))


if __name__ == "__main__":
    sys.exit(main())
