// Kho cụm từ: danh sách cụm KHÔNG có clip nào (kể cả bù bằng dạng khác / cụm trong câu / phần lõi) → nút "Có video" ẩn chúng.
// Chạy sau tools/phrase_clips.py index:
//    node tools/phrase_clips_noclip.js        # -> docs/tools/phrase-bank-noclip.js
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..'), R = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const has = new Set();
for (let i = 0; i < 64; i++) for (const [k, v] of Object.entries(JSON.parse(R(`docs/assets/clips/${String(i).padStart(2, '0')}.json`)))) if (v.length) has.add(k);
const c = { window: {}, document: { currentScript: null, addEventListener() {} } }; vm.createContext(c);
vm.runInContext(R('docs/assets/clip-player.js'), c);
const CP = c.window.ClipPlayer;
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(R('docs/tools/phrase-bank-data.js'), ctx);
vm.runInContext(R('docs/tools/phrase-bank.html').match(/function ygq\(p\) \{[\s\S]*?\n  \}/)[0], ctx);
const none = [];
ctx.window.PHRASES.items.forEach((a, ix) => {
  const q = ctx.ygq(a[1]);
  const keys = [CP.norm(q), ...CP.variants(q), ...CP.parts(q), ...CP.cores(q)];
  if (!keys.some(k => has.has(k))) none.push(ix);
});
fs.writeFileSync(path.join(ROOT, 'docs/tools/phrase-bank-noclip.js'),
  '// sinh bởi tools/phrase_clips_noclip.js — chỉ số cụm (PHRASES.items) chưa có clip nào trong docs/assets/clips\nwindow.PB_NOCLIP=' + JSON.stringify(none) + ';\n');
console.log(`${none.length}/${ctx.window.PHRASES.items.length} cụm chưa có clip → docs/tools/phrase-bank-noclip.js`);
