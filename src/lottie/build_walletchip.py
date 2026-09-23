"""Generates walletchip.json — the wallet chip's gift <-> add-button swap, as a real Lottie.

The prototype drew this with four CSS keyframe blocks (swapGift, swapPlus, gift6, spark6). That
runs fine in a browser and is worth nothing to anyone else: it cannot go into the Android app, into
Figma, or into a handoff. This script re-authors the identical motion as a Lottie so there is one
downloadable file that every surface can play.

Written as a generator rather than hand-authored JSON because the timings are percentages of a 6s
loop lifted straight from the CSS, and they have to stay readable. Change a number in TIMELINE and
re-run; do not hand-edit walletchip.json.

    python3 src/lottie/build_walletchip.py

Geometry is 2x the prototype's 26px chip, so the file is 52x52 and stays crisp when a consumer
renders it larger. Everything is drawn with Lottie primitives (el/rc) — no imported paths — so the
colours below are the single source of truth for the artwork.
"""
import json, os

FPS, DUR = 30, 6.0
FRAMES = int(FPS * DUR)          # 180
W = H = 52
CX = CY = 26.0

# The CSS used cubic-bezier(.45,0,.25,1) for the swap. Lottie splits the same curve into an
# outgoing control point (o) and an incoming one (i).
EASE_O, EASE_I = {"x": [0.45], "y": [0.0]}, {"x": [0.25], "y": [1.0]}
LIN_O, LIN_I = {"x": [0.33], "y": [0.0]}, {"x": [0.67], "y": [1.0]}


def pct(p):
    """A percentage of the 6s loop as a frame number — the CSS keyframes are all percentages."""
    return round(FRAMES * p / 100.0, 3)


def rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1]


# Artwork colours. The gift's disc is the prototype's success-50 on an #abefc6 hairline; the box
# borrows the red/amber of the emoji it replaces, and the add button is icons/plus.svg's grey.
C_DISC_FILL, C_DISC_LINE = "#ECFDF3", "#ABEFC6"
C_BOX, C_LID, C_RIBBON = "#F04438", "#F97066", "#FEDF89"
C_PLUS_DISC, C_PLUS_MARK = "#475467", "#FFFFFF"
C_SPARK = ["#FDB022", "#12B76A", "#F472B6"]


def anim(keys, eo=EASE_O, ei=EASE_I):
    """An animated scalar/vector property. `keys` is [(frame, value)...]; the last one holds."""
    out = []
    for n, (t, v) in enumerate(keys):
        k = {"t": t, "s": v if isinstance(v, list) else [v]}
        if n < len(keys) - 1:
            k["o"], k["i"] = eo, ei
        out.append(k)
    return {"a": 1, "k": out}


def static(v):
    return {"a": 0, "k": v}


def fill(hexc):
    return {"ty": "fl", "c": static(rgb(hexc)), "o": static(100), "r": 1, "nm": "fill"}


def stroke(hexc, w):
    return {"ty": "st", "c": static(rgb(hexc)), "o": static(100), "w": static(w),
            "lc": 1, "lj": 1, "nm": "stroke"}


def tr(pos=None, anchor=None, scale=None, rot=None, op=None):
    """A transform block. Used both for shape groups and (unrolled) for layers."""
    return {"ty": "tr",
            "p": pos or static([0, 0]), "a": anchor or static([0, 0]),
            "s": scale or static([100, 100]), "r": rot or static(0),
            "o": op or static(100), "sk": static(0), "sa": static(0), "nm": "transform"}


def ellipse(cx, cy, d):
    return {"ty": "el", "p": static([cx, cy]), "s": static([d, d]), "nm": "ellipse"}


def rect(cx, cy, w, h, r=0):
    return {"ty": "rc", "p": static([cx, cy]), "s": static([w, h]), "r": static(r), "nm": "rect"}


def group(items, name, **kw):
    return {"ty": "gr", "nm": name, "it": items + [tr(**kw)]}


def layer(ind, name, shapes, ks):
    return {"ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1, "ks": ks, "ao": 0,
            "shapes": shapes, "ip": 0, "op": FRAMES, "st": 0, "bm": 0}


# --- the two halves of the swap -------------------------------------------------------------
# Straight from @keyframes swapGift / swapPlus: each is visible for 40% of the loop, spins down to
# 30% over the next 10%, sits hidden, and spins back. They are exact opposites, so one table with
# the roles flipped keeps them in sync — if these ever drift the two icons overlap mid-spin.
def swap_ks(showing_first):
    if showing_first:
        o = [(0, 100), (pct(40), 100), (pct(50), 0), (pct(90), 0), (FRAMES, 100)]
        s = [(0, [100, 100]), (pct(40), [100, 100]), (pct(50), [30, 30]),
             (pct(90), [30, 30]), (FRAMES, [100, 100])]
        r = [(0, 0), (pct(40), 0), (pct(50), -120), (pct(90), -120), (FRAMES, 0)]
    else:
        o = [(0, 0), (pct(40), 0), (pct(50), 100), (pct(90), 100), (FRAMES, 0)]
        s = [(0, [30, 30]), (pct(40), [30, 30]), (pct(50), [100, 100]),
             (pct(90), [100, 100]), (FRAMES, [30, 30])]
        r = [(0, 120), (pct(40), 120), (pct(50), 0), (pct(90), 0), (FRAMES, 120)]
    return {"o": anim(o), "r": anim(r), "s": anim(s),
            "p": static([CX, CY, 0]), "a": static([CX, CY, 0])}


# --- gift ------------------------------------------------------------------------------------
# @keyframes gift6: a shake that fires once per loop, at 10-34%, while the gift is the visible half.
# It rotates about 50%/85% of the icon box — near the base of the box, so it tips rather than
# spins — which is why this sits on the GROUP transform and not on the layer's.
WIGGLE_R = [(0, 0), (pct(10), 0), (pct(14), -14), (pct(18), 12), (pct(22), -8),
            (pct(26), 5), (pct(30), 0), (pct(34), 0), (FRAMES, 0)]
WIGGLE_S = [(0, [100, 100]), (pct(10), [100, 100]), (pct(14), [118, 118]), (pct(18), [118, 118]),
            (pct(22), [110, 110]), (pct(26), [100, 100]), (FRAMES, [100, 100])]
WIGGLE_P = [(0, [0, 0]), (pct(10), [0, 0]), (pct(14), [0, -2]), (pct(18), [0, -2]),
            (pct(22), [0, 0]), (FRAMES, [0, 0])]
WIGGLE_ANCHOR = [CX, 40.0]   # 50% / 85% of the 40px icon box that sits at (6,6)

gift_box = group([
    group([ellipse(21, 17, 9), ellipse(31, 17, 9), fill(C_RIBBON)], "bow"),
    group([rect(CX, 30, 4, 24), fill(C_RIBBON)], "ribbon"),
    group([rect(CX, 23, 28, 8, 2), fill(C_LID)], "lid"),
    group([rect(CX, 34, 24, 16, 1.5), fill(C_BOX)], "body"),
], "box",
    anchor=static(WIGGLE_ANCHOR),
    pos=anim([(t, [WIGGLE_ANCHOR[0] + v[0], WIGGLE_ANCHOR[1] + v[1]]) for t, v in WIGGLE_P]),
    rot=anim(WIGGLE_R), scale=anim(WIGGLE_S))

gift_layer = layer(2, "gift", [
    gift_box,
    group([ellipse(CX, CY, 50), stroke(C_DISC_LINE, 2), fill(C_DISC_FILL)], "disc"),
], swap_ks(True))

# --- add button ------------------------------------------------------------------------------
# icons/plus.svg is a solid disc with the plus knocked out by an evenodd path. Two white bars over
# a filled disc render identically at this size and survive being rasterised by any Lottie player,
# where a knockout in a single path does not always.
plus_layer = layer(1, "add", [
    group([rect(CX, CY, 16.25, 3.25, 1.6), rect(CX, CY, 3.25, 16.25, 1.6), fill(C_PLUS_MARK)], "mark"),
    group([ellipse(CX, CY, 44), fill(C_PLUS_DISC)], "disc"),
], swap_ks(False))

# --- sparks ----------------------------------------------------------------------------------
# @keyframes spark6, three dots staggered by 0.1s. They pop with the shake and drift up as they go.
SPARK_POS = [(46, 8, 4), (3, 15, 3), (49, 43, 3)]
spark_layers = []
for n, ((sx, sy, sd), col) in enumerate(zip(SPARK_POS, C_SPARK)):
    delay = round(n * 0.1 * FPS, 3)          # 0s / 0.1s / 0.2s
    keys_o = [(0, 0), (pct(12) + delay, 0), (pct(17) + delay, 100), (pct(28) + delay, 0), (FRAMES, 0)]
    keys_s = [(0, [20, 20]), (pct(12) + delay, [20, 20]), (pct(17) + delay, [120, 120]),
              (pct(28) + delay, [40, 40]), (FRAMES, [40, 40])]
    keys_p = [(0, [sx, sy, 0]), (pct(12) + delay, [sx, sy, 0]), (pct(17) + delay, [sx, sy, 0]),
              (pct(28) + delay, [sx, sy - 4, 0]), (FRAMES, [sx, sy - 4, 0])]
    spark_layers.append(layer(3 + n, "spark%d" % (n + 1),
                              [group([ellipse(sx, sy, sd * 2), fill(col)], "dot")],
                              {"o": anim(keys_o, LIN_O, LIN_I), "r": static(0),
                               "s": anim(keys_s, LIN_O, LIN_I),
                               "p": anim(keys_p, LIN_O, LIN_I), "a": static([sx, sy, 0])}))

doc = {"v": "5.7.4", "fr": FPS, "ip": 0, "op": FRAMES, "w": W, "h": H,
       "nm": "AstroChat wallet chip", "ddd": 0, "assets": [],
       "layers": [plus_layer, gift_layer] + spark_layers}

# Lands in assets/ rather than beside this script: that is the one directory the deployed site
# serves as-is, so the same file the prototype plays is also the file she can hand to anyone at
# <site>/assets/walletchip.json. Do not move it without updating the <a download> in template.html.
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "walletchip.json")
out = os.path.normpath(out)
with open(out, "w") as f:
    json.dump(doc, f, separators=(",", ":"))
print("Built %s (%d bytes, %d layers, %.0f frames @ %dfps)"
      % (out, os.path.getsize(out), len(doc["layers"]), FRAMES, FPS))
