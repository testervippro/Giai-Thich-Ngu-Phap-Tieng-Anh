#!/usr/bin/env python3
"""Trang làm đề IELTS Reading Cambridge 19–21 (HTML, chấm điểm ngay trên trang).

Nguồn đề: ieltstrainingonline.com (trang "Practice Cam NN Reading Test 0N"), bên thứ ba.
Đáp án: tools/data/ielts_answers.json (cùng nguồn).

Ra docs/ielts-reading/:
  index.html            mục lục 12 đề
  camNN-testN.html      bài đọc + câu hỏi; cuối mỗi passage có phiếu trả lời (chấm / xem đáp án)

    python3 tools/ielts_reading_html.py [thư_mục_cache]
"""
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "ielts-reading")
ANS = os.path.join(ROOT, "tools", "data", "ielts_answers.json")
CAMS = (19, 20, 21)
RANGES = {1: (1, 13), 2: (14, 26), 3: (27, 40)}


def url(cam, t):
    suf = "" if cam >= 21 else "-with-answer"
    return "https://ieltstrainingonline.com/practice-cam-%d-reading-test-0%d%s/" % (cam, t, suf)


def fetch(cam, t, cache):
    p = os.path.join(cache, "raw%d_%d.html" % (cam, t))
    if not os.path.exists(p):
        req = urllib.request.Request(url(cam, t), headers={"User-Agent": "Mozilla/5.0"})
        open(p, "wb").write(urllib.request.urlopen(req, timeout=60).read())
    return open(p, encoding="utf-8").read()


KEEP = {"p", "h2", "h3", "h4", "strong", "b", "em", "i", "table", "tbody", "thead", "tr", "td", "th",
        "ul", "ol", "li", "br"}


def clean(fragment):
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<ins.*?</ins>|<!--.*?-->", "", fragment, flags=re.S)

    def tag(m):
        close, name, attrs = m.group(1), m.group(2).lower(), m.group(3) or ""
        if name not in KEEP:
            return ""
        if name == "b":
            name = "strong"
        if name == "i":
            name = "em"
        extra = ""
        if name in ("td", "th") and not close:
            for a in ("colspan", "rowspan"):
                mm = re.search(r'%s="(\d+)"' % a, attrs)
                if mm:
                    extra += ' %s="%s"' % (a, mm.group(1))
        return "<%s%s%s>" % (close, name, extra)

    s = re.sub(r"<(/?)(\w+)([^>]*)>", tag, s)
    s = s.replace(" ", " ")
    s = re.sub(r"<p>\s*(Advertisements)?\s*</p>", "", s)
    s = re.sub(r"Advertisements", "", s)
    s = re.sub(r"<(strong|em)>\s*</\1>", "", s)
    s = re.sub(r"<p>\s*(<br>\s*)*</p>", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def split_passages(body):
    """-> {1: html, 2: html, 3: html} theo dòng READING PASSAGE n."""
    marks = [(m.start(), int(m.group(1))) for m in re.finditer(r"READING PASSAGE\s*(\d)", body)]
    out = {}
    for k, (pos, no) in enumerate(marks):
        start = body.rfind("<h3", 0, pos)
        start = start if start >= 0 and pos - start < 400 else pos
        end = marks[k + 1][0] if k + 1 < len(marks) else len(body)
        if k + 1 < len(marks):
            e2 = body.rfind("<h3", 0, end)
            end = e2 if e2 >= 0 and end - e2 < 400 else end
        if no not in out:
            out[no] = body[start:end]
    return out


def title_of(part):
    for m in re.finditer(r"<h2>(.*?)</h2>", part, flags=re.S):
        t = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if t:
            return t
    return ""


def sheet(cam, t, no, ans):
    lo, hi = RANGES[no]
    rows = "".join(
        '<label class="q"><span class="n">%d</span><input data-q="%d" autocomplete="off" spellcheck="false">'
        '<span class="key" hidden>%s</span></label>' % (n, n, html.escape(ans.get(str(n), "")))
        for n in range(lo, hi + 1))
    return ('<section class="sheet" data-p="%d"><h3>📝 Phiếu trả lời — Passage %d (câu %d–%d)</h3>'
            '<div class="qs">%s</div><div class="btns"><button class="grade">Chấm điểm</button>'
            '<button class="show ghost">Xem đáp án</button><button class="reset ghost">Làm lại</button>'
            '<span class="score"></span></div></section>' % (no, no, lo, hi, rows))


CSS = r"""
:root{--bg:#faf8f4;--card:#fff;--ink:#1f2328;--mute:#5f6670;--line:#e3ded4;--acc:#0f6b5c;--accbg:#e6f2ef;
--ok:#1a7f37;--okbg:#e7f5ea;--bad:#c2372d;--badbg:#fbeaea;--hl:#fff3b0}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15171a;--card:#1d2024;--ink:#e6e6e3;--mute:#9aa0a6;
--line:#30343a;--acc:#5cc4ae;--accbg:#1b2e2a;--ok:#5ccb7a;--okbg:#18301f;--bad:#f0837a;--badbg:#3a1e1c;--hl:#4a4320}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.7 Georgia,"Times New Roman",serif}
.wrap{max-width:860px;margin:0 auto;padding:16px 16px 80px}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);
font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}
header.top .in{max-width:860px;margin:0 auto;padding:10px 16px;display:flex;gap:8px 14px;flex-wrap:wrap;align-items:center}
header.top a{color:var(--acc);text-decoration:none}header.top b{font-size:15px}
.timer{margin-left:auto;font-variant-numeric:tabular-nums;cursor:pointer;border:1px solid var(--line);border-radius:6px;padding:2px 8px;background:var(--card)}
h1{font:700 26px/1.3 system-ui,-apple-system,"Segoe UI",sans-serif;margin:18px 0 4px}
.sub{color:var(--mute);font:14px system-ui,sans-serif;margin:0 0 18px}
.passage{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 22px 14px;margin:18px 0}
.passage h2{font:700 22px/1.3 system-ui,sans-serif;text-align:center;margin:18px 0 8px}
.passage h3{font:700 17px/1.4 system-ui,sans-serif;margin:20px 0 6px;color:var(--acc)}
.passage p{margin:8px 0}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:15px;display:block;overflow-x:auto}
td,th{border:1px solid var(--line);padding:6px 8px;vertical-align:top}
.sheet{font:15px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--accbg);border:1px solid var(--line);
border-radius:10px;padding:12px 16px;margin:18px 0 34px}
.sheet h3{margin:2px 0 10px;font-size:16px}
.qs{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px 14px}
.q{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.q .n{min-width:24px;font-weight:700;text-align:right}
.q input{flex:1;min-width:0;font:15px system-ui,sans-serif;padding:6px 8px;border:1px solid var(--line);border-radius:6px;
background:var(--card);color:var(--ink)}
.q.ok input{border-color:var(--ok);background:var(--okbg)}.q.bad input{border-color:var(--bad);background:var(--badbg)}
.q .key{flex-basis:100%;padding-left:32px;color:var(--ok);font-size:13px}
.btns{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:12px}
button{font:600 14px system-ui,sans-serif;padding:7px 14px;border-radius:6px;border:1px solid var(--acc);background:var(--acc);color:#fff;cursor:pointer}
button.ghost{background:transparent;color:var(--acc)}
.score{font-weight:700}
.total{font:600 16px system-ui,sans-serif;text-align:center;padding:12px;border:1px dashed var(--line);border-radius:10px}
.note{color:var(--mute);font:13px system-ui,sans-serif}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;color:var(--ink);
text-decoration:none;font:14px/1.45 system-ui,sans-serif}
.card:hover{border-color:var(--acc)}.card b{display:block;font-size:16px;margin-bottom:4px;color:var(--acc)}
.card .best{color:var(--mute);font-size:12px;margin-top:6px}
h2.cam{font:700 20px system-ui,sans-serif;margin:26px 0 10px}
"""

JS = r"""
(function(){
var KEY=document.body.dataset.id;
function norm(s){return (s||'').toLowerCase().replace(/[’']/g,"'").replace(/\s+/g,' ').replace(/^\s+|\s+$/g,'').replace(/[.,;]$/,'');}
var TF={t:'true',f:'false',ng:'not given',notgiven:'not given',y:'yes',n:'no',n0:'no'};
function canon(s){s=norm(s);var c=s.replace(/\s/g,'');return TF[c]||s;}
function alts(key){
  var k=key.replace(/^in either order.*?\)\s*/i,'');
  var out=[];k.split(/\s*\/\s*|\s+I\s+|\s+OR\s+/).forEach(function(a){
    out.push(canon(a));out.push(canon(a.replace(/\(.*?\)/g,' ')));out.push(canon(a.replace(/[()]/g,'')));});
  return out;}
function check(inp,key){
  var u=canon(inp.value);if(!u)return false;
  if(/^[A-Z](\s*,\s*[A-Z])+$/.test(key.trim())){var set=key.toLowerCase().split(/\s*,\s*/);return set.indexOf(u)>=0;}
  return alts(key).indexOf(u)>=0;}
function save(){try{var d={};document.querySelectorAll('.q input').forEach(function(i){if(i.value)d[i.dataset.q]=i.value;});
  localStorage.setItem('ielts-'+KEY,JSON.stringify(d));}catch(e){}}
try{var d=JSON.parse(localStorage.getItem('ielts-'+KEY)||'{}');document.querySelectorAll('.q input').forEach(function(i){if(d[i.dataset.q])i.value=d[i.dataset.q];});}catch(e){}
function grade(sec){
  var ok=0,n=0,used={};
  sec.querySelectorAll('.q').forEach(function(q){
    var i=q.querySelector('input'),k=q.querySelector('.key').textContent;n++;
    var r=check(i,k);
    if(r&&/,/.test(k)){var g=k+'|'+canon(i.value);if(used[g])r=false;used[g]=1;}
    q.classList.toggle('ok',r);q.classList.toggle('bad',!r);if(r)ok++;
  });
  sec.querySelector('.score').textContent=ok+' / '+n;sec.dataset.ok=ok;total();}
function total(){var s=0,m=0,all=true;document.querySelectorAll('.sheet').forEach(function(x){if(x.dataset.ok===undefined)all=false;else s+=+x.dataset.ok;m+=x.querySelectorAll('.q').length;});
  var t=document.getElementById('total');if(t)t.textContent=all?('Tổng: '+s+' / '+m+' câu đúng'):'Chấm cả 3 passage để xem tổng điểm.';
  if(all){try{var b=JSON.parse(localStorage.getItem('ielts-best')||'{}');if(!b[KEY]||s>b[KEY])b[KEY]=s;localStorage.setItem('ielts-best',JSON.stringify(b));}catch(e){}}}
document.querySelectorAll('.sheet').forEach(function(sec){
  sec.querySelector('.grade').onclick=function(){grade(sec);};
  sec.querySelector('.show').onclick=function(){var h=sec.querySelector('.key').hidden;sec.querySelectorAll('.key').forEach(function(k){k.hidden=!h;});this.textContent=h?'Ẩn đáp án':'Xem đáp án';};
  sec.querySelector('.reset').onclick=function(){sec.querySelectorAll('.q').forEach(function(q){q.classList.remove('ok','bad');q.querySelector('input').value='';});
    sec.querySelector('.score').textContent='';delete sec.dataset.ok;save();total();};
  sec.addEventListener('input',save);
});
total();
var tm=document.getElementById('timer');if(tm){var left=3600,run=false,iv;function show(){var m=Math.floor(left/60),s=left%60;tm.textContent='⏱ '+m+':'+(s<10?'0':'')+s+(run?'':' ▶');}
  tm.onclick=function(){run=!run;if(run){iv=setInterval(function(){if(left>0)left--;show();},1000);}else clearInterval(iv);show();};show();}
})();
"""


def page(cam, t, parts, ans):
    pid = "cam%d-test%d" % (cam, t)
    tests = [(c, x) for c in CAMS for x in range(1, 5)]
    k = tests.index((cam, t))
    prev = ('<a href="cam%d-test%d.html">← Cam %d T%d</a>' % (tests[k - 1] * 2)) if k else ""
    nxt = ('<a href="cam%d-test%d.html">Cam %d T%d →</a>' % (tests[k + 1] * 2)) if k + 1 < len(tests) else ""
    body = []
    for no in sorted(parts):
        body.append('<article class="passage">%s</article>' % clean(parts[no]))
        body.append(sheet(cam, t, no, ans))
    titles = " · ".join(title_of(clean(parts[no])) for no in sorted(parts))
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cam %(cam)d Reading Test %(t)d</title><style>%(css)s</style></head>
<body data-id="%(pid)s">
<header class="top"><div class="in"><a href="index.html">📚 Cam 19–21</a><b>Cam %(cam)d · Test %(t)d</b>%(prev)s %(nxt)s
<span class="timer" id="timer" title="Bấm để chạy / dừng đồng hồ 60 phút"></span></div></header>
<div class="wrap">
<h1>Cambridge IELTS %(cam)d — Reading Test %(t)d</h1>
<p class="sub">%(titles)s<br>Ghi đáp án vào phiếu cuối mỗi passage → <b>Chấm điểm</b>. Bài làm được lưu trên trình duyệt.
· <a href="../#/ielts-dap-an-cam-%(cam)d">Đáp án & dẫn chứng</a> · <a href="../#/ielts-ngu-phap-cam-%(cam)d">Ngữ pháp từng câu</a></p>
%(body)s
<p class="total" id="total"></p>
<p class="note">Nguồn đề & đáp án: ieltstrainingonline.com (bên thứ ba, không phải đáp án chính thức của Cambridge).</p>
</div><script>%(js)s</script></body></html>
""" % dict(cam=cam, t=t, css=CSS, pid=pid, prev=prev, nxt=nxt, titles=html.escape(titles), body="\n".join(body), js=JS)


def index(info):
    cards = []
    for cam in CAMS:
        cards.append('<h2 class="cam">Cambridge IELTS %d</h2><div class="grid">' % cam)
        for t in range(1, 5):
            cards.append('<a class="card" href="cam%d-test%d.html" data-id="cam%d-test%d"><b>Test %d</b>%s'
                         '<div class="best"></div></a>' % (cam, t, cam, t, t, "<br>".join(html.escape(x) for x in info[(cam, t)])))
        cards.append("</div>")
    return """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IELTS Reading Cam 19–21</title><style>%s</style></head><body>
<header class="top"><div class="in"><a href="../#/">← Ngữ pháp tiếng Anh</a><b>IELTS Reading · Cambridge 19–21</b></div></header>
<div class="wrap"><h1>📚 Làm đề IELTS Reading — Cambridge 19–21</h1>
<p class="sub">12 đề · 3 passage/đề · 40 câu · 60 phút. Mỗi passage có phiếu trả lời, chấm điểm ngay trên trang.</p>
%s
<p class="note" style="margin-top:28px">Nguồn: ieltstrainingonline.com (bên thứ ba).</p></div>
<script>try{var b=JSON.parse(localStorage.getItem('ielts-best')||'{}');document.querySelectorAll('.card').forEach(function(c){
var v=b[c.dataset.id];if(v!=null)c.querySelector('.best').textContent='Điểm cao nhất: '+v+' / 40';});}catch(e){}</script>
</body></html>
""" % (CSS, "\n".join(cards))


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, ".cache-ielts")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    answers = json.load(open(ANS, encoding="utf-8"))["answers"]
    info = {}
    for cam in CAMS:
        for t in range(1, 5):
            s = fetch(cam, t, cache)
            i = s.find('<div class="et-l et-l--post">')
            a = s.find("Answer Cam", i)
            body = s[i:s.rfind('<div class="et_pb_section', 0, a)]
            parts = split_passages(body)
            ans = answers.get("%d-%d" % (cam, t), {})
            assert sorted(parts) == [1, 2, 3], (cam, t, sorted(parts))
            open(os.path.join(OUT, "cam%d-test%d.html" % (cam, t)), "w", encoding="utf-8").write(page(cam, t, parts, ans))
            info[(cam, t)] = [title_of(clean(parts[n])) for n in (1, 2, 3)]
            print(cam, t, len(ans), info[(cam, t)])
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(index(info))


if __name__ == "__main__":
    main()
