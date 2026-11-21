#!/usr/bin/env python3
"""Tạo trước (song song) mọi câu đọc cho kanji_shorts + kanji_saga_shorts vào cache của kanji_video.tts,
để lúc dựng video không phải chờ mạng từng câu một.
    .venv/bin/python tools/tts_prefetch.py [-c 10]"""
import asyncio
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanji_saga_shorts as SS  # noqa: E402  (đặt KV.RATE = +10%)
import kanji_video as KV  # noqa: E402
from kanji_video import title  # noqa: E402


def texts():
    kanji, info, _ = KV.load_data()
    out = []
    for r in kanji:
        if not r[5]:
            continue
        d0 = info[r[1]]
        out.append(f"{title(d0['hv'])}. {KV.end(d0['m'].split(';')[0])}")
        say, _ = KV.spoken(d0["s"], info)
        if say:
            out.append(say)
    for ep in SS.episodes():
        n_k = len(ep["kanji"])
        out.append(f"Tập {ep['n']}. {n_k} chữ Kanji trong một câu chuyện." if n_k else f"Tập {ep['n']}.")
        for s in SS.sentences(ep["paras"]):
            say, _ = SS.speak(s)
            if say:
                out.append(say)
        if n_k:
            out.append("Ôn lại: " + ", ".join(title(info[k]["hv"]).split(",")[0].split("/")[0] for k in ep["kanji"]) + ".")
    return list(dict.fromkeys(out))


def dest_of(text):
    r = KV.RATE
    return KV.CACHE / (hashlib.sha1(f"{KV.VOICE}|{text}{'|' + r if r else ''}".encode()).hexdigest()[:16] + ".mp3")


async def one(text, sem, stat):
    import edge_tts
    dest = dest_of(text)
    async with sem:
        for attempt in range(8):
            try:
                data = bytearray()
                async for msg in edge_tts.Communicate(text, KV.VOICE, **({"rate": KV.RATE} if KV.RATE else {})).stream():
                    if msg["type"] == "audio":
                        data += msg["data"]
                if len(data) > 512:
                    tmp = dest.with_suffix(".part")
                    tmp.write_bytes(bytes(data))
                    tmp.replace(dest)
                    stat[0] += 1
                    if stat[0] % 200 == 0:
                        print("đã tạo", stat[0], flush=True)
                    return
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(1.0 * (attempt + 1))
        stat[1] += 1


async def main():
    conc = int(sys.argv[sys.argv.index("-c") + 1]) if "-c" in sys.argv else 10
    KV.CACHE.mkdir(parents=True, exist_ok=True)
    todo = [t for t in texts() if not (dest_of(t).exists() and dest_of(t).stat().st_size > 512)]
    print(len(todo), "câu cần tạo", flush=True)
    sem, stat = asyncio.Semaphore(conc), [0, 0]
    await asyncio.gather(*(one(t, sem, stat) for t in todo))
    print(f"xong: {stat[0]} tạo mới, {stat[1]} lỗi", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
