#!/usr/bin/env python3
"""
Generate placeholder icon PNGs for the runner-status state diagram.
These are simplified stand-ins for the real SF Symbols used in
perplexity-cpu-loop.js (questionmark.circle.fill, pause.circle.fill,
exclamationmark.triangle.fill, checkmark.circle.fill, xmark.circle.fill,
nosign, trash.circle.fill, arrow.counterclockwise.circle.fill, and the
new clock.badge.xmark used for the "orphaned" state).
"""
from PIL import Image, ImageDraw
import math
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "icons")
os.makedirs(OUT_DIR, exist_ok=True)

SIZE = 160


def canvas():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def save(img, name):
    img.save(os.path.join(OUT_DIR, f"{name}.png"))


def circle_icon(fill):
    img = canvas()
    d = ImageDraw.Draw(img)
    pad = 6
    d.ellipse([pad, pad, SIZE - pad, SIZE - pad], fill=fill)
    return img, d


# questionmark.circle.fill (orange)
img, d = circle_icon("#FF9500")
d.text((SIZE * 0.36, SIZE * 0.18), "?", fill="white",
       font=None, font_size=int(SIZE * 0.55) if hasattr(d, "font_size") else None)
# Pillow default font has no size param on older versions; draw manually instead.
from PIL import ImageFont
try:
    font_big = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(SIZE * 0.55))
except Exception:
    font_big = ImageFont.load_default()
img, d = circle_icon("#FF9500")
bbox = d.textbbox((0, 0), "?", font=font_big)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((SIZE - tw) / 2 - bbox[0], (SIZE - th) / 2 - bbox[1]), "?", fill="white", font=font_big)
save(img, "questionmark_circle")

# pause.circle.fill (gray)
img, d = circle_icon("#8E8E93")
bar_w = SIZE * 0.10
gap = SIZE * 0.08
y0, y1 = SIZE * 0.32, SIZE * 0.68
cx = SIZE / 2
d.rectangle([cx - gap / 2 - bar_w, y0, cx - gap / 2, y1], fill="white")
d.rectangle([cx + gap / 2, y0, cx + gap / 2 + bar_w, y1], fill="white")
save(img, "pause_circle")


def triangle_icon(color):
    img = canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(SIZE * 0.5, SIZE * 0.06), (SIZE * 0.04, SIZE * 0.92), (SIZE * 0.96, SIZE * 0.92)],
              fill=color)
    d.rectangle([SIZE * 0.46, SIZE * 0.34, SIZE * 0.54, SIZE * 0.68], fill="white")
    d.ellipse([SIZE * 0.45, SIZE * 0.74, SIZE * 0.55, SIZE * 0.84], fill="white")
    return img


save(triangle_icon("#FF3B30"), "triangle_red")
save(triangle_icon("#FF9500"), "triangle_orange")

# checkmark.circle.fill (green)
img, d = circle_icon("#34C759")
d.line([(SIZE * 0.28, SIZE * 0.52), (SIZE * 0.44, SIZE * 0.68), (SIZE * 0.75, SIZE * 0.32)],
       fill="white", width=int(SIZE * 0.07), joint="curve")
save(img, "check_circle")

# xmark.circle.fill (red)
img, d = circle_icon("#FF3B30")
lw = int(SIZE * 0.07)
d.line([(SIZE * 0.32, SIZE * 0.32), (SIZE * 0.68, SIZE * 0.68)], fill="white", width=lw)
d.line([(SIZE * 0.32, SIZE * 0.68), (SIZE * 0.68, SIZE * 0.32)], fill="white", width=lw)
save(img, "xmark_circle")

# nosign (red circle outline + diagonal slash)
img = canvas()
d = ImageDraw.Draw(img)
lw = int(SIZE * 0.09)
pad = 8
d.ellipse([pad, pad, SIZE - pad, SIZE - pad], outline="#FF3B30", width=lw)
d.line([(SIZE * 0.20, SIZE * 0.20), (SIZE * 0.80, SIZE * 0.80)], fill="#FF3B30", width=lw)
save(img, "nosign")

# trash.circle.fill (red)
img, d = circle_icon("#FF3B30")
d.rectangle([SIZE * 0.34, SIZE * 0.30, SIZE * 0.66, SIZE * 0.64], fill="white")
d.rectangle([SIZE * 0.30, SIZE * 0.62, SIZE * 0.70, SIZE * 0.68], fill="white")
d.rectangle([SIZE * 0.42, SIZE * 0.66, SIZE * 0.58, SIZE * 0.71], fill="white")
for fx in (0.42, 0.50, 0.58):
    d.line([(SIZE * fx, SIZE * 0.36), (SIZE * fx, SIZE * 0.58)], fill="#FF3B30", width=3)
save(img, "trash_circle")

# arrow.counterclockwise.circle.fill (orange)
img, d = circle_icon("#FF9500")
r = SIZE * 0.26
cx, cy = SIZE / 2, SIZE / 2
start_deg, end_deg = 40, 340
pts = []
for deg in range(start_deg, end_deg + 1, 4):
    rad = math.radians(deg)
    pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
d.line(pts, fill="white", width=int(SIZE * 0.055))
tip = pts[0]
ang = math.radians(start_deg)
ahx, ahy = cx + r * math.cos(ang), cy + r * math.sin(ang)
d.polygon([
    (ahx - SIZE * 0.10, ahy + SIZE * 0.02),
    (ahx + SIZE * 0.08, ahy + SIZE * 0.02),
    (ahx - SIZE * 0.01, ahy - SIZE * 0.11),
], fill="white")
save(img, "arrow_ccw_circle")

# idle replacement: history-style clock with counterclockwise return arrow.
# This follows the user's reference more closely than pause.circle.fill while
# keeping the same filled-gray-disc + white glyph treatment as the rest of the
# icon set.
img, d = circle_icon("#8E8E93")
cx, cy = SIZE * 0.56, SIZE * 0.50
r = SIZE * 0.28
# clock arc, leaving a gap at upper-left for the return arrow
arc_box = [cx - r, cy - r, cx + r, cy + r]
d.arc(arc_box, start=215, end=520, fill="white", width=int(SIZE * 0.06))
# return arrow shaft + head at lower-left
lw = int(SIZE * 0.06)
d.line([(SIZE * 0.28, SIZE * 0.70), (SIZE * 0.28, SIZE * 0.42)], fill="white", width=lw)
d.line([(SIZE * 0.28, SIZE * 0.42), (SIZE * 0.52, SIZE * 0.42)], fill="white", width=lw)
d.polygon([
    (SIZE * 0.28, SIZE * 0.42),
    (SIZE * 0.40, SIZE * 0.34),
    (SIZE * 0.40, SIZE * 0.50),
], fill="white")
# clock hands
d.line([(cx, cy), (cx, cy - r * 0.46)], fill="white", width=int(SIZE * 0.055))
d.line([(cx, cy), (cx + r * 0.30, cy + r * 0.30)], fill="white", width=int(SIZE * 0.055))
save(img, "idle_history_circle")

# clock.badge.xmark composite (new "orphaned" icon)
# Base: clock face (filled circle + hands + ticks). Badge: small red circle
# w/ white border + white x, lower-right, signaling "interrupt this".
img = canvas()
d = ImageDraw.Draw(img)
cx, cy, r = SIZE * 0.44, SIZE * 0.52, SIZE * 0.40
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#FF3B30")
# hands
d.line([(cx, cy), (cx, cy - r * 0.62)], fill="white", width=int(SIZE * 0.05))
d.line([(cx, cy), (cx + r * 0.42, cy)], fill="white", width=int(SIZE * 0.05))
# ticks
for deg in range(0, 360, 30):
    rad = math.radians(deg)
    x1, y1 = cx + r * 0.82 * math.cos(rad), cy + r * 0.82 * math.sin(rad)
    x2, y2 = cx + r * 0.95 * math.cos(rad), cy + r * 0.95 * math.sin(rad)
    d.line([(x1, y1), (x2, y2)], fill="white", width=2)
# badge
bx, by, br = SIZE * 0.80, SIZE * 0.80, SIZE * 0.22
d.ellipse([bx - br, by - br, bx + br, by + br], fill="white")
d.ellipse([bx - br * 0.8, by - br * 0.8, bx + br * 0.8, by + br * 0.8], fill="#FF3B30")
lw = int(SIZE * 0.035)
d.line([(bx - br * 0.4, by - br * 0.4), (bx + br * 0.4, by + br * 0.4)], fill="white", width=lw)
d.line([(bx - br * 0.4, by + br * 0.4), (bx + br * 0.4, by - br * 0.4)], fill="white", width=lw)
save(img, "clock_badge_xmark")

print("Generated icons:", sorted(os.listdir(OUT_DIR)))
