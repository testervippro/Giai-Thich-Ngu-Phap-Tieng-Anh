"""Build 2 trang: docs/common-words-hidden-meanings.md và docs/tu-vung-sac-thai.md
Chạy: python3 tools/vocab_nuance/build.py
Nhãn: ⑤ = có trong 5000.txt · Ⓣ = có trong Index Hackers TOEIC (docs/toeic-vocabulary-index.md)
"""
import os, re, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from hidden_data import THEMES, QUIZ
from nuance_data import CATS

W5000 = {l.strip().lower() for l in open(os.path.join(ROOT, '5000.txt'), encoding='utf-8') if l.strip()}
TOEIC = set()
for l in open(os.path.join(ROOT, 'docs', 'toeic-vocabulary-index.md'), encoding='utf-8'):
    m = re.match(r'\|\s*\d+\s*\|\s*([^|]+?)\s*\|', l)
    if m:
        TOEIC.add(m.group(1).lower())

def badges(word):
    w = word.lower().strip()
    keys = {w, w.split(' ')[0]}
    b = ''
    if keys & W5000: b += '⑤'
    if w in TOEIC or any(t.startswith(w + ' ') or t == w for t in TOEIC): b += 'Ⓣ'
    return b

LEGEND = "> Nhãn: **⑤** có trong [5000 từ thông dụng](WordFamilies.md) · **Ⓣ** có trong [Index từ vựng Hackers TOEIC](toeic-vocabulary-index.md)."
LETTER = 'ABCD'

def shuffle(opts, ans, seed):
    """Xáo vị trí đáp án (cố định theo seed) để đáp án đúng rải đều A–D."""
    idx = list(range(len(opts)))
    random.Random(seed).shuffle(idx)
    return [opts[i] for i in idx], idx.index(ans)

def cell(s):
    return s.replace('|', '\\|')

def build_hidden():
    n = sum(len(t[2]) for t in THEMES)
    out = [
        "# 🕵️ Common Words with Hidden Meanings — từ quen, nghĩa lạ (TOEIC 990 · IELTS 9.0)",
        "",
        "> Những từ **ai cũng tưởng đã biết** nhưng đề thi lại dùng ở **nghĩa thứ hai**. Đây chính là dạng câu Part 7 của ETS: "
        "*“The word **X** in paragraph 2, line 3, is closest in meaning to …”* — đáp án sai luôn là **nghĩa quen**, đáp án đúng là **nghĩa ẩn**. "
        "IELTS Reading cũng paraphrase bằng đúng những nghĩa này (vd. *the decade **saw** a rise* = *there was a rise*).",
        "",
        LEGEND,
        "",
        f"**{n} từ** · chia {len(THEMES)} nhóm · cuối trang có **{len(QUIZ)} câu luyện kiểu ETS**.",
        "",
        "**Cách học:** che cột “Nghĩa ẩn”, nhìn câu ví dụ và đoán nghĩa trước. Học kèm: [Từ vựng theo sắc thái](tu-vung-sac-thai.md) · "
        "[Word families & đồng nghĩa](WordFamilies.md) · [Part 7 — pattern câu hỏi](toeic-part7-question-patterns.md)",
        "",
        "---",
        "",
    ]
    for title, intro, rows in THEMES:
        out += [f"## {title}", "", f"> {intro}", "",
                "| Từ | Nghĩa quen | 🔑 Nghĩa ẩn (đề hay hỏi) | ≈ Đáp án đồng nghĩa | Ví dụ |",
                "|---|---|---|---|---|"]
        for w, pos, common, hidden, syn, ex, vi in rows:
            b = badges(w)
            out.append(f"| **{w}** <sub>{pos}</sub> {b} | {cell(common)} | **{cell(hidden)}** | *{cell(syn)}* | {cell(ex)}<br>→ {cell(vi)} |")
        out += ["", ""]
    out += ["---", "", "## ✍️ Luyện tập: “closest in meaning to” (kiểu ETS Part 7)", "",
            "> Chọn đáp án gần nghĩa nhất với từ in đậm **trong ngữ cảnh**. Bấm để xem đáp án.", ""]
    for i, (sent, word, opts, ans, why) in enumerate(QUIZ, 1):
        opts, ans = shuffle(opts, ans, 'h' + word + sent)
        s = re.sub(r'\b(' + re.escape(word) + r')\b', r'**\1**', sent, count=1)
        out.append(f"**{i}.** {s}  ")
        out.append("  ".join(f"({LETTER[j]}) {o}" for j, o in enumerate(opts)))
        out.append("")
        out.append(f"<details><summary>Đáp án</summary>\n\n**({LETTER[ans]}) {opts[ans]}** — {why}\n\n</details>")
        out.append("")
    return '\n'.join(out) + '\n'

def build_nuance():
    ng = sum(len(c[2]) for c in CATS)
    out = [
        "# 🎚️ Từ vựng theo sắc thái — chọn đúng từ khi nghĩa na ná nhau (TOEIC 990 · IELTS 9.0)",
        "",
        "> Ở Part 5–6 (ETS, Hackers, YBM…), câu từ vựng khó nhất là **4 đáp án dịch ra tiếng Việt đều giống nhau**. "
        "Thứ phân biệt chúng là **sắc thái** (mức độ, khen/chê, trang trọng), **collocation** (đi với danh từ nào) và **cấu trúc** "
        "(giới từ, to V hay V-ing, có tân ngữ không). IELTS chấm Lexical Resource 8–9 cũng dựa đúng vào điều này: "
        "*“uses less common lexical items with an awareness of style and collocation.”*",
        "",
        LEGEND,
        "",
        f"**{ng} nhóm từ** · mỗi nhóm có bảng sắc thái, **bẫy hay gặp** và **1 câu hỏi kiểu đề** (bấm để xem đáp án).",
        "",
        "**Quy trình 3 bước khi gặp câu 4 đáp án na ná:**",
        "1. **Nhìn sau chỗ trống**: có tân ngữ không? giới từ gì (on / to / with / from / for)? to V hay V-ing?",
        "2. **Nhìn danh từ đi kèm** (collocation): *fare* đi với vé xe, *fee* với dịch vụ, *rate* với đơn vị…",
        "3. **Nhìn giọng văn**: quảng cáo → từ tích cực (*affordable* chứ không *cheap*); văn bản pháp lý → *liable, stated*; học thuật → *suggest* thay *prove*.",
        "",
        "**Mục lục:** " + " · ".join(f"{c[0]} ({len(c[2])})" for c in CATS),
        "",
        "Học kèm: [Common Words with Hidden Meanings](common-words-hidden-meanings.md) · [Collins Common Errors](collins-common-errors.md) · "
        "[Collocations — 5000 từ](Collocations5000.md)",
        "",
        "---",
        "",
    ]
    qn = 0
    for title, intro, groups in CATS:
        out += [f"## {title}", "", f"> {intro}", ""]
        for gtitle, rows, trap, quiz in groups:
            out += [f"### {gtitle}", "", "| Từ | Sắc thái / khi nào dùng | Cấu trúc · collocation |", "|---|---|---|"]
            for w, nu, pat in rows:
                bs = ' '.join(filter(None, (badges(x.strip()) for x in re.split(r'[/·]', w))))
                bs = ''.join(sorted(set(bs.replace(' ', '')), key='⑤Ⓣ'.index))
                out.append(f"| **{cell(w)}** {bs} | {cell(nu)} | {cell(pat) if pat else '—'} |")
            out.append("")
            if trap:
                out += [f"⚠️ **Bẫy:** {trap}", ""]
            qn += 1
            stem, opts, ans, why = quiz
            opts, ans = shuffle(opts, ans, 'n' + stem)
            out.append(f"**❓ Câu {qn}.** {stem}  ")
            out.append("  ".join(f"({LETTER[j]}) {o}" for j, o in enumerate(opts)))
            out.append("")
            out.append(f"<details><summary>Đáp án</summary>\n\n**({LETTER[ans]}) {opts[ans]}** — {why}\n\n</details>")
            out += ["", ""]
    return '\n'.join(out) + '\n'

if __name__ == '__main__':
    for name, fn in (('common-words-hidden-meanings.md', build_hidden), ('tu-vung-sac-thai.md', build_nuance)):
        p = os.path.join(ROOT, 'docs', name)
        open(p, 'w', encoding='utf-8').write(fn())
        print('wrote', p)
    # báo các từ nghĩa ẩn không có trong cả 2 danh sách
    miss = [r[0] for t in THEMES for r in t[2] if not badges(r[0])]
    print('hidden: not in 5000/TOEIC:', miss)
    print('hidden total:', sum(len(t[2]) for t in THEMES), '| nuance groups:', sum(len(c[2]) for c in CATS))
