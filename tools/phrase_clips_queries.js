// Danh sách cụm cần tìm clip (tools/phrase_clips.py index) — lấy ĐÚNG cụm mà nút 🎬 của từng trang sẽ hỏi.
// Hàm cắt cụm (ygq, chunk…) đọc thẳng từ mã nguồn các trang để luôn khớp với trang.
//    node tools/phrase_clips_queries.js > build/phrase-clips/queries.txt
const fs = require('fs'), path = require('path'), vm = require('vm');
const R = p => fs.readFileSync(path.join(__dirname, '..', p), 'utf8');
const grab = (src, re) => { const m = src.match(re); if (!m) throw new Error('không thấy ' + re); return m[0]; };
const out = new Set();
const add = q => { q = String(q || '').replace(/["“”]/g, '').replace(/\s+/g, ' ').trim(); if (q && /[A-Za-z]/.test(q)) out.add(q); };

// 1. Kho cụm từ
{
  const html = R('docs/tools/phrase-bank.html');
  const ctx = { window: {} }; vm.createContext(ctx);
  vm.runInContext(R('docs/tools/phrase-bank-data.js'), ctx);
  vm.runInContext(grab(html, /function ygq\(p\) \{[\s\S]*?\n  \}/), ctx);
  for (const a of ctx.window.PHRASES.items) add(ctx.ygq(a[1]));
}
// 2. Master Listening: các cụm (chunk) của mọi câu
{
  const html = R('docs/tools/listening-master.html');
  const ctx = { window: {} }; vm.createContext(ctx);
  vm.runInContext(R('docs/tools/listening-master-data.js'), ctx);
  vm.runInContext(grab(html, /const CONJ = .*\n/) + grab(html, /const PREP = .*\n/) + grab(html, /function chunk\(s\) \{[\s\S]*?\n  \}/) +
    grab(html, /const ygq = .*\n/).replace('const ygq', 'var ygq'), ctx);
  for (const [t] of ctx.window.LM_SENT || []) for (const c of ctx.chunk(t)) add(ctx.ygq(c));
}
// 3. Cụm giao tiếp trong phim
{
  const html = R('docs/movie-viewer/cum-giao-tiep.html');
  const D = JSON.parse(grab(html, /const D = (\{.*\});\n/).replace(/^const D = /, '').replace(/;\n$/, ''));
  const q = t => String(t).replace(/[…()]/g, '').replace(/\s+/g, ' ').trim();
  for (const S of D.shows) {
    for (const r of S.rows || []) add(q(r[0]));
  }
  for (const k of ['daily', 'all']) for (const r of D[k] || []) add(q(String(r[1]).replace(/\([^)]*\)|\.\.\.|…/g, '').trim()));
}
// 4. cụm ngắn trong câu dài (trình phát bù khi câu chưa đủ clip nguyên văn) — dùng chính parts() của clip-player.js
{
  const ctx = { window: {}, document: { currentScript: null, addEventListener() {} } }; vm.createContext(ctx);
  vm.runInContext(R('docs/assets/clip-player.js'), ctx);
  for (const q of [...out]) for (const p of ctx.window.ClipPlayer.parts(q)) out.add(p);
}
process.stdout.write([...out].join('\n') + '\n');
process.stderr.write(out.size + ' cụm\n');
