#!/bin/bash
# Tiến độ làm nét ảnh (tools/kanji_story_upscale.py) -> build/kanji_story_x2/progress.js, xem bằng progress.html.
# Chỉ đọc thư mục kết quả (đếm file), không đụng tới tiến trình làm nét. Tự thoát khi làm nét xong.
#     bash tools/kanji_story_progress.sh &        rồi mở build/kanji_story_x2/progress.html
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/build/kanji_story_x2"
TOTAL=$(ls "$ROOT/docs/kanji-viewer/kanji_story/"*.webp 2>/dev/null | wc -l | tr -d ' ')
while true; do
  done_n=$(ls "$OUT" | grep -c '^[0-9]*\.webp$')
  last=$(ls -t "$OUT" | grep '^[0-9]*\.webp$' | head -8 | sed 's/.*/"&"/' | paste -sd, -)
  run=0; pgrep -f kanji_story_upscale.py >/dev/null && run=1
  swap=$(sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/')
  log=$(grep -E '^\[|^[0-9]+/' "$OUT/run.log" 2>/dev/null | tail -1 | sed 's/"/\\"/g')
  printf 'window.PROGRESS={"t":%s,"done":%s,"total":%s,"running":%s,"swap":%s,"last":[%s],"log":"%s"};\n' \
    "$(date +%s)" "$done_n" "$TOTAL" "$run" "${swap:-0}" "$last" "$log" > "$OUT/progress.tmp.js"
  mv "$OUT/progress.tmp.js" "$OUT/progress.js"
  [ "$run" = 0 ] && [ "$done_n" -ge "$TOTAL" ] && break
  sleep 5
done
