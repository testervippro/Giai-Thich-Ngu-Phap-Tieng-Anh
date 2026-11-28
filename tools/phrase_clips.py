#!/usr/bin/env python3
"""Kho clip "người bản xứ nói cụm này" tự dựng, miễn phí (thay YouGlish).

Nguồn: phụ đề tiếng Anh của video YouTube nói chuyện tự nhiên (TED, talk show, podcast), tải bằng yt-dlp
(mã nguồn mở). Phụ đề tự động (en-orig) có mốc thời gian TỪNG TỪ → phát đúng đoạn chứa cụm.

    /opt/miniconda3/bin/python tools/phrase_clips.py list            # liệt kê video các kênh -> build/phrase-clips/videos.tsv
    /opt/miniconda3/bin/python tools/phrase_clips.py fetch [--jobs 4]  # tải phụ đề (tiếp tục được) -> build/phrase-clips/tok/*.json.gz
    /opt/miniconda3/bin/python tools/phrase_clips.py songs           # + bài hát LRCLIB (lời có mốc giờ + video YouTube đã dò sẵn)
    /opt/miniconda3/bin/python tools/phrase_clips.py index           # tìm ĐÚNG NGUYÊN cụm -> docs/assets/clips/*.json

Đầu ra (trình phát: docs/assets/clip-player.js):
  docs/assets/clips/v.json      [[videoId, kênh], ...]
  docs/assets/clips/NN.json     {"cụm": [[i_video, bắt_đầu_ds, kết_thúc_ds, "trước", "sau"], ...]}   (ds = 1/10 giây)
  Cụm cần tìm: build/phrase-clips/queries.txt (tools/phrase_clips_queries.js sinh từ dữ liệu các trang).
"""
import argparse
import gzip
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "build/phrase-clips"
TOK = B / "tok"
VIDS = B / "videos.tsv"
BAD = B / "bad.txt"
OUT = ROOT / "docs/assets/clips"
SHARDS = 64
MAX_CLIPS = 10
SUB_CLIPS = 5           # cụm phụ (dạng khác / cụm trong câu / phần lõi) chỉ để bù
MIN_DUR, MAX_DUR = 120, 4 * 3600

# kênh nói tiếng Anh tự nhiên: (handle, số video tối đa)
CHANNELS = [
    ("TED", 900), ("TEDEd", 250), ("JimmyKimmelLive", 600), ("ColbertLateShow", 500), ("FallonTonight", 500),
    ("TheEllenShow", 400), ("latenightseth", 250), ("TheDiaryOfACEO", 300), ("lexfridman", 200),
    ("hubermanlab", 150), ("WIRED", 300), ("VanityFair", 250), ("JREClips", 400), ("BBCNews", 200),
    ("CNBCMakeIt", 200), ("Vox", 200), ("Insider", 150), ("Mythical", 200), ("hotones", 150), ("SNL", 300),
    # tiếng Anh IT
    ("Fireship", 300), ("freecodecamp", 120), ("ThePrimeTimeagen", 250), ("t3dotgg", 250), ("ByteByteGo", 120),
    ("ContinuousDelivery", 200), ("GOTO-", 200), ("NetworkChuck", 150), ("TechWithTim", 120), ("mkbhd", 200),
    ("TheCodingSloth", 60), ("TwoMinutePapers", 100), ("AndrejKarpathy", 20), ("lowlevellearning", 100),
    # thành ngữ / tiếng Anh đời thường
    ("bbclearningenglish", 600), ("EnglishwithLucy", 200), ("RachelsEnglish", 200), ("mmmEnglish", 150),
    ("theoffice", 300), ("Brooklyn99", 200), ("TheGrahamNortonShow", 300), ("grahamnorton", 300),
    ("CaseyNeistat", 150), ("PeterMcKinnon", 100), ("veritasium", 150), ("kurzgesagt", 80), ("Wendoverproductions", 100),
    # nói chuyện đời thường: podcast trò chuyện, talk show, reality, vlog, phỏng vấn
    ("TheoVon", 300), ("ImpaulsiveShow", 300), ("FirstWeFeast", 300), ("colinandsamir", 150), ("CallHerDaddy", 200),
    ("TeamCoco", 400), ("TheLateLateShow", 400), ("TheDailyShow", 300), ("LastWeekTonight", 150), ("nbcsnl", 400),
    ("BuzzFeedVideo", 300), ("Cut", 300), ("jubilee", 300), ("YesTheory", 200), ("MrBeast", 200), ("MarkRober", 100),
    ("GordonRamsay", 300), ("KitchenNightmares", 300), ("HellsKitchen", 300), ("DrPhil", 400), ("TheView", 300),
    ("TODAY", 300), ("GMA", 300), ("60minutes", 200), ("CBSSundayMorning", 200), ("emmachamberlain", 100),
    ("trypod", 200), ("SmartLess", 150), ("Theneedledrop", 100), ("PowerfulJRE", 100), ("ChrisWilliamson", 200),
    ("StevenBartlett", 100), ("HowToMoney", 100), ("AliAbdaal", 200), ("mattdavella", 100), ("BBCRadio1", 300),
    ("TheTonightShow", 200), ("graham", 0),
    # IT: kiểm thử, quy trình, công cụ
    ("MinistryofTesting", 200), ("AutomationStepbyStep", 300), ("TechWorldwithNana", 200), ("ArjanCodes", 200),
    ("CodeAesthetic", 30), ("mCoding", 100), ("Atlassian", 200), ("GitHub", 300), ("googlecloudtech", 300),
    ("awsevents", 300), ("dotnet", 300), ("JetBrainsTV", 200), ("NDC", 300), ("CppCon", 200), ("PyConUS", 200),
    # bù cụm còn thiếu: IELTS / collocation / idiom, business, Agile / quy trình phần mềm
    ("ieltsadvantage", 250), ("IELTSLiz", 150), ("EnglishSpeakingSuccess", 250), ("EnglishLessonswithAdam", 250),
    ("SpeakEnglishWithVanessa", 250), ("LearnEnglishWithTVSeries", 250), ("letthemtalktv", 200), ("BBCLearningEnglish", 0),
    ("EnglishAddictwithMrDuncan", 150), ("engvid", 200), ("JamesESL", 150), ("RebeccaESL", 150),
    ("HarvardBusinessReview", 250), ("TheEconomist", 250), ("FinancialTimes", 200), ("BloombergOriginals", 200),
    ("CNBC", 250), ("guardiannews", 200), ("YCombinator", 250), ("a16z", 150), ("GaryVee", 150),
    ("ScrumOrg", 200), ("DevelopmentThatPays", 150), ("AgileForHumans", 100), ("ProductSchool", 200),
    ("LennysPodcast", 150), ("theprimeagen", 0), ("TechLead", 100), ("ThePragmaticEngineer", 100),
]


# phụ đề tự động của YouTube viết dạng đầy đủ ("going to", không "gonna") → quy cụm về cùng dạng
# (giống SPOKEN trong docs/assets/clip-player.js)
SPOKEN = {"gonna": "going to", "wanna": "want to", "gotta": "got to", "kinda": "kind of", "sorta": "sort of",
          "lemme": "let me", "gimme": "give me", "ya": "you", "outta": "out of", "dunno": "don't know",
          "mornin": "morning", "nothin": "nothing", "somethin": "something", "'em": "them", "cuz": "because"}


def norm_words(t):
    t = t.replace("’", "'").replace("‘", "'").lower()
    out = []
    for w in re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)*", t):
        out += SPOKEN.get(w, w).split()
    return out


# ---------------------------------------------------------------- list
def cmd_list(a):
    """--add h1,h2: chỉ lấy các kênh này và THÊM vào videos.tsv (không ghi đè video đã có / video tìm được / bài hát)."""
    B.mkdir(parents=True, exist_ok=True)
    rows = []
    add = set(a.add.split(",")) if a.add else None
    for h, n in CHANNELS:
        if add is not None and h not in add or not n:
            continue
        try:
            out = subprocess.run(["yt-dlp", "--flat-playlist", "--no-warnings", "--playlist-end", str(n * 2),
                                  "--print", "%(id)s\t%(duration)s", f"https://www.youtube.com/@{h}/videos"],
                                 capture_output=True, text=True, timeout=600).stdout
        except subprocess.TimeoutExpired:
            out = ""
        got = []
        for line in out.splitlines():
            vid, _, d = line.partition("\t")
            try:
                d = float(d)
            except ValueError:
                continue
            if MIN_DUR <= d <= MAX_DUR:
                got.append((vid, h, int(d)))
        rows += got[:n]
        print(f"{h}: {len(got[:n])}", flush=True)
    if add is not None:
        have = {l.split("\t")[0] for l in VIDS.read_text().splitlines() if l.strip()}
        rows = [r for r in rows if r[0] not in have]
        with open(VIDS, "a") as f:
            f.write("".join(f"{v}\t{h}\t{d}\n" for v, h, d in rows))
        print("+", len(rows), "video →", VIDS.relative_to(ROOT)); return
    VIDS.write_text("".join(f"{v}\t{h}\t{d}\n" for v, h, d in rows))
    print(len(rows), "video →", VIDS.relative_to(ROOT))


# ---------------------------------------------------------------- songs
SONG_CACHE = ROOT / "build/song_grammar/yt_cache.json"          # tools/song_grammar_yt.py: lời LRCLIB có mốc giờ + video YouTube khớp
SONG_CORPUS = ROOT / "tools/data/lrclib_corpus.jsonl.gz"
MUSIC = "♪"                                                       # kênh bắt đầu bằng ♪ = bài hát (LRCLIB)
SONG_MAX = 3                                                      # tối đa 3 / 10 clip của một cụm là bài hát
SONG_BAD = re.compile(r"\b(fuck|shit|bitch|nigg|pussy|dick|cock|cunt|whore|slut|motherf|porn)", re.I)


def cmd_songs(_):
    """Bài hát LRCLIB (lời có mốc thời gian từng dòng, mã nguồn mở) + video YouTube đã dò sẵn → thêm vào kho như 1 nguồn."""
    sys.path.insert(0, str(ROOT / "tools"))
    import song_grammar_yt as SY
    meta = {}
    with gzip.open(SONG_CORPUS, "rt", encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            meta[str(o["id"])] = (o.get("t") or "", o.get("a") or "", o.get("l") or "")
    cache = json.loads(SONG_CACHE.read_text(encoding="utf-8"))
    have = {l.split("\t")[0] for l in VIDS.read_text().splitlines() if l.strip()}
    TOK.mkdir(parents=True, exist_ok=True)
    rows, n, skip = [], 0, 0
    for sid, c in cache.items():
        t, a, lyr = meta.get(sid, ("", "", ""))
        sync = c.get("sync") or []
        try:
            dur = float(c.get("dur") or 0)
        except ValueError:
            dur = 0
        vid = SY._pick_video(c.get("vids") or [], dur, t) if sync else None
        if not vid or vid in have:
            continue
        if SONG_BAD.search(lyr) or SONG_BAD.search(" ".join(x[1] for x in sync)):
            skip += 1
            continue
        toks = []
        for i, (sec, text) in enumerate(sync):
            nxt = sync[i + 1][0] if i + 1 < len(sync) else sec + 4
            ws = norm_words(text)
            span = max(0.5, min(nxt - sec, 8))
            for j, w in enumerate(ws):
                toks.append((w, int((sec + span * j / max(1, len(ws))) * 1000)))
        if len(toks) < 30:
            continue
        ts, prev = [], 0
        for _, ms in toks:
            d = max(0, ms // 100 - prev); ts.append(d); prev += d
        with gzip.open(TOK / f"{vid}.json.gz", "wt", encoding="utf-8") as f:
            json.dump({"w": " ".join(w for w, _ in toks), "t": ts, "wl": 0}, f, separators=(",", ":"))
        name = (t if " - " in t else f"{a} - {t}").replace("\t", " ")
        rows.append(f"{vid}\t{MUSIC} {name}\t{int(dur)}\n"); have.add(vid); n += 1
    with open(VIDS, "a") as f:
        f.writelines(rows)
    print(f"+{n} bài hát → {TOK.relative_to(ROOT)} (bỏ {skip} bài lời thô tục)")


# ---------------------------------------------------------------- search
def cmd_search(a):
    """Cụm chưa có clip: tìm YouTube theo đúng cụm ("..."), thêm video vào videos.tsv (kênh = tên kênh thật)."""
    qs = [q.strip() for q in Path(a.file).read_text(encoding="utf-8").splitlines() if q.strip()]
    have = {l.split("\t")[0] for l in VIDS.read_text().splitlines() if l.strip()}
    lock, new, done = threading.Lock(), [], [0]

    def one(q):
        try:
            out = subprocess.run(["yt-dlp", "--flat-playlist", "--no-warnings", "--print", "%(id)s\t%(channel)s\t%(duration)s",
                                  f'ytsearch{a.n}:"{q}"'], capture_output=True, text=True, timeout=120).stdout
        except subprocess.TimeoutExpired:
            out = ""
        with lock:
            for line in out.splitlines():
                p = line.split("\t")
                try:
                    d = float(p[2])
                except (ValueError, IndexError):
                    continue
                if p[0] not in have and 60 <= d <= MAX_DUR:
                    have.add(p[0]); new.append(f"{p[0]}\t{(p[1] or 'search').replace(chr(9), ' ')}\t{int(d)}\n")
            done[0] += 1
            if done[0] % 100 == 0:
                print(f"  {done[0]}/{len(qs)} cụm · +{len(new)} video", flush=True)

    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(one, qs))
    with open(VIDS, "a") as f:
        f.writelines(new)
    print(f"+{len(new)} video → {VIDS.relative_to(ROOT)}")


# ---------------------------------------------------------------- fetch
def json3_tokens(j, word_level):
    """-> [(từ, ms)] ; phụ đề tự động có tOffsetMs từng từ, phụ đề tay thì chia đều thời gian trong dòng."""
    out = []
    for e in j.get("events", []):
        segs, t0 = e.get("segs"), e.get("tStartMs", 0)
        if not segs:
            continue
        if word_level:
            for s in segs:
                for w in norm_words(s.get("utf8", "")):
                    out.append((w, t0 + s.get("tOffsetMs", 0)))
        else:
            ws = norm_words("".join(s.get("utf8", "") for s in segs))
            dur = e.get("dDurationMs", 2000)
            for i, w in enumerate(ws):
                out.append((w, t0 + int(dur * i / max(1, len(ws)))))
    return out


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


_ydl = threading.local()


def fetch_one(vid):
    import yt_dlp
    if not hasattr(_ydl, "y"):
        _ydl.y = yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True})
    info = _ydl.y.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
    if info.get("playable_in_embed") is False:
        return "noembed"
    auto, subs = info.get("automatic_captions") or {}, info.get("subtitles") or {}

    def url(tracks):
        return next((t["url"] for t in tracks or [] if t.get("ext") == "json3"), None)
    u, word = url(auto.get("en-orig")), True
    if not u and (info.get("language") or "en").startswith("en"):
        u = url(auto.get("en"))
    if not u:
        u, word = url(subs.get("en") or subs.get("en-US") or subs.get("en-GB")), False
    if not u:
        return "nosub"
    toks = json3_tokens(get_json(u), word)
    if len(toks) < 50:
        return "nosub"
    words = " ".join(w for w, _ in toks)
    ts, prev = [], 0
    for _, ms in toks:                       # lưu độ lệch thời gian (1/10 giây) cho gọn
        d = max(0, ms // 100 - prev)
        ts.append(d)
        prev += d
    with gzip.open(TOK / f"{vid}.json.gz", "wt", encoding="utf-8") as f:
        json.dump({"w": words, "t": ts, "wl": int(word)}, f, separators=(",", ":"))
    return "ok"


def cmd_fetch(a):
    TOK.mkdir(parents=True, exist_ok=True)
    rows = [l.split("\t") for l in VIDS.read_text().splitlines() if l.strip()]
    bad = set(BAD.read_text().split()) if BAD.exists() else set()
    done = {p.name.split(".")[0] for p in TOK.glob("*.json.gz")}
    todo = [r[0] for r in rows if r[0] not in done and r[0] not in bad]
    random.Random(1).shuffle(todo)            # trộn kênh: dừng giữa chừng vẫn đủ đa dạng
    print(f"{len(done)} đã có · {len(bad)} bỏ · {len(todo)} cần tải", flush=True)
    lock, st, t0, pause = threading.Lock(), defaultdict(int), time.time(), [0.0]

    def job(vid):
        while time.time() < pause[0]:
            time.sleep(5)
        for attempt in range(3):
            try:
                r = fetch_one(vid)
                break
            except Exception as e:            # noqa: BLE001
                msg = str(e)
                if "429" in msg or "Too Many" in msg or "not a bot" in msg:     # YouTube chặn tạm: chờ rồi thử lại, KHÔNG bỏ video
                    r = "429"
                    with lock:
                        if time.time() > pause[0]:
                            pause[0] = time.time() + 90 * (attempt + 1)        # cả nhóm cùng nghỉ
                    while time.time() < pause[0]:
                        time.sleep(5)
                    continue
                r = "err"
                if re.search(r"unavailable|private|removed|members|confirm your age|not made this video available", msg, re.I):
                    r = "gone"
                break
        with lock:
            st[r] += 1
            if r in ("noembed", "nosub", "gone"):
                with open(BAD, "a") as f:
                    f.write(vid + "\n")
            n = sum(st.values())
            if n % 25 == 0:
                rate = (time.time() - t0) / n
                print(f"  {n}/{len(todo)} {dict(st)} · {rate:.1f}s/video · còn ~{(len(todo) - n) * rate / 60:.0f} phút", flush=True)
        time.sleep(a.sleep)

    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(job, todo))
    print("xong", dict(st))


# ---------------------------------------------------------------- index
def cmd_index(a):
    raw = [q for q in (B / "queries.txt").read_text(encoding="utf-8").splitlines() if q.strip()]
    main_q = {" ".join(norm_words(q)) for q in raw if not q.startswith("~")}
    qs = [q.lstrip("~") for q in raw]
    rows = {l.split("\t")[0]: l.split("\t")[1] for l in VIDS.read_text().splitlines() if l.strip()}
    trie = {}                                          # cây tiền tố theo từ; khoá None = cụm kết thúc tại đây
    for q in qs:
        w = norm_words(q)
        if w:
            node = trie
            for x in w:
                node = node.setdefault(x, {})
            node[None] = (" ".join(w), len(w))
    hits = defaultdict(lambda: defaultdict(list))      # cụm -> kênh -> [clip]
    files = sorted(TOK.glob("*.json.gz"))
    vids, vix = [], {}
    for n, p in enumerate(files, 1):
        vid = p.name.split(".")[0]
        d = json.loads(gzip.open(p, "rt", encoding="utf-8").read())
        ws = d["w"].split(" ")
        t, acc = [], 0
        for x in d["t"]:
            acc += x; t.append(acc)
        ch = rows.get(vid, "")
        seen = set()
        nw = len(ws)
        for i in range(nw):
            node, j = trie.get(ws[i]), i + 1
            while node is not None:
                hit = node.get(None)
                if hit and hit[0] not in seen:
                    q, L = hit
                    seen.add(q)                            # mỗi video 1 lần (lần đầu)
                    if vid not in vix:
                        vix[vid] = len(vids); vids.append([vid, ch])
                    end = t[i + L] if i + L < nw else t[i + L - 1] + 6
                    end = max(end, t[i] + 4)
                    hits[q][ch].append([vix[vid], t[i], end, " ".join(ws[max(0, i - 8):i]), " ".join(ws[i + L:i + L + 8])])
                node = node.get(ws[j]) if j < nw else None
                j += 1
        if n % 1000 == 0:
            print(f"  {n}/{len(files)} video", flush=True)
    # chọn tối đa MAX_CLIPS clip / cụm (cụm phụ: SUB_CLIPS)
    out = [dict() for _ in range(SHARDS)]
    found = 0
    for q, chs in hits.items():
        songs = [x for c, v in chs.items() if c.startswith(MUSIC) for x in v]
        lists = [random.Random(q + c).sample(v, len(v)) for c, v in sorted(chs.items()) if not c.startswith(MUSIC)]
        cap = MAX_CLIPS if q in main_q else SUB_CLIPS
        random.Random(q).shuffle(songs)
        pick = []
        talk_cap = cap - min(len(songs), SONG_MAX)                # chừa chỗ cho tối đa SONG_MAX bài hát
        while len(pick) < talk_cap and any(lists):              # người nói: xen kẽ các kênh cho đa dạng giọng
            for l in lists:
                if l and len(pick) < talk_cap:
                    pick.append(l.pop())
        songs = songs[:cap - len(pick)]                          # người nói ít thì bài hát bù phần còn lại
        for k, x in enumerate(songs):                            # bài hát (LRCLIB) chèn vào vị trí 3, 6, 9…
            pick.insert(min(len(pick), 2 + 3 * k), x)
        out[shard(q)][q] = pick
        found += 1
    OUT.mkdir(parents=True, exist_ok=True)
    for i, o in enumerate(out):
        (OUT / f"{i:02d}.json").write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "v.json").write_text(json.dumps(vids, separators=(",", ":")))
    mb = sum(p.stat().st_size for p in OUT.glob("*.json")) / 1e6
    print(f"{len(files)} video · {found}/{len(set(' '.join(norm_words(q)) for q in qs))} cụm có clip · {mb:.1f} MB → {OUT.relative_to(ROOT)}")
    miss = [q for q in dict.fromkeys(" ".join(norm_words(q)) for q in raw if not q.startswith("~")) if q not in hits]
    (B / "missing.txt").write_text("\n".join(miss), encoding="utf-8")


def shard(q):
    """giống clip-player.js: FNV-1a 32 bit trên chuỗi cụm đã chuẩn hoá (chữ thường, cách nhau 1 dấu cách)"""
    h = 0x811C9DC5
    for c in q.encode("utf-8"):
        h = ((h ^ c) * 0x01000193) & 0xFFFFFFFF
    return h % SHARDS


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list").add_argument("--add", default="")
    f = sp.add_parser("fetch"); f.add_argument("--jobs", type=int, default=4); f.add_argument("--sleep", type=float, default=1.0)
    sp.add_parser("index")
    sp.add_parser("songs")
    s2 = sp.add_parser("search"); s2.add_argument("file"); s2.add_argument("--n", type=int, default=15); s2.add_argument("--jobs", type=int, default=16)
    a = ap.parse_args()
    {"list": cmd_list, "fetch": cmd_fetch, "index": cmd_index, "search": cmd_search, "songs": cmd_songs}[a.cmd](a)


if __name__ == "__main__":
    main()
