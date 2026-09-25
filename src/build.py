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

def font(name):
    """One woff2 as a data URI, for the @font-face src.

    Inter is inlined rather than pulled from fonts.googleapis.com at runtime. On a network that
    blocks Google Fonts the link tag fails silently, the page falls back to system-ui, and the
    whole prototype quietly renders in the wrong typeface — which is exactly what happened.
    Inlining costs ~180KB and removes the failure mode entirely.
    """
    data = base64.b64encode(open(os.path.join(HERE, 'fonts', name), 'rb').read()).decode()
    return f"data:font/woff2;base64,{data}"

html = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
html = html.replace('/*ICONS*/{}/*END*/', json.dumps(load('icons')))
html = html.replace('/*PHOTOS*/{}/*END*/', json.dumps(load('photos')))
html = html.replace('/*INTER-LATIN*/', font('inter-latin.woff2'))
html = html.replace('/*INTER-LATIN-EXT*/', font('inter-latin-ext.woff2'))
out = os.path.join(ROOT, 'index.html')
open(out, 'w', encoding='utf-8').write(html)
print(f"Built {out} ({len(html)//1024} KB)")
