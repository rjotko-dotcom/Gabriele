"""Renderius uždeda ant balto fono, mazgo vaizdui prideda rodykles ir užrašus.

  python3 finish_renders.py <render_dir> <out_dir>
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont
import matplotlib

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data/fonts/ttf/DejaVuSans.ttf")
FONTB = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data/fonts/ttf/DejaVuSans-Bold.ttf")


def on_white(path):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert("RGB")


def arrow(d, p1, p2, color, w):
    d.line([p1, p2], fill=color, width=w)
    a = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    L, W = w * 5, w * 2.5
    b = (p2[0] - L * math.cos(a), p2[1] - L * math.sin(a))
    n = (-math.sin(a) * W, math.cos(a) * W)
    d.polygon([p2, (b[0] + n[0], b[1] + n[1]), (b[0] - n[0], b[1] - n[1])], fill=color)


def callout(d, anchor, txt_pos, text, font, color=(40, 40, 40)):
    w = max(2, font.size // 12)
    d.line([anchor, txt_pos], fill=color, width=w)
    d.ellipse([anchor[0] - 2 * w, anchor[1] - 2 * w, anchor[0] + 2 * w, anchor[1] + 2 * w], fill=color)
    bbox = d.multiline_textbbox(txt_pos, text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    left = txt_pos[0] < anchor[0]
    x = txt_pos[0] - tw - 12 if left else txt_pos[0] + 12
    y = txt_pos[1] - th / 2
    pad = 10
    d.rounded_rectangle([x - pad, y - pad, x + tw + pad, y + th + pad + 4], radius=8,
                        fill=(255, 255, 255), outline=color, width=w)
    d.multiline_text((x, y), text, font=font, fill=color)


for f in sorted(os.listdir(SRC)):
    if f.endswith(".png") and f[:2] in ("01", "02", "03", "04"):
        on_white(os.path.join(SRC, f)).save(os.path.join(OUT, f.replace(".png", ".jpg")), quality=93)

# mazgas
im = on_white(os.path.join(SRC, "05_mazgas_TIP-ON.png"))
pts = json.load(open(os.path.join(SRC, "05_mazgas_points.json")))
W, H = im.size
k = W / 1000
d = ImageDraw.Draw(im)
f = ImageFont.truetype(FONT, int(26 * k))
fb = ImageFont.truetype(FONTB, int(34 * k))
fs = ImageFont.truetype(FONT, int(22 * k))
callout(d, pts["tipon"], (0.40 * W, 0.09 * H),
        "Blum TIP-ON (atšokimo mechanizmas),\nprisuktas prie spintelės šono,\n70 mm nuo durelės viršaus", f)
callout(d, pts["plate"], (0.80 * W, 0.25 * H), "Metalinė plokštelė\nant durelės", f)
callout(d, pts["hinge_top"], (0.62 * W, 0.80 * H),
        "Vyriai Blum CLIP top 110°\nBE spyruoklės (2 vnt.)", f)
callout(d, pts["shelf"], (0.36 * W, 0.62 * H), "Reguliuojama lentyna", f)


def tag(xy, text, color):
    bb = d.multiline_textbbox(xy, text, font=f)
    d.rounded_rectangle([bb[0] - 8, bb[1] - 6, bb[2] + 8, bb[3] + 8], radius=6, fill=(255, 255, 255))
    d.multiline_text(xy, text, font=f, fill=color)


red, green = (190, 30, 60), (30, 120, 60)
arrow(d, (0.985 * W, 0.71 * H), (0.90 * W, 0.645 * H), red, int(7 * k))
tag((0.70 * W, 0.62 * H), "1. paspausti", red)
arrow(d, (0.90 * W, 0.75 * H), (0.985 * W, 0.815 * H), green, int(7 * k))
tag((0.72 * W, 0.70 * H), "2. atšoka", green)
d.rectangle([0, H - 130 * k, W, H], fill=(255, 255, 255))
d.text((25 * k, H - 120 * k), "MAZGAS: atšokančios durelės mechanizmas", font=fb, fill=(30, 30, 30))
d.text((25 * k, H - 75 * k),
       "Durelė be rankenos. Paspaudus kraštą, TIP-ON išstumia durelę, toliau atidaroma ranka.\n"
       "Uždaroma pastumiant iki galo – magnetas prilaiko durelę.", font=fs, fill=(70, 70, 70))
im.save(os.path.join(OUT, "05_mazgas_TIP-ON.jpg"), quality=93)
print("ok")
