#!/usr/bin/env python3
"""Văn bản -> MP3.

Hai engine:
  edge  (mặc định) giọng neural của Microsoft Edge, miễn phí, cần mạng.
        pip install edge-tts
  say   giọng Linh có sẵn trong macOS, offline, không cần cài gì.

Hai chế độ đọc:
  mono      một giọng Việt đọc tất cả (nhanh, ít request)
  bilingual câu tiếng Anh dùng giọng Anh, câu tiếng Việt dùng giọng Việt

Dùng:
    python3 tools/audio/tts.py build/audio-text -o build/audio
    python3 tools/audio/tts.py build/audio-text/01-*.txt --mode bilingual
    python3 tools/audio/tts.py build/audio-text --engine say
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VI_MARKS = set("ăâđêôơư") | set(
    "àáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ"
)


def tool(name: str) -> str:
    """ffmpeg/ffprobe theo đường dẫn tuyệt đối.

    Tiến trình chạy nền (hoặc qua launchd/cron) thường có PATH tối giản không
    chứa /opt/homebrew/bin, nên không thể chỉ dựa vào which().
    """
    found = shutil.which(name)
    if found:
        return found
    for base in ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"):
        cand = Path(base) / name
        if cand.exists():
            return str(cand)
    return name


FFMPEG = tool("ffmpeg")
FFPROBE = tool("ffprobe")

# ------------------------------------------------------------------- cắt đoạn


def sentences(text: str) -> list[str]:
    # Tách cả ở dấu ":" vì bảng đã được đổi thành "Ví dụ: <câu tiếng Anh>".
    parts = re.split(r"(?<=[.!?…:])\s+", text)
    return [p for p in (p.strip() for p in parts) if p]


def is_english(s: str) -> bool:
    low = s.lower()
    if any(c in VI_MARKS for c in low):
        return False
    words = re.findall(r"[a-z]{2,}", low)
    return len(words) >= 2


def language_runs(text: str, min_run: int = 40) -> list[tuple[str, str]]:
    """[('vi', '...'), ('en', '...')] — gộp đoạn ngắn vào đoạn trước cho đỡ vụn."""
    runs: list[tuple[str, list[str]]] = []
    for s in sentences(text):
        lang = "en" if is_english(s) else "vi"
        # Mảnh ngắn ("(What is a Phrasal Verb?)") gộp vào đoạn trước và đọc
        # bằng giọng của đoạn đó; đổi giọng chỉ vì vài chữ nghe rất vụn.
        if runs and (runs[-1][0] == lang or len(s) < min_run):
            runs[-1][1].append(s)
        else:
            runs.append((lang, [s]))
    return [(lang, " ".join(parts)) for lang, parts in runs]


def chunks(text: str, max_chars: int) -> list[str]:
    """Cắt theo đoạn văn, giữ nguyên câu."""
    out: list[str] = []
    buf = ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if len(para) > max_chars:                      # đoạn quá dài -> cắt theo câu
            for sent in sentences(para):
                if len(buf) + len(sent) + 1 > max_chars and buf:
                    out.append(buf)
                    buf = ""
                buf = f"{buf} {sent}".strip()
            continue
        if len(buf) + len(para) + 2 > max_chars and buf:
            out.append(buf)
            buf = ""
        buf = f"{buf}\n{para}".strip()
    if buf:
        out.append(buf)
    return out


# --------------------------------------------------------------------- engine


def cache_key(text: str, voice: str, rate: str) -> str:
    return hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:20]


def split_half(text: str) -> tuple[str, str]:
    """Cắt đôi ở ranh giới câu gần giữa nhất."""
    mid = len(text) // 2
    cuts = [m.end() for m in re.finditer(r"[.!?…:]\s+", text)]
    if not cuts:
        cuts = [m.end() for m in re.finditer(r"\s+", text)]
    if not cuts:
        return text[:mid], text[mid:]
    cut = min(cuts, key=lambda c: abs(c - mid))
    return text[:cut].strip(), text[cut:].strip()


def cap(text: str, limit: int) -> list[str]:
    """Chia nhỏ để không đoạn nào vượt `limit` ký tự."""
    if len(text) <= limit:
        return [text]
    a, b = split_half(text)
    if not a or not b:
        return [text]
    return cap(a, limit) + cap(b, limit)


async def _stream(text: str, voice: str, rate: str) -> bytes:
    import edge_tts

    data = bytearray()
    async for msg in edge_tts.Communicate(text, voice, rate=rate).stream():
        if msg["type"] == "audio":
            data += msg["data"]
    return bytes(data)


async def synth_edge(
    text: str, voice: str, rate: str, dest: Path,
    retries: int = 2, depth: int = 0, timeout: float = 60.0,
) -> None:
    err: Exception | None = None
    for attempt in range(retries):
        try:
            # Bắt buộc phải có timeout: websocket của dịch vụ thỉnh thoảng mở
            # được nhưng không bao giờ gửi gì, treo cả mẻ render.
            data = await asyncio.wait_for(_stream(text, voice, rate), timeout)
            if len(data) < 512:
                raise RuntimeError("dịch vụ trả về audio rỗng")
            dest.write_bytes(data)
            return
        except Exception as exc:                       # noqa: BLE001
            err = exc
            if attempt < retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))

    # Vài đoạn dài bị dịch vụ trả rỗng một cách ổn định — retry bao nhiêu cũng
    # vậy. Cắt đôi ở ranh giới câu rồi thử lại từng nửa thì qua được.
    if depth < 4 and len(text) > 220:
        a, b = split_half(text)
        if a and b:
            # Phải NỐI thêm đuôi chứ không dùng with_suffix: ở mức đệ quy sâu
            # dest đã có đuôi ".a", with_suffix(".a") trả về chính nó -> con tự
            # ghi đè rồi tự xoá file của mình.
            pa, pb = Path(f"{dest}.a"), Path(f"{dest}.b")
            await synth_edge(a, voice, rate, pa, retries, depth + 1, timeout)
            await synth_edge(b, voice, rate, pb, retries, depth + 1, timeout)
            # Nối thô ở mức frame MP3; bước concat cuối cùng sẽ encode lại.
            dest.write_bytes(pa.read_bytes() + pb.read_bytes())
            pa.unlink(missing_ok=True)
            pb.unlink(missing_ok=True)
            return

    raise err or RuntimeError("không tổng hợp được")


def silence(dest: Path, seconds: float = 0.4) -> None:
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"anullsrc=r=24000:cl=mono", "-t", str(seconds),
         "-c:a", "libmp3lame", "-b:a", "64k", str(dest)],
        check=True,
    )


def synth_say(text: str, voice: str, rate: str, dest: Path) -> None:
    wpm = 180
    if m := re.match(r"([+-]?\d+)%", rate):
        wpm = int(wpm * (1 + int(m.group(1)) / 100))
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
        aiff = Path(tmp.name)
    try:
        subprocess.run(
            [tool("say"), "-v", voice, "-r", str(wpm), "-o", str(aiff), text],
            check=True, capture_output=True,
        )
        subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-i", str(aiff),
             "-c:a", "libmp3lame", "-b:a", "64k", "-ar", "24000", "-ac", "1", str(dest)],
            check=True,
        )
    finally:
        aiff.unlink(missing_ok=True)


def concat(parts: list[Path], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        for p in parts:
            fh.write(f"file '{p.resolve()}'\n")
        listfile = Path(fh.name)
    try:
        # Encode lại thay vì -c copy: nối thô nhiều mp3 hay sinh timestamp
        # lệch, một số máy nghe nhạc sẽ nhảy hoặc hiện sai tổng thời lượng.
        subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(listfile), "-c:a", "libmp3lame", "-b:a", "64k",
             "-ar", "24000", "-ac", "1", str(dest)],
            check=True,
        )
    finally:
        listfile.unlink(missing_ok=True)


def duration(path: Path) -> float:
    try:
        out = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return float(out)
    except Exception:                                   # noqa: BLE001
        return 0.0


# ----------------------------------------------------------------------- main


async def render(txt: Path, args, cache: Path) -> Path | None:
    dest = args.out / (txt.stem + ".mp3")
    if dest.exists() and not args.force:
        print(f"[bỏ qua] {dest.name} đã có")
        return dest

    text = txt.read_text(encoding="utf-8")
    jobs: list[tuple[str, str]] = []                    # (voice, text)
    for chunk in chunks(text, args.max_chars):
        if args.mode == "mono":
            jobs.append((args.voice, chunk))
        else:
            jobs.extend(
                (args.en_voice if lang == "en" else args.voice, seg)
                for lang, seg in language_runs(chunk)
            )
    # Đoạn không có chữ nào (chỉ dấu câu) làm dịch vụ trả về rỗng.
    jobs = [(v, t) for v, t in jobs if re.search(r"[^\W_]", t, re.UNICODE)]
    # Đoạn quá dài bị dịch vụ trả rỗng ổn định -> cắt trước cho chắc.
    jobs = [(v, part) for v, t in jobs for part in cap(t, args.req_chars)]

    print(f"[{txt.name}] {len(text):,} ký tự -> {len(jobs)} đoạn")
    if args.dry_run:
        return None

    paths = [cache / f"{cache_key(t, v, args.rate)}.mp3" for v, t in jobs]
    for p in paths:                                     # đoạn hỏng lần trước -> render lại
        if p.with_suffix(".failed").exists():
            p.unlink(missing_ok=True)
            p.with_suffix(".failed").unlink(missing_ok=True)
    todo = [(i, v, t) for i, ((v, t), p) in enumerate(zip(jobs, paths)) if not p.exists()]
    done = len(jobs) - len(todo)
    if done:
        print(f"  {done} đoạn lấy từ cache")

    sem = asyncio.Semaphore(args.jobs)
    counter = {"n": 0}
    failed: list[str] = []

    async def work(i: int, voice: str, text: str) -> None:
        async with sem:
            try:
                if args.engine == "edge":
                    await synth_edge(text, voice, args.rate, paths[i], timeout=args.timeout)
                else:
                    await asyncio.to_thread(synth_say, text, voice, args.rate, paths[i])
            except Exception as exc:                    # noqa: BLE001
                # Một đoạn hỏng không được làm hỏng cả track: chèn khoảng lặng,
                # ghi lại để báo cuối run.
                failed.append(f"{text[:70]}… ({exc})")
                silence(paths[i])
                paths[i].with_suffix(".failed").touch()
            counter["n"] += 1
            if counter["n"] % 25 == 0 or counter["n"] == len(todo):
                print(f"  {counter['n']}/{len(todo)} đoạn", flush=True)

    if todo:
        await asyncio.gather(*(work(i, v, t) for i, v, t in todo))

    if failed:
        print(f"  ! {len(failed)} đoạn không đọc được, đã thay bằng khoảng lặng:")
        for line in failed[:10]:
            print(f"      {line}")

    concat(paths, dest)
    secs = duration(dest)
    print(f"  -> {dest}  ({secs / 60:.1f} phút, {dest.stat().st_size / 1e6:.1f} MB)")
    return dest


async def amain() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="File .txt hoặc thư mục chứa .txt")
    ap.add_argument("-o", "--out", type=Path, default=Path("build/audio"))
    ap.add_argument("--engine", choices=["edge", "say"], default="edge")
    ap.add_argument("--mode", choices=["mono", "bilingual"], default="mono")
    ap.add_argument("--voice", default=None, help="Giọng Việt (mặc định theo engine)")
    ap.add_argument("--en-voice", default="en-US-AriaNeural", help="Giọng Anh cho chế độ bilingual")
    ap.add_argument("--rate", default="+0%", help='Tốc độ đọc, ví dụ "+15%%"')
    ap.add_argument("--max-chars", type=int, default=2000, help="Ký tự tối đa mỗi khối văn bản")
    ap.add_argument("--req-chars", type=int, default=1200, help="Ký tự tối đa mỗi request TTS")
    ap.add_argument("-j", "--jobs", type=int, default=6, help="Số request chạy song song")
    ap.add_argument("--timeout", type=float, default=60.0, help="Timeout mỗi request TTS (giây)")
    ap.add_argument("--cache", type=Path, default=Path("build/audio-cache"))
    ap.add_argument("--force", action="store_true", help="Render lại cả file mp3 đã có")
    ap.add_argument("--dry-run", action="store_true", help="Chỉ đếm đoạn, không gọi TTS")
    args = ap.parse_args()

    if args.voice is None:
        args.voice = "vi-VN-HoaiMyNeural" if args.engine == "edge" else "Linh"
    if args.engine == "say":
        if args.mode == "bilingual" and args.en_voice == "en-US-AriaNeural":
            args.en_voice = "Samantha"
    elif not args.dry_run:
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            print("Chưa có edge-tts. Cài bằng:  pip install edge-tts", file=sys.stderr)
            return 1
    if not args.dry_run and not Path(FFMPEG).is_absolute():
        print("Cần ffmpeg:  brew install ffmpeg", file=sys.stderr)
        return 1

    files = sorted(args.input.glob("*.txt")) if args.input.is_dir() else [args.input]
    if not files:
        print(f"Không thấy .txt nào trong {args.input}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)

    total = 0.0
    for txt in files:
        got = await render(txt, args, args.cache)
        if got:
            total += duration(got)
    if total:
        print(f"\nTổng: {total / 3600:.2f} giờ audio trong {args.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(amain()))
