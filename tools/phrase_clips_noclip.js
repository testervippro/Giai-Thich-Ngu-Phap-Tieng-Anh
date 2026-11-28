// Kho cụm từ: mức clip của từng cụm → ô chọn "🎬 Video" lọc theo mức:
//   0 không có · 1 chỉ có clip bù (dạng khác / cụm trong câu / phần lõi) · 2 đúng nguyên cụm 1–9 · 3 đủ 10 video đúng nguyên cụm
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
const cnt = [0, 0, 0, 0];
ctx.window.PHRASES.items.forEach(a => {
  const q = ctx.ygq(a[1]), n = has.get(CP.norm(q)) || 0;
  const l = n >= 10 ? 3 : n ? 2 : [...CP.variants(q), ...CP.parts(q), ...CP.cores(q)].some(k => has.has(k)) ? 1 : 0;
  lv += l; cnt[l]++;
});
fs.writeFileSync(path.join(ROOT, 'docs/tools/phrase-bank-noclip.js'),
  '// sinh bởi tools/phrase_clips_noclip.js — mức clip từng cụm (theo thứ tự PHRASES.items): 0 không có · 1 chỉ clip bù · 2 đúng cụm 1–9 · 3 đủ 10 video đúng cụm\nwindow.PB_CLIPLV=' + JSON.stringify(lv) + ';\n');
console.log('mức 0..3:', cnt.join(' / '), '→ docs/tools/phrase-bank-noclip.js');
// trang Từ vựng TOEIC·IELTS·Oxford: cùng thang mức, theo thứ tự VOCAB_INDEX.rows
const vx = { window: {} }; vm.createContext(vx);
vm.runInContext(R('docs/tools/vocab-index-data.js'), vx);
let vl = ''; const vc = [0, 0, 0, 0];
vx.window.VOCAB_INDEX.rows.forEach(r => {
  const q = CP.clean(r[0]), n = has.get(CP.norm(q)) || 0;
  const l = n >= 10 ? 3 : n ? 2 : [...CP.variants(q), ...CP.parts(q), ...CP.cores(q)].some(k => has.has(k)) ? 1 : 0;
  vl += l; vc[l]++;
});
fs.writeFileSync(path.join(ROOT, 'docs/tools/vocab-index-cliplv.js'),
  '// sinh bởi tools/phrase_clips_noclip.js — mức clip từng mục (theo thứ tự VOCAB_INDEX.rows): 0 không có · 1 chỉ clip bù · 2 đúng 1–9 · 3 đủ 10 video\nwindow.VI_CLIPLV=' + JSON.stringify(vl) + ';\n');
console.log('Từ vựng mức 0..3:', vc.join(' / '), '→ docs/tools/vocab-index-cliplv.js');
