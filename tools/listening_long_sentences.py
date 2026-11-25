#!/usr/bin/env python3
"""Thêm mục "Câu dài — nghe trọn câu" vào cuối docs/toeic-ets-2026-listening-phrases.md.

Nguồn: transcript Part 3 / Part 4 (docs/toeic-listening-part-3.md, -4.md; "Set N" = Test N).
- Lấy câu ≥ 15 từ, bỏ câu có từ lạ do OCR/ASR (zipf < 2.3, trừ tên riêng viết hoa).
- Mỗi câu tự chú thích: chỗ ÂM khó nghe (đồng hoá, rút gọn, âm yếu, nuốt t, flap T, rơi h)
  và CẤU TRÚC làm câu dài (mệnh đề quan hệ, điều kiện, bị động, so that…).
Chạy lại an toàn: phần từ MARK trở xuống được ghi đè.

    uv run -q --python 3.12 --with wordfreq python tools/listening_long_sentences.py
"""
import os
import re

from wordfreq import zipf_frequency as zf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, "docs", "toeic-ets-2026-listening-phrases.md")
MARK = "## Câu dài — nghe trọn câu (Part 3–4)"

SOUND = [
    (r"\b(did|would|could|should|didn't|wouldn't|couldn't|need|told|had|send)\s+you\b", lambda m: f"{m.group(0)} → …-joo"),
    (r"\b(don't|won't|can't|meet|let|get|got|what|that|want|but|bet|about|at|not|sent)\s+you\b", lambda m: f"{m.group(0)} → …-choo"),
    (r"\b(going) to\b(?!\s+(the|a|an|our|my|your|his|her|their|this|that)\b)", lambda m: "going to → gonna"),
    (r"\bwant to\b", lambda m: "want to → wanna"),
    (r"\b(have|has) to\b", lambda m: f"{m.group(1)} to → {'hafta' if m.group(1) == 'have' else 'hasta'}"),
    (r"\bgot to\b", lambda m: "got to → gotta"),
    (r"\ba lot of\b", lambda m: "a lot of → a lotta"),
    (r"\b(kind|sort) of\b", lambda m: f"{m.group(1)} of → {m.group(1)}a"),
    (r"\blet me\b", lambda m: "let me → lemme"),
    (r"\b(would|could|should|must|might) have\b", lambda m: f"{m.group(0)} → {m.group(1)}'ve /əv/"),
    (r"\b(next|last|first|must|just|most|best|don't|can't|won't|didn't|wasn't|isn't|aren't)\s+(?=[bcdfghjklmnpqrstvwxz])\w+", lambda m: f"{m.group(0)} (nuốt t)"),
    (r"\b\w*[aeiou]tt?(er|ing|y|ed)\b", lambda m: f"{m.group(0)} (t → d nhẹ, giọng Mỹ)"),
    (r"\b(tell|ask|give|call|help|meet|show|send|told|asked|gave|called)\s+(him|her|them)\b", lambda m: f"{m.group(0)} (rơi h / đọc yếu)"),
    (r"\bcan't\b", lambda m: "can't (nhấn mạnh — phân biệt can /kən/)"),
    (r"\bcan\b(?!')", lambda m: "can /kən/ (đọc yếu)"),
    (r"\b(I|you|we|they|he|she|it|that|there|who)'(d|ll|ve|re)\b", lambda m: f"{m.group(0)} (đuôi rút gọn, rất nhẹ)"),
    (r"\b(out|one|some|all|most|each|both|part|lot|piece|front|instead|because|ahead|rid|kind|sort|number|top|end) of\b", lambda m: f"{m.group(0)} (nối âm)"),
    (r"\b(pick|check|fill|turn|log|sign|set|put|take|come|find|figure|hand|look|run|work|get|carry|point|try|hold|go|clean|fill|back|call)(s|ed|ing)? (it|them|up|out|in|on|off|over|away|around|it out|it up)\b", lambda m: f"{m.group(0)} (nối âm)"),
]
SKIP_FLAP = {"after", "matter"}  # vẫn flap nhưng quá phổ biến, khỏi ghi
STRUCT = [
    (r"\b(which|who|whose|whom)\b", "mệnh đề quan hệ"),
    (r"\bif\b|\bunless\b|\bas long as\b", "điều kiện"),
    (r"\b(is|are|was|were|be|been|being|has been|have been|will be)\s+(\w+ly\s+)?\w+(ed|en|wn|lt|ught|ade|old|ent|id)\b", "bị động"),
    (r"\bso that\b|\bin order to\b", "chỉ mục đích"),
    (r"\b(because|due to|as a result|that's why)\b", "nguyên nhân / kết quả"),
    (r"\b(although|though|even though|however|but)\b", "đối lập"),
    (r"\b(not only|as well as|in addition|also)\b", "bổ sung thông tin"),
    (r"\b(before|after|once|until|as soon as|while|when|since)\b", "mốc thời gian"),
    (r"\b(I'm afraid|unfortunately|actually)\b", "báo tin xấu / đính chính (hay ra đề)"),
    (r"\b(make sure|please note|remember to|don't forget)\b", "nhắc nhở (hay ra đề)"),
]


def notes(s):
    snd, seen = [], set()
    for pat, f in SOUND:
        for m in re.finditer(pat, s, re.I):
            w = m.group(0).lower()
            if pat.startswith(r"\b\w*[aeiou]tt") and (w in SKIP_FLAP or zf(w, "en") < 3 or w.endswith("ated") or not re.search(r"[aeiou]tt?(er|ing|y|ed)$", w)):
                continue
            t = f(m)
            if w not in seen and t.lower() not in seen:
                seen.add(w); seen.add(t.lower()); snd.append(t)
    st = []
    for pat, lab in STRUCT:
        if re.search(pat, s, re.I) and lab not in st:
            st.append(lab)
    return "; ".join(snd[:4]), ", ".join(st[:3])


def collect():
    rows = []
    for p in (3, 4):
        txt = open(os.path.join(ROOT, "docs", f"toeic-listening-part-{p}.md"), encoding="utf-8").read()
        for sm in re.finditer(r"^## Set (\d+)\s*$(.*?)(?=^## Set |\Z)", txt, re.M | re.S):
            test = int(sm.group(1))
            for qm in re.finditer(r"### Questions ([\d–-]+).*?<div class=\"transcript\">(.*?)</div>", sm.group(2), re.S):
                for line in qm.group(2).strip().split("\n"):
                    line = line.strip()
                    w = re.findall(r"[A-Za-z']+", line)
                    if len(w) < 15 or len(w) > 45:
                        continue
                    if any(zf(x.lower(), "en") < 2.3 and not x[0].isupper() for x in w):
                        continue
                    rows.append(dict(test=test, part=p, q=qm.group(1), s=line, n=len(w)))
    return rows


def main():
    rows = collect()
    seen, uniq = set(), []
    for r in rows:
        k = r["s"].lower()
        if k not in seen:
            seen.add(k); uniq.append(r)
    esc = lambda x: x.replace("|", "/")
    L = [MARK, "",
         f"**{len(uniq)} câu dài (≥ 15 từ)** lấy nguyên văn từ transcript Part 3 – Part 4 của T1–T10. Muốn max điểm nghe thì phải nghe "
         "trọn những câu này ở tốc độ thật, không chỉ bắt được cụm. Cột **Âm khó nghe** chỉ ra chỗ người đọc nối / nuốt / đọc yếu. "
         "Cột **Cấu trúc** cho biết vì sao câu dài, để bạn đoán trước câu sẽ đi tiếp ra sao.", "",
         "> 🎧 Luyện các câu này có tiếng: [Master Listening](tools/listening-master.html) → tab **✍️ Chép chính tả** "
         "(chọn nguồn TOEIC Part 3/4) hoặc tab **🧩 Câu dài** (tách cụm, xây từ cuối lên, nhại theo).", "",
         "**Cách dùng để max điểm:** (1) che cột Câu, nghe audio đề thật, chép lại; (2) so với bảng, gạch chân chỗ sai; "
         "(3) nếu chỗ sai trùng với cột *Âm khó nghe* thì ôn lại quy luật âm nối ở Master Listening; (4) nhại câu đó 3 lần ở tốc độ thật.", ""]
    for t in range(1, 11):
        rs = [r for r in uniq if r["test"] == t]
        if not rs:
            continue
        L += [f"### Câu dài — Test {t} ({len(rs)})", "", "| # | Câu | Âm khó nghe | Cấu trúc | Part |", "|---|---|---|---|---|"]
        for i, r in enumerate(rs, 1):
            snd, st = notes(r["s"])
            L.append(f"| {i} | {esc(r['s'])} | {esc(snd)} | {esc(st)} | P{r['part']} · Q{r['q']} |")
        L.append("")
    s = open(MD, encoding="utf-8").read()
    if MARK in s:
        s = s[:s.index(MARK)].rstrip() + "\n\n"
    else:
        s = s.rstrip() + "\n\n"
    head_link = f"[câu dài nghe trọn câu]({os.path.basename(MD)}?id=câu-dài-—-nghe-trọn-câu-part-3–4)"
    s = s + "\n".join(L)
    # dòng tổng đầu trang: thêm link tới mục mới (một lần)
    first_nl = s.index("\n\n", s.index("\n") + 1)
    if "câu dài nghe trọn câu" not in s[:first_nl + 400]:
        s = re.sub(r"^(Tổng: .*?)(\. Nguồn:)", lambda m: m.group(1) + f" + **{len(uniq)} {head_link}**" + m.group(2), s, count=1, flags=re.M)
    else:
        s = re.sub(r"\*\*\d+ \[câu dài nghe trọn câu\]", f"**{len(uniq)} [câu dài nghe trọn câu]", s, count=1)
    open(MD, "w", encoding="utf-8").write(s)
    print(len(uniq), "câu dài →", MD)


if __name__ == "__main__":
    main()
