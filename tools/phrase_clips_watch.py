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
TOK, OUT, HTML = B / "tok", B / "chua-co-video.txt", B / "chua-co-video.html"
SINCE = float(os.environ.get("SINCE") or (ROOT / "docs/assets/clips/00.json").stat().st_mtime - 1800)   # phụ đề tải sau lúc bắt đầu index gần nhất


def fetching():
    return subprocess.run(["pgrep", "-f", "phrase_clips.py fetch"], capture_output=True).returncode == 0


def progress():
    try:
        logs = sorted(B.glob("fetch*.log"), key=lambda p: p.stat().st_mtime)
        lines = [l for l in logs[-1].read_text().splitlines() if "/" in l and "{" in l]
        return lines[-1].strip().split(" {")[0] if lines else ""
    except Exception:
        return ""


def write_html(todo, total, found, scanned, running):
    data = {"at": f"{datetime.now():%H:%M:%S %d/%m}", "scanned": scanned, "prog": progress() or "xong", "running": running,
            "total": total, "todo": {k: sorted((q for q, _ in v), key=str.lower) for k, v in todo.items()},
            "found": [[k, q, h, v, t, at] for k, q, h, v, t, at in reversed(found)]}
    tmp = HTML.with_suffix(".tmp")
    tmp.write_text(PAGE.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")), encoding="utf-8")
    os.replace(tmp, HTML)


PAGE = r"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cụm chưa có video</title>
<style>
:root{--bg:#f7f7f5;--card:#fff;--fg:#1d1d1b;--mut:#6b6b66;--line:#e4e3de;--acc:#2f6fdb;--ok:#1f8a4c;--warn:#b5481f;--bar:#e9e8e3}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161615;--card:#1f1f1d;--fg:#ecebe6;--mut:#9b9a94;--line:#33332f;--acc:#7aa7ff;--ok:#5cc98b;--warn:#f08a5d;--bar:#2c2c29}}
:root[data-theme=dark]{--bg:#161615;--card:#1f1f1d;--fg:#ecebe6;--mut:#9b9a94;--line:#33332f;--acc:#7aa7ff;--ok:#5cc98b;--warn:#f08a5d;--bar:#2c2c29}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:980px;margin:0 auto;padding:20px 16px 60px}h1{font-size:22px;margin:0 0 4px}.mut{color:var(--mut);font-size:13px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:16px 0}
.st{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}.st b{font-size:26px;font-variant-numeric:tabular-nums}
.bar{height:6px;background:var(--bar);border-radius:3px;margin-top:8px;overflow:hidden}.bar i{display:block;height:100%;background:var(--ok)}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 10px}.tabs button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:20px;padding:6px 12px;font:inherit;cursor:pointer}
.tabs button.on{background:var(--acc);border-color:var(--acc);color:#fff}
input{width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:inherit;margin-bottom:10px}
ul{list-style:none;margin:0;padding:0;background:var(--card);border:1px solid var(--line);border-radius:10px}
li{padding:7px 14px;border-top:1px solid var(--line);display:flex;gap:10px;flex-wrap:wrap;align-items:baseline}li:first-child{border-top:0}
.tag{font-size:11px;padding:1px 7px;border-radius:10px;border:1px solid var(--line);color:var(--mut)}.h{color:var(--mut);font-size:13px}
a{color:var(--acc)}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--ok);margin-right:6px;animation:p 1.6s infinite}
.dot.off{background:var(--mut);animation:none}@keyframes p{50%{opacity:.3}}
.cols{columns:3 220px;column-gap:0}.cols li{break-inside:avoid}
</style></head><body><main>
<h1>Từ / cụm chưa có video</h1>
<div class="mut" id="meta"></div>
<div class="stats" id="stats"></div>
<div class="tabs" id="tabs"></div>
<input id="q" placeholder="Lọc… (gõ một phần cụm)" autocomplete="off">
<div class="mut" id="cnt" style="margin-bottom:6px"></div>
<ul id="list"></ul>
</main><script>
const D=/*DATA*/null;
const $=id=>document.getElementById(id), esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const NAME={pb:'Kho cụm từ',vi:'Từ vựng TOEIC · IELTS · Oxford'};
let st={tab:'pb',q:''};try{Object.assign(st,JSON.parse(decodeURIComponent(location.hash.slice(1))||'{}'))}catch(e){}
$('meta').innerHTML=`<span class="dot ${D.running?'':'off'}"></span>Cập nhật ${esc(D.at)} · đã quét ${D.scanned.toLocaleString('vi')} video mới · tải phụ đề: ${esc(D.prog)} · ${D.running?'trang tự tải lại mỗi phút':'đã tải xong phụ đề'}`;
const nf={pb:0,vi:0};D.found.forEach(f=>nf[f[0]]++);
$('stats').innerHTML=['pb','vi'].map(k=>{const t=D.total[k],r=D.todo[k].length;return `<div class="st"><div class="mut">${NAME[k]} — còn chưa có video</div><b>${r.toLocaleString('vi')}</b> <span class="mut">/ ${t.toLocaleString('vi')} · đã tìm thêm ${(t-r).toLocaleString('vi')}</span><div class="bar"><i style="width:${t?(100*(t-r)/t).toFixed(1):0}%"></i></div></div>`}).join('')+
 `<div class="st"><div class="mut">Vừa tìm thấy (lên web sau lần dựng kho clip tới)</div><b>${D.found.length.toLocaleString('vi')}</b></div>`;
function render(){
  $('tabs').innerHTML=[['pb',`🚫 ${NAME.pb} · ${D.todo.pb.length}`],['vi',`🚫 Từ vựng · ${D.todo.vi.length}`],['found',`✅ Vừa tìm thấy · ${D.found.length}`]].map(([k,l])=>`<button data-k="${k}" class="${st.tab===k?'on':''}">${esc(l)}</button>`).join('');
  const q=st.q.toLowerCase().trim();$('q').value=st.q;
  let html,n;
  if(st.tab==='found'){const r=D.found.filter(f=>!q||f[1].toLowerCase().includes(q));n=r.length;
    html=r.slice(0,3000).map(([k,ph,h,v,t,at])=>`<li><span class="tag">${k==='pb'?'Cụm':'Từ vựng'}</span><b>${esc(ph)}</b><span class="h">← “${esc(h)}”</span><a href="https://www.youtube.com/watch?v=${v}&t=${t}s" target="_blank" rel="noopener">▶ xem (${Math.floor(t/60)}:${String(t%60).padStart(2,'0')})</a><span class="h">${esc(at)}</span></li>`).join('');
    $('list').className='';}
  else{const r=D.todo[st.tab].filter(x=>!q||x.toLowerCase().includes(q));n=r.length;
    html=r.map(x=>`<li><span>${esc(x)}</span><a class="h" href="https://www.youtube.com/results?search_query=${encodeURIComponent('"'+x+'"')}" target="_blank" rel="noopener">tìm</a></li>`).join('');
    $('list').className='cols';}
  $('list').innerHTML=html||'<li class="mut">Không có mục nào.</li>';$('cnt').textContent=n.toLocaleString('vi')+' mục';
  history.replaceState(null,'','#'+encodeURIComponent(JSON.stringify(st)));
}
$('tabs').onclick=e=>{const b=e.target.closest('button');if(b){st.tab=b.dataset.k;render()}};
$('q').oninput=e=>{st.q=e.target.value;render()};
render();
if(D.running)setTimeout(()=>{if(document.activeElement!==$('q'))location.reload();else setTimeout(()=>location.reload(),30000)},60000);
</script></body></html>
"""


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
                d = json.load(gzip.open(p))
                w = d["w"]
                text = " " + (w if isinstance(w, str) else " ".join(w)) + " "
                tt, acc = [], 0
                for x in d.get("t", []):
                    acc += x; tt.append(acc)
            except Exception:
                continue
            scanned += 1
            vid = p.name.split(".")[0]
            for k in todo:
                keep = []
                for q, ks in todo[k]:
                    hit = next((x for x in ks if x in text), None)
                    if hit:
                        wi = text[:text.index(hit) + 1].count(" ") - 1       # vị trí từ đầu tiên của đoạn khớp
                        sec = int(tt[wi] / 10) if 0 <= wi < len(tt) else 0
                        found.append((k, q, hit.strip(), vid, sec, f"{datetime.now():%H:%M}"))
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
            L += [f"[{'Cụm' if k == 'pb' else 'Từ vựng'}] {q}  ←  \"{h}\"  ·  youtu.be/{v}?t={t}" for k, q, h, v, t, _ in reversed(found)]
            tmp = OUT.with_suffix(".tmp")
            tmp.write_text("\n".join(L) + "\n", encoding="utf-8")
            os.replace(tmp, OUT)
            write_html(todo, total, found, scanned, running)
        if not running:
            break
        time.sleep(60)


if __name__ == "__main__":
    main()
