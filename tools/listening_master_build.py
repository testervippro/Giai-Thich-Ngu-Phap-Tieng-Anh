#!/usr/bin/env python3
"""Kho câu dài cho trang docs/tools/listening-master.html → docs/tools/listening-master-data.js

- Lấy câu ≥ 16 từ trong transcript TOEIC Part 3 / Part 4 (docs/toeic-listening-part-3.md, -4.md),
  bỏ câu có từ lạ do ASR (zipf < 2.3, trừ tên riêng viết hoa) → câu sạch để chép chính tả.
- Cộng thêm câu kiểu IELTS Section 3/4 (tự viết, không chép đề Cambridge).

    uv run -q --python 3.12 --with wordfreq python tools/listening_master_build.py
"""
import json
import os
import re

from wordfreq import zipf_frequency as zf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "tools", "listening-master-data.js")

IELTS = """
What I'd like to focus on today is not so much the technology itself, but the way it has changed how people in rural areas access basic services.
Although the original survey was carried out in the early nineteen nineties, many of its findings are still surprisingly relevant to urban planners today.
The researchers found that birds which had been exposed to artificial light at night tended to start singing almost an hour earlier than those in darker areas.
One of the main reasons the project ran over budget was that nobody had anticipated how long it would take to get permission from the local council.
If you're planning to submit your assignment after the deadline, you'll need to get a form signed by your tutor and hand it in to the faculty office.
Having said that, there's a growing body of evidence to suggest that the benefits of the scheme have been greatly exaggerated by its supporters.
The museum, which was originally built as a private home for a wealthy merchant, has recently been restored with the help of a government grant.
What surprised us most was that the participants who slept for less than six hours performed just as well on the memory test as those who slept for eight.
Rather than relying on a single large dam, the engineers decided to build a series of smaller ones along the river, which turned out to be far more efficient.
Before we move on to the results, I should point out that the sample size was quite small, so we need to be careful about drawing any firm conclusions.
It wasn't until the invention of refrigeration in the late nineteenth century that people were able to transport fresh meat over long distances.
The tickets for the guided tour are available from the information desk, but if you'd like to join the boat trip as well, you'll have to book it online.
Not only did the new policy reduce traffic in the city centre, but it also led to a noticeable improvement in air quality within the first six months.
I'd go along with what you said about the introduction, although I think the section on methodology could do with a bit more detail.
The reason why so many of these species are under threat is that their natural habitat has been gradually replaced by farmland over the past fifty years.
Students who wish to use the laboratory outside normal opening hours must first complete a safety course, which runs every Tuesday afternoon.
Unlike most other mammals of a similar size, these animals can survive for several weeks without drinking any water at all.
So what we're going to do is divide the class into small groups, and each group will be responsible for collecting data from a different part of the coast.
The first thing you'll notice when you arrive at the campsite is that there's no mobile phone signal, so make sure you've told someone where you're going.
By the time the bridge was finally completed, the cost had risen to more than three times the figure that had originally been agreed.
What makes this particular painting so unusual is the fact that the artist seems to have used a technique that wasn't widely known until much later.
If it hadn't been for a chance meeting with a local fisherman, the archaeologists might never have discovered the remains of the ancient settlement.
The course is mainly aimed at people who already have some experience of working in retail, but beginners are welcome to apply as well.
Looking back, I think we underestimated how much time we'd need for the interviews, which meant we had to rush the final stage of the analysis.
The membership fee covers the use of the gym and the swimming pool, but you'll have to pay extra if you want to attend any of the fitness classes.
Despite the fact that the island is relatively small, it's home to an astonishing variety of plants, many of which can't be found anywhere else in the world.
Another factor that we hadn't really considered was the impact of the weather, since most of the outdoor activities had to be cancelled in the first week.
Anyone who's interested in volunteering at the festival should get in touch with Sarah, who's in charge of organising the helpers this year.
The way the brain processes language seems to depend far more on context than was previously thought, according to a study published last month.
Once the samples have been collected, they're sent off to a laboratory in the capital, where they're tested for any signs of contamination.
""".strip().split("\n")


def toeic():
    out, seen = [], set()
    for p in (3, 4):
        s = open(os.path.join(ROOT, "docs", f"toeic-listening-part-{p}.md"), encoding="utf-8").read()
        for blk in re.findall(r'<div class="transcript">(.*?)</div>', s, re.S):
            for line in blk.strip().split("\n"):
                line = line.strip()
                w = re.findall(r"[A-Za-z']+", line)
                if len(w) < 16 or len(w) > 40:
                    continue
                if any(zf(x.lower(), "en") < 2.3 and not x[0].isupper() for x in w):
                    continue
                k = line.lower()
                if k in seen:
                    continue
                seen.add(k)
                out.append([line, "T%d" % p])
    return out


def main():
    rows = toeic() + [[s.strip(), "I"] for s in IELTS if s.strip()]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("// sinh bởi tools/listening_master_build.py — [câu, nguồn: T3/T4 = TOEIC Part 3/4, I = kiểu IELTS]\n")
        f.write("window.LM_SENT=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(len(rows), "câu →", OUT)


if __name__ == "__main__":
    main()
