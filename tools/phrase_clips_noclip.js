// Kho cụm từ: mức clip của từng cụm → ô chọn "🎬 Video" lọc theo mức:
//   0 không có · 1 chỉ có clip bù (dạng khác / cụm trong câu / phần lõi) · 2 đúng nguyên cụm 1–9 · 3 đúng nguyên cụm 10–49 · 4 đủ 50
// Chạy sau tools/phrase_clips.py index:
//    node tools/phrase_clips_noclip.js        # -> docs/tools/phrase-bank-noclip.js
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..'), R = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const has = new Map();
for (let i = 0; i < 64; i++) for (const [k, v] of Object.entries(JSON.parse(R(`docs/assets/clips/${String(i).padStart(2, '0')}.json`)))) if (v.length) has.set(k, v.length);
const c = { window: {}, document: { currentScript: null, addEventListener() {} } }; vm.createContext(c);
vm.runInContext(R('docs/assets/clip-player.js'), c);
const CP = c.window.ClipPlayer;
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(R('docs/tools/phrase-bank-data.js'), ctx);
vm.runInContext(R('docs/tools/phrase-bank.html').match(/function ygq\(p\) \{[\s\S]*?\n  \}/)[0], ctx);
let lv = '';
const cnt = [0, 0, 0, 0, 0];
ctx.window.PHRASES.items.forEach(a => {
  const q = ctx.ygq(a[1]), n = has.get(CP.norm(q)) || 0;
  const l = n >= 50 ? 4 : n >= 10 ? 3 : n ? 2 : [...CP.variants(q), ...CP.parts(q), ...CP.cores(q)].some(k => has.has(k)) ? 1 : 0;
  lv += l; cnt[l]++;
});
fs.writeFileSync(path.join(ROOT, 'docs/tools/phrase-bank-noclip.js'),
  '// sinh bởi tools/phrase_clips_noclip.js — mức clip từng cụm (theo thứ tự PHRASES.items): 0 không có · 1 chỉ clip bù · 2 đúng cụm 1–9 · 3 đúng cụm 10–49 · 4 đủ 50\nwindow.PB_CLIPLV=' + JSON.stringify(lv) + ';\n');
console.log('mức 0..4:', cnt.join(' / '), '→ docs/tools/phrase-bank-noclip.js');
