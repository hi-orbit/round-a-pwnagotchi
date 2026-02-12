#!/usr/bin/env python3
"""
Face image generator for Pwnagotchi – cartoon eyeball style.

Design (from reference art):
  - Eyes: dark navy/teal centre (iris) + bright cyan outer ring (sclera) + white specular dot
  - Half-closed eyes: same style but top sliced at angle (built-in eyebrow)
  - Sleep eyes: thick curved cyan arcs / crescents
  - Mouth: small cyan half-circle (smile/frown) relative to eyes
  - Cool: oversized dark sunglasses with cyan frame and highlight dots
  - Hearts: cyan gradient hearts
  - No face outline – floating features on transparent background
"""

from PIL import Image, ImageDraw, ImageFilter
import os
import math

# ── Colour palette ──────────────────────────────────────────────────────────
DARK       = (15, 50, 70)        # Dark navy-teal for eye iris / sunglasses fill
DARK_MID   = (25, 70, 95)        # Slightly lighter dark for gradient
CYAN       = (90, 210, 235)      # Bright cyan for eye border / sclera / outlines
CYAN_LIGHT = (160, 240, 250)     # Lighter cyan for mouth fills, inner highlights
CYAN_PALE  = (190, 248, 253)     # Palest cyan for centres of mouth/hearts
WHITE      = (255, 255, 255)     # Specular highlights

# ── Canvas / layout ─────────────────────────────────────────────────────────
SIZE = 160
CX = SIZE // 2
EYE_Y = 58                 # Eye vertical centre
EYE_SEP = 38               # Half-distance between eye centres
EYE_R = 28                 # Outer eye radius (sclera)
IRIS_RATIO = 0.72           # Iris radius as fraction of sclera
HIGHLIGHT_RATIO = 0.20      # Highlight dot radius as fraction of sclera
MOUTH_Y = 120               # Mouth vertical centre
MOUTH_RX = 28               # Mouth half-width
MOUTH_RY = 14               # Mouth half-height


# ── Drawing primitives ──────────────────────────────────────────────────────

def _circle(draw, cx, cy, r, fill):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def _ellipse(draw, cx, cy, rx, ry, fill):
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)


def _soft_edge(img, radius=1.2):
    """Very subtle anti-alias softening."""
    blurred = img.filter(ImageFilter.GaussianBlur(radius))
    out = Image.alpha_composite(Image.new('RGBA', img.size, (0, 0, 0, 0)), blurred)
    return Image.alpha_composite(out, img)


# ── Eye drawing ─────────────────────────────────────────────────────────────

def _draw_eye(img, cx, cy, r=EYE_R):
    """Full round cartoon eye: cyan ring + dark centre + white highlight."""
    draw = ImageDraw.Draw(img)
    # Outer ring (sclera) – cyan
    _circle(draw, cx, cy, r, CYAN)
    # Thin darker ring for depth
    _circle(draw, cx, cy, int(r * 0.88), (50, 130, 160))
    # Dark iris
    ir = int(r * IRIS_RATIO)
    _circle(draw, cx, cy, ir, DARK)
    # Subtle gradient – slightly lighter inner zone
    _circle(draw, cx, cy, int(ir * 0.5), DARK_MID)
    # White specular highlight – upper-left
    hr = max(int(r * HIGHLIGHT_RATIO), 3)
    hx = cx - int(r * 0.32)
    hy = cy - int(r * 0.32)
    _circle(draw, hx, hy, hr, WHITE)


def _draw_eye_half_top(img, cx, cy, r=EYE_R, angle=-15):
    """Half-closed eye – flat/angled bottom, open top. For sad/droopy looks.
    Draws full eye then masks bottom portion with an angled cut."""
    # Draw full eye on temp layer
    temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
    _draw_eye(temp, cx, cy, r)
    # Create angled mask – keep top portion
    mask = Image.new('L', img.size, 255)
    md = ImageDraw.Draw(mask)
    # Angled cut line across the eye
    cut_y = cy + int(r * 0.15)
    angle_rad = math.radians(angle)
    dx = int(r * 1.5 * math.cos(angle_rad))
    dy = int(r * 1.5 * math.sin(angle_rad))
    # Fill below the cut with black (remove)
    poly = [
        (cx - dx, cut_y - dy),
        (cx + dx, cut_y + dy),
        (cx + dx, cy + r + 10),
        (cx - dx, cy + r + 10),
    ]
    md.polygon(poly, fill=0)
    # Apply mask
    r_c, g_c, b_c, a_c = temp.split()
    a_c = Image.composite(a_c, Image.new('L', img.size, 0), mask)
    temp = Image.merge('RGBA', (r_c, g_c, b_c, a_c))
    img.alpha_composite(temp)


def _draw_eye_half_bottom(img, cx, cy, r=EYE_R, angle=15):
    """Half-closed eye – flat/angled top, open bottom. Angry/glaring look.
    Like eyelids pushed down from above."""
    temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
    _draw_eye(temp, cx, cy, r)
    mask = Image.new('L', img.size, 255)
    md = ImageDraw.Draw(mask)
    cut_y = cy - int(r * 0.15)
    angle_rad = math.radians(angle)
    dx = int(r * 1.5 * math.cos(angle_rad))
    dy = int(r * 1.5 * math.sin(angle_rad))
    poly = [
        (cx - dx, cut_y + dy),
        (cx + dx, cut_y - dy),
        (cx + dx, cy - r - 10),
        (cx - dx, cy - r - 10),
    ]
    md.polygon(poly, fill=0)
    r_c, g_c, b_c, a_c = temp.split()
    a_c = Image.composite(a_c, Image.new('L', img.size, 0), mask)
    temp = Image.merge('RGBA', (r_c, g_c, b_c, a_c))
    img.alpha_composite(temp)


def _draw_arc_eye(img, cx, cy, r=EYE_R):
    """Curved crescent arc eye – for sleep / grateful (like ⇀ or ↼)."""
    draw = ImageDraw.Draw(img)
    bbox = [cx - r, cy - int(r * 0.6), cx + r, cy + int(r * 0.6)]
    draw.arc(bbox, 200, 340, fill=CYAN, width=max(5, int(r * 0.22)))
    # Add subtle lighter inner arc
    inner_bbox = [cx - r * 0.8, cy - int(r * 0.45), cx + r * 0.8, cy + int(r * 0.45)]
    draw.arc(inner_bbox, 210, 330, fill=CYAN_LIGHT, width=max(3, int(r * 0.13)))


def _draw_line_eye(img, cx, cy, w=None):
    """Thin line eye – fully closed / flat."""
    if w is None:
        w = int(EYE_R * 0.9)
    draw = ImageDraw.Draw(img)
    draw.line([cx - w, cy, cx + w, cy], fill=CYAN, width=4)


def _draw_x_eye(img, cx, cy, r=None):
    """X-shaped eye – broken."""
    if r is None:
        r = int(EYE_R * 0.6)
    draw = ImageDraw.Draw(img)
    draw.line([cx - r, cy - r, cx + r, cy + r], fill=CYAN, width=5)
    draw.line([cx - r, cy + r, cx + r, cy - r], fill=CYAN, width=5)


def _draw_hash_eye(img, cx, cy, r=None):
    """# shaped eye – debug."""
    if r is None:
        r = int(EYE_R * 0.55)
    draw = ImageDraw.Draw(img)
    w = 4
    draw.line([cx - r, cy - r * 0.45, cx + r, cy - r * 0.45], fill=CYAN, width=w)
    draw.line([cx - r, cy + r * 0.45, cx + r, cy + r * 0.45], fill=CYAN, width=w)
    draw.line([cx - r * 0.45, cy - r, cx - r * 0.45, cy + r], fill=CYAN, width=w)
    draw.line([cx + r * 0.45, cy - r, cx + r * 0.45, cy + r], fill=CYAN, width=w)


def _draw_heart_eye(img, cx, cy, s=None):
    """Heart-shaped eye with cyan gradient fill."""
    if s is None:
        s = int(EYE_R * 1.1)
    draw = ImageDraw.Draw(img)
    bump = s * 0.44
    # Two bumps + triangle for heart shape
    # Outer cyan
    _circle(draw, cx - bump * 0.6, cy - bump * 0.25, bump, CYAN)
    _circle(draw, cx + bump * 0.6, cy - bump * 0.25, bump, CYAN)
    pts = [
        (cx - s * 0.82, cy),
        (cx + s * 0.82, cy),
        (cx, cy + s * 0.85),
    ]
    draw.polygon(pts, fill=CYAN)
    # Inner lighter fill
    inner = bump * 0.6
    _circle(draw, cx - bump * 0.55, cy - bump * 0.2, inner, CYAN_LIGHT)
    _circle(draw, cx + bump * 0.55, cy - bump * 0.2, inner, CYAN_LIGHT)
    pts_in = [
        (cx - s * 0.5, cy + s * 0.05),
        (cx + s * 0.5, cy + s * 0.05),
        (cx, cy + s * 0.55),
    ]
    draw.polygon(pts_in, fill=CYAN_LIGHT)
    # Centre highlight
    tiny = inner * 0.35
    _circle(draw, cx, cy - bump * 0.05, tiny, CYAN_PALE)


def _draw_tear_eye(img, cx, cy, r=EYE_R):
    """Eye with tear drops – for broken/crying face."""
    _draw_eye(img, cx, cy, r)
    draw = ImageDraw.Draw(img)
    # Tear bubbles below the eye
    tr = int(r * 0.28)
    _circle(draw, cx - int(r * 0.45), cy + int(r * 0.85), tr, CYAN_LIGHT)
    _circle(draw, cx + int(r * 0.25), cy + int(r * 1.0), int(tr * 0.7), CYAN_LIGHT)
    # Tiny highlight in tear
    _circle(draw, cx - int(r * 0.5), cy + int(r * 0.75), int(tr * 0.3), WHITE)


# ── Mouth drawing ───────────────────────────────────────────────────────────

def _draw_smile(img, cx, cy, rx=MOUTH_RX, ry=MOUTH_RY):
    """Smile: half-ellipse, round on bottom, flat top. Cyan with lighter centre."""
    temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp)
    # Outer cyan
    _ellipse(draw, cx, cy, rx, ry, CYAN)
    # Inner lighter
    _ellipse(draw, cx, cy - int(ry * 0.1), int(rx * 0.6), int(ry * 0.55), CYAN_LIGHT)
    # Mask out top half
    mask = Image.new('L', img.size, 255)
    md = ImageDraw.Draw(mask)
    md.rectangle([0, 0, SIZE, cy], fill=0)
    r_c, g_c, b_c, a_c = temp.split()
    a_c = Image.composite(a_c, Image.new('L', img.size, 0), mask)
    temp = Image.merge('RGBA', (r_c, g_c, b_c, a_c))
    img.alpha_composite(temp)


def _draw_frown(img, cx, cy, rx=MOUTH_RX, ry=MOUTH_RY):
    """Frown: half-ellipse, round on top, flat bottom."""
    temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp)
    _ellipse(draw, cx, cy, rx, ry, CYAN)
    _ellipse(draw, cx, cy + int(ry * 0.1), int(rx * 0.6), int(ry * 0.55), CYAN_LIGHT)
    mask = Image.new('L', img.size, 255)
    md = ImageDraw.Draw(mask)
    md.rectangle([0, cy, SIZE, SIZE], fill=0)
    r_c, g_c, b_c, a_c = temp.split()
    a_c = Image.composite(a_c, Image.new('L', img.size, 0), mask)
    temp = Image.merge('RGBA', (r_c, g_c, b_c, a_c))
    img.alpha_composite(temp)


def _draw_flat_mouth(img, cx, cy, w=MOUTH_RX):
    """Flat line mouth."""
    draw = ImageDraw.Draw(img)
    draw.line([cx - w, cy, cx + w, cy], fill=CYAN, width=4)


def _draw_open_mouth(img, cx, cy, r=None):
    """Small open 'o' mouth."""
    if r is None:
        r = int(MOUTH_RY * 0.6)
    draw = ImageDraw.Draw(img)
    _circle(draw, cx, cy, r, CYAN)
    _circle(draw, cx, cy, int(r * 0.5), CYAN_LIGHT)


def _draw_small_smile(img, cx, cy):
    _draw_smile(img, cx, cy, rx=int(MOUTH_RX * 0.65), ry=int(MOUTH_RY * 0.65))


def _draw_small_frown(img, cx, cy):
    _draw_frown(img, cx, cy, rx=int(MOUTH_RX * 0.65), ry=int(MOUTH_RY * 0.65))


# ── Layout helpers ──────────────────────────────────────────────────────────

def _lx():
    return CX - EYE_SEP

def _rx():
    return CX + EYE_SEP


# ── Face definitions ────────────────────────────────────────────────────────

def _face_awake(img):
    _draw_eye(img, _lx(), EYE_Y)
    _draw_eye(img, _rx(), EYE_Y)
    _draw_flat_mouth(img, CX, MOUTH_Y)

def _face_happy(img):
    _draw_eye(img, _lx(), EYE_Y)
    _draw_eye(img, _rx(), EYE_Y)
    _draw_smile(img, CX, MOUTH_Y)

def _face_sad(img):
    # Half-closed from top (droopy) + frown
    _draw_eye_half_top(img, _lx(), EYE_Y, angle=10)
    _draw_eye_half_top(img, _rx(), EYE_Y, angle=-10)
    _draw_frown(img, CX, MOUTH_Y)

def _face_excited(img):
    r = int(EYE_R * 1.25)
    _draw_eye(img, _lx(), EYE_Y, r)
    _draw_eye(img, _rx(), EYE_Y, r)
    _draw_smile(img, CX, MOUTH_Y, rx=int(MOUTH_RX * 1.15), ry=int(MOUTH_RY * 1.15))

def _face_bored(img):
    # Eyelids pushed down from top – half-closed
    _draw_eye_half_bottom(img, _lx(), EYE_Y, angle=0)
    _draw_eye_half_bottom(img, _rx(), EYE_Y, angle=0)
    _draw_flat_mouth(img, CX, MOUTH_Y, w=int(MOUTH_RX * 0.7))

def _face_angry(img):
    # Eyelids angled down toward centre – angry glare
    _draw_eye_half_bottom(img, _lx(), EYE_Y, angle=-20)
    _draw_eye_half_bottom(img, _rx(), EYE_Y, angle=20)
    _draw_frown(img, CX, MOUTH_Y, rx=int(MOUTH_RX * 0.8), ry=int(MOUTH_RY * 0.8))

def _face_cool(img):
    draw = ImageDraw.Draw(img)
    # Large sunglasses – dark filled with cyan frame
    lens_w = int(EYE_R * 1.35)
    lens_h = int(EYE_R * 0.95)
    frame = 5  # frame thickness
    for side_cx in [_lx(), _rx()]:
        # Cyan frame (outer)
        draw.rounded_rectangle(
            [side_cx - lens_w, EYE_Y - lens_h, side_cx + lens_w, EYE_Y + lens_h],
            radius=int(lens_h * 0.45), fill=CYAN)
        # Dark lens (inner)
        draw.rounded_rectangle(
            [side_cx - lens_w + frame, EYE_Y - lens_h + frame,
             side_cx + lens_w - frame, EYE_Y + lens_h - frame],
            radius=int(lens_h * 0.35), fill=DARK)
        # White highlight dots on lens
        hr = max(4, int(lens_h * 0.15))
        _circle(draw, side_cx - int(lens_w * 0.35), EYE_Y - int(lens_h * 0.3), hr, WHITE)
        _circle(draw, side_cx + int(lens_w * 0.15), EYE_Y + int(lens_h * 0.1), int(hr * 0.5), (200, 230, 240))
    # Bridge
    draw.line([_lx() + lens_w, EYE_Y - int(lens_h * 0.15),
               _rx() - lens_w, EYE_Y - int(lens_h * 0.15)], fill=CYAN, width=5)
    _draw_small_smile(img, CX, MOUTH_Y + 5)

def _face_grateful(img):
    _draw_arc_eye(img, _lx(), EYE_Y)
    _draw_arc_eye(img, _rx(), EYE_Y)
    _draw_smile(img, CX, MOUTH_Y)

def _face_sleep(img):
    _draw_arc_eye(img, _lx(), EYE_Y)
    _draw_arc_eye(img, _rx(), EYE_Y)
    _draw_flat_mouth(img, CX, MOUTH_Y, w=int(MOUTH_RX * 0.5))

def _face_sleep2(img):
    _draw_arc_eye(img, _lx(), EYE_Y)
    _draw_arc_eye(img, _rx(), EYE_Y)
    _draw_flat_mouth(img, CX, MOUTH_Y, w=int(MOUTH_RX * 0.35))

def _face_motivated(img):
    r = int(EYE_R * 1.15)
    _draw_eye(img, _lx(), EYE_Y, r)
    _draw_eye(img, _rx(), EYE_Y, r)
    _draw_smile(img, CX, MOUTH_Y)

def _face_demotivated(img):
    _draw_eye_half_bottom(img, _lx(), EYE_Y, angle=0)
    _draw_eye_half_bottom(img, _rx(), EYE_Y, angle=0)
    _draw_flat_mouth(img, CX, MOUTH_Y, w=int(MOUTH_RX * 0.6))

def _face_intense(img):
    r = int(EYE_R * 1.25)
    _draw_eye(img, _lx(), EYE_Y, r)
    _draw_eye(img, _rx(), EYE_Y, r)
    _draw_open_mouth(img, CX, MOUTH_Y)

def _face_smart(img):
    _draw_eye(img, _lx(), EYE_Y)
    _draw_eye(img, _rx(), EYE_Y)
    _draw_small_smile(img, CX, MOUTH_Y)

def _face_lonely(img):
    r = int(EYE_R * 0.85)
    _draw_eye(img, _lx(), EYE_Y, r)
    _draw_eye(img, _rx(), EYE_Y, r)
    _draw_small_frown(img, CX, MOUTH_Y)

def _face_friend(img):
    _draw_heart_eye(img, _lx(), EYE_Y)
    _draw_heart_eye(img, _rx(), EYE_Y)
    _draw_smile(img, CX, MOUTH_Y)

def _face_broken(img):
    _draw_tear_eye(img, _lx(), EYE_Y)
    _draw_tear_eye(img, _rx(), EYE_Y)
    _draw_frown(img, CX, MOUTH_Y, rx=int(MOUTH_RX * 0.6), ry=int(MOUTH_RY * 0.6))

def _face_debug(img):
    _draw_hash_eye(img, _lx(), EYE_Y)
    _draw_hash_eye(img, _rx(), EYE_Y)
    _draw_flat_mouth(img, CX, MOUTH_Y, w=int(MOUTH_RX * 0.5))

def _face_look_r(img):
    off = 8
    _draw_eye(img, _lx() + off, EYE_Y)
    _draw_eye(img, _rx() + off, EYE_Y)
    _draw_flat_mouth(img, CX, MOUTH_Y)

def _face_look_l(img):
    off = 8
    _draw_eye(img, _lx() - off, EYE_Y)
    _draw_eye(img, _rx() - off, EYE_Y)
    _draw_flat_mouth(img, CX, MOUTH_Y)

def _face_look_r_happy(img):
    off = 8
    _draw_eye(img, _lx() + off, EYE_Y)
    _draw_eye(img, _rx() + off, EYE_Y)
    _draw_smile(img, CX, MOUTH_Y)

def _face_look_l_happy(img):
    off = 8
    _draw_eye(img, _lx() - off, EYE_Y)
    _draw_eye(img, _rx() - off, EYE_Y)
    _draw_smile(img, CX, MOUTH_Y)

def _face_upload(img):
    _draw_eye(img, _lx(), EYE_Y)
    _draw_line_eye(img, _rx(), EYE_Y)
    _draw_open_mouth(img, CX, MOUTH_Y)

def _face_upload1(img):
    _draw_eye(img, _lx(), EYE_Y)
    _draw_eye(img, _rx(), EYE_Y)
    _draw_open_mouth(img, CX, MOUTH_Y)

def _face_upload2(img):
    _draw_line_eye(img, _lx(), EYE_Y)
    _draw_eye(img, _rx(), EYE_Y)
    _draw_open_mouth(img, CX, MOUTH_Y)


# ── Face registry ───────────────────────────────────────────────────────────

FACES = {
    'awake':        (_face_awake,        "Open eyes, neutral"),
    'happy':        (_face_happy,        "Round eyes, smile"),
    'sad':          (_face_sad,          "Droopy half-closed eyes, frown"),
    'excited':      (_face_excited,      "Big eyes, big smile"),
    'bored':        (_face_bored,        "Half-closed eyes, flat mouth"),
    'angry':        (_face_angry,        "Angry angled eyes, frown"),
    'cool':         (_face_cool,         "Dark sunglasses, small smile"),
    'grateful':     (_face_grateful,     "Arc eyes, smile"),
    'sleep':        (_face_sleep,        "Crescent eyes, small flat mouth"),
    'sleep2':       (_face_sleep2,       "Crescent eyes, tiny flat mouth"),
    'motivated':    (_face_motivated,    "Wide eyes, smile"),
    'demotivated':  (_face_demotivated,  "Half-closed eyes, flat mouth"),
    'intense':      (_face_intense,      "Wide eyes, open mouth"),
    'smart':        (_face_smart,        "Round eyes, small smile"),
    'lonely':       (_face_lonely,       "Small eyes, small frown"),
    'friend':       (_face_friend,       "Heart eyes, smile"),
    'broken':       (_face_broken,       "Teary eyes, frown"),
    'debug':        (_face_debug,        "Hash eyes, flat mouth"),
    'look_r':       (_face_look_r,       "Eyes right, neutral"),
    'look_l':       (_face_look_l,       "Eyes left, neutral"),
    'look_r_happy': (_face_look_r_happy, "Eyes right, smile"),
    'look_l_happy': (_face_look_l_happy, "Eyes left, smile"),
    'upload':       (_face_upload,       "1-0 uploading"),
    'upload1':      (_face_upload1,      "1-1 uploading"),
    'upload2':      (_face_upload2,      "0-1 uploading"),
}


# ── Generator ───────────────────────────────────────────────────────────────

def create_face(name, draw_fn, size=SIZE):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw_fn(img)
    img = _soft_edge(img)
    return img


def generate_all_faces(output_dir='.'):
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
