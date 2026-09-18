"""Build the prototype: inlines every icon (and any photos) into one self-contained HTML file.

Usage:  python3 src/build.py        → writes index.html next to the src folder
"""
import base64, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MIME = {'.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif'}

def load(folder):
    out = {}
    path = os.path.join(HERE, folder)
    if not os.path.isdir(path):
        return out
    for f in sorted(os.listdir(path)):
        name, ext = os.path.splitext(f)
        if ext.lower() in MIME:
            data = base64.b64encode(open(os.path.join(path, f), 'rb').read()).decode()
            out[name] = f"data:{MIME[ext.lower()]};base64,{data}"
    return out

html = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
html = html.replace('/*ICONS*/{}/*END*/', json.dumps(load('icons')))
html = html.replace('/*PHOTOS*/{}/*END*/', json.dumps(load('photos')))
out = os.path.join(ROOT, 'index.html')
open(out, 'w', encoding='utf-8').write(html)
print(f"Built {out} ({len(html)//1024} KB)")
