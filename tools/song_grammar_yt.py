"""Link YouTube phát đúng đoạn có câu hát (kiểu YouGlish) cho song_grammar.py.

Với mỗi (bài LRCLIB, dòng lời):
  1. LRCLIB /api/get/{id} → syncedLyrics ([mm:ss.xx] dòng) + duration của bản ghi.
  2. Tìm trên YouTube "artist title", chọn video đầu tiên có độ dài lệch ≤ TOL giây so với duration
     (cùng bản ghi → mốc thời gian khớp), bỏ live/cover/karaoke/remix/sped up/slowed/8D/nightcore.
  3. Link = watch?v=ID&t=(mốc dòng − 1)s.  Không đủ dữ liệu → None (giữ link tìm kiếm).
Cache: build/song_grammar/yt_cache.json (chạy lại không gọi mạng lần nữa).
"""
import json
import os
import re
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "build/song_grammar/yt_cache.json")
TOL = 3
BAD_VID = re.compile(r"\b(live|cover|karaoke|remix|sped|slowed|8d|nightcore|reverb|instrumental|lesson|tutorial|"
                     r"reaction|piano|guitar|drum|bass boosted|1 hour|loop|mashup)\b", re.I)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
_lock = threading.Lock()


def _get(url, ua=UA, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "en-US,en"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            if getattr(e, "code", None) == 404:
                return None
            time.sleep(2 + 3 * i)
    return None


def _secs(s):
    p = [int(x) for x in s.split(":")]
    v = 0
    for x in p:
        v = v * 60 + x
    return v


def lrclib(sid):
    txt = _get("https://lrclib.net/api/get/%d" % sid, ua="grammar-lyrics-tool/1.0")
    if not txt:
        return {"dur": None, "sync": []}
    d = json.loads(txt)
    sync = []
    for ln in (d.get("syncedLyrics") or "").splitlines():
        m = re.match(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)", ln)
        if m and m.group(3).strip():
            sync.append([round(int(m.group(1)) * 60 + float(m.group(2)), 2), m.group(3).strip()])
    return {"dur": d.get("duration"), "sync": sync}


def youtube(query):
    h = _get("https://www.youtube.com/results?search_query=" + quote_plus(query))
    if not h:
        return []
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", h, re.S)
    if not m:
        return []
    out = []

    def walk(o):
        if isinstance(o, dict):
            v = o.get("videoRenderer")
            if v and "lengthText" in v:
                out.append([v["videoId"], _secs(v["lengthText"]["simpleText"]),
                            "".join(r.get("text", "") for r in v["title"].get("runs", []))])
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(json.loads(m.group(1)))
    return out[:12]


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _line_time(sync, text):
    n = _norm(text)
    for t, ln in sync:
        if _norm(ln) == n:
            return t
    for t, ln in sync:
        if n and n in _norm(ln):
            return t
    return None


def _pick_video(vids, dur, title):
    if not dur:
        return None
    bad_ok = bool(BAD_VID.search(title))      # bài gốc tên đã có "live"… thì không loại
    want = set(w for w in _norm(title).split() if len(w) > 1 or w.isdigit())
    for vid, ln, vt in vids:
        have = set(_norm(vt).split())
        if want and len(want & have) * 2 < len(want):       # tên video phải chứa ≥ ½ từ của tên bài
            continue
        if abs(ln - dur) <= TOL and (bad_ok or not BAD_VID.search(vt)):
            return vid
    return None


def links(items, workers=4):
    """items: list of (sid, title, artist, line) → {(sid, line): url}"""
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))
    songs = {}
    for sid, t, a, _ in items:
        songs[str(sid)] = (t, a)
    todo = [k for k in songs if k not in cache]
    print("YouTube/LRCLIB: %d bài, cần tải %d" % (len(songs), len(todo)), flush=True)
    done = [0]

    def job(k):
        t, a = songs[k]
        lr = lrclib(int(k))
        vids = youtube("%s %s" % (a, t)) if lr["sync"] and lr["dur"] else []
        with _lock:
            cache[k] = {"dur": lr["dur"], "sync": lr["sync"], "vids": vids}
            done[0] += 1
            if done[0] % 100 == 0:
                print("  %d/%d" % (done[0], len(todo)), flush=True)
                json.dump(cache, open(CACHE, "w", encoding="utf-8"))
        time.sleep(0.3)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(job, todo))
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))

    res = {}
    for sid, t, a, line in items:
        c = cache.get(str(sid)) or {}
        vid = _pick_video(c.get("vids") or [], c.get("dur"), t)
        tm = _line_time(c.get("sync") or [], line)
        if vid and tm is not None:
            res[(sid, line)] = "https://www.youtube.com/watch?v=%s&t=%ds" % (vid, max(0, int(tm) - 1))
    return res


def _lrclib_alt(t, a):
    """Bản ghi khác của cùng bài trên LRCLIB có syncedLyrics."""
    txt = _get("https://lrclib.net/api/search?track_name=%s&artist_name=%s" % (quote_plus(t), quote_plus(a)),
               ua="grammar-lyrics-tool/1.0")
    for d in json.loads(txt or "[]"):
        if d.get("syncedLyrics") and d.get("duration"):
            return lrclib(d["id"])
    return None


def retry(items, workers=3):
    """Lần 2 cho bài thiếu: LRCLIB bản ghi khác; tìm lại YouTube; thêm truy vấn 'audio' / 'lyrics'."""
    cache = json.load(open(CACHE, encoding="utf-8"))
    songs = {str(sid): (t, a) for sid, t, a, _ in items}
    need = [k for k in songs if k in cache and not cache[k].get("retried")
            and not (_pick_video(cache[k]["vids"], cache[k]["dur"], songs[k][0]) and cache[k]["sync"])]
    print("retry %d bài" % len(need), flush=True)

    def job(k):
        t, a = songs[k]
        c = dict(cache[k])
        if not c["sync"]:
            alt = _lrclib_alt(t, a)
            if alt:
                c.update(dur=alt["dur"], sync=alt["sync"])
        if c["sync"] and c["dur"]:
            vids = list(c["vids"]) or youtube("%s %s" % (a, t))
            for extra in ("audio", "lyrics"):
                if _pick_video(vids, c["dur"], t):
                    break
                vids += youtube("%s %s %s" % (a, t, extra))
            c["vids"] = vids
        c["retried"] = 1
        with _lock:
            cache[k] = c
        time.sleep(0.5)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(job, need))
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))
