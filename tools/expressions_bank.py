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
            k = re.sub(r"\(.*?\)|[^a-z' ]", " ", e["expr"].lower())
            k = " ".join(k.split())
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
    return entries, extras


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

    for e in entries:
        own = set(WORD.findall(norm(e["expr"])))
        keys = {w for c in e["colls"] for w in WORD.findall(norm(c)) if len(w) > 3 and w not in own and w not in STOP}
        rx = compile_rx(e["rx"])
        hits = [l for l in lines if any(rx.search(c) for c in l[3])]
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
    out = ["### %s · %s" % (e["id"], e["expr"]), "", "| | |", "|---|---|"]
    out += ["| %s | %s |" % (k, str(v).replace("|", "/")) for k, v in rows]
    out.append("")
    for lab, x in zip(EX_LABEL, e["ex"]):
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
        q = ["# Bài tập đợt %d" % b, "", "Làm trước, rồi mới mở [đáp án](expressions/exercises-batch-%03d-answers.md).\n" % b]
        a = ["# Đáp án bài tập đợt %d" % b, "", "[← Quay lại đề bài](expressions/exercises-batch-%03d.md)\n" % b]
        secs = [("translate", "A. Dịch Việt → Anh (10)"), ("complete", "B. Điền vào chỗ trống (10)"),
                ("choose", "C. Chọn cụm đúng (10)"), ("rewrite", "D. Viết lại câu (5)"), ("speaking", "E. Nói (5)")]
        for k, t in secs:
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
            "common_mistakes", "similar", "opposite", "us_uk", "evidence_type", "evidence", "batch"]
    with open(os.path.join(OUT_MD, "idioms-phrasal-verbs.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for e in entries:
            ev, kind = ev_text(e)
            w.writerow([e["id"], e["expr"], e["type"], e["group"], e["vi"], e["en"], e["func"], e["grammar"], e.get("trans", ""),
                        "; ".join(e["colls"]), *e["ex"], e["register"], e["freq"], e["cefr"], e["prio"], e["mistake"],
                        e["similar"], e.get("opposite", ""), e.get("usuk", ""), kind, ev, e["batch"]])
    with open(os.path.join(OUT_MD, "anki-import.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("#separator:Comma\n#html:true\n#tags column:3\n")
        w = csv.writer(f)
        for e in entries:
            front = "<b>%s</b><br><small>%s · %s</small><br><br><i>%s</i>" % (e["expr"], e["type"], e["register"], e["ex"][0])
            back = ("<b>%s</b><br>%s<br><br><b>Ngữ pháp:</b> %s<br><b>Kết hợp:</b> %s<br><b>Ví dụ:</b><br>• %s<br>• %s<br>• %s"
                    "<br><b>Lỗi hay mắc:</b> %s") % (e["vi"], e["en"], e["grammar"], " · ".join(e["colls"]), *e["ex"], e["mistake"])
            tags = " ".join([prefix(e["id"]), e["prio"], e["cefr"], "batch%03d" % e["batch"], re.sub(r"\W+", "_", e["group"])])
            w.writerow([front, back, tags])


def main():
    entries, extras = load()
    n_eps, n_lines = evidence(entries)
    write_md(entries, extras, n_eps, n_lines)
    write_csv(entries)
    data = dict(entries=entries, extras=extras, files=[f[:3] for f in FILES], target=TARGET, eps=n_eps, lines=n_lines)
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("window.EXB=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("mục:", len(entries), "| có trong phim:", sum(1 for e in entries if e["n"]), "| ghi", OUT_MD, OUT_JS)
    for e in entries:
        print("%5d  %-30s %s" % (e["n"], e["expr"][:30], (e.get("src") or {}).get("line", "")[:70]))


if __name__ == "__main__":
    main()
