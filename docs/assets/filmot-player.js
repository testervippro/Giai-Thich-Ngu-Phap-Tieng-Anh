/* Nghe người thật nói một cụm từ: tìm CHÍNH XÁC cụm (trong dấu "") trên phụ đề YouTube qua Filmot,
   tối đa 50 video, phát đúng đoạn có cụm ngay trên trang, mỗi đoạn tự phát 3 lần rồi sang video sau.
   Dữ liệu: API chính thức của Filmot trên RapidAPI (filmot-tube-metadata-archive) — cần key của người dùng,
   key chỉ lưu trong localStorage của trình duyệt, không nằm trong mã nguồn.

   Dùng:  <script src="../assets/filmot-player.js"></script>
          FilmotPlayer.open('break the ice')          // hoặc thẻ <a data-filmot="break the ice">
*/
(function () {
  'use strict';
  var HOST = 'filmot-tube-metadata-archive.p.rapidapi.com';
  var SUB = 'https://rapidapi.com/hub';
  var MAX = 50, REPEAT = 3;
  var KEY = 'filmotKey';
  var st = { q: '', vids: [], i: 0, rep: 0, seg: null, timer: null, token: 0, more: [] };
  var yt = null, ytReady = null, box = null;

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function getKey() { try { return localStorage.getItem(KEY) || ''; } catch (e) { return ''; } }
  function setKey(k) { try { if (k) localStorage.setItem(KEY, k); else localStorage.removeItem(KEY); } catch (e) {} }
  function fUrl(q) { return 'https://filmot.com/search/' + encodeURIComponent('"' + q + '"') + '/1?lang=en'; }

  function css() {
    var s = document.createElement('style');
    s.textContent =
      '#fmp{position:fixed;left:50%;bottom:0;transform:translateX(-50%);width:min(580px,100%);max-height:94vh;overflow:auto;z-index:9999;' +
      'background:var(--card,#fff);color:var(--ink,#222);border:1px solid var(--line,#ddd);border-bottom:0;border-radius:14px 14px 0 0;box-shadow:0 -8px 30px rgba(0,0,0,.28);font:14px/1.45 system-ui,sans-serif}' +
      '#fmp[hidden]{display:none}' +
      '#fmp .fh{position:sticky;top:0;z-index:1;display:flex;gap:6px;align-items:center;padding:8px 10px;background:inherit;border-bottom:1px solid var(--line,#ddd)}' +
      '#fmp .fh b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
      '#fmp .fb{border:1px solid var(--line,#ddd);background:transparent;color:inherit;border-radius:8px;padding:3px 9px;cursor:pointer;font:inherit;text-decoration:none;white-space:nowrap}' +
      '#fmp .fn{color:var(--muted,#777);font-size:12.5px;white-space:nowrap}' +
      '#fmp .fv{position:relative;width:100%;aspect-ratio:16/9;background:#000}' +
      '#fmp .fv>*{position:absolute;inset:0;width:100%;height:100%}' +
      '#fmp .ft{padding:8px 12px;font-size:15.5px}' +
      '#fmp .ft mark{background:rgba(250,204,21,.5);color:inherit;border-radius:3px;padding:0 2px;font-weight:700}' +
      '#fmp .fm{padding:0 12px 10px;color:var(--muted,#777);font-size:12px}' +
      '#fmp .fm a{color:inherit}' +
      '#fmp .fk{padding:14px 12px}#fmp .fk input{width:100%;padding:7px 9px;border:1px solid var(--line,#ddd);border-radius:8px;font:inherit;margin:6px 0;background:transparent;color:inherit}';
    document.head.appendChild(s);
  }

  function build() {
    if (box) return;
    css();
    box = document.createElement('div');
    box.id = 'fmp'; box.hidden = true;
    box.innerHTML =
      '<div class="fh"><b id="fmq"></b><span class="fn" id="fmn"></span>' +
      '<button class="fb" id="fmpv" title="Video trước">⏮</button><button class="fb" id="fmrp" title="Phát lại đoạn này">🔁</button>' +
      '<button class="fb" id="fmnx" title="Video sau">⏭</button><a class="fb" id="fmo" target="_blank" rel="noopener" title="Mở trên filmot.com">↗</a>' +
      '<button class="fb" id="fmk" title="Đổi API key">⚙</button><button class="fb" id="fmx" title="Đóng (Esc)">✕</button></div>' +
      '<div id="fmbody"></div>' +
      '<div class="fm">Tìm đúng cụm trong phụ đề YouTube qua <a href="https://filmot.com" target="_blank" rel="noopener">Filmot</a> · mỗi đoạn phát ' + REPEAT + ' lần rồi tự sang video sau (tối đa ' + MAX + ' video) · ' +
      '<a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener">YouTube Terms</a></div>';
    document.body.appendChild(box);
    $('fmx').onclick = close;
    $('fmnx').onclick = function () { go(st.i + 1); };
    $('fmpv').onclick = function () { go(Math.max(0, st.i - 1)); };
    $('fmrp').onclick = function () { st.rep = 0; seekStart(); };
    $('fmk').onclick = function () { askKey(true); };
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !box.hidden) close(); });
  }

  function status(t) { $('fmn').textContent = t; }

  function askKey(change) {
    stopTimer(); if (yt && yt.pauseVideo) try { yt.pauseVideo(); } catch (e) {}
    yt = null;
    $('fmbody').innerHTML = '<div class="fk">Cần <b>API key Filmot</b> (RapidAPI) để tìm và phát clip ngay trên trang.<br>' +
      '1. Mở <a href="' + SUB + '" target="_blank" rel="noopener">trang Filmot trên RapidAPI</a> → đăng nhập → <b>Subscribe</b> gói Basic.<br>' +
      '2. Chép <b>X-RapidAPI-Key</b> dán vào đây (chỉ lưu trên trình duyệt này).' +
      '<input id="fmki" type="password" placeholder="X-RapidAPI-Key" value="' + esc(change ? getKey() : '') + '" autocomplete="off">' +
      '<button class="fb" id="fmks">Lưu & tìm</button> ' + (getKey() ? '<button class="fb" id="fmkd">Xoá key</button>' : '') + '</div>';
    status('');
    $('fmks').onclick = function () { setKey($('fmki').value.trim()); if (getKey() && st.q) search(st.q); };
    if ($('fmkd')) $('fmkd').onclick = function () { setKey(''); askKey(false); };
    $('fmki').onkeydown = function (e) { if (e.key === 'Enter') $('fmks').click(); };
    setTimeout(function () { $('fmki').focus(); }, 0);
  }

  function api(params) {
    var u = 'https://' + HOST + '/getsubtitlesearch?' + new URLSearchParams(params);
    return fetch(u, { headers: { 'X-RapidAPI-Key': getKey(), 'X-RapidAPI-Host': HOST } }).then(function (r) {
      if (r.status === 401 || r.status === 403) { var e = new Error('key'); e.key = true; throw e; }
      if (r.status === 429) throw new Error('Hết lượt gọi API (429) — thử lại sau hoặc nâng gói');
      if (!r.ok) throw new Error('Filmot lỗi ' + r.status);
      return r.json();
    });
  }

  // một video -> {id, title, ch, hit:{start,dur,before,after}} (chỉ lấy lần xuất hiện đầu tiên của cụm)
  function toVid(v) {
    var hits = (v.hits || []).slice().sort(function (a, b) { return +a.start - +b.start; });
    var h = hits[0];
    return { id: v.id, title: v.title || '', ch: v.channelname || '', hit: h ? { start: +h.start, dur: +h.dur || 0, before: h.ctx_before || '', after: h.ctx_after || '' } : null };
  }

  function search(q) {
    var tok = ++st.token;
    st.q = q; st.vids = []; st.more = []; st.i = 0;
    $('fmq').textContent = '🎬 "' + q + '"'; $('fmo').href = fUrl(q);
    if (!getKey()) return askKey(false);
    status('đang tìm…');
    $('fmbody').innerHTML = '<div class="fv"><div id="fmyt"></div></div><div class="ft" id="fmt"></div>';
    yt = null;
    var seen = {};
    function add(list) {
      (list || []).forEach(function (v) { if (v && v.id && !seen[v.id] && st.vids.length < MAX) { seen[v.id] = 1; st.vids.push(toVid(v)); } });
    }
    function page(p) {
      return api({ query: '"' + q + '"', lang: 'en', page: p }).then(function (j) {
        if (tok !== st.token) return;
        var before = st.vids.length;
        add(j.result);
        (j.more_results || []).forEach(function (m) { var id = m && (m.id || m); if (id && !seen[id] && st.vids.length < MAX) { seen[id] = 1; st.vids.push({ id: id, hit: null }); } });
        if (p === 1 && st.vids.length) go(0);
        if (st.vids.length < MAX && st.vids.length > before && p < 10) return page(p + 1);
      });
    }
    page(1).then(function () {
      if (tok !== st.token) return;
      if (!st.vids.length) { status(''); $('fmbody').innerHTML = '<div class="fk">Không có video nào nói đúng cụm <b>"' + esc(q) + '"</b>. Thử bớt từ hoặc bấm ↗.</div>'; }
      else count();
    }).catch(function (e) {
      if (tok !== st.token) return;
      if (e.key) { askKey(true); status('key sai / chưa Subscribe'); return; }
      if (st.vids.length) { count(); return; }       // đã có vài video: cứ phát
      status(''); $('fmbody').innerHTML = '<div class="fk">' + esc(e.message || 'Lỗi mạng') + ' — bấm ↗ để xem trên filmot.com.</div>';
    });
  }

  function count() { if (st.vids.length) status((st.i + 1) + '/' + st.vids.length + ' video · lần ' + Math.min(st.rep + 1, REPEAT) + '/' + REPEAT); }

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

  // video chỉ có id (từ more_results): hỏi Filmot thời điểm cụm xuất hiện trong video đó
  function ensureHit(v) {
    if (v.hit) return Promise.resolve(v);
    return api({ query: '"' + st.q + '"', lang: 'en', queryVideoID: v.id }).then(function (j) {
      var r = (j.result || []).filter(function (x) { return x.id === v.id; })[0] || (j.result || [])[0];
      if (r) { var t = toVid(r); v.hit = t.hit; v.title = t.title; v.ch = t.ch; }
      return v;
    });
  }

  function go(i) {
    if (i >= st.vids.length) { status('đã hết ' + st.vids.length + ' video'); stopTimer(); return; }
    var tok = st.token;
    st.i = i; st.rep = 0;
    var v = st.vids[i];
    status('đang mở ' + (i + 1) + '/' + st.vids.length + '…');
    ensureHit(v).then(function () {
      if (tok !== st.token || st.i !== i) return;
      if (!v.hit) return go(i + 1);
      var words = st.q.split(/\s+/).length;
      var s0 = Math.max(0, v.hit.start - 1);
      st.seg = { s: s0, e: v.hit.start + Math.max(v.hit.dur, 0.45 * words + 1.2) + 1 };
      $('fmt').innerHTML = esc(v.hit.before) + ' <mark>' + esc(st.q) + '</mark> ' + esc(v.hit.after) +
        '<div class="fn" style="margin-top:4px">' + esc(v.title) + (v.ch ? ' · ' + esc(v.ch) : '') + '</div>';
      count();
      return ytApi().then(function () {
        if (tok !== st.token || st.i !== i) return;
        if (yt && yt.loadVideoById) { yt.loadVideoById({ videoId: v.id, startSeconds: s0 }); startTimer(); return; }
        yt = new YT.Player('fmyt', {
          videoId: v.id, width: '100%', height: '100%',
          playerVars: { start: Math.floor(s0), autoplay: 1, playsinline: 1, rel: 0, modestbranding: 1, cc_load_policy: 1, cc_lang_pref: 'en' },
          events: {
            onReady: function (e) { e.target.seekTo(st.seg.s, true); e.target.playVideo(); startTimer(); },
            onError: function () { go(st.i + 1); }              // video bị gỡ / chặn nhúng → bỏ qua
          }
        });
      });
    }).catch(function () { if (tok === st.token) go(i + 1); });
  }

  function seekStart() { if (yt && yt.seekTo) { yt.seekTo(st.seg.s, true); yt.playVideo(); } count(); }
  function stopTimer() { clearInterval(st.timer); st.timer = null; }
  function startTimer() {
    stopTimer();
    st.timer = setInterval(function () {
      if (!yt || !yt.getCurrentTime || !st.seg || box.hidden) return;
      var t = yt.getCurrentTime();
      if (t >= st.seg.e) {
        st.rep++;
        if (st.rep < REPEAT) seekStart(); else go(st.i + 1);
      }
    }, 200);
  }

  function open(q) {
    q = String(q || '').replace(/["“”]/g, '').replace(/\s+/g, ' ').trim();
    if (!q) return;
    // trang RapidAPI của Filmot đã gỡ, không đăng ký key mới được → chưa có key thì mở thẳng filmot.com (tìm đúng cụm "...")
    if (!getKey()) { window.open(fUrl(q), '_blank', 'noopener'); return; }
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
    var a = e.target.closest && e.target.closest('[data-filmot]');
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
    e.preventDefault(); open(a.getAttribute('data-filmot'));
  });
  window.FilmotPlayer = { open: open, close: close, url: fUrl };
})();
