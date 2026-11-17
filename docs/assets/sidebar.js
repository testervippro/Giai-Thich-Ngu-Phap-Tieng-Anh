/* Sidebar gọn: nhóm thu gọn / mở rộng (nhớ trạng thái), nút Mở hết / Thu hết, ô tìm trong menu.
   Mỗi "# Tiêu đề" trong _sidebar.md = 1 nhóm; mục có danh sách con = nhóm con. */
(function () {
  var KEY = 'sb-open', open = [];
  try { open = JSON.parse(localStorage.getItem(KEY) || '[]') || []; } catch (e) { open = []; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(open)); } catch (e) {} }
  function setOpen(k, v) {
    var i = open.indexOf(k);
    if (v && i < 0) open.push(k);
    if (!v && i >= 0) open.splice(i, 1);
    save();
  }
  function norm(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd');
  }
  function ownText(li) {
    var t = '';
    li.childNodes.forEach(function (n) { if (n.nodeName !== 'UL' && !(n.classList && n.classList.contains('sb-caret'))) t += n.textContent; });
    return t.trim();
  }

  function build() {
    var nav = document.querySelector('.sidebar-nav');
    if (!nav || nav.getAttribute('data-sb')) return nav;
    nav.setAttribute('data-sb', '1');
    var g = null, body = null;
    [].slice.call(nav.children).forEach(function (el) {
      if (el.tagName === 'H1') {
        var t = el.textContent.trim();
        g = document.createElement('div'); g.className = 'sb-group'; g.setAttribute('data-k', t);
        var h = document.createElement('button'); h.type = 'button'; h.className = 'sb-head';
        h.innerHTML = '<span class="sb-arrow"></span><span></span>'; h.lastChild.textContent = t;
        body = document.createElement('div'); body.className = 'sb-body';
        g.appendChild(h); g.appendChild(body);
        nav.insertBefore(g, el); el.parentNode.removeChild(el);
      } else if (el.tagName === 'HR') {
        el.parentNode.removeChild(el);
      } else if (body) {
        body.appendChild(el);
      }
    });
    nav.querySelectorAll('li').forEach(function (li) {
      var ul = null;
      for (var i = 0; i < li.children.length; i++) if (li.children[i].tagName === 'UL') ul = li.children[i];
      if (!ul) return;
      var grp = li.closest('.sb-group');
      li.classList.add('sb-sub');
      li.setAttribute('data-k', (grp ? grp.getAttribute('data-k') : '') + ' / ' + ownText(li));
      var c = document.createElement('button'); c.type = 'button'; c.className = 'sb-caret'; c.setAttribute('aria-label', 'Mở / thu');
      li.insertBefore(c, li.firstChild);
      var n = 0; ul.querySelectorAll('a').forEach(function () { n++; });
      var lab = li.querySelector(':scope > strong, :scope > p');
      if (lab) { lab.classList.add('sb-lab'); lab.insertAdjacentHTML('beforeend', ' <span class="sb-n">' + n + '</span>'); }
    });
    apply(nav);
    return nav;
  }

  function apply(nav) {
    nav.querySelectorAll('.sb-group, li.sb-sub').forEach(function (el) {
      el.classList.toggle('sb-closed', open.indexOf(el.getAttribute('data-k')) < 0);
    });
  }

  function revealActive() {
    var nav = document.querySelector('.sidebar-nav'); if (!nav) return;
    var a = nav.querySelector('li.active');
    if (!a) return;
    for (var p = a.parentElement; p && p !== nav; p = p.parentElement) {
      if (p.classList.contains('sb-closed')) {
        p.classList.remove('sb-closed');
        setOpen(p.getAttribute('data-k'), true);
      }
    }
    var r = a.getBoundingClientRect(), sb = document.querySelector('.sidebar');
    if (sb && (r.top < 80 || r.bottom > window.innerHeight)) a.scrollIntoView({ block: 'center' });
  }

  function filter() {
    var nav = document.querySelector('.sidebar-nav'), inp = document.getElementById('sb-q');
    if (!nav || !inp) return;
    var q = norm(inp.value.trim());
    nav.classList.toggle('sb-filtering', !!q);
    var lis = nav.querySelectorAll('li');
    lis.forEach(function (li) { li.classList.remove('sb-hide'); });
    nav.querySelectorAll('.sb-group').forEach(function (g) { g.classList.remove('sb-hide'); });
    if (!q) return;
    lis.forEach(function (li) {
      var self = norm(ownText(li)).indexOf(q) >= 0;
      var up = false;
      for (var p = li.parentElement; p && p !== nav; p = p.parentElement) {
        if (p.tagName === 'LI' && norm(ownText(p)).indexOf(q) >= 0) { up = true; break; }
      }
      var down = false;
      li.querySelectorAll('li').forEach(function (d) { if (norm(ownText(d)).indexOf(q) >= 0) down = true; });
      if (!(self || up || down)) li.classList.add('sb-hide');
    });
    nav.querySelectorAll('.sb-group').forEach(function (g) {
      var head = norm(g.getAttribute('data-k')).indexOf(q) >= 0;
      if (head) { g.querySelectorAll('li').forEach(function (li) { li.classList.remove('sb-hide'); }); return; }
      if (!g.querySelector('li:not(.sb-hide)')) g.classList.add('sb-hide');
    });
  }

  function tools() {
    var sb = document.querySelector('.sidebar'), nav = document.querySelector('.sidebar-nav');
    if (!sb || !nav || document.getElementById('sb-tools')) return;
    var d = document.createElement('div'); d.id = 'sb-tools';
    d.innerHTML = '<input id="sb-q" type="search" placeholder="🔍 Tìm trong menu…" autocomplete="off">' +
      '<div class="sb-row"><button type="button" data-act="open">⊞ Mở hết</button>' +
      '<button type="button" data-act="close">⊟ Thu hết</button></div>';
    sb.insertBefore(d, nav);
    d.querySelector('#sb-q').addEventListener('input', filter);
    d.addEventListener('click', function (e) {
      e.stopPropagation(); // trên điện thoại docsify đóng sidebar khi bấm vào nó
      var b = e.target.closest('button'); if (!b) return;
      var n = document.querySelector('.sidebar-nav');
      if (b.getAttribute('data-act') === 'open') {
        open = []; n.querySelectorAll('.sb-group, li.sb-sub').forEach(function (el) { open.push(el.getAttribute('data-k')); });
      } else open = [];
      save(); apply(n);
    });
  }

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t.closest || !t.closest('.sidebar-nav')) return;
    var head = t.closest('.sb-head'), caret = t.closest('.sb-caret'), lab = t.closest('.sb-lab');
    var el = head ? head.parentElement : (caret || lab) ? (caret || lab).parentElement : null;
    if (!el) return;
    e.preventDefault(); e.stopPropagation();
    var closed = el.classList.toggle('sb-closed');
    setOpen(el.getAttribute('data-k'), !closed);
  }, true);

  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.doneEach(function () {
      build(); tools(); filter();
      setTimeout(revealActive, 0);
    });
  });
})();
