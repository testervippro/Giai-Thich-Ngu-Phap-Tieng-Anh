#!/usr/bin/env python3
"""Vòng 2: tìm bài hát cho các từ TOEIC mà vòng 1 (toeic_songs_lrclib.py) chưa tìm được.

API LRCLIB không tìm theo lời hát, nên vòng này:
  1. Tải về máy một KHO LỜI BÀI HÁT tiếng Anh: gọi /api/search với (a) mọi từ khoá TOEIC,
     (b) các dạng chia của từ chưa tìm được (-s/-ed/-ing…, từng từ dài trong cụm),
     (c) danh sách ca sĩ/ban nhạc tiếng Anh phổ biến. Lời lưu ở tools/data/lrclib_corpus.jsonl.gz
     (không đưa lên git), chạy lại sẽ tiếp tục.
  2. Tìm thẳng trong kho lời các từ chưa có bài — chấp nhận cả dạng chia của từ
     (reimburse → reimbursed, company → companies…). Ghi bổ sung vào tools/data/lrclib_cache.json,
     trường "word" là dạng thực sự xuất hiện trong lời hát.

    python3 tools/toeic_songs_corpus.py [--jobs 6]     # rồi chạy lại toeic_songs_lrclib.py để dựng trang
"""
import argparse
import gzip
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toeic_songs_lrclib as L  # noqa: E402

DATA = os.path.join(L.ROOT, "tools", "data")
CORPUS = os.path.join(DATA, "lrclib_corpus.jsonl.gz")
DONEQ = os.path.join(DATA, "lrclib_corpus_queries.txt")
lock = threading.Lock()

ARTISTS = """taylor swift|ed sheeran|adele|coldplay|the beatles|queen|bruno mars|beyonce|rihanna|drake|eminem|kanye west|
jay-z|kendrick lamar|j. cole|lana del rey|lorde|billie eilish|ariana grande|justin bieber|katy perry|lady gaga|madonna|
michael jackson|prince|david bowie|elton john|bob dylan|bruce springsteen|johnny cash|dolly parton|elvis presley|frank sinatra|
pink floyd|led zeppelin|the rolling stones|u2|radiohead|oasis|blur|arctic monkeys|the killers|the strokes|muse|green day|
linkin park|foo fighters|nirvana|pearl jam|red hot chili peppers|metallica|ac/dc|guns n' roses|bon jovi|aerosmith|eagles|
fleetwood mac|abba|the who|the kinks|the doors|simon & garfunkel|paul simon|neil young|joni mitchell|leonard cohen|
tom waits|nick cave|the smiths|morrissey|the cure|depeche mode|new order|joy division|talking heads|r.e.m.|the clash|
sex pistols|ramones|blondie|the police|sting|dire straits|genesis|phil collins|peter gabriel|billy joel|stevie wonder|
marvin gaye|aretha franklin|whitney houston|mariah carey|celine dion|alicia keys|john legend|usher|chris brown|the weeknd|
frank ocean|childish gambino|tyler, the creator|a tribe called quest|nas|2pac|the notorious b.i.g.|outkast|run the jewels|
mf doom|wu-tang clan|public enemy|beastie boys|lil wayne|nicki minaj|cardi b|post malone|travis scott|21 savage|logic|
macklemore|twenty one pilots|imagine dragons|onerepublic|maroon 5|the chainsmokers|calvin harris|dua lipa|sia|halsey|
shawn mendes|harry styles|one direction|olivia rodrigo|sabrina carpenter|sza|doja cat|lizzo|hozier|mumford & sons|
the lumineers|of monsters and men|vampire weekend|the national|arcade fire|bon iver|sufjan stevens|fleet foxes|
death cab for cutie|modest mouse|the shins|wilco|the decemberists|neutral milk hotel|pavement|the white stripes|
the black keys|kings of leon|the 1975|paramore|fall out boy|panic! at the disco|my chemical romance|blink-182|
sum 41|weezer|the offspring|system of a down|rage against the machine|tool|nine inch nails|marilyn manson|
iron maiden|black sabbath|judas priest|motorhead|slayer|megadeth|the smashing pumpkins|soundgarden|alice in chains|
stone temple pilots|counting crows|goo goo dolls|matchbox twenty|third eye blind|the cranberries|alanis morissette|
sheryl crow|norah jones|amy winehouse|florence + the machine|lily allen|kate bush|bjork|portishead|massive attack|
gorillaz|daft punk|the chemical brothers|moby|eurythmics|duran duran|tears for fears|pet shop boys|wham!|george michael|
cyndi lauper|tina turner|janet jackson|the jackson 5|earth, wind & fire|bee gees|the supremes|otis redding|ray charles|
nina simone|billie holiday|ella fitzgerald|louis armstrong|nat king cole|dean martin|tony bennett|michael buble|
frank zappa|jethro tull|yes|rush|kansas|journey|boston|toto|foreigner|styx|reo speedwagon|heart|the cars|
tom petty|john mellencamp|bryan adams|rod stewart|van morrison|cat stevens|james taylor|carole king|john denver|
garth brooks|shania twain|carrie underwood|kacey musgraves|chris stapleton|zach bryan|luke combs|morgan wallen|
kenny rogers|willie nelson|merle haggard|hank williams|woody guthrie|pete seeger|weird al yankovic|they might be giants|
the mountain goats|okkervil river|the hold steady|car seat headrest|phoebe bridgers|boygenius|mitski|japanese breakfast|
big thief|fiona apple|regina spektor|ani difranco|tori amos|sara bareilles|ingrid michaelson|jason mraz|jack johnson|
john mayer|dave matthews band|hootie & the blowfish|barenaked ladies|ben folds|ben folds five|elvis costello|joe jackson|
squeeze|xtc|the jam|the specials|madness|pulp|suede|manic street preachers|the verve|travis|keane|snow patrol|
the script|james blunt|james bay|lewis capaldi|sam smith|george ezra|tom odell|passenger|ellie goulding|jessie j|
little mix|spice girls|backstreet boys|nsync|westlife|boyzone|take that|robbie williams|the streets|dizzee rascal|
stormzy|dave|skepta|kano|lethal bizzle|plan b|example|professor green|aesop rock|atmosphere|brother ali|
immortal technique|talib kweli|mos def|common|lupe fiasco|kid cudi|chance the rapper|mac miller|joey bada$$|
hamilton|lin-manuel miranda|les miserables|disney|the lonely island|flight of the conchords|tim minchin|tom lehrer|
jonathan coulton|bo burnham|randy newman|harry chapin|jim croce|gordon lightfoot|don mclean|billy bragg|
the pogues|dropkick murphys|flogging molly|the decemberists|andrew bird|father john misty|the war on drugs|
sun kil moon|elliott smith|jeff buckley|nick drake|john prine|townes van zandt|jason isbell|drive-by truckers""".replace("\n", "")


def variants(q):
    """Dạng chia của một từ đơn (tiếng Anh) để tìm thêm."""
    out = {q}
    if " " in q or not q.isalpha():
        return out
    if len(q) < 4:
        return out
    out.add(q + "s")
    if q.endswith("e"):
        out |= {q + "d", q[:-1] + "ing", q + "r", q + "rs"}
    else:
        out |= {q + "ed", q + "ing", q + "er", q + "ers"}
    if q.endswith("y") and len(q) > 2 and q[-2] not in "aeiou":
        out |= {q[:-1] + "ies", q[:-1] + "ied"}
    if re.search(r"(s|x|z|ch|sh)$", q):
        out.add(q + "es")
    if re.search(r"[^aeiou][aeiou][bdgklmnprt]$", q) and len(q) <= 6:
        out |= {q + q[-1] + "ed", q + q[-1] + "ing"}
    return out


def query_variants(q):
    """Vài dạng chia hợp lý nhất để gọi API (ít truy vấn): -s, -ed/-d, -ing."""
    if " " in q or not q.isalpha() or len(q) < 4:
        return [q]
    if q.endswith("e"):
        return [q, q + "s", q + "d", q[:-1] + "ing"]
    if q.endswith("y") and q[-2] not in "aeiou":
        return [q, q[:-1] + "ies", q[:-1] + "ied", q + "ing"]
    return [q, q + ("es" if re.search(r"(s|x|z|ch|sh)$", q) else "s"), q + "ed", q + "ing"]


def form_rx(q):
    """Regex khớp q hoặc dạng chia (chia ở từ đầu tiên với động từ cụm, ở từ cuối với danh từ ghép)."""
    ws = q.split()
    alt = lambda w: "(?:%s)" % "|".join(sorted((re.escape(v) for v in variants(w)), key=len, reverse=True))
    if len(ws) == 1:
        body = alt(ws[0])
    else:
        a = r"\s+".join([alt(ws[0])] + [re.escape(w) for w in ws[1:]])
        b = r"\s+".join([re.escape(w) for w in ws[:-1]] + [alt(ws[-1]) if len(ws[-1]) >= 4 else re.escape(ws[-1])])
        body = "(?:%s|%s)" % (a, b)
    return re.compile(r"(?<![A-Za-z'])(%s)(?![A-Za-z'])" % body, re.I)


def load_corpus():
    seen, rows = set(), []
    if os.path.exists(CORPUS):
        with gzip.open(CORPUS, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r["id"] not in seen:
                    seen.add(r["id"])
                    rows.append(r)
    return seen, rows


def build_corpus(queries, jobs):
    seen, _ = load_corpus()
    done = set(open(DONEQ, encoding="utf-8").read().split("\n")) if os.path.exists(DONEQ) else set()
    todo = [q for q in queries if q and q not in done]
    print("kho hien co %d bai, can goi %d truy van" % (len(seen), len(todo)), flush=True)
    out = gzip.open(CORPUS, "at", encoding="utf-8")
    dq = open(DONEQ, "a", encoding="utf-8")
    n = [0]

    def work(q):
        data = L.fetch(q)
        with lock:
            n[0] += 1
            if data is None:
                return
            for x in data:
                pl = x.get("plainLyrics") or ""
                if not pl or x.get("instrumental") or x["id"] in seen or L.english_score(pl) < 0.08:
                    continue
                seen.add(x["id"])
                out.write(json.dumps(dict(id=x["id"], t=x["trackName"], a=x["artistName"], l=pl), ensure_ascii=False) + "\n")
            dq.write(q + "\n")
            if n[0] % 200 == 0:
                out.flush()
                dq.flush()
                print("  %d/%d truy van, kho %d bai" % (n[0], len(todo), len(seen)), flush=True)

    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(work, todo))
    out.close()
    dq.close()
    print("kho xong: %d bai" % len(seen), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    ets, idx = L.load_ets(), L.load_index()
    terms = sorted({L.query_of(r["term"]) for r in ets + idx} - {""})
    cache = json.load(open(L.CACHE, encoding="utf-8"))
    missing = [q for q in terms if not cache.get(q)]
    print("tong %d tu khoa, con thieu %d" % (len(terms), len(missing)), flush=True)

    if not a.no_fetch:
        qs = []
        for q in missing:  # thiếu trước: dạng chia + từng từ dài trong cụm
            qs += query_variants(q)
            if " " in q:
                qs += [w for w in q.split() if len(w) >= 5]
        qs += [x.strip() for x in ARTISTS.split("|")]
        qs += terms  # rồi mọi từ khoá (lấy thêm lời cho kho)
        uniq = list(dict.fromkeys(q for q in qs if q))
        build_corpus(uniq, a.jobs)

    _, corpus = load_corpus()
    print("tim trong kho %d bai cho %d tu..." % (len(corpus), len(missing)), flush=True)
    corpus.sort(key=lambda r: -L.english_score(r["l"]))
    text = [(r, r["l"]) for r in corpus]

    from multiprocessing import Pool
    with Pool(8, initializer=_init, initargs=(text,)) as p:
        res = p.map(_search, missing, chunksize=20)
    got = 0
    for q, hits in res:
        if hits:
            cache[q] = hits
            got += 1
    json.dump(cache, open(L.CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    print("tim them duoc %d/%d tu; tong %d/%d" % (got, len(missing), sum(1 for q in terms if cache.get(q)), len(terms)))


_TEXT = None


def _init(text):
    global _TEXT
    _TEXT = text


def _search(q):
    rx = form_rx(q)
    exact = re.compile(r"(?<![A-Za-z'])%s(?![A-Za-z'])" % re.escape(q).replace(r"\ ", r"\s+"), re.I)
    hits, arts = [], set()
    for pat in (exact, rx):
        for r, pl in _TEXT:
            if r["a"].lower() in arts:
                continue
            m = pat.search(pl)
            if not m:
                continue
            s = pl.rfind("\n", 0, m.start()) + 1
            e = pl.find("\n", m.end())
            line = pl[s:e if e >= 0 else len(pl)].strip()
            arts.add(r["a"].lower())
            hits.append(dict(track=r["t"], artist=r["a"], line=line[:200], word=m.group(0),
                             es=round(L.english_score(pl), 2), src="corpus"))
            if len(hits) == 2:
                return q, hits
    return q, hits


if __name__ == "__main__":
    sys.exit(main())
