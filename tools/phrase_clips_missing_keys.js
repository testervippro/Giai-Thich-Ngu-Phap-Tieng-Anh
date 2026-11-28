// Mục chưa có video (mức 0) của Kho cụm từ + Từ vựng → build/phrase-clips/missing_keys.json
// { "pb": [[cụm, [khoá…]]…], "vi": [[từ, [khoá…]]…] }  khoá = cụm đã chuẩn hoá + dạng khác / cụm trong câu / phần lõi
// dùng cho tools/phrase_clips_watch.py (cập nhật file txt khi tải thêm phụ đề)
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..'), R = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const c = { window: {}, document: { currentScript: null, addEventListener() {} } }; vm.createContext(c);
vm.runInContext(R('docs/assets/clip-player.js'), c);
const CP = c.window.ClipPlayer;
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(R('docs/tools/phrase-bank-data.js'), ctx);
vm.runInContext(R('docs/tools/phrase-bank.html').match(/function ygq\(p\) \{[\s\S]*?\n  \}/)[0], ctx);
vm.runInContext(R('docs/tools/vocab-index-data.js'), ctx);
vm.runInContext(R('docs/tools/phrase-bank-noclip.js'), ctx); vm.runInContext(R('docs/tools/vocab-index-cliplv.js'), ctx);
const keys = q => [...new Set([CP.norm(q), ...CP.variants(q), ...CP.parts(q), ...CP.cores(q)].filter(Boolean))];
const pb = [], vi = [], seen = new Set();
ctx.window.PHRASES.items.forEach((a, i) => { if (ctx.window.PB_CLIPLV[i] !== '0') return; const q = ctx.ygq(a[1]); if (!seen.has(q)) { seen.add(q); pb.push([q, keys(q)]); } });
seen.clear();
ctx.window.VOCAB_INDEX.rows.forEach((r, i) => { if (ctx.window.VI_CLIPLV[i] !== '0') return; const q = CP.clean(r[0]); if (!seen.has(q)) { seen.add(q); vi.push([q, keys(q)]); } });
fs.writeFileSync(path.join(ROOT, 'build/phrase-clips/missing_keys.json'), JSON.stringify({ pb, vi }));
console.log('Kho cụm từ', pb.length, '· Từ vựng', vi.length, '→ build/phrase-clips/missing_keys.json');
