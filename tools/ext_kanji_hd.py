#!/usr/bin/env python3
"""Thay ảnh thẻ kanji của Chrome extension (images/kanji/<HEX>.jpg) bằng ảnh nét hơn
lấy từ docs/kanji-viewer/kanji_p1|p2 (1568px), ghép theo số thẻ trong kanji-game-data.js.
Dùng: python3 tools/ext_kanji_hd.py <thư mục extension> [--width 1100] [--quality 82]"""
import argparse, json, os
from PIL import Image
ap=argparse.ArgumentParser(); ap.add_argument('ext'); ap.add_argument('--width',type=int,default=1100); ap.add_argument('--quality',type=int,default=82)
a=ap.parse_args()
V=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'docs','kanji-viewer')
s=open(os.path.join(V,'kanji-game-data.js'),encoding='utf8').read()
arr,_=json.JSONDecoder().raw_decode(s[s.index('window.KANJI=')+13:])
by={r[1]:r[6] for r in arr if r[6]}
d=os.path.join(a.ext,'images','kanji'); ok=miss=0
for f in sorted(os.listdir(d)):
    if not f.endswith('.jpg'): continue
    ch=chr(int(f[:-4],16)); p=by.get(ch)
    if not p or not os.path.exists(os.path.join(V,p)): miss+=1; print('thiếu',ch,f); continue
    im=Image.open(os.path.join(V,p)).convert('RGB')
    if im.width>a.width: im=im.resize((a.width,round(im.height*a.width/im.width)),Image.LANCZOS)
    im.save(os.path.join(d,f),'JPEG',quality=a.quality,optimize=True); ok+=1
print('đã thay',ok,'thiếu',miss)
