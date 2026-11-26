/* Nghe người bản xứ nói một cụm — kho clip tự dựng, miễn phí, không cần key / captcha.
   Dữ liệu: docs/assets/clips/ (tools/phrase_clips.py: phụ đề YouTube TED / talk show / podcast, tìm ĐÚNG NGUYÊN cụm).
   Bấm cụm → khung ngay trên trang phát đúng đoạn có cụm, mỗi đoạn 3 lần rồi tự sang video sau (tối đa 50 video).

   Dùng:  <script src="../assets/clip-player.js"></script>
          <a data-clip="break the ice" href="(link dự phòng)">…</a>    hoặc  ClipPlayer.open('break the ice')
*/
(function () {
  'use strict';
  var BASE = (document.currentScript && document.currentScript.src || '').replace(/[^/]*$/, '') + 'clips/';
  var SHARDS = 64, REPEAT = 3;
  var st = { q: '', clips: [], i: 0, rep: 0, seg: null, timer: null, token: 0 };
  var vids = null, shards = {}, yt = null, ytReady = null, box = null, pop = null;

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  // giống norm_words() trong tools/phrase_clips.py
  function norm(t) { return (String(t).replace(/[’‘]/g, "'").toLowerCase().match(/[a-z0-9]+(?:'[a-z0-9]+)*/g) || []).join(' '); }
  function shard(q) {
    var b = unescape(encodeURIComponent(q)), h = 0x811c9dc5;
    for (var i = 0; i < b.length; i++) { h ^= b.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
    return h % SHARDS;
  }
  // câu dài không có nguyên văn trong kho → các cụm ngắn trong câu (cắt ở dấu câu, rồi ở liên từ / giới từ gần giữa)
  var CONJ = /^(that|which|who|whom|whose|where|when|because|although|though|if|unless|while|whereas|but|so|and|or|since|until|than|once|whether|despite|rather|instead|before|after)$/i;
  var PREP = /^(in|on|at|for|with|from|by|about|into|during|without|within|through|over|under|along|between|across|towards?|including|according|to|of)$/i;
  function parts(raw) {
    var all = norm(raw).split(' ');
    if (all.length < 4) return [];
    var segs = String(raw).replace(/[’‘]/g, "'").split(/[,;:.?!…—()"“”]+/).map(function (x) { return norm(x).split(' ').filter(Boolean); })
      .filter(function (a) { return a.length; });
    function split(a) {
      if (a.length <= 5) return [a];
      var best = -1, bs = 1e9;
      for (var i = 2; i <= a.length - 2; i++) {
        var p = CONJ.test(a[i]) ? 0 : PREP.test(a[i]) ? 1 : -1;
        if (p < 0) continue;
        var sc = p * 6 + Math.abs(i - a.length / 2);
        if (sc < bs) { bs = sc; best = i; }
      }
      if (best < 0) best = Math.ceil(a.length / 2);               // không có liên từ / giới từ: cắt đôi
      return split(a.slice(0, best)).concat(split(a.slice(best)));
    }
    var out = [], full = all.join(' ');
    segs.forEach(function (a) { split(a).forEach(function (b) { var t = b.join(' '); if (b.length >= 2 && t !== full && out.indexOf(t) < 0) out.push(t); }); });
    return out;
  }
  function filmotUrl(q) { return 'https://filmot.com/search/' + encodeURIComponent('"' + q + '"') + '/1?lang=en'; }
  function getJSON(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); }
  function load(q) {
    var k = shard(q);
    if (!vids) vids = getJSON(BASE + 'v.json');
    if (!shards[k]) shards[k] = getJSON(BASE + (k < 10 ? '0' : '') + k + '.json');
    return Promise.all([vids, shards[k]]).then(function (r) {
      return (r[1][q] || []).map(function (c) { var v = r[0][c[0]]; return { id: v[0], ch: v[1], s: c[1] / 10, e: c[2] / 10, b: c[3], a: c[4], q: q }; });
    });
  }
  // đủ 50 clip đúng nguyên cụm thì thôi; thiếu thì bù bằng clip của các cụm ngắn trong câu (xen kẽ)
  function loadAll(raw) {
    var q = norm(raw);
    return load(q).then(function (full) {
      var ps = full.length >= 50 ? [] : parts(raw);
      if (!ps.length) return full;
      return Promise.all(ps.map(load)).then(function (L) {
        var out = full.slice(), seen = {};
        out.forEach(function (c) { seen[c.id] = 1; });
        for (var r = 0; out.length < 50; r++) {
          var any = false;
          L.forEach(function (l) { if (l[r] && out.length < 50) { any = true; if (!seen[l[r].id]) { seen[l[r].id] = 1; out.push(l[r]); } } });
          if (!any) break;
        }
        out.nFull = full.length;
        return out;
      });
    });
  }

  function css() {
    var s = document.createElement('style');
    s.textContent =
      '#clp{position:fixed;left:50%;bottom:0;transform:translateX(-50%);width:min(580px,100%);max-height:94vh;overflow:auto;z-index:9999;' +
      'background:var(--card,#fff);color:var(--ink,#222);border:1px solid var(--line,#ddd);border-bottom:0;border-radius:14px 14px 0 0;box-shadow:0 -8px 30px rgba(0,0,0,.28);font:14px/1.45 system-ui,sans-serif}' +
      '#clp[hidden]{display:none}' +
      '#clp .fh{position:sticky;top:0;z-index:1;display:flex;gap:6px;align-items:center;padding:8px 10px;background:var(--card,#fff);border-bottom:1px solid var(--line,#ddd)}' +
      '#clp .fh b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
      '#clp .fb{border:1px solid var(--line,#ddd);background:transparent;color:inherit;border-radius:8px;padding:3px 9px;cursor:pointer;font:inherit;text-decoration:none;white-space:nowrap}' +
      '#clp .fn{color:var(--muted,#777);font-size:12.5px;white-space:nowrap}' +
      '#clp .fv{position:relative;width:100%;aspect-ratio:16/9;background:#000}' +
      '#clp .fv>*{position:absolute;inset:0;width:100%;height:100%}' +
      '#clp .ft{padding:8px 12px;font-size:15.5px}' +
      '#clp .ft mark{background:rgba(250,204,21,.5);color:inherit;border-radius:3px;padding:0 2px;font-weight:700}' +
      '#clp .fm{padding:0 12px 10px;color:var(--muted,#777);font-size:12px}#clp .fm a{color:inherit}' +
      '#clp .fk{padding:16px 12px}';
    document.head.appendChild(s);
  }

  function build() {
    if (box) return;
    css();
    box = document.createElement('div');
    box.id = 'clp'; box.hidden = true;
    box.innerHTML =
      '<div class="fh"><b id="clq"></b><span class="fn" id="cln"></span>' +
      '<button class="fb" id="clpv" title="Video trước">⏮</button><button class="fb" id="clrp" title="Phát lại đoạn này">🔁</button>' +
      '<button class="fb" id="clnx" title="Video sau">⏭</button><button class="fb" id="clfm" title="Tìm thêm trên Filmot (pop-up)">Filmot</button>' +
      '<button class="fb" id="clx" title="Đóng (Esc)">✕</button></div>' +
      '<div id="clbody"></div>' +
      '<div class="fm">Clip YouTube (TED, talk show, podcast) có người nói <b>đúng nguyên cụm</b> · mỗi đoạn phát ' + REPEAT + ' lần rồi tự sang video sau · ' +
      '<a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener">YouTube Terms</a></div>';
    document.body.appendChild(box);
    $('clx').onclick = close;
    $('clnx').onclick = function () { go(st.i + 1); };
    $('clpv').onclick = function () { go(Math.max(0, st.i - 1)); };
    $('clrp').onclick = function () { st.rep = 0; seekStart(); };
    $('clfm').onclick = function () { filmot(st.q); };
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !box.hidden) close(); });
  }
  function status(t) { $('cln').textContent = t; }
  function count() { if (st.clips.length) status((st.i + 1) + '/' + st.clips.length + ' video · lần ' + Math.min(st.rep + 1, REPEAT) + '/' + REPEAT); }

  function filmot(q) {                        // tìm thêm: filmot.com trong 1 cửa sổ pop-up dùng lại (captcha giải 1 lần)
    var u = filmotUrl(q);
    try { if (pop && !pop.closed) { pop.location.href = u; pop.focus(); return; } } catch (e) {}
    var w = Math.min(760, screen.availWidth - 40), h = Math.min(900, screen.availHeight - 60);
    pop = window.open(u, 'filmot', 'popup=yes,width=' + w + ',height=' + h + ',left=' + ((screen.availLeft || 0) + screen.availWidth - w - 20) + ',top=' + ((screen.availTop || 0) + 30));
    if (pop) { try { pop.opener = null; } catch (e) {} pop.focus(); }
  }

  function ytApi() {
    if (ytReady) return ytReady;
    ytReady = new Promise(function (res) {
      if (window.YT && window.YT.Player) return res();
      var prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () { if (prev) prev(); res(); };
      var s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(s);
    });
    return ytReady;
  }

  function search(raw) {
    var tok = ++st.token, q = norm(raw);
    st.q = raw; st.clips = []; st.i = 0;
    $('clq').textContent = '🎬 "' + raw + '"';
    status('đang tìm…');
    stopTimer(); if (yt && yt.pauseVideo) try { yt.pauseVideo(); } catch (e) {}
    yt = null;
    $('clbody').innerHTML = '<div class="fv"><div id="clyt"></div></div><div class="ft" id="clt"></div>';
    loadAll(raw).then(function (cl) {
      if (tok !== st.token) return;
      st.clips = cl; st.qn = q;
      if (!st.clips.length) {
        status('');
        $('clbody').innerHTML = '<div class="fk">Kho clip chưa có video nào nói đúng cụm <b>"' + esc(raw) + '"</b>.<br>' +
          'Bấm <button class="fb" id="clfm2">Filmot</button> để tìm trên toàn bộ YouTube (pop-up, giải captcha 1 lần).</div>';
        $('clfm2').onclick = function () { filmot(raw); };
        return;
      }
      go(0);
    }).catch(function () { if (tok === st.token) { status(''); $('clbody').innerHTML = '<div class="fk">Không tải được kho clip — thử lại sau.</div>'; } });
  }

  function go(i) {
    if (i >= st.clips.length) { status('đã hết ' + st.clips.length + ' video'); stopTimer(); return; }
    var tok = st.token, c = st.clips[i];
    st.i = i; st.rep = 0;
    st.seg = { s: Math.max(0, c.s - 1), e: c.e + 0.8 };
    var part = c.q !== st.qn;
    $('clt').innerHTML = (part ? '<div class="fn" style="margin-bottom:3px">Chưa có clip nói nguyên câu — đây là một cụm trong câu:</div>' : '') +
      '… ' + esc(c.b) + ' <mark>' + esc(part ? c.q : st.q) + '</mark> ' + esc(c.a) + ' …' +
      '<div class="fn" style="margin-top:4px">' + esc(c.ch) + ' · <a href="https://www.youtube.com/watch?v=' + c.id + '&t=' + Math.floor(st.seg.s) + 's" target="_blank" rel="noopener">mở trên YouTube</a></div>';
    count();
    ytApi().then(function () {
      if (tok !== st.token || st.i !== i) return;
      if (yt && yt.loadVideoById) { yt.loadVideoById({ videoId: c.id, startSeconds: st.seg.s }); startTimer(); return; }
      yt = new YT.Player('clyt', {
        videoId: c.id, width: '100%', height: '100%',
        playerVars: { start: Math.floor(st.seg.s), autoplay: 1, playsinline: 1, rel: 0, modestbranding: 1, cc_load_policy: 1, cc_lang_pref: 'en' },
        events: {
          onReady: function (e) { e.target.seekTo(st.seg.s, true); e.target.playVideo(); startTimer(); },
          onError: function () { go(st.i + 1); }            // video bị gỡ / chặn nhúng → bỏ qua
        }
      });
    });
  }
  function seekStart() { if (yt && yt.seekTo) { yt.seekTo(st.seg.s, true); yt.playVideo(); } count(); }
  function stopTimer() { clearInterval(st.timer); st.timer = null; }
  function startTimer() {
    stopTimer();
    st.timer = setInterval(function () {
      if (!yt || !yt.getCurrentTime || !st.seg || box.hidden) return;
      if (yt.getCurrentTime() >= st.seg.e) {
        st.rep++;
        if (st.rep < REPEAT) seekStart(); else go(st.i + 1);
      }
    }, 150);
  }

  function open(q) {
    q = String(q || '').replace(/["“”]/g, '').replace(/\s+/g, ' ').trim();
    if (!q) return;
    build(); box.hidden = false; box.scrollTop = 0;
    search(q);
  }
  function close() {
    if (!box) return;
    st.token++; stopTimer();
    if (yt && yt.pauseVideo) try { yt.pauseVideo(); } catch (e) {}
    box.hidden = true;
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-clip]');
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
    e.preventDefault(); open(a.getAttribute('data-clip'));
  });
  window.ClipPlayer = { open: open, close: close, url: filmotUrl, norm: norm, parts: parts };
})();
