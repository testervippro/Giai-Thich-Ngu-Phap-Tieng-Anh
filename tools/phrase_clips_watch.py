"""Theo dõi phụ đề mới tải về → cập nhật liên tục build/phrase-clips/chua-co-video.txt
(danh sách từ / cụm CHƯA có video nào ở Kho cụm từ + Từ vựng TOEIC·IELTS·Oxford).

    node tools/phrase_clips_missing_keys.js          # sau mỗi lần index: lấy danh sách mức 0
    python tools/phrase_clips_watch.py               # chạy nền; tự dừng khi `phrase_clips.py fetch` xong

Cụm có trong phụ đề mới → chuyển xuống mục "VỪA TÌM THẤY" (lên web sau lần `index` tới).
"""
import gzip, json, os, subprocess, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build/phrase-clips"
TOK, OUT = B / "tok", B / "chua-co-video.txt"
SINCE = (ROOT / "docs/assets/clips/00.json").stat().st_mtime - 1800   # phụ đề tải sau lúc bắt đầu index gần nhất


def fetching():
    return subprocess.run(["pgrep", "-f", "phrase_clips.py fetch"], capture_output=True).returncode == 0


def progress():
    try:
        logs = sorted(B.glob("fetch*.log"), key=lambda p: p.stat().st_mtime)
        lines = [l for l in logs[-1].read_text().splitlines() if "/" in l and "{" in l]
        return lines[-1].strip().split(" {")[0] if lines else ""
    except Exception:
        return ""


def main():
    data = json.loads((B / "missing_keys.json").read_text())
    todo = {k: [[q, [" " + x + " " for x in ks]] for q, ks in data[k]] for k in ("pb", "vi")}
    total = {k: len(v) for k, v in todo.items()}
    found, seen, scanned = [], set(), 0
    while True:
        running = fetching()
        new = [p for p in TOK.iterdir() if p.name not in seen and p.stat().st_mtime >= SINCE]
        for p in new:
            seen.add(p.name)
            try:
                w = json.load(gzip.open(p))["w"]
                text = " " + (w if isinstance(w, str) else " ".join(w)) + " "
            except Exception:
                continue
            scanned += 1
            vid = p.name.split(".")[0]
            for k in todo:
                keep = []
                for q, ks in todo[k]:
                    hit = next((x for x in ks if x in text), None)
                    if hit:
                        found.append((k, q, hit.strip(), vid))
                    else:
                        keep.append([q, ks])
                todo[k] = keep
        if new or not OUT.exists():
            name = {"pb": "KHO CỤM TỪ", "vi": "TỪ VỰNG TOEIC · IELTS · OXFORD"}
            L = [f"Cập nhật {datetime.now():%H:%M:%S %d/%m} · đã quét {scanned} video mới · tải phụ đề: {progress() or 'xong'}",
                 "(tự cập nhật mỗi phút khi tải thêm phụ đề — cụm tìm thấy sẽ lên web sau lần dựng kho clip tới)", ""]
            for k in todo:
                L.append(f"== {name[k]}: còn {len(todo[k])} / {total[k]} chưa có video nào ==")
                L += [q for q, _ in sorted(todo[k], key=lambda x: x[0].lower())] + [""]
            L.append(f"== VỪA TÌM THẤY: {len(found)} ==  (cụm  ←  đoạn khớp  ·  video)")
            L += [f"[{'Cụm' if k == 'pb' else 'Từ vựng'}] {q}  ←  \"{h}\"  ·  youtu.be/{v}" for k, q, h, v in reversed(found)]
            tmp = OUT.with_suffix(".tmp")
            tmp.write_text("\n".join(L) + "\n", encoding="utf-8")
            os.replace(tmp, OUT)
        if not running:
            break
        time.sleep(60)


if __name__ == "__main__":
    main()
