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
  var vids = null, shards = {}, yt = null, ytReady = null, box = null;

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  // giống norm_words() trong tools/phrase_clips.py
  var SPOKEN = { gonna: 'going to', wanna: 'want to', gotta: 'got to', kinda: 'kind of', sorta: 'sort of', lemme: 'let me', gimme: 'give me',
    ya: 'you', outta: 'out of', dunno: "don't know", mornin: 'morning', nothin: 'nothing', somethin: 'something', "'em": 'them', cuz: 'because' };
  function norm(t) {
    return (String(t).replace(/[’‘]/g, "'").toLowerCase().match(/[a-z0-9]+(?:'[a-z0-9]+)*/g) || [])
      .map(function (w) { return SPOKEN.hasOwnProperty(w) ? SPOKEN[w] : w; }).join(' ');
  }
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
  // ---- bậc 1: dạng khác của CÙNG cụm (viết tắt ↔ đầy đủ, động từ đầu cụm chia thì) ----
  var CONTR = { "i'm": 'i am', "you're": 'you are', "we're": 'we are', "they're": 'they are', "it's": 'it is', "that's": 'that is',
    "he's": 'he is', "she's": 'she is', "what's": 'what is', "there's": 'there is', "here's": 'here is', "who's": 'who is', "how's": 'how is',
    "i've": 'i have', "you've": 'you have', "we've": 'we have', "they've": 'they have', "i'll": 'i will', "you'll": 'you will',
    "we'll": 'we will', "it'll": 'it will', "i'd": 'i would', "you'd": 'you would', "we'd": 'we would', "don't": 'do not',
    "doesn't": 'does not', "didn't": 'did not', "can't": 'cannot', "won't": 'will not', "isn't": 'is not', "aren't": 'are not',
    "wasn't": 'was not', "weren't": 'were not', "haven't": 'have not', "hasn't": 'has not', "wouldn't": 'would not',
    "couldn't": 'could not', "shouldn't": 'should not', "let's": 'let us', "how've": 'how have', "what've": 'what have',
    "could've": 'could have', "should've": 'should have', "would've": 'would have', "might've": 'might have', "must've": 'must have',
    "where's": 'where is', "why's": 'why is', "you'd've": 'you would have', "y'all": 'you all' };
  var UNCONTR = {}; Object.keys(CONTR).forEach(function (k) { UNCONTR[CONTR[k]] = k; });
  var IRR = { be: 'is are was were been being', have: 'has had having', do: 'does did done doing', go: 'goes went gone going',
    get: 'gets got gotten getting', make: 'makes made making', take: 'takes took taken taking', give: 'gives gave given giving',
    come: 'comes came coming', keep: 'keeps kept keeping', bring: 'brings brought bringing', pay: 'pays paid paying',
    say: 'says said saying', tell: 'tells told telling', see: 'sees saw seen seeing', find: 'finds found finding',
    think: 'thinks thought thinking', hold: 'holds held holding', run: 'runs ran running', put: 'puts putting',
    set: 'sets setting', cut: 'cuts cutting', let: 'lets letting', hit: 'hits hitting', catch: 'catches caught catching',
    break: 'breaks broke broken breaking', speak: 'speaks spoke spoken speaking', lose: 'loses lost losing',
    leave: 'leaves left leaving', feel: 'feels felt feeling', meet: 'meets met meeting', sell: 'sells sold selling',
    send: 'sends sent sending', spend: 'spends spent spending', stand: 'stands stood standing', buy: 'buys bought buying',
    fall: 'falls fell fallen falling', write: 'writes wrote written writing', drive: 'drives drove driven driving',
    know: 'knows knew known knowing', grow: 'grows grew grown growing', throw: 'throws threw thrown throwing',
    draw: 'draws drew drawn drawing', bite: 'bites bit bitten biting', hide: 'hides hid hidden hiding',
    ride: 'rides rode ridden riding', rise: 'rises rose risen rising', shake: 'shakes shook shaken shaking',
    sleep: 'sleeps slept sleeping', sit: 'sits sat sitting', win: 'wins won winning', lead: 'leads led leading',
    read: 'reads reading', hear: 'hears heard hearing', mean: 'means meant meaning', build: 'builds built building',
    lend: 'lends lent lending', bear: 'bears bore borne bearing', wear: 'wears wore worn wearing', tear: 'tears tore torn tearing',
    swim: 'swims swam swum swimming', sing: 'sings sang sung singing', begin: 'begins began begun beginning',
    shut: 'shuts shutting', blow: 'blows blew blown blowing', fly: 'flies flew flown flying', lay: 'lays laid laying',
    lie: 'lies lay lain lying', teach: 'teaches taught teaching', fight: 'fights fought fighting', seek: 'seeks sought seeking',
    deal: 'deals dealt dealing', stick: 'sticks stuck sticking', strike: 'strikes struck striking', hang: 'hangs hung hanging' };
  var NOTVERB = /^(i|you|we|they|he|she|it|this|that|these|those|there|here|what|who|how|why|when|where|which|the|a|an|my|your|our|their|his|her|its|no|not|all|any|some|every|each|one|in|on|at|for|with|from|by|about|of|to|as|and|or|but|so|if|very|too|just|really|well|oh|hey|hi|yes|yeah|ok|okay|please|sorry|thanks|thank|can|could|will|would|shall|should|may|might|must|is|are|was|were|am|i'm|it's|that's|let's|don't|nice|good|great|long|first|last|more|most|less|much|many|never|always|once|again|out|up|down|off|over)$/;
  function inflect(v) {
    if (IRR[v]) return IRR[v].split(' ');
    if (!/^[a-z]{3,}$/.test(v)) return [];
    var c = /[^aeiou]y$/.test(v) ? v.slice(0, -1) + 'ie' : v, e = /e$/.test(v) ? v.slice(0, -1) : v;
    var dbl = /^[^aeiou]*[aeiou][bdgmnprt]$/.test(v) ? v + v.slice(-1) : e;            // stop → stopped
    return [/(s|x|z|ch|sh)$/.test(v) ? v + 'es' : (c !== v ? c + 's' : v + 's'), (c !== v ? c + 'd' : /e$/.test(v) ? v + 'd' : dbl + 'ed'), dbl + 'ing'];
  }
  function variants(raw) {
    var w = norm(raw).split(' '), out = [], full = w.join(' ');
    function add(a) { var t = a.join(' '); if (t !== full && out.indexOf(t) < 0) out.push(t); }
    // viết tắt ↔ đầy đủ
    var a = [], b = w.join(' ');
    w.forEach(function (x) { a.push(CONTR[x] || x); });
    add(a.join(' ').split(' '));
    Object.keys(UNCONTR).forEach(function (k) { var r = new RegExp('(^| )' + k + '( |$)'); if (r.test(b)) add(b.replace(r, '$1' + UNCONTR[k] + '$2').split(' ')); });
    if (w.length >= 2 && !NOTVERB.test(w[0])) inflect(w[0]).forEach(function (f) { add([f].concat(w.slice(1))); });
    return out;
  }
  // ---- bậc 3: cụm 3–5 từ vẫn chưa có → phần lõi (bỏ bớt 1–2 từ ở đầu / cuối, phải còn từ có nghĩa) ----
  var STOP = /^(i|you|we|they|he|she|it|me|him|her|us|them|my|your|the|a|an|to|of|in|on|at|for|with|and|or|but|so|that|this|is|are|was|be|am|i'm|it's|do|don't|can|will|would|just|really|very|not|no|if|as|by|from|up|out|get|got|have|has|what|how|well|oh)$/;
  function cores(raw) {
    var w = norm(raw).split(' '), out = [];
    if (w.length < 3) return out;
    for (var L = w.length - 1; L >= 2; L--) {
      for (var i = 0; i + L <= w.length; i++) {
        var s = w.slice(i, i + L);
        if (s.filter(function (x) { return !STOP.test(x); }).length < 2) continue;      // phải còn ≥ 2 từ có nghĩa
        var t = s.join(' '); if (out.indexOf(t) < 0) out.push(t);
      }
      if (L <= w.length - 2) break;                         // chỉ bỏ tối đa 2 từ
    }
    return out;
  }
  function ytUrl(q) { return 'https://www.youtube.com/results?search_query=' + encodeURIComponent('"' + q + '"'); }   // Ctrl/⌘ + bấm
  function getJSON(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); }
  function load(q) {
    var k = shard(q);
    if (!vids) vids = getJSON(BASE + 'v.json');
    if (!shards[k]) shards[k] = getJSON(BASE + (k < 10 ? '0' : '') + k + '.json');
    return Promise.all([vids, shards[k]]).then(function (r) {
      return (r[1][q] || []).map(function (c) { var v = r[0][c[0]]; return { id: v[0], ch: v[1], s: c[1] / 10, e: c[2] / 10, b: c[3], a: c[4], q: q }; });
    });
  }
  // ưu tiên: đúng nguyên cụm → dạng khác của cụm → các cụm ngắn trong câu dài → phần lõi của cụm; đủ 50 thì dừng
  function fill(out, seen, L, kind) {
    for (var r = 0; out.length < 50; r++) {
      var any = false;
      L.forEach(function (l) { if (l[r] && out.length < 50) { any = true; if (!seen[l[r].id]) { seen[l[r].id] = 1; l[r].kind = kind; out.push(l[r]); } } });
      if (!any) break;
    }
  }
  function loadAll(raw) {
    var tiers = [[norm(raw)], variants(raw), parts(raw), cores(raw)], out = [], seen = {};
    function step(k) {
      if (k >= tiers.length || out.length >= 50) return Promise.resolve(out);
      if (k === 3 && out.length) return Promise.resolve(out);          // phần lõi chỉ dùng khi chưa có clip nào
      return Promise.all(tiers[k].map(load)).then(function (L) { fill(out, seen, L, k); return step(k + 1); });
    }
    return step(0);
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
      '<button class="fb" id="clnx" title="Video sau">⏭</button>' +
      '<button class="fb" id="clx" title="Đóng (Esc)">✕</button></div>' +
      '<div id="clbody"></div>' +
      '<div class="fm">Clip YouTube (TED, talk show, podcast) có người nói <b>đúng nguyên cụm</b> · mỗi đoạn phát ' + REPEAT + ' lần rồi tự sang video sau · ' +
      '<a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener">YouTube Terms</a></div>';
    document.body.appendChild(box);
    $('clx').onclick = close;
    $('clnx').onclick = function () { go(st.i + 1); };
    $('clpv').onclick = function () { go(Math.max(0, st.i - 1)); };
    $('clrp').onclick = function () { st.rep = 0; seekStart(); };
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !box.hidden) close(); });
  }
  function status(t) { $('cln').textContent = t; }
  function count() { if (st.clips.length) status((st.i + 1) + '/' + st.clips.length + ' video · lần ' + Math.min(st.rep + 1, REPEAT) + '/' + REPEAT); }

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
        $('clbody').innerHTML = '<div class="fk">Kho clip chưa có video nào nói đúng cụm <b>"' + esc(raw) + '"</b>.</div>';
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
    var NOTE = ['', 'Dạng khác của cùng cụm:', 'Chưa có clip nói nguyên câu — đây là một cụm trong câu:', 'Chưa có clip nói nguyên cụm — đây là phần chính của cụm:'];
    var kind = c.kind || 0;
    $('clt').innerHTML = (kind ? '<div class="fn" style="margin-bottom:3px;white-space:normal">' + NOTE[kind] + '</div>' : '') +
      '… ' + esc(c.b) + ' <mark>' + esc(kind ? c.q : st.q) + '</mark> ' + esc(c.a) + ' …' +
      '<div class="fn" style="margin-top:4px">' + esc(c.ch) + ' · <a href="https://www.youtube.com/watch?v=' + c.id + '&t=' + Math.floor(st.seg.s) + 's" target="_blank" rel="noopener">mở trên YouTube</a></div>';
    count();
    ytApi().then(function () {
      if (tok !== st.token || st.i !== i) return;
      if (yt && yt.loadVideoById) { yt.loadVideoById({ videoId: c.id, startSeconds: st.seg.s, suggestedQuality: Q }); q360(); startTimer(); return; }
      yt = new YT.Player('clyt', {
        videoId: c.id, width: '100%', height: '100%',
        playerVars: { start: Math.floor(st.seg.s), vq: Q, autoplay: 1, playsinline: 1, rel: 0, modestbranding: 1, cc_load_policy: 1, cc_lang_pref: 'en' },
        events: {
          onReady: function (e) { q360(); e.target.seekTo(st.seg.s, true); e.target.playVideo(); startTimer(); },
          onStateChange: function (e) { if (e.data === 1) q360(); },
          onError: function () { go(st.i + 1); }            // video bị gỡ / chặn nhúng → bỏ qua
        }
      });
    });
  }
  // chất lượng 360p ('medium') cho nhẹ — YouTube coi đây là gợi ý, có thể tự đổi theo mạng
  var Q = 'medium';
  function q360() { try { if (yt && yt.setPlaybackQuality) yt.setPlaybackQuality(Q); } catch (e) {} }
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
  window.ClipPlayer = { open: open, close: close, url: ytUrl, norm: norm, parts: parts, variants: variants, cores: cores };
})();
