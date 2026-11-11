"""ForgeGate carousel renderer.

Usage: python3 render/render.py posts/<post-folder>/post.json
Writes slide-01.jpg ... next to post.json (1080x1350, JPEG, under 1 MB each).

Each division has a locked style:
  techworx -> "The Agents"      neon mascots (Theo, Cleo, Sentinel, Forge), bold Figtree type
  media    -> "Editorial"       DM Serif Display headlines, framed scene photo, red accents
  estate   -> "Cinematic Hall"  full-bleed scene art, Tenor Sans capitals, gold lines

Slide types: cover, point, list, table, cta (see RUNBOOK.md for the JSON shape).
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ART = os.path.join(ROOT, "assets", "art")
FD = os.path.join(ROOT, "assets", "fonts")

BG = (10, 9, 8)
CREAM = (236, 232, 225)
BODY = (214, 206, 194)
GOLD = (236, 211, 162)
MUTED = (163, 152, 136)
RULE = (60, 55, 50)
RED = (210, 31, 31)
AGENTS = [("theo", (168, 85, 247)), ("cleo", (56, 170, 255)), ("sentinel", (74, 222, 80)), ("forge", (235, 45, 45))]
SCENES = {
    "media": ["media-full.webp", "hall.webp", "cleo-archive.webp", "command.webp", "gateway.webp"],
    "estate": ["arch-studio.webp", "hall.webp", "gateway.webp"],
}
_fc = {}


# ---------------- helpers ----------------
def F(name, size):
    k = (name, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(FD, f"{name}.ttf"), int(size))
    return _fc[k]


def tlen(d, t, font, tr=0):
    return d.textlength(t, font=font) + tr * max(0, len(t) - 1)


def wrap(d, text, font, width, tr=0):
    lines, cur = [], ""
    for w in str(text).split():
        t = (cur + " " + w).strip()
        if tlen(d, t, font, tr) > width and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    # avoid a single orphan word on the last line
    if len(lines) >= 2 and len(lines[-1].split()) == 1 and len(lines[-2].split()) > 2:
        prev = lines[-2].split()
        cand = " ".join(prev[-1:] + lines[-1].split())
        if tlen(d, cand, font, tr) <= width:
            lines[-2] = " ".join(prev[:-1]); lines[-1] = cand
    return lines


def draw_tracked(d, xy, t, font, fill, tr):
    x, y = xy
    if not tr:
        d.text((x, y), t, font=font, fill=fill); return x + d.textlength(t, font=font)
    for ch in t:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tr
    return x


def fit(d, text, fname, size, width, max_lines, lh=1.12, tr_ratio=0.0, upper=False, min_size=36, balance=False):
    """Shrink the font until the text fits in max_lines. Returns (font, lines, line_height, tracking)."""
    text = text.upper() if upper else text
    s = size
    while True:
        f = F(fname, s); tr = s * tr_ratio
        lines = wrap(d, text, f, width, tr)
        if len(lines) <= max_lines or s <= min_size:
            if balance and len(lines) > 1:
                # narrowest width that keeps the same line count -> even, balanced lines
                lo, hi = int(width * 0.55), int(width)
                while hi - lo > 8:
                    mid = (lo + hi) // 2
                    if len(wrap(d, text, f, mid, tr)) <= len(lines):
                        hi = mid
                    else:
                        lo = mid
                lines = wrap(d, text, f, hi, tr)
            return f, lines, int(s * lh), tr
        s -= 4


def draw_lines(d, x, y, lines, font, fill, lh, tr=0):
    for ln in lines:
        draw_tracked(d, (x, y), ln, font, fill, tr); y += lh
    return y


def logo(width):
    lg = Image.open(os.path.join(ART, "forgegate-logo.png")).convert("RGBA")
    return lg.resize((width, int(lg.height * width / lg.width)), Image.LANCZOS)


def division_label(d, xy, division, size=24, fill=MUTED):
    f = F("TenorSans-Regular", size); tr = size * 0.22
    if division == "techworx":
        x = draw_tracked(d, xy, "TECHWOR", f, fill, tr); draw_tracked(d, (x + tr, xy[1]), "X", f, RED, 0)
    elif division == "media":
        draw_tracked(d, xy, "MEDIA", f, fill, tr)
    else:
        draw_tracked(d, xy, "ESTATE OPERATIONS", f, fill, tr)


def cover_fit(name, w, h, focus=(0.5, 0.5)):
    im = Image.open(os.path.join(ART, name)).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - w) * focus[0]); y = int((im.height - h) * focus[1])
    return im.crop((x, y, x + w, y + h))


def counter(d, i, n, xy, fill=MUTED, right=False):
    f = F("IBMPlexMono-Medium", 24); t = f"{i:02d} / {n:02d}"
    x, y = xy
    if right:
        x = x - d.textlength(t, font=f)
    d.text((x, y), t, font=f, fill=fill)


def add_light(img, layer):
    a = np.asarray(img, dtype=np.int32) + np.asarray(layer, dtype=np.int32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------- TechWorx: The Agents ----------------
def techworx(s, i, n, post):
    name, col = AGENTS[(i - 1) % 4] if s.get("agent") is None else next(a for a in AGENTS if a[0] == s["agent"])
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    X = 80; TW = W - 2 * X
    cover = s["type"] == "cover"
    big_mascot = s["type"] in ("cover", "point", "cta")
    ms = 600 if cover else (440 if big_mascot else 300)
    my = H - ms - 120 if cover else 150
    mx = W - ms - 20
    halo = Image.new("RGB", (W, H)); hd = ImageDraw.Draw(halo)
    hd.ellipse((mx - 40, my - 20, mx + ms + 40, my + ms + 60), fill=tuple(int(c * 0.5) for c in col))
    img = add_light(img, halo.filter(ImageFilter.GaussianBlur(120)))
    m = Image.open(os.path.join(ART, f"agent-{name}.webp")).convert("RGBA").resize((ms, ms), Image.LANCZOS)
    img.paste(m, (mx, my), m)
    d = ImageDraw.Draw(img)
    lg = logo(280); img.paste(lg, (X, 70), lg)
    counter(d, i, n, (X, 124))

    def label(y):
        d.rectangle((X, y + 4, X + 14, y + 18), fill=col)
        draw_tracked(d, (X + 30, y), s.get("label", "").upper(), F("IBMPlexMono-Medium", 24), col, 4)
        return y + 56

    if cover:
        y = label(250)
        f, lines, lh, _ = fit(d, s["title"], "Figtree-Bold", 96, TW, 4, 1.06, balance=True)
        y = draw_lines(d, X, y, lines, f, CREAM, lh) + 20
        if s.get("body"):
            bf, bl, blh, _ = fit(d, s["body"] + "  ›", "Figtree-Medium", 42, TW - 380, 2, 1.25)
            draw_lines(d, X, y, bl, bf, col, blh)
    else:
        y = (my + ms + 40) if big_mascot else 470
        if s["type"] == "list":
            y = 480
        y = label(y)
        f, lines, lh, _ = fit(d, s["title"], "Figtree-Bold", 76, TW, 3, 1.1, balance=True)
        y = draw_lines(d, X, y, lines, f, CREAM, lh) + 18
        if s.get("body"):
            bf, bl, blh, _ = fit(d, s["body"], "Figtree-Regular", 40, TW, 4, 1.38)
            y = draw_lines(d, X, y, bl, bf, BODY, blh) + 10
        if s.get("you"):
            y += 24
            yf, yl, ylh, _ = fit(d, s["you"], "Figtree-SemiBold", 38, TW - 70, 2, 1.3)
            hgt = len(yl) * ylh + 50
            d.rounded_rectangle((X, y, W - X, y + hgt), 18, outline=col, width=3)
            draw_lines(d, X + 34, y + 24, yl, yf, CREAM, ylh); y += hgt
        if s["type"] == "table":
            y += 10
            for k, v in s.get("rows", []):
                d.line((X, y, W - X, y), fill=RULE, width=2)
                d.text((X, y + 28), k.upper(), font=F("IBMPlexMono-Medium", 26), fill=col)
                vf, vl, vlh, _ = fit(d, v, "Figtree-Regular", 38, TW - 250, 2, 1.3)
                draw_lines(d, X + 250, y + 22, vl, vf, CREAM, vlh)
                y += max(120, len(vl) * vlh + 64)
            d.line((X, y, W - X, y), fill=RULE, width=2)
        if s["type"] == "cta":
            y += 30
            kf = F("Figtree-Bold", 128); bw = d.textlength(s["keyword"], font=kf) + 110
            d.rounded_rectangle((X, y, X + bw, y + 186), 26, fill=col)
            d.text((X + 55, y + 12), s["keyword"], font=kf, fill=BG)
    division_label(d, (X, H - 96), "techworx")
    return img


# ---------------- Media: Editorial ----------------
def media(s, i, n, post):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    M = 90; TW = W - 2 * M
    scenes = SCENES["media"]; scene = s.get("scene") or scenes[(i - 1) % len(scenes)]
    lg = logo(250); img.paste(lg, (M, 78), lg)
    counter(d, i, n, (W - M, 84), right=True)
    d.line((M, 150, W - M, 150), fill=RULE, width=1)
    foot = H - 120

    def label(y):
        draw_tracked(d, (M, y), s.get("label", "").upper(), F("IBMPlexMono-Medium", 22), RED, 5)
        return y + 52

    if s["type"] == "cover":
        win = cover_fit(scene, TW, 560, (0.45, 0.5)); img.paste(ImageEnhance.Brightness(win).enhance(0.92), (M, 200))
        d = ImageDraw.Draw(img)
        y = label(810)
        f, lines, lh, _ = fit(d, s["title"], "DMSerifDisplay-Regular", 88, TW, 3, 1.06, balance=True)
        y = draw_lines(d, M, y, lines, f, CREAM, lh) + 14
        if s.get("body"):
            bf, bl, blh, _ = fit(d, s["body"], "DMSerifDisplay-Italic", 44, TW, 2, 1.2)
            draw_lines(d, M, y, bl, bf, GOLD, blh)
    else:
        y = label(220)
        f, lines, lh, _ = fit(d, s["title"], "DMSerifDisplay-Regular", 80, TW, 3, 1.08, balance=True)
        y = draw_lines(d, M, y, lines, f, CREAM, lh) + 24
        if s.get("body"):
            bf, bl, blh, _ = fit(d, s["body"], "Figtree-Light", 40, TW, 4, 1.42)
            y = draw_lines(d, M, y, bl, bf, BODY, blh) + 16
        if s.get("you"):
            y += 14
            d.rectangle((M, y, M + 4, y + 96), fill=RED)
            yf, yl, ylh, _ = fit(d, s["you"], "DMSerifDisplay-Italic", 40, TW - 40, 2, 1.2)
            draw_lines(d, M + 32, y + 4, yl, yf, GOLD, ylh); y += 120
        if s["type"] == "table":
            for k, v in s.get("rows", []):
                d.line((M, y, W - M, y), fill=RULE, width=1)
                draw_tracked(d, (M, y + 30), k.upper(), F("IBMPlexMono-Medium", 22), RED, 4)
                vf, vl, vlh, _ = fit(d, v, "Figtree-Regular", 38, TW - 250, 2, 1.3)
                draw_lines(d, M + 250, y + 22, vl, vf, CREAM, vlh)
                y += max(116, len(vl) * vlh + 60)
            d.line((M, y, W - M, y), fill=RULE, width=1); y += 30
        if s["type"] == "cta":
            y += 10
            d.line((M, y, W - M, y), fill=RULE, width=1); y += 36
            draw_tracked(d, (M, y), "COMMENT", F("IBMPlexMono-Medium", 22), MUTED, 5); y += 30
            d.text((M - 6, y), s["keyword"], font=F("DMSerifDisplay-Regular", 180), fill=RED); y += 230
        if foot - 40 - y > 220:
            win = cover_fit(scene, TW, foot - 40 - y, (0.45, 0.5))
            img.paste(ImageEnhance.Brightness(win).enhance(0.85), (M, y)); d = ImageDraw.Draw(img)
    d.line((M, foot, W - M, foot), fill=RULE, width=1)
    division_label(d, (M, H - 92), "media", 22)
    t = "forgegatemedia.com"; f = F("IBMPlexMono-Regular", 20)
    d.text((W - M - d.textlength(t, font=f), H - 90), t, font=f, fill=MUTED)
    return img


# ---------------- Estate Operations: Cinematic Hall ----------------
def estate(s, i, n, post):
    scenes = SCENES["estate"]; scene = s.get("scene") or scenes[(i - 1) % len(scenes)]
    img = cover_fit(scene, W, H, (0.5, 0.75))
    img = ImageEnhance.Brightness(img).enhance(0.6 if s["type"] == "cover" else 0.4)
    img = ImageEnhance.Color(img).enhance(0.85)
    d = ImageDraw.Draw(img, "RGBA")
    X = 88; TW = W - 2 * X
    dense = s["type"] in ("list", "table", "cta") or len(s.get("body", "")) > 120
    top = 560 if dense else 700
    d.rectangle((0, top, W, H), fill=(10, 9, 8, 230))
    d.line((X, top, W - X, top), fill=(*GOLD, 150), width=2)
    lg = logo(330); img.paste(lg, (X, 72), lg)
    counter(d, i, n, (W - X, 76), fill=GOLD, right=True)
    y = top + 60
    draw_tracked(d, (X, y), s.get("label", "").upper(), F("IBMPlexMono-Medium", 24), GOLD, 5); y += 62
    size = 78 if s["type"] == "cover" else 62
    f, lines, lh, tr = fit(d, s["title"], "TenorSans-Regular", size, TW, 3, 1.18, 0.04, upper=True, balance=True)
    y = draw_lines(d, X, y, lines, f, CREAM, lh, tr) + 24
    if s.get("body"):
        bf, bl, blh, _ = fit(d, s["body"], "Figtree-Light", 40, TW, 4, 1.42)
        y = draw_lines(d, X, y, bl, bf, BODY, blh) + 10
    if s.get("you"):
        y += 20
        yf, yl, ylh, _ = fit(d, s["you"], "Figtree-Regular", 36, TW - 60, 2, 1.3)
        hgt = len(yl) * ylh + 44
        d.rectangle((X, y, W - X, y + hgt), outline=(*GOLD, 200), width=2)
        draw_lines(d, X + 30, y + 22, yl, yf, GOLD, ylh); y += hgt
    if s["type"] == "table":
        y += 10
        for k, v in s.get("rows", []):
            d.line((X, y, W - X, y), fill=(*GOLD, 90), width=1)
            draw_tracked(d, (X, y + 26), k.upper(), F("IBMPlexMono-Medium", 22), GOLD, 4)
            vf, vl, vlh, _ = fit(d, v, "Figtree-Regular", 36, TW - 250, 2, 1.3)
            draw_lines(d, X + 250, y + 20, vl, vf, CREAM, vlh)
            y += max(104, len(vl) * vlh + 56)
    if s["type"] == "cta":
        y += 30
        kf = F("TenorSans-Regular", 116); tr = 14
        bw = tlen(d, s["keyword"], kf, tr) + 112
        d.rectangle((X, y, X + bw, y + 184), outline=GOLD, width=3)
        draw_tracked(d, (X + 56, y + 30), s["keyword"], kf, CREAM, tr)
    division_label(d, (X, H - 96), "estate")
    return img


STYLES = {"techworx": techworx, "media": media, "estate": estate}


def render(post_path):
    post = json.load(open(post_path))
    out = os.path.dirname(os.path.abspath(post_path))
    fn = STYLES[post["division"]]
    n = len(post["slides"])
    assert 2 <= n <= 10, "Instagram carousels take 2 to 10 slides"
    assert post["slides"][-1]["type"] == "cta", "last slide must be the CTA"
    paths = []
    for i, s in enumerate(post["slides"], 1):
        img = fn(s, i, n, post)
        p = os.path.join(out, f"slide-{i:02d}.jpg")
        img.save(p, quality=90, optimize=True, progressive=True)
        assert os.path.getsize(p) < 8 * 1024 * 1024
        paths.append(p)
    return paths


if __name__ == "__main__":
    for p in sys.argv[1:]:
        for f in render(p):
            print(f)
