#!/usr/bin/env python3
"""Idioms, Phrasal Verbs & Natural Expressions Bank — dựng từ các đợt 50 cụm.

Đầu vào : tools/data/expressions/batch-NNN.json        (50 cụm/đợt, đủ 17 trường)
          tools/data/expressions/batch-NNN-extra.json  (so sánh cặp dễ nhầm + bài tập của đợt)
          phụ đề phim (xem movie_subs_study.py) — để lấy bằng chứng dùng thật
Đầu ra  : docs/expressions/*.md, *.csv (Anki), progress-index.md
          docs/tools/expressions-data.js (trang docs/tools/expressions-bank.html)

Chống trùng: dừng lại báo lỗi nếu ID hoặc cụm (đã chuẩn hóa) bị lặp giữa các đợt.

    python3 tools/expressions_bank.py
"""
import csv
import glob
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "data", "expressions")
OUT_MD = os.path.join(ROOT, "docs", "expressions")
OUT_JS = os.path.join(ROOT, "docs", "tools", "expressions-data.js")
sys.path.insert(0, HERE)
from pattern_bank import norm, WORD  # noqa: E402

FILES = [  # (file, tiêu đề, tiền tố ID)
    ("idioms-master.md", "Idioms — thành ngữ", "IDIOM"),
    ("phrasal-verbs-master.md", "Phrasal verbs — cụm động từ thông dụng", "PHR"),
    ("professional-phrasal-verbs.md", "Phrasal verbs nơi công sở", "PRO-PHR"),
    ("it-english-expressions.md", "IT / software engineering expressions", "IT-EXP"),
    ("collocations-master.md", "Collocations — kết hợp từ", "COL"),
    ("fixed-expressions.md", "Fixed expressions & conversational chunks", "FIX"),
]
TARGET = {"IDIOM": 250 + 100, "PHR": 350, "PRO-PHR": 200, "IT-EXP": 150, "COL": 250, "FIX": 200}
EX_LABEL = ["Đời thường (Mỹ)", "Công việc / QA", "IELTS"]


def prefix(i):
    return i.rsplit("-", 1)[0]


def load():
    entries, extras = [], []
    seen_id, seen_ex = {}, {}
    for f in sorted(glob.glob(os.path.join(SRC, "batch-[0-9][0-9][0-9].json"))):
        d = json.load(open(f, encoding="utf-8"))
        for e in d["entries"]:
            e["batch"] = d["batch"]
            k = key_of(e["expr"])
            e.setdefault("tcode", "")
            if e["id"] in seen_id:
                sys.exit("TRÙNG ID %s (đợt %s và %s)" % (e["id"], seen_id[e["id"]], d["batch"]))
            if k in seen_ex:
                sys.exit("TRÙNG CỤM '%s' (%s và %s)" % (e["expr"], seen_ex[k], e["id"]))
            seen_id[e["id"]], seen_ex[k] = d["batch"], e["id"]
            entries.append(e)
        x = f.replace(".json", "-extra.json")
        if os.path.exists(x):
            ex = json.load(open(x, encoding="utf-8"))
            ex["batch"] = d["batch"]
            extras.append(ex)
    # các đợt sau: file TSV gọn (b*.tsv) — ID và số đợt (50 cụm/đợt) được đánh tự động theo thứ tự file
    nxt = Counter(prefix(e["id"]) for e in entries)
    batch, in_batch = max(e["batch"] for e in entries), 50
    skipped = []
    for f in sorted(glob.glob(os.path.join(SRC, "b*.tsv"))):
        pre = None
        for ln in open(f, encoding="utf-8"):
            ln = ln.rstrip("\n")
            m = re.match(r"#\s*type:\s*(\S+)", ln)
            if m:
                pre = m.group(1)
                continue
            if not ln.strip() or ln.startswith("#"):
                continue
            c = ln.split("\t")
            if len(c) != 18 or c[2].strip() in ("—", "-", ""):
                continue  # dòng giữ chỗ / lỗi cột
            k = key_of(c[0])
            if k in seen_ex:
                skipped.append("%s (%s, đã có %s)" % (c[0], os.path.basename(f), seen_ex[k]))
                continue
            nxt[pre] += 1
            if in_batch == 50:
                batch, in_batch = batch + 1, 0
            in_batch += 1
            e = dict(id="%s-%04d" % (pre, nxt[pre]), expr=c[0].strip(), type=TYPE_NAME[pre], group=c[1].strip(),
                     vi=c[2].strip(), en=c[3].strip(), func=c[4].strip(), grammar=c[5].strip(),
                     trans=TRANS.get(c[6].strip(), ""), tcode=c[6].strip(),
                     colls=[x.strip() for x in c[7].split(";") if x.strip() and x.strip() != "-"],
                     ex=[x.strip() for x in c[8:11]], register=c[11].strip(), freq=FREQ.get(c[12].strip(), c[12].strip()),
                     cefr=c[13].strip(), prio="P" + c[14].strip(), mistake=c[15].strip(), similar=c[16].strip(),
                     opposite="" if c[17].strip() == "-" else c[17].strip(), usuk="", batch=batch)
            for fld in ("mistake", "similar", "func", "grammar"):
                if e[fld] == "-":
                    e[fld] = ""
            seen_ex[k] = e["id"]
            entries.append(e)
    if skipped:
        print("bỏ %d cụm trùng:" % len(skipped), "; ".join(skipped))
    return entries, extras


TYPE_NAME = {"IDIOM": "Idiom", "PHR": "Phrasal Verb", "PRO-PHR": "Phrasal Verb", "IT-EXP": "IT Expression",
             "COL": "Collocation", "FIX": "Fixed Expression"}
FREQ = {"vc": "very common", "c": "common", "lc": "less common", "r": "rare"}
TRANS = {
    "T-S": "Ngoại động từ · TÁCH ĐƯỢC (tân ngữ đứng giữa hoặc sau; đại từ bắt buộc đứng giữa: V it up) · cần tân ngữ",
    "T-I": "Ngoại động từ · KHÔNG TÁCH (tân ngữ luôn đứng sau tiểu từ/giới từ) · cần tân ngữ",
    "I": "Nội động từ · không có tân ngữ",
    "I/T-S": "Vừa nội vừa ngoại động từ · khi có tân ngữ thì tách được (đại từ đứng giữa)",
}


def key_of(expr):
    k = re.sub(r"\(.*?\)|[^a-z' ]", " ", expr.lower().replace("’", "'"))
    return " ".join(k.split())


# chỗ chen tân ngữ (figure IT out, push THE RELEASE back): 0–3 từ, không phải giới từ / liên từ
GAP = r"(?: (?!(?:of|to|and|but|or|so|because|if|when|in|at|on|for|with|from|like)\b)\S+){0,3}"
STOP = set("a an the it to of in on for with and or your my his her their our this that someone something sb sth be is are".split())


def compile_rx(spec):
    alts = []
    for alt in spec.split(";"):
        parts = []
        for t in alt.split():
            if t == "^":
                parts.append("^")
            elif t == "~":
                parts.append(GAP)
            elif t == "*":
                parts.append("(?: \\S+)")
            else:
                parts.append(" (?:%s)" % "|".join(re.escape(norm(x)) for x in t.split("|")))
        alts.append("".join(parts))
    return re.compile("(?:%s) " % "|".join(alts))


IRREG = {"be": "am is are was were been being", "go": "goes went gone going", "take": "takes took taken taking",
         "get": "gets got gotten getting", "give": "gives gave given giving", "come": "comes came coming",
         "run": "runs ran running", "bring": "brings brought bringing", "put": "puts putting", "set": "sets setting",
         "cut": "cuts cutting", "hit": "hits hitting", "let": "lets letting", "keep": "keeps kept keeping",
         "hold": "holds held holding", "make": "makes made making", "think": "thinks thought thinking",
         "find": "finds found finding", "break": "breaks broke broken breaking", "fall": "falls fell fallen falling",
         "stand": "stands stood standing", "throw": "throws threw thrown throwing", "draw": "draws drew drawn drawing",
         "drive": "drives drove driven driving", "write": "writes wrote written writing", "speak": "speaks spoke spoken speaking",
         "wear": "wears wore worn wearing", "tear": "tears tore torn tearing", "sell": "sells sold selling",
         "tell": "tells told telling", "send": "sends sent sending", "spend": "spends spent spending", "lend": "lends lent lending",
         "build": "builds built building", "pay": "pays paid paying", "say": "says said saying", "lay": "lays laid laying",
         "lie": "lies lay lain lying", "lead": "leads led leading", "leave": "leaves left leaving", "feel": "feels felt feeling",
         "deal": "deals dealt dealing", "mean": "means meant meaning", "meet": "meets met meeting", "sit": "sits sat sitting",
         "win": "wins won winning", "shut": "shuts shutting", "spin": "spins spun spinning", "show": "shows showed shown showing",
         "blow": "blows blew blown blowing", "grow": "grows grew grown growing", "know": "knows knew known knowing",
         "fly": "flies flew flown flying", "catch": "catches caught catching", "teach": "teaches taught teaching",
         "buy": "buys bought buying", "fight": "fights fought fighting", "beat": "beats beaten beating",
         "bite": "bites bit bitten biting", "bear": "bears bore borne bearing", "shake": "shakes shook shaken shaking",
         "wake": "wakes woke woken waking", "hang": "hangs hung hanging", "light": "lights lit lighting", "read": "reads reading",
         "sleep": "sleeps slept sleeping", "stick": "sticks stuck sticking", "strike": "strikes struck striking",
         "swing": "swings swung swinging", "dig": "digs dug digging", "freeze": "freezes froze frozen freezing",
         "hide": "hides hid hidden hiding", "choose": "chooses chose chosen choosing", "eat": "eats ate eaten eating",
         "rise": "rises rose risen rising", "shoot": "shoots shot shooting", "split": "splits splitting",
         "spread": "spreads spreading", "quit": "quits quitting", "burn": "burns burned burnt burning", "do": "does did done doing",
         "have": "has had having", "see": "sees saw seen seeing", "lose": "loses lost losing", "pull": "pulls pulled pulling",
         "wind": "winds wound winding", "sink": "sinks sank sunk sinking", "hear": "hears heard hearing", "drink": "drinks drank drunk drinking",
         "begin": "begins began begun beginning", "forget": "forgets forgot forgotten forgetting", "ring": "rings rang rung ringing",
         "kneel": "kneels knelt kneeling", "dwell": "dwells dwelt dwelled dwelling", "bend": "bends bent bending",
         "weave": "weaves wove woven weaving", "swim": "swims swam swum swimming", "sweep": "sweeps swept sweeping"}
NOT_VERB = set("a an the in on at by as to for of with out under over up off back down it's that's i i'm i'd i'll you you've "
               "you're your what's how's let's my no not just so if when all every more from once too last first above after "
               "before needless long sooner better easy actions any does could sorry here there this that what where who how "
               "why under within one ten another each both either neither some most many much few little very really quite "
               "rather pretty such fair good great high low big small home head heart world word time life money".split())
PLACE = {"sb", "sth", "someone", "something", "someone's", "sb's", "one's", "your", "yourself", "oneself", "his", "her",
         "my", "their", "x", "y"}
PART = set("up down in out on off over away back about around round through along across into with to of for from at by "
           "after apart forward ahead behind under together aside".split())


def forms(w):
    if w in IRREG:
        return [w] + IRREG[w].split()
    out = [w]
    if re.search(r"(s|x|z|ch|sh)$", w):
        out.append(w + "es")
    elif re.search(r"[^aeiou]y$", w):
        out.append(w[:-1] + "ies")
    else:
        out.append(w + "s")
    if w.endswith("e"):
        out += [w + "d", w[:-1] + "ing"]
    elif re.search(r"[^aeiou]y$", w):
        out += [w[:-1] + "ied", w + "ing"]
    else:
        out += [w + "ed", w + "ing"]
        if re.search(r"^[^aeiou]*[aeiou][^aeiouwxy]$", w):  # stop → stopped, plan → planning
            out += [w + w[-1] + "ed", w + w[-1] + "ing"]
    return out


VERBS = set(IRREG)


def auto_rx(e):
    """Sinh cú pháp dò (xem compile_rx) từ chính cụm: chia động từ đầu, chèn ~ cho cụm tách được, bỏ “be”, sb/sth → ~."""
    expr = e["expr"].replace("’", "'")
    expr = re.sub(r"\(.*?\)|…|\.\.\.|[?!.,:;\"“”]", " ", expr)
    alts = []
    for alt in re.split(r"\s+/\s+|\s+vs\.?\s+", expr):
        ws = [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]*(?:/[A-Za-z']+)*", alt)]
        ws = [w.lower() for w in ws]
        if ws and ws[0] == "be" and len(ws) > 2:
            ws = ws[1:]
        toks, lits = [], 0
        for i, w in enumerate(ws):
            if w in PLACE and not (i == 0 or (w in ("my", "your", "his", "her", "their") and not e["id"].startswith(("PHR", "PRO-PHR", "IT-EXP", "COL")))):
                if toks and toks[-1] != "~":
                    toks.append("~")
                continue
            if "/" in w:
                toks.append(w.replace("/", "|"))
                lits += 1
                continue
            w = w.replace("-", "")
            if i == 0 and (e["id"].startswith(("PHR", "PRO-PHR")) or w in VERBS) and w not in NOT_VERB:
                toks.append("|".join(dict.fromkeys(forms(w))))
                if e.get("tcode") in ("T-S", "I/T-S") and len(ws) > 1 and ws[1] in PART:
                    toks.append("~")
            else:
                toks.append(w)
            lits += 1
        while toks and toks[-1] == "~":
            toks.pop()
        while toks and toks[0] == "~":
            toks.pop(0)
        one = toks[0] if len(toks) == 1 else ""
        if lits >= 2:
            alts.append(" ".join(toks))
        elif lits == 1 and "-" in alt and len(one) >= 8:  # time-consuming → timeconsuming (phụ đề cũng bỏ gạch nối)
            alts.append(one)
        elif lits == 1 and e["id"].startswith("FIX") and len(ws) == 1:  # Actually, … / Anyway, … — đứng đầu vế câu
            alts.append("^ " + one)
        elif lits == 1 and e["id"].startswith("IT-EXP") and (alt.strip().isupper() or len(one) >= 5) and \
                one not in ("patch", "spike", "alert", "crash", "freeze", "monitor", "retro", "cache"):
            alts.append(one)
    return ";".join(alts)


def evidence(entries):
    import movie_subs_study as M
    eps = M.load_episodes()
    lines = []
    for e in eps:
        show = e["show"] if not e["show"].startswith("Phim") else e["title"].split(" 20")[0]
        if len(show) > 28:
            show = "Video: " + show.split("'")[0].split(" ")[0]
        code = "S%02dE%02d" % (e["s"], e["e"]) if e["s"] else ""
        for _, t in e["lines"]:
            # dò theo từng vế câu (cắt ở . ! ? , ; : —) để chỗ trống ~ không vắt qua câu khác
            cl = [" " + " ".join(WORD.findall(c)) + " " for c in re.split(r"[.!?…,;:—]+|\s-\s", norm(t))]
            lines.append((show, code, t, [c for c in cl if c.strip()]))

    def score(t):
        sc = abs(len(t) - 55) / 10
        if not (t[:1].isupper() and t.rstrip('"\'')[-1:] in ".!?"):
            sc += 4
        if len(t) > 120:
            sc += 20
        if re.search(r"\b(fuck|shit|bitch|dick|cock|pussy|asshole)", t, re.I):
            sc += 50
        return sc

    # chỉ mục từ → các dòng, để dò 1.500 cụm nhanh
    from collections import defaultdict
    uni = defaultdict(set)
    for li, l in enumerate(lines):
        for c in l[3]:
            for w in c.split():
                uni[w].add(li)

    def candidates(spec):
        out = set()
        for alt in spec.split(";"):
            best = None
            for t in alt.split():
                if t in ("~", "*", "^"):
                    continue
                s = set().union(*[uni.get(norm(x), set()) for x in t.split("|")])
                if best is None or len(s) < len(best):
                    best = s
            out |= best or set()
        return out

    for e in entries:
        # phrasal verb & cụm ngắn: đếm theo mặt chữ nên gồm cả nghĩa đen (go on the date, come in last…)
        if e["id"].startswith(("PHR", "PRO-PHR")) or (e["id"].startswith(("IT-EXP", "FIX")) and len(e["expr"].split()) <= 2):
            e["lit"] = True
        own = set(WORD.findall(norm(e["expr"])))
        keys = {w for c in e["colls"] for w in WORD.findall(norm(c)) if len(w) > 3 and w not in own and w not in STOP}
        if not e.get("rx"):
            e["rx"] = auto_rx(e)
        e["n"], e["by"] = 0, {}
        if not e["rx"]:
            continue
        rx = compile_rx(e["rx"])
        hits = [lines[i] for i in sorted(candidates(e["rx"])) if any(rx.search(c) for c in lines[i][3])]
        e["n"] = len(hits)
        e["by"] = dict(Counter(h[0] for h in hits).most_common())
        if hits:
            ranked = sorted(hits, key=lambda h: score(h[2]) - 4 * bool(keys & set(WORD.findall(norm(h[2])))))
            pick, shows = [], set()
            for h in ranked:  # tối đa 3 câu, ưu tiên khác phim
                if h[0] not in shows or len(ranked) < 6:
                    pick.append(h)
                    shows.add(h[0])
                if len(pick) == 3:
                    break
            e["srcs"] = [{"line": h[2], "show": h[0], "ep": h[1]} for h in pick]
            e["src"] = e["srcs"][0]
    return len(eps), len(lines)


def ev_text(e):
    if e.get("src"):
        s = e["src"]
        by = ", ".join("%s %d" % kv for kv in e["by"].items())
        lit = " Số lần đếm theo mặt chữ, gồm cả nghĩa đen / nghĩa khác của cụm." if e.get("lit") else ""
        ex = " | ".join("“%s” — %s %s" % (x["line"], x["show"], x["ep"]) for x in e["srcs"])
        return "✅ Có trong phụ đề phim: %d lượt thoại (%s).%s Câu thoại thật: %s" % (e["n"], by, lit, ex), "verified"
    return "ℹ️ Không gặp trong phụ đề sitcom đã dò (thường do văn phong trang trọng / chuyên ngành). Câu ví dụ là câu tự soạn để học.", "observation"


def md_entry(e):
    ev, _ = ev_text(e)
    rows = [
        ("Loại", "%s · %s" % (e["type"], e["group"])),
        ("Nghĩa tiếng Việt", e["vi"]),
        ("Plain English", e["en"]),
        ("Chức năng giao tiếp", e["func"]),
        ("Ngữ pháp", e["grammar"]),
    ]
    if e.get("trans"):
        rows.append(("Ngoại/nội · tách được?", e["trans"]))
    rows += [
        ("Kết hợp hay gặp", " · ".join(e["colls"])),
        ("Văn phong · tần suất · CEFR", "%s · %s · %s" % (e["register"], e["freq"], e["cefr"])),
        ("Ưu tiên", e["prio"]),
        ("Lỗi người Việt hay mắc", e["mistake"]),
        ("Cụm gần nghĩa & khác biệt", e["similar"]),
    ]
    if e.get("opposite"):
        rows.append(("Trái nghĩa", e["opposite"]))
    if e.get("usuk"):
        rows.append(("Anh-Mỹ / Anh-Anh", e["usuk"]))
    rows.append(("Nguồn & bằng chứng", ev))
    if e.get("book"):
        rows.append(("📕 Sách " + BOOK, " / ".join("**%s** — %s — *%s*" % (b["mark"].replace("*", "\\*"), b["def"], b["ex"])
                                                  for b in e["book"])))
    out = ["### %s · %s" % (e["id"], e["expr"]), "", "| | |", "|---|---|"]
    out += ["| %s | %s |" % (k, str(v).replace("|", "/")) for k, v in rows]
    out.append("")
    for lab, x in zip(EX_LABEL, e["ex"]):
        if x and x != "-":
            out.append("- **%s** *(câu tự soạn)*: %s" % (lab, x))
    out.append("")
    return "\n".join(out)


def write_md(entries, extras, n_eps, n_lines):
    os.makedirs(OUT_MD, exist_ok=True)
    head = ("> Thuộc **Idioms, Phrasal Verbs & Natural Expressions Bank** — xem bản tương tác: "
            "[🔤 Trang tra cứu + bài tập](tools/expressions-bank.html). Bằng chứng dùng thật lấy từ phụ đề "
            "%d tập phim / video (%s lượt thoại). Câu ví dụ đánh dấu *(câu tự soạn)* là câu soạn để học, "
            "không phải trích dẫn.\n\n" % (n_eps, f"{n_lines:,}".replace(",", ".")))
    for fn, title, pre in FILES:
        es = [e for e in entries if prefix(e["id"]) == pre]
        body = ["# %s" % title, "", head, "**%d mục** (mục tiêu %d).\n" % (len(es), TARGET[pre])]
        groups = []
        for e in es:
            if e["group"] not in groups:
                groups.append(e["group"])
        for g in groups:
            body.append("## %s\n" % g)
            body += [md_entry(e) for e in es if e["group"] == g]
        open(os.path.join(OUT_MD, fn), "w", encoding="utf-8").write("\n".join(body))

    # so sánh
    out = ["# So sánh các cụm dễ nhầm", "", head]
    byid = {e["id"]: e for e in entries}
    for x in extras:
        for c in x.get("comparisons", []):
            out += ["## %s vs. %s" % (c["a"], c["b"]), "",
                    "*%s · %s*" % (" · ".join(c["refs"]), " · ".join(byid[r]["vi"] for r in c["refs"] if r in byid)), "",
                    c["diff"], "", "- ✅ **%s**: %s" % (c["a"], c["exA"]), "- ✅ **%s**: %s" % (c["b"], c["exB"]),
                    "", "> 💡 %s" % c["tip"], ""]
    open(os.path.join(OUT_MD, "similar-expressions-comparison.md"), "w", encoding="utf-8").write("\n".join(out))

    # bài tập + đáp án tách riêng
    for x in extras:
        b, E = x["batch"], x["exercises"]
        auto = " *(tự sinh từ các cụm trong đợt)*" if x.get("auto") else ""
        q = ["# Bài tập đợt %d%s" % (b, auto), "", "Làm trước, rồi mới mở [đáp án](expressions/exercises-batch-%03d-answers.md).\n" % b]
        a = ["# Đáp án bài tập đợt %d%s" % (b, auto), "", "[← Quay lại đề bài](expressions/exercises-batch-%03d.md)\n" % b]
        secs = [("translate", "A. Việt → Anh"), ("complete", "B. Điền vào chỗ trống"),
                ("choose", "C. Chọn cụm đúng"), ("rewrite", "D. Viết lại / đặt câu"), ("speaking", "E. Nói")]
        for k, t in secs:
            t = "%s (%d)" % (t, len(E[k]))
            q.append("## %s\n" % t)
            a.append("## %s\n" % t)
            for i, it in enumerate(E[k], 1):
                line = "%d. %s" % (i, it["q"])
                if it.get("opts"):
                    line += "  \n   (%s)" % " / ".join(it["opts"])
                q.append(line)
                if k == "speaking":
                    a.append("%d. Gợi ý khung: *%s*" % (i, it["hint"]))
                else:
                    a.append("%d. **%s** — %s" % (i, it["a"], it["why"]))
            q.append("")
            a.append("")
        open(os.path.join(OUT_MD, "exercises-batch-%03d.md" % b), "w", encoding="utf-8").write("\n".join(q))
        open(os.path.join(OUT_MD, "exercises-batch-%03d-answers.md" % b), "w", encoding="utf-8").write("\n".join(a))

    # chỉ mục tiến độ
    cnt = Counter(prefix(e["id"]) for e in entries)
    out = ["# Chỉ mục tiến độ — Idioms & Phrasal Verbs Bank", "",
           "File này được sinh tự động; trình dựng **dừng lại nếu ID hoặc cụm bị trùng** giữa các đợt.", "",
           "| Nhóm | Đã có | Mục tiêu | ID tiếp theo |", "|---|---:|---:|---|"]
    for fn, title, pre in FILES:
        out.append("| %s | %d | %d | %s-%04d |" % (title, cnt[pre], TARGET[pre], pre, cnt[pre] + 1))
    out += ["| **Tổng** | **%d** | **%d** | |" % (len(entries), sum(TARGET.values())), "",
            "## Danh sách đã có (để tránh trùng)", "", "| ID | Cụm | Loại | Đợt | Ưu tiên | Trong phim |", "|---|---|---|---:|---|---:|"]
    out += ["| %s | %s | %s | %d | %s | %d |" % (e["id"], e["expr"], e["type"], e["batch"], e["prio"], e["n"]) for e in entries]
    open(os.path.join(OUT_MD, "progress-index.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")


def write_csv(entries):
    cols = ["id", "expression", "type", "group", "vietnamese", "plain_english", "function", "grammar", "transitivity_separability",
            "collocations", "example_everyday", "example_work", "example_ielts", "register", "frequency", "cefr", "priority",
            "common_mistakes", "similar", "opposite", "us_uk", "evidence_type", "evidence", "ielts_fighter_book", "batch"]
    with open(os.path.join(OUT_MD, "idioms-phrasal-verbs.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for e in entries:
            ev, kind = ev_text(e)
            w.writerow([e["id"], e["expr"], e["type"], e["group"], e["vi"], e["en"], e["func"], e["grammar"], e.get("trans", ""),
                        "; ".join(e["colls"]), *e["ex"], e["register"], e["freq"], e["cefr"], e["prio"], e["mistake"],
                        e["similar"], e.get("opposite", ""), e.get("usuk", ""), kind, ev,
                        " | ".join("%s: %s (%s)" % (b["mark"], b["def"], b["ex"]) for b in e.get("book", [])), e["batch"]])
    with open(os.path.join(OUT_MD, "anki-import.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("#separator:Comma\n#html:true\n#tags column:3\n")
        w = csv.writer(f)
        for e in entries:
            front = "<b>%s</b><br><small>%s · %s</small><br><br><i>%s</i>" % (e["expr"], e["type"], e["register"], e["ex"][0])
            back = ("<b>%s</b><br>%s<br><br><b>Ngữ pháp:</b> %s<br><b>Kết hợp:</b> %s<br><b>Ví dụ:</b><br>• %s<br>• %s<br>• %s"
                    "<br><b>Lỗi hay mắc:</b> %s") % (e["vi"], e["en"], e["grammar"], " · ".join(e["colls"]), *e["ex"], e["mistake"])
            tags = " ".join([prefix(e["id"]), e["prio"], e["cefr"], "batch%03d" % e["batch"], re.sub(r"\W+", "_", e["group"])])
            w.writerow([front, back, tags])


BOOK = "800 Phrasal Verb tiếng Anh thông dụng (IELTS Fighter)"


def attach_book(entries):
    """Gắn nghĩa + ví dụ trong sách IELTS Fighter cho các phrasal verb trùng; trả về danh sách sách kèm ID trong ngân hàng."""
    path = os.path.join(SRC, "pv800.json")
    if not os.path.exists(path):
        return []
    book = json.load(open(path, encoding="utf-8"))
    idx = {}
    for e in entries:
        if not e["id"].startswith(("PHR", "PRO-PHR", "IT-EXP")):
            continue
        base = re.sub(r"\(.*?\)", " ", e["expr"].lower())
        base = " ".join(w for w in re.findall(r"[a-z']+", base) if w not in PLACE)
        idx.setdefault(base, e)
    for b in book:
        pv = b["pv"].lower()
        e = idx.get(pv) or idx.get(re.sub(r" (?:with|on|to|of|for|at|about|from|in)$", "", pv))
        if e is None:
            continue
        b["id"] = e["id"]
        e.setdefault("book", []).append({"mark": b["mark"], "def": b["def"], "ex": b["ex"]})
    return book


def blank_span(e, sent):
    """Tìm vị trí cụm trong câu ví dụ (theo cú pháp dò) -> (đầu, cuối) ký tự, hoặc None."""
    if not e.get("rx"):
        return None
    rx = compile_rx(e["rx"])
    ws = [(m.start(), m.end(), norm(m.group(0))) for m in re.finditer(r"[A-Za-z]+(?:['’][A-Za-z]+)*", sent)]
    joined, pos = " ", []
    for s, t, w in ws:
        pos.append((len(joined), len(joined) + len(w), s, t))
        joined += w + " "
    m = rx.search(joined)
    if not m:
        return None
    inside = [p for p in pos if p[0] >= m.start() and p[1] <= m.end()]
    return (inside[0][2], inside[-1][3]) if inside else None


def gen_exercises(entries, extras):
    """Bài tập cho các đợt chưa có bài soạn tay: tự sinh từ chính các cụm trong đợt (ghi rõ là tự sinh)."""
    import random
    have = {x["batch"] for x in extras}
    by_batch = {}
    for e in entries:
        by_batch.setdefault(e["batch"], []).append(e)
    for b, es in sorted(by_batch.items()):
        if b in have:
            continue
        rnd = random.Random(b)
        pool = es[:]
        rnd.shuffle(pool)
        tr = [{"q": "Cụm tiếng Anh nào nghĩa là “%s”? (gợi ý: %s)" % (e["vi"], e["en"]), "a": e["expr"],
               "why": "%s · %s" % (e["id"], e["grammar"][:160])} for e in pool[:10]]
        comp, choose = [], []
        for e in pool:
            for s in (e["ex"][1], e["ex"][0], e["ex"][2]):
                if s in ("-", "") or s.startswith("("):
                    continue
                sp = blank_span(e, s)
                if not sp:
                    continue
                frag = s[sp[0]:sp[1]]
                if len(comp) < 10 and len(frag.split()) >= 2:
                    last = re.findall(r"[A-Za-z']+", frag)[-1]
                    i = s.rfind(last, sp[0], sp[1])
                    comp.append({"q": s[:i] + "___" + s[i + len(last):], "a": last,
                                 "why": "%s · %s — %s" % (e["id"], e["expr"], e["vi"])})
                elif len(choose) < 10:
                    others = [o["expr"] for o in es if o is not e and prefix(o["id"]) == prefix(e["id"])]
                    others = rnd.sample(others, min(2, len(others))) if others else []
                    if len(others) < 2:
                        others += rnd.sample([o["expr"] for o in es if o is not e and o["expr"] not in others], 2 - len(others))
                    opts = others + [e["expr"]]
                    rnd.shuffle(opts)
                    choose.append({"q": s[:sp[0]] + "______" + s[sp[1]:], "opts": opts, "a": e["expr"],
                                   "why": "%s — %s (câu gốc: %s)" % (e["expr"], e["vi"], s)})
                break
            if len(comp) >= 10 and len(choose) >= 10:
                break
        rw = [{"q": "Đặt một câu (về công việc hoặc cuộc sống của bạn) có dùng “%s” — %s." % (e["expr"], e["vi"]),
               "a": e["ex"][1] if e["ex"][1] not in ("-", "") else e["ex"][0], "why": "Câu mẫu (tự soạn). " + e["grammar"][:120]}
              for e in pool[10:15]]
        groups = {}
        for e in pool:
            groups.setdefault(e["group"], []).append(e)
        sp_ = []
        chunks = [(g, ge[i:i + 3]) for g, ge in sorted(groups.items(), key=lambda kv: -len(kv[1])) for i in range(0, len(ge), 3)]
        seen_g = []
        order = [c for c in chunks if not (c[0] in seen_g or seen_g.append(c[0]))] + chunks  # mỗi nhóm 1 đề trước, rồi lặp lại
        for g, use in order:
            if len(sp_) == 5:
                break
            if any(sp["q"].endswith(", ".join(x["expr"] for x in use) + ".") for sp in sp_):
                continue
            sp_.append({"q": "Nói 45–60 giây về chủ đề “%s” (đời sống hoặc công việc), dùng: %s." % (g, ", ".join(x["expr"] for x in use)),
                        "hint": " / ".join(x["ex"][0] for x in use)})
        extras.append({"batch": b, "auto": True,
                       "exercises": {"translate": tr, "complete": comp, "choose": choose, "rewrite": rw, "speaking": sp_}})
    extras.sort(key=lambda x: x["batch"])


def write_book_md(book):
    if not book:
        return
    out = ["# %s — bảng tra" % BOOK, "",
           "Tách từ file PDF của IELTS Fighter (%d nghĩa, %d phrasal verb). Ký hiệu của sách: **\\*** = chèn được tân ngữ "
           "vào giữa (tách được); **+** = tân ngữ đứng sau tiểu từ. Cột *Ngân hàng* trỏ tới mục giải thích đầy đủ (tiếng Việt, "
           "ví dụ, lỗi hay mắc) nếu cụm đã có trong ngân hàng. Định nghĩa và ví dụ là nguyên văn trong sách.\n" % (
               len(book), len({b["pv"] for b in book})),
           "| Phrasal verb (ký hiệu sách) | Định nghĩa (sách) | Ví dụ (sách) | Ngân hàng |", "|---|---|---|---|"]
    for b in book:
        out.append("| **%s** | %s | %s | %s |" % (b["mark"].replace("*", "\\*"), b["def"].replace("|", "/"),
                                              b["ex"].replace("|", "/"), b.get("id", "")))
    open(os.path.join(OUT_MD, "ielts-fighter-800-phrasal-verbs.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")


def main():
    entries, extras = load()
    for e in entries:
        if e["id"].startswith(("PHR", "PRO-PHR")):
            VERBS.add(e["expr"].split()[0].lower())
    VERBS.update("make do take have give keep pay raise meet reach draw pose face solve tackle resolve cause play set achieve "
                 "run save waste spend gain conduct express hold strike bridge widen fulfil follow lose catch break commit fill "
                 "earn exert attach bear come gather offer place provide voice work burn hit call cut sleep spill let beat read "
                 "sit think weigh jump bite kill learn pull walk wear bury tie pop blow pass rock smell speak twist add fall "
                 "leave reap open lay pave weather tip turn throw foot stand cross toe whet ruffle spread reinvent fly see "
                 "triage file log reproduce merge review approve address deploy push roll ship patch bump pin mock stub seed "
                 "kick trigger cut automate write check pull quarantine skip rerun escalate monitor migrate deprecate sunset "
                 "estimate groom prioritize debug troubleshoot hand loop sign flag circle drill scope map wrap pencil slot free "
                 "chase sound bounce chime".split())
    n_eps, n_lines = evidence(entries)
    book = attach_book(entries)
    gen_exercises(entries, extras)
    write_md(entries, extras, n_eps, n_lines)
    write_book_md(book)
    write_csv(entries)
    data = dict(entries=entries, extras=extras, files=[f[:3] for f in FILES], target=TARGET, eps=n_eps, lines=n_lines,
                book=book, bookname=BOOK)
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("window.EXB=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    cnt = Counter(prefix(e["id"]) for e in entries)
    print("mục:", len(entries), dict(cnt), "| có trong phim:", sum(1 for e in entries if e["n"]),
          "| có trong sách IELTS Fighter:", sum(1 for e in entries if e.get("book")), "| đợt:", max(e["batch"] for e in entries))
    print("JS:", os.path.getsize(OUT_JS) // 1024, "KB")


if __name__ == "__main__":
    main()
