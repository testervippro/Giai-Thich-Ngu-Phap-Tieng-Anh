#!/usr/bin/env python3
"""Chép ảnh câu chuyện HD (docs/kanji-viewer/kanji_story) vào extension: <ext>/images/story/<HEX>.webp (rộng 1000px).
Ghi danh sách chữ vào <ext>/kanji_story_images.js. Dùng: python3 tools/ext_story_hd.py <thư mục extension>"""
import json, os, sys
from PIL import Image
ext=sys.argv[1]; V=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'docs','kanji-viewer')
s=open(os.path.join(V,'kanji-game-data.js'),encoding='utf8').read()
K=json.JSONDecoder().raw_decode(s[s.index('window.KANJI=')+13:])[0]
d=os.path.join(ext,'images','story'); os.makedirs(d,exist_ok=True); chars=''
for r in K:
    f=os.path.join(V,'kanji_story','%04d.webp'%r[0])
    if not os.path.exists(f) or r[1] in chars: continue
    im=Image.open(f).convert('RGB')
    if im.width>1000: im=im.resize((1000,round(im.height*1000/im.width)),Image.LANCZOS)
    im.save(os.path.join(d,'%04X.webp'%ord(r[1])),quality=80,method=4); chars+=r[1]
open(os.path.join(ext,'kanji_story_images.js'),'w',encoding='utf8').write('// File tự sinh bởi tools/ext_story_hd.py\nconst KANJI_STORY_IMAGES = "%s";\n'%chars)
print('xong',len(chars))
