"""Generates the six icon Lotties in assets/ — the popup seal, the SKU selection marks, and the
four alert-band icons.

Same reason as build_walletchip.py: these motions exist only as CSS keyframes in template.html,
which is worth nothing outside a browser. A .json every Lottie player reads can go into the
Android app, into iOS, into Figma and into a ticket.

    python3 src/lottie/build_icons.py

The artwork is NOT redrawn here. Each file's shapes are the real `d` attribute out of
src/icons/*.svg, run through `parse_d` below, so the seal in the Lottie is the same seal the
prototype paints. The timings are the CSS percentages, kept as percentages.

Three deliberate departures from the CSS, all for size or for player support:

 - The soft blurred shadow under the two bells (`<g filter=...feGaussianBlur>`) is dropped.
   Lottie's blur is an effect layer that half the players ignore, and at 26px the shadow is two
   or three grey pixels.
 - The SKU border FADES IN rather than changing colour. The CSS crossfades gray-300 to orange
   over the same .2s; faded in over a developer's own grey border that is the same picture, and
   it keeps the file transparent so it can sit on any tile.
 - The corner triangle is drawn already-clipped to the tile's 13px corner radius instead of
   being masked by an overflow:hidden box. A track matte would cost a whole extra layer to
   change nothing you can see in 0.28s.
"""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(os.path.dirname(HERE), "icons")
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "assets")

FPS = 30

# CSS easings, split into Lottie's outgoing (o) and incoming (i) control points. A cubic-bezier
# with y past 1 overshoots; Lottie carries that fine and it is what gives the tick its snap.
EASE_IN_OUT = ({"x": [0.42], "y": [0.0]}, {"x": [0.58], "y": [1.0]})   # ease-in-out
EASE = ({"x": [0.25], "y": [0.1]}, {"x": [0.25], "y": [1.0]})          # the default, `ease`
CORNER_E = ({"x": [0.2], "y": [0.9]}, {"x": [0.3], "y": [1.2]})        # .corner
TICK_E = ({"x": [0.2], "y": [0.9]}, {"x": [0.3], "y": [1.3]})          # .corner svg .tick


# --- SVG path -> Lottie bezier ---------------------------------------------------------------
# Lottie stores a closed path as three parallel arrays: v (the on-curve points), o (each point's
# outgoing control, RELATIVE to it) and i (its incoming one). An SVG `d` is a stream of commands
# in absolute or relative coordinates, so this walks it once and converts every segment to a
# cubic — a straight line being the cubic whose controls sit on its own endpoints.
_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_d(d, tx=0.0, ty=0.0, scale=1.0):
    """`d` as a list of Lottie shape-path dicts, one per subpath. [tx],[ty],[scale] apply the
    SVG `<g transform>` the icon files wrap their glyph in."""
    toks, out, cmd = _TOKEN.findall(d), [], None
    cur = start = (0.0, 0.0)
    prev_c = prev_q = None                  # reflection points for S and T
    verts = ins = outs = None
    n = 0

    def num():
        nonlocal n
        v = float(toks[n]); n += 1
        return v

    def begin(p):
        nonlocal verts, ins, outs
        flush()
        verts, ins, outs = [p], [p], [p]

    def flush():
        if verts and len(verts) > 1:
            out.append(shape(verts, ins, outs, tx, ty, scale))

    def add(c1, c2, p):
        """One cubic from `cur`: c1 is this point's outgoing control, c2 the next one's incoming."""
        outs[-1] = c1
        verts.append(p); ins.append(c2); outs.append(p)

    while n < len(toks):
        t = toks[n]
        if t.isalpha():
            cmd = t; n += 1
        elif cmd in ("M", "m"):
            cmd = "L" if cmd == "M" else "l"    # repeated pairs after an M are implicit linetos
        rel = cmd.islower()
        c = cmd.upper()

        if c == "Z":
            if verts and len(verts) > 1:
                # A closed subpath usually repeats its first point; fold the two together so the
                # closing segment keeps its curvature instead of becoming a zero-length node.
                if abs(verts[-1][0] - verts[0][0]) < 1e-6 and abs(verts[-1][1] - verts[0][1]) < 1e-6:
                    ins[0] = ins[-1]
                    verts.pop(); ins.pop(); outs.pop()
                flush()
            verts = ins = outs = None
            cur = start
            continue

        if c == "M":
            x, y = num(), num()
            cur = start = (cur[0] + x, cur[1] + y) if rel else (x, y)
            begin(cur)
            prev_c = prev_q = None
            continue

        if c == "L":
            x, y = num(), num()
            p = (cur[0] + x, cur[1] + y) if rel else (x, y)
        elif c == "H":
            x = num()
            p = (cur[0] + x, cur[1]) if rel else (x, cur[1])
        elif c == "V":
            y = num()
            p = (cur[0], cur[1] + y) if rel else (cur[0], y)
        elif c in ("C", "S", "Q", "T"):
            if c == "C":
                c1 = _pt(num(), num(), cur, rel); c2 = _pt(num(), num(), cur, rel)
            elif c == "S":
                c1 = _reflect(prev_c, cur); c2 = _pt(num(), num(), cur, rel)
            else:
                q = _reflect(prev_q, cur) if c == "T" else _pt(num(), num(), cur, rel)
                prev_q = q
            p = _pt(num(), num(), cur, rel)
            if c in ("Q", "T"):
                c1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
                c2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
            add(c1, c2, p)
            prev_c = c2
            cur = p
            continue
        else:
            raise ValueError(f"unsupported path command {cmd!r}")

        add(cur, p, p)          # a line: both controls on the endpoints
        prev_c = prev_q = None
        cur = p

    flush()
    return out


def _pt(x, y, cur, rel):
    return (cur[0] + x, cur[1] + y) if rel else (x, y)


def _reflect(ctrl, cur):
    return cur if ctrl is None else (2 * cur[0] - ctrl[0], 2 * cur[1] - ctrl[1])


def shape(verts, ins, outs, tx, ty, scale):
    """Absolute points -> Lottie's {v, i, o}, with i/o made relative. Rounded to 2dp: the icons
    are 24px wide, so the third decimal is a thousandth of a pixel and pure file weight."""
    def m(p):
        return [round(tx + scale * p[0], 2), round(ty + scale * p[1], 2)]

    v = [m(p) for p in verts]
    i = [[round(a - b, 2) for a, b in zip(m(ins[k]), v[k])] for k in range(len(v))]
    o = [[round(a - b, 2) for a, b in zip(m(outs[k]), v[k])] for k in range(len(v))]
    return {"ty": "sh", "nm": "path", "ks": {"a": 0, "k": {"i": i, "o": o, "v": v, "c": True}}}


def path_of(svg_file, index=0):
    """The `index`-th `d=` in an icon file. Reading it straight out of the SVG is the point:
    recolour or redraw the icon and re-running this picks the change up."""
    src = open(os.path.join(ICONS, svg_file), encoding="utf-8").read()
    return re.findall(r'\sd="([^"]+)"', src)[index]


# --- Lottie scaffolding ----------------------------------------------------------------------
def rgb(h):
    h = h.lstrip("#")
    return [int(h[k:k + 2], 16) / 255.0 for k in (0, 2, 4)] + [1]


def static(v):
    return {"a": 0, "k": v}


def anim(keys, ease=EASE_IN_OUT):
    """[(frame, value)...]; the last key holds."""
    eo, ei = ease
    out = []
    for n, (t, v) in enumerate(keys):
        k = {"t": round(t, 3), "s": v if isinstance(v, list) else [v]}
        if n < len(keys) - 1:
            k["o"], k["i"] = eo, ei
        out.append(k)
    return {"a": 1, "k": out}


def fill(hexc, evenodd=False):
    return {"ty": "fl", "c": static(rgb(hexc)), "o": static(100), "r": 2 if evenodd else 1,
            "nm": "fill"}


def stroke(hexc, w):
    return {"ty": "st", "c": static(rgb(hexc)), "o": static(100), "w": static(w),
            "lc": 2, "lj": 2, "nm": "stroke"}


def tr():
    return {"ty": "tr", "p": static([0, 0]), "a": static([0, 0]), "s": static([100, 100]),
            "r": static(0), "o": static(100), "sk": static(0), "sa": static(0), "nm": "transform"}


def group(items, name):
    return {"ty": "gr", "nm": name, "it": items + [tr()]}


def layer(ind, name, shapes, ks, frames, parent=None):
    lay = {"ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1, "ks": ks, "ao": 0,
           "shapes": shapes, "ip": 0, "op": frames, "st": 0, "bm": 0}
    if parent:
        lay["parent"] = parent
    return lay


def write(name, w, h, frames, layers, title):
    doc = {"v": "5.7.4", "fr": FPS, "ip": 0, "op": frames, "w": w, "h": h, "nm": title,
           "ddd": 0, "assets": [], "layers": layers}
    p = os.path.join(OUT, name)
    # separators without spaces: ~15% off every file, and nobody reads these by hand
    open(p, "w", encoding="utf-8").write(json.dumps(doc, separators=(",", ":")))
    print(f"  {name:<26} {os.path.getsize(p) / 1024:5.1f} KB")


# --- the alert band seals ----------------------------------------------------------------------
# @keyframes tagWiggle, 3.4s. Not a metronome: it holds dead still for the first 62% and then
# snaps through -13 / +10 / -7 / +4 / -2 degrees, scaling up 8% on the two big swings. The
# stillness is what makes the shake land; a constant slow rock reads as a rendering artefact.
TAG_SECONDS = 3.4
TAG_ROT = [(0, 0), (62, 0), (68, -13), (74, 10), (80, -7), (86, 4), (92, -2), (100, 0)]
TAG_SCALE = [(0, 100), (62, 100), (68, 108), (74, 108), (80, 104), (86, 100), (100, 100)]


def band_icon(name, svg, glyph_colour, title):
    """A 24px seal on its white disc, wiggling on tagWiggle. The disc is an `el` primitive rather
    than the SVG's own circle path — four beziers against nine bytes."""
    frames = int(FPS * TAG_SECONDS)

    def key(table):
        return [(frames * p / 100.0, v) for p, v in table]

    glyph = [group(parse_d(path_of(svg, i), *OFFSET.get(svg, (0, 0, 1.0))) +
                   [fill(glyph_colour, evenodd=True)], f"glyph{i}")
             for i in GLYPH_PATHS[svg]]
    # Lottie draws the FIRST entry on top, so the disc goes last or it hides the glyph.
    shapes = glyph + [group([{"ty": "el", "p": static([12, 12]), "s": static([24, 24]),
                              "nm": "disc"}, fill("#FFFFFF")], "disc")]
    ks = {"o": static(100), "p": static([12, 12, 0]), "a": static([12, 12, 0]),
          "r": anim(key(TAG_ROT)), "s": anim([(t, [v, v]) for t, v in key(TAG_SCALE)])}
    write(name, 24, 24, frames, [layer(1, "seal", shapes, ks, frames)], title)


# Which `d`s in each icon file are the glyph (the rest is the white disc, and — on the bells —
# the blurred shadow this drops), and the `<g transform>` the rosette is wrapped in.
GLYPH_PATHS = {"discount.svg": [1], "discount-dark.svg": [1],
               "warning.svg": [0, 1], "warning-red.svg": [1, 2]}
OFFSET = {"discount.svg": (2.04, 2.04, 0.83), "discount-dark.svg": (2.04, 2.04, 0.83)}


# --- the popup seal ----------------------------------------------------------------------------
# .pop .badge: `wiggle 1.2s ease-in-out .3s`, once. The .3s is a real hold — the card is still
# springing in underneath — so it is kept as a still first 9 frames rather than trimmed off.
def popup_badge():
    hold, frames = int(FPS * 0.3), int(FPS * 1.5)
    rot = [(0, 0), (hold, 0), (hold + 9, -14), (hold + 18, 10), (hold + 27, -5), (frames, 0)]
    sca = [(0, 100), (hold, 100), (hold + 9, 110), (hold + 18, 100), (frames, 100)]
    shapes = [group(parse_d(path_of("popup-badge.svg")) + [fill("#05603A"), stroke("#FFFFFF", 2)],
                    "badge")]
    ks = {"o": static(100), "p": static([26, 26, 0]), "a": static([26, 26, 0]),
          "r": anim(rot), "s": anim([(t, [v, v]) for t, v in sca])}
    write("popup-discount.json", 52, 52, frames,
          [layer(1, "badge", shapes, ks, frames)], "AstroChat popup discount seal")


# --- the SKU selection marks ---------------------------------------------------------------------
# Measured off the running prototype at the 360px design width: the tile is 91x73 with a 14px
# radius and a 1.5px border, and .corner is a 38x38 box in its top-right with a 13px radius.
# Nothing here is the tile itself — it is only what selecting the tile adds, on transparent.
TILE_W, TILE_H, TILE_R, BORDER = 91, 73, 14, 1.5
CORNER, CORNER_R = 38, 13
ORANGE = "#EF6939"


def sku_selected():
    frames = int(FPS * 1.5)
    left, k = TILE_W - CORNER, CORNER_R * 0.5523

    # The triangle, already clipped to the tile's top-right radius. Two straight corners and one
    # quarter-circle where it meets the rounded edge of the card.
    v = [[left, 0], [TILE_W - CORNER_R, 0], [TILE_W, CORNER_R], [TILE_W, CORNER]]
    o = [[0, 0], [k, 0], [0, 0], [0, 0]]
    i = [[0, 0], [0, 0], [0, -k], [0, 0]]
    wedge = {"ty": "sh", "nm": "wedge", "ks": {"a": 0, "k": {"i": i, "o": o, "v": v, "c": True}}}

    border = layer(1, "border", [group([
        {"ty": "rc", "p": static([TILE_W / 2, TILE_H / 2]),
         "s": static([TILE_W - BORDER, TILE_H - BORDER]),
         "r": static(TILE_R - BORDER / 2), "nm": "rect"}, stroke(ORANGE, BORDER)], "border")],
        {"o": anim([(0, 0), (FPS * 0.2, 100)], EASE), "p": static([0, 0, 0]),
         "a": static([0, 0, 0]), "r": static(0), "s": static([100, 100])}, frames)

    # @keyframes cornerIn: in from translate(8px,-8px) over .28s, fading up as it goes.
    corner = layer(2, "corner", [group([wedge, fill(ORANGE)], "wedge")],
                   {"o": anim([(0, 0), (FPS * 0.28, 100)], CORNER_E),
                    "p": anim([(0, [8, -8, 0]), (FPS * 0.28, [0, 0, 0])], CORNER_E),
                    "a": static([0, 0, 0]), "r": static(0), "s": static([100, 100])}, frames)

    # @keyframes tickIn: rotate(-90deg) scale(.4) -> none, .08s behind the corner, about a point
    # near the tick's own elbow (25.8/13.2 inside the 38px box) so it swings up into place.
    ox, oy = left + 25.8, 13.2
    d0, d1 = FPS * 0.08, FPS * 0.43
    tick = layer(3, "tick",
                 [group(parse_d(TICK_D, tx=left) + [fill("#FFFFFF")], "tick")],
                 {"o": anim([(0, 0), (d0, 0), (d0 + FPS * 0.12, 100)], TICK_E),
                  "p": static([ox, oy, 0]), "a": static([ox, oy, 0]),
                  "r": anim([(0, -90), (d0, -90), (d1, 0)], TICK_E),
                  "s": anim([(0, [40, 40]), (d0, [40, 40]), (d1, [100, 100])], TICK_E)},
                 frames, parent=2)

    # Topmost first: the tick sits on the wedge, the wedge over the border.
    write("sku-selected.json", TILE_W, TILE_H, frames, [tick, corner, border],
          "AstroChat SKU selection marks")


# The tick as the prototype draws it, in .corner's own 38x38 box (template.html, const CORNER).
TICK_D = "M30.2 11.1L24.3 16.2L21.4 13.5L21.9 12.8L24.3 14.9L29.7 10.3L30.2 11.1Z"


if __name__ == "__main__":
    print("Writing Lotties to assets/")
    popup_badge()
    sku_selected()
    band_icon("band-bonus.json", "discount.svg", "#039855", "AstroChat band seal · green")
    band_icon("band-bonus-dark.json", "discount-dark.svg", "#065F41",
              "AstroChat band seal · dark green")
    band_icon("band-alert-amber.json", "warning.svg", "#7A2E0E", "AstroChat band bell · amber")
    band_icon("band-alert-red.json", "warning-red.svg", "#7A271A", "AstroChat band bell · red")
