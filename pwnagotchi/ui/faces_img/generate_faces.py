#!/usr/bin/env python3
"""
Face image generator for Pwnagotchi – soft glowing cyan cartoon style.

Design:
  - Big, simple cartoon shapes on transparent background
  - Soft radial gradient: cyan edges → near-white centres (glass/translucent)
  - No outlines, no highlights, no fine details – just soft glowing blobs
  - Kawaii / emoji-style proportions
"""

from PIL import Image, ImageDraw, ImageFilter
import os
import math

# ── Colour palette ──────────────────────────────────────────────────────────
# Gradient goes from EDGE (outer) → MID → CENTER (inner)
EDGE   = (120, 220, 230)   # Outer cyan
MID    = (170, 240, 245)   # Mid-tone
CENTER = (220, 252, 253)   # Near-white centre

# ── Canvas / layout constants ───────────────────────────────────────────────
SIZE = 160
CX = SIZE // 2             # Canvas centre x
EYE_Y = 52                 # Vertical centre of eyes
EYE_SEP = 52               # Distance from centre to each eye
EYE_R = 26                 # Default eye radius
MOUTH_Y = 118              # Vertical centre of mouth
MOUTH_RX = 34              # Mouth horizontal radius
MOUTH_RY = 18              # Mouth vertical radius (arc depth)


# ── Drawing helpers ─────────────────────────────────────────────────────────

def _gradient_circle(img, cx, cy, r):
    """Draw a filled circle with a soft radial gradient (cyan edge → white centre)."""
    for i in range(r, 0, -1):
        t = 1.0 - (i / r)  # 0 at edge, 1 at centre
        t = t * t           # Ease-in for softer falloff
        color = (
            int(EDGE[0] + (CENTER[0] - EDGE[0]) * t),
            int(EDGE[1] + (CENTER[1] - EDGE[1]) * t),
            int(EDGE[2] + (CENTER[2] - EDGE[2]) * t),
            255,
        )
        draw = ImageDraw.Draw(img)
        draw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=color)


def _gradient_half_circle(img, cx, cy, r, top=True):
    """Draw a half-circle with radial gradient.
    top=True  → flat bottom, round top  (open-top / happy eye)
    top=False → flat top, round bottom  (droopy / sleepy)
    """
    # Draw a full gradient circle, then mask out the unwanted half
    temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
    _gradient_circle(temp, cx, cy, r)
    # Create mask: keep only the desired half
    mask = Image.new('L', img.size, 255)
    md = ImageDraw.Draw(mask)
    if top:
        # Keep top half → black-out bottom
        md.rectangle([0, cy, SIZE, SIZE], fill=0)
    else:
        # Keep bottom half → black-out top
        md.rectangle([0, 0, SIZE, cy], fill=0)
    temp.putalpha(Image.merge('L', [temp.split()[3]]).point(lambda a: a))
    # Apply the half-mask
    r_chan, g_chan, b_chan, a_chan = temp.split()
    a_chan = Image.composite(a_chan, Image.new('L', img.size, 0), mask)
    temp = Image.merge('RGBA', (r_chan, g_chan, b_chan, a_chan))
    img.alpha_composite(temp)


def _gradient_ellipse(img, cx, cy, rx, ry):
    """Draw a filled ellipse with a soft radial gradient."""
    steps = max(rx, ry)
    for i in range(steps, 0, -1):
        t = 1.0 - (i / steps)
        t = t * t
        color = (
            int(EDGE[0] + (CENTER[0] - EDGE[0]) * t),
            int(EDGE[1] + (CENTER[1] - EDGE[1]) * t),
            int(EDGE[2] + (CENTER[2] - EDGE[2]) * t),
            255,
        )
        sx = int(rx * (i / steps))
        sy = int(ry * (i / steps))
        draw = ImageDraw.Draw(img)
        draw.ellipse([cx - sx, cy - sy, cx + sx, cy + sy], fill=color)


def _gradient_half_ellipse(img, cx, cy, rx, ry, top=True):
    """Draw a half-ellipse with radial gradient (for mouth shapes)."""
    temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
    _gradient_ellipse(temp, cx, cy, rx, ry)
    mask = Image.new('L', img.size, 255)
    md = ImageDraw.Draw(mask)
    if top:
        md.rectangle([0, cy, SIZE, SIZE], fill=0)
    else:
        md.rectangle([0, 0, SIZE, cy], fill=0)
    r_chan, g_chan, b_chan, a_chan = temp.split()
    a_chan = Image.composite(a_chan, Image.new('L', img.size, 0), mask)
    temp = Image.merge('RGBA', (r_chan, g_chan, b_chan, a_chan))
    img.alpha_composite(temp)


def _soft_blur(img, radius=2, passes=2):
    """Gentle edge softening – keeps shapes but removes hard aliased edges."""
    result = img
    for _ in range(passes):
        result = result.filter(ImageFilter.GaussianBlur(radius))
    # Composite soft version behind sharp for subtle glow
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out = Image.alpha_composite(out, result)
    out = Image.alpha_composite(out, img)
    return out


def _draw_line(img, x1, y1, x2, y2, width=5):
    """Draw a thick soft line."""
    draw = ImageDraw.Draw(img)
    draw.line([x1, y1, x2, y2], fill=EDGE, width=width)


def _draw_x(img, cx, cy, r):
    """Draw an X shape."""
    draw = ImageDraw.Draw(img)
    draw.line([cx - r, cy - r, cx + r, cy + r], fill=MID, width=5)
    draw.line([cx - r, cy + r, cx + r, cy - r], fill=MID, width=5)


def _draw_arc_eyes(img, cx, cy, r):
    """Draw ^^ arc eyes (grateful)."""
    draw = ImageDraw.Draw(img)
    bbox = [cx - r, cy - r, cx + r, cy + r]
    draw.arc(bbox, 200, 340, fill=MID, width=6)


def _draw_heart(img, cx, cy, s):
    """Draw a simple filled heart shape."""
    draw = ImageDraw.Draw(img)
    r = s * 0.4
    # Two circles for top bumps
    for ox in [-r * 0.55, r * 0.55]:
        for i in range(int(r), 0, -1):
            t = 1.0 - (i / r)
            t = t * t
            c = (
                int(EDGE[0] + (CENTER[0] - EDGE[0]) * t),
                int(EDGE[1] + (CENTER[1] - EDGE[1]) * t),
                int(EDGE[2] + (CENTER[2] - EDGE[2]) * t),
                255,
            )
            draw.ellipse([cx + ox - i, cy - r * 0.4 - i, cx + ox + i, cy - r * 0.4 + i], fill=c)
    # Triangle bottom
    pts = [
        (cx - s * 0.48, cy - r * 0.15),
        (cx + s * 0.48, cy - r * 0.15),
        (cx, cy + s * 0.55),
    ]
    draw.polygon(pts, fill=MID)


def _draw_hash(img, cx, cy, r):
    """Draw a # symbol."""
    draw = ImageDraw.Draw(img)
    o = r * 0.4
    draw.line([cx - r, cy - o, cx + r, cy - o], fill=MID, width=4)
    draw.line([cx - r, cy + o, cx + r, cy + o], fill=MID, width=4)
    draw.line([cx - o, cy - r, cx - o, cy + r], fill=MID, width=4)
    draw.line([cx + o, cy - r, cx + o, cy + r], fill=MID, width=4)


# ── Eye + mouth shorthand ──────────────────────────────────────────────────

def _lx():
    return CX - EYE_SEP

def _rx():
    return CX + EYE_SEP

def _round_eyes(img, r=EYE_R, y=EYE_Y, x_offset=0):
    _gradient_circle(img, _lx() + x_offset, y, r)
    _gradient_circle(img, _rx() + x_offset, y, r)

def _half_eyes_top(img, r=EYE_R, y=EYE_Y):
    """Half circle eyes, round on top, flat bottom → sad / angry."""
    _gradient_half_circle(img, _lx(), y, r, top=True)
    _gradient_half_circle(img, _rx(), y, r, top=True)

def _half_eyes_bottom(img, r=EYE_R, y=EYE_Y):
    """Half circle eyes, round on bottom, flat top → sleepy / bored."""
    _gradient_half_circle(img, _lx(), y, r, top=False)
    _gradient_half_circle(img, _rx(), y, r, top=False)

def _line_eyes(img, y=EYE_Y, w=None):
    if w is None:
        w = EYE_R
    _draw_line(img, _lx() - w, y, _lx() + w, y)
    _draw_line(img, _rx() - w, y, _rx() + w, y)

def _smile(img, rx=MOUTH_RX, ry=MOUTH_RY, y=MOUTH_Y):
    """Smile: round on bottom, flat top."""
    _gradient_half_ellipse(img, CX, y, rx, ry, top=False)

def _frown(img, rx=MOUTH_RX, ry=MOUTH_RY, y=MOUTH_Y):
    """Frown: round on top, flat bottom."""
    _gradient_half_ellipse(img, CX, y, rx, ry, top=True)

def _flat_mouth(img, w=None, y=MOUTH_Y):
    if w is None:
        w = MOUTH_RX
    _draw_line(img, CX - w, y, CX + w, y)

def _open_mouth(img, r=None, y=MOUTH_Y):
    if r is None:
        r = int(MOUTH_RY * 0.8)
    _gradient_circle(img, CX, y, r)


# ── Face definitions ────────────────────────────────────────────────────────

def _face_awake(img):
    _round_eyes(img)
    _flat_mouth(img)

def _face_happy(img):
    _round_eyes(img)
    _smile(img)

def _face_sad(img):
    _half_eyes_top(img)
    _frown(img)

def _face_excited(img):
    _round_eyes(img, r=int(EYE_R * 1.25))
    _smile(img, rx=int(MOUTH_RX * 1.2), ry=int(MOUTH_RY * 1.2))

def _face_bored(img):
    _half_eyes_bottom(img)
    _flat_mouth(img, w=int(MOUTH_RX * 0.7))

def _face_angry(img):
    _half_eyes_top(img)
    _frown(img, rx=int(MOUTH_RX * 0.75), ry=int(MOUTH_RY * 0.75))

def _face_cool(img):
    # Wide flat rectangles for sunglasses
    draw = ImageDraw.Draw(img)
    for ex in [_lx(), _rx()]:
        rx, ry = int(EYE_R * 1.15), int(EYE_R * 0.55)
        # gradient fill the bar
        for i in range(max(rx, ry), 0, -1):
            t = 1.0 - (i / max(rx, ry))
            t = t * t
            c = (
                int(EDGE[0] + (CENTER[0] - EDGE[0]) * t),
                int(EDGE[1] + (CENTER[1] - EDGE[1]) * t),
                int(EDGE[2] + (CENTER[2] - EDGE[2]) * t),
                255,
            )
            sx = int(rx * (i / max(rx, ry)))
            sy = int(ry * (i / max(rx, ry)))
            draw.rounded_rectangle([ex - sx, EYE_Y - sy, ex + sx, EYE_Y + sy],
                                   radius=max(1, int(sy * 0.4)), fill=c)
    # Bridge
    draw.line([_lx() + EYE_R, EYE_Y, _rx() - EYE_R, EYE_Y], fill=EDGE, width=4)
    _smile(img, rx=int(MOUTH_RX * 0.7), ry=int(MOUTH_RY * 0.7))

def _face_grateful(img):
    _draw_arc_eyes(img, _lx(), EYE_Y, EYE_R)
    _draw_arc_eyes(img, _rx(), EYE_Y, EYE_R)
    _smile(img)

def _face_sleep(img):
    _line_eyes(img)
    _flat_mouth(img, w=int(MOUTH_RX * 0.55))

def _face_sleep2(img):
    _line_eyes(img)
    _flat_mouth(img, w=int(MOUTH_RX * 0.35))

def _face_motivated(img):
    _round_eyes(img, r=int(EYE_R * 1.15))
    _smile(img, rx=int(MOUTH_RX * 1.05))

def _face_demotivated(img):
    _half_eyes_bottom(img)
    _flat_mouth(img, w=int(MOUTH_RX * 0.65))

def _face_intense(img):
    _round_eyes(img, r=int(EYE_R * 1.25))
    _open_mouth(img)

def _face_smart(img):
    _round_eyes(img)
    _smile(img, rx=int(MOUTH_RX * 0.65), ry=int(MOUTH_RY * 0.65))

def _face_lonely(img):
    _round_eyes(img, r=int(EYE_R * 0.8))
    _frown(img, rx=int(MOUTH_RX * 0.6), ry=int(MOUTH_RY * 0.6))

def _face_friend(img):
    _draw_heart(img, _lx(), EYE_Y, EYE_R * 1.8)
    _draw_heart(img, _rx(), EYE_Y, EYE_R * 1.8)
    _smile(img)

def _face_broken(img):
    _draw_x(img, _lx(), EYE_Y, EYE_R * 0.75)
    _draw_x(img, _rx(), EYE_Y, EYE_R * 0.75)
    _flat_mouth(img, w=int(MOUTH_RX * 0.45))

def _face_debug(img):
    _draw_hash(img, _lx(), EYE_Y, EYE_R * 0.7)
    _draw_hash(img, _rx(), EYE_Y, EYE_R * 0.7)
    _flat_mouth(img, w=int(MOUTH_RX * 0.55))

def _face_look_r(img):
    _round_eyes(img, x_offset=8)
    _flat_mouth(img)

def _face_look_l(img):
    _round_eyes(img, x_offset=-8)
    _flat_mouth(img)

def _face_look_r_happy(img):
    _round_eyes(img, x_offset=8)
    _smile(img)

def _face_look_l_happy(img):
    _round_eyes(img, x_offset=-8)
    _smile(img)

def _face_upload(img):
    _gradient_circle(img, _lx(), EYE_Y, EYE_R)
    _line_eyes_single(img, _rx(), EYE_Y)
    _open_mouth(img)

def _face_upload1(img):
    _round_eyes(img)
    _open_mouth(img)

def _face_upload2(img):
    _line_eyes_single(img, _lx(), EYE_Y)
    _gradient_circle(img, _rx(), EYE_Y, EYE_R)
    _open_mouth(img)

def _line_eyes_single(img, cx, y, w=None):
    """Single line eye for upload faces."""
    if w is None:
        w = EYE_R
    _draw_line(img, cx - w, y, cx + w, y)


# ── Face registry ───────────────────────────────────────────────────────────

FACES = {
    'awake':        (_face_awake,        "Open eyes, neutral"),
    'happy':        (_face_happy,        "Round eyes, big smile"),
    'sad':          (_face_sad,          "Droopy eyes, frown"),
    'excited':      (_face_excited,      "Big eyes, big smile"),
    'bored':        (_face_bored,        "Half-closed eyes, flat mouth"),
    'angry':        (_face_angry,        "Narrow eyes, frown"),
    'cool':         (_face_cool,         "Sunglasses, small smile"),
    'grateful':     (_face_grateful,     "^^ eyes, gentle smile"),
    'sleep':        (_face_sleep,        "Closed line eyes, flat mouth"),
    'sleep2':       (_face_sleep2,       "Deep sleep"),
    'motivated':    (_face_motivated,    "Wide eyes, determined smile"),
    'demotivated':  (_face_demotivated,  "Droopy eyes, flat mouth"),
    'intense':      (_face_intense,      "Wide eyes, open mouth"),
    'smart':        (_face_smart,        "Round eyes, small smile"),
    'lonely':       (_face_lonely,       "Small eyes, small frown"),
    'friend':       (_face_friend,       "Heart eyes, big smile"),
    'broken':       (_face_broken,       "X eyes, flat mouth"),
    'debug':        (_face_debug,        "Hash eyes, flat mouth"),
    'look_r':       (_face_look_r,       "Eyes looking right"),
    'look_l':       (_face_look_l,       "Eyes looking left"),
    'look_r_happy': (_face_look_r_happy, "Looking right, smile"),
    'look_l_happy': (_face_look_l_happy, "Looking left, smile"),
    'upload':       (_face_upload,       "Binary 1-0, uploading"),
    'upload1':      (_face_upload1,      "Binary 1-1, uploading"),
    'upload2':      (_face_upload2,      "Binary 0-1, uploading"),
}


# ── Generator ───────────────────────────────────────────────────────────────

def create_face(name, draw_fn, size=SIZE):
    """Render a face on a transparent canvas with soft edges."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw_fn(img)
    img = _soft_blur(img, radius=1.5, passes=1)
    return img


def generate_all_faces(output_dir='.'):
    """Generate all face images."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating face images in {output_dir}/...")

    for name, (draw_fn, desc) in FACES.items():
        img = create_face(name, draw_fn)
        output_path = os.path.join(output_dir, f'{name}.png')
        img.save(output_path)
        print(f"  ✓ Created {name}.png – {desc}")

    print(f"\nGenerated {len(FACES)} face images!")
    print(f"Images are {SIZE}×{SIZE} PNG with transparent backgrounds.")

if __name__ == '__main__':
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    generate_all_faces(output_dir)
