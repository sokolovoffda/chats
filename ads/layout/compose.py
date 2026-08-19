#!/usr/bin/env python3
"""Compose a square Avito thumbnail for website-layout services.

Work at 2048×2048, then Lanczos-downscale to 1024 so Cyrillic stays sharp
in the Avito feed. Visual language: ThoughtLab scale + AuthKit glass +
one crimson CTA.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
BG_PATH = ROOT / "bg.png"
OUT_DIR = Path("/opt/cursor/artifacts/assets")
LOCAL_OUT = ROOT / "out"

SIZE = 2048
CYAN = (92, 225, 230, 255)  # #5CE1E6 — same accent as the VKR card
CYAN_LINE = (92, 225, 230, 235)
WHITE = (255, 255, 255, 255)
MIST = (171, 174, 187, 235)
CRIMSON = (252, 28, 70, 255)  # ThoughtLab #fc1c46
VOID = (0, 0, 0, 255)

FONT_DISPLAY = "/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf"
FONT_UI = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
FONT_UI_MED = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"
FONT_MONO = "/usr/share/fonts/truetype/macos/JetBrainsMono-Regular.ttf"

PILLS = [
    ("Лендинг / многостраничник", "Pixel-perfect из Figma"),
    ("Адаптив под все экраны", "React · Next.js · HTML"),
    ("Анимации и микроэффекты", "SEO и быстрая загрузка"),
]


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def advance(fnt: ImageFont.FreeTypeFont, ch: str) -> float:
    return fnt.getlength(ch)


def tracked_width(fnt: ImageFont.FreeTypeFont, text: str, tracking: float) -> float:
    if not text:
        return 0.0
    gap = tracking * fnt.size
    return sum(advance(fnt, ch) for ch in text) + gap * (len(text) - 1)


def cap_height(fnt: ImageFont.FreeTypeFont) -> int:
    """Visual cap height using a diacritic-free Cyrillic capital."""
    box = fnt.getbbox("Н", anchor="lt")
    return box[3] - box[1]


def extra_above_cap(fnt: ImageFont.FreeTypeFont, text: str) -> int:
    """Pixels Й / Ё stick out above the cap line (lt box vs cap height)."""
    box = fnt.getbbox(text, anchor="lt")
    return max(0, (box[3] - box[1]) - cap_height(fnt))


def draw_tracked(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill,
    tracking: float = 0.0,
    anchor: str = "lt",
) -> int:
    x, y = xy
    gap = tracking * fnt.size
    cx = float(x)
    for i, ch in enumerate(text):
        draw.text((cx, y), ch, font=fnt, fill=fill, anchor=anchor)
        cx += advance(fnt, ch) + (gap if i < len(text) - 1 else 0)
    return int(round(cx - x))


def draw_tracked_glow(
    base: Image.Image,
    xy: tuple[float, float],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill,
    tracking: float,
    blur: int = 10,
) -> int:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = draw_tracked(d, xy, text, fnt, (0, 0, 0, 230), tracking)
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))
    d2 = ImageDraw.Draw(base)
    draw_tracked(d2, xy, text, fnt, fill, tracking)
    return w


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def make_glass(
    src: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    tint: tuple[int, int, int, int] = (8, 12, 28, 72),
    blur: int = 26,
    border: tuple[int, int, int, int] = (182, 215, 247, 68),
    border_width: int = 2,
) -> Image.Image:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    crop = src.crop(box).filter(ImageFilter.GaussianBlur(blur))
    glass = Image.alpha_composite(crop, Image.new("RGBA", (w, h), tint))
    shine = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shine).rectangle((0, 0, w, max(10, h // 7)), fill=(255, 255, 255, 14))
    glass = Image.alpha_composite(glass, shine)
    mask = rounded_mask((w, h), radius)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(glass, (0, 0), mask)
    edge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    inset = border_width // 2
    ImageDraw.Draw(edge).rounded_rectangle(
        (inset, inset, w - 1 - inset, h - 1 - inset),
        radius=radius,
        outline=border,
        width=border_width,
    )
    return Image.alpha_composite(out, edge)


def pill_text_size(fnt: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    tw = int(round(fnt.getlength(text)))
    box = fnt.getbbox(text, anchor="lt")
    th = box[3] - box[1]
    return tw, th


def draw_pill(
    canvas: Image.Image,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    w: int,
    h: int,
) -> None:
    x, y = xy
    pill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle(
        (1, 1, w - 2, h - 2),
        radius=h // 2,
        fill=(6, 10, 22, 170),
        outline=CYAN_LINE,
        width=3,
    )
    pd.text((w / 2, h / 2 - 1), text, font=fnt, fill=WHITE, anchor="mm")
    canvas.alpha_composite(pill, (x, y))


def left_vignette(size: int) -> Image.Image:
    ys, xs = np.mgrid[0:size, 0:size]
    nx = xs / size
    ny = ys / size
    left = np.clip(1.0 - nx / 0.56, 0.0, 1.0) ** 1.35
    top = np.clip(1.0 - ny / 0.36, 0.0, 1.0) ** 1.2
    a = np.clip(0.42 * left + 0.16 * top, 0.0, 1.0)
    alpha = (a * 190).astype(np.uint8)
    layer = Image.fromarray(np.dstack([np.zeros((size, size, 3), dtype=np.uint8), alpha]), "RGBA")
    return layer.filter(ImageFilter.GaussianBlur(20))


def cyan_glow(size: tuple[int, int]) -> Image.Image:
    w, h = size
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = int(w * 0.30), int(h * 0.18)
    for i, alpha in enumerate((40, 20, 8)):
        r = int(min(w, h) * (0.38 - i * 0.08))
        g.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(92, 225, 230, alpha))
    return glow.filter(ImageFilter.GaussianBlur(96))


def compose() -> Image.Image:
    bg = Image.open(BG_PATH).convert("RGBA")
    if bg.size != (SIZE, SIZE):
        bg = bg.resize((SIZE, SIZE), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (SIZE, SIZE), VOID)
    canvas.alpha_composite(bg)
    canvas.alpha_composite(cyan_glow((SIZE, SIZE)))
    canvas.alpha_composite(left_vignette(SIZE))

    draw = ImageDraw.Draw(canvas)

    f_display = font(FONT_DISPLAY, 400)
    f_kicker = font(FONT_MONO, 38)
    f_sub = font(FONT_UI_MED, 46)
    f_pill = font(FONT_UI, 42)
    f_cta = font(FONT_UI, 44)

    left = 88
    tracking_display = -0.02

    # Width guard: shrink display size if the longer word would clip.
    longest = max(
        tracked_width(f_display, "ВЕРСТКА", tracking_display),
        tracked_width(f_display, "САЙТОВ", tracking_display),
    )
    max_w = SIZE - left - 72
    if longest > max_w:
        scale = max_w / longest
        f_display = font(FONT_DISPLAY, max(280, int(400 * scale)))

    draw_tracked(draw, (left, 96), "IWEB  ·  FRONTEND", f_kicker, MIST, tracking=0.20)

    # Stacked title: cap-aligned lines, extra leading so Й doesn't collide.
    y1 = 168
    ch = cap_height(f_display)
    y2 = y1 + ch + extra_above_cap(f_display, "САЙТОВ") + 22
    draw_tracked_glow(canvas, (left, y1), "ВЕРСТКА", f_display, WHITE, tracking_display)
    w2 = draw_tracked_glow(canvas, (left, y2), "САЙТОВ", f_display, WHITE, tracking_display)

    # Cyan rule exactly under САЙТОВ; crimson dot on the geometric center.
    line2_box = f_display.getbbox("САЙТОВ", anchor="lt")
    rule_y = y2 + (line2_box[3] - line2_box[1]) + 18
    rule_w = w2
    draw.rounded_rectangle((left, rule_y, left + rule_w, rule_y + 6), radius=3, fill=CYAN)
    dot_r = 14
    dot_cx = left + rule_w / 2
    dot_cy = rule_y + 3
    draw.ellipse((dot_cx - dot_r - 3, dot_cy - dot_r - 3, dot_cx + dot_r + 3, dot_cy + dot_r + 3), fill=(0, 0, 0, 200))
    draw.ellipse((dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r), fill=CRIMSON)

    sub_y = rule_y + 68
    draw_tracked(
        draw,
        (left, sub_y),
        "СОВРЕМЕННЫЙ ДИЗАЙН  ·  FIGMA → КОД",
        f_sub,
        CYAN,
        tracking=0.055,
    )

    # Tight vertical rhythm: same left edge, equal pill cells, glass hugs content.
    pad_x, pad_y = 40, 24
    gap_x, gap_y = 20, 20
    panel_pad_x, panel_pad_y = 40, 40
    gap_sub_to_glass = 176  # clearly below the subtitle, not stuck to it
    gap_glass_to_cta = 72

    max_th = 0
    col_tw = [0, 0]
    for left_t, right_t in PILLS:
        for col, t in enumerate((left_t, right_t)):
            tw, th = pill_text_size(f_pill, t)
            col_tw[col] = max(col_tw[col], tw)
            max_th = max(max_th, th)
    col_w = [tw + pad_x * 2 for tw in col_tw]
    pill_h = max_th + pad_y * 2
    inner_w = col_w[0] + gap_x + col_w[1]
    inner_h = pill_h * 3 + gap_y * 2

    sub_box = f_sub.getbbox("СОВРЕМЕННЫЙ ДИЗАЙН  ·  FIGMA → КОД", anchor="lt")
    sub_h = sub_box[3] - sub_box[1]
    panel_x0 = left
    panel_y0 = sub_y + sub_h + gap_sub_to_glass
    panel_x1 = panel_x0 + panel_pad_x * 2 + inner_w
    panel_y1 = panel_y0 + panel_pad_y * 2 + inner_h
    panel = tuple(int(round(v)) for v in (panel_x0, panel_y0, panel_x1, panel_y1))
    panel_x0, panel_y0, panel_x1, panel_y1 = panel

    pills_origin_x = panel_x0 + panel_pad_x
    pills_origin_y = panel_y0 + panel_pad_y

    cta = "Консультация бесплатно"
    cta_tw = int(round(f_cta.getlength(cta)))
    cta_box = f_cta.getbbox(cta, anchor="lt")
    cta_th = cta_box[3] - cta_box[1]
    cta_h = cta_th + 36
    cta_w = cta_tw + 88
    cta_x = left
    cta_y = panel_y1 + gap_glass_to_cta
    if cta_y + cta_h > SIZE - 40:
        overflow = cta_y + cta_h - (SIZE - 40)
        panel_y0 -= overflow
        panel_y1 -= overflow
        pills_origin_y -= overflow
        cta_y -= overflow
        panel = (panel_x0, panel_y0, panel_x1, panel_y1)

    glass = make_glass(canvas, panel, radius=44, tint=(5, 9, 22, 72), blur=22)
    canvas.alpha_composite(glass, (panel[0], panel[1]))

    cy = pills_origin_y
    for left_t, right_t in PILLS:
        draw_pill(canvas, (pills_origin_x, cy), left_t, f_pill, col_w[0], pill_h)
        draw_pill(canvas, (pills_origin_x + col_w[0] + gap_x, cy), right_t, f_pill, col_w[1], pill_h)
        cy += pill_h + gap_y

    glow = Image.new("RGBA", (cta_w + 64, cta_h + 48), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(
        (16, 20, cta_w + 47, cta_h + 27),
        radius=cta_h // 2 + 8,
        fill=(252, 28, 70, 55),
    )
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)), (cta_x - 32, cta_y - 8))

    btn = Image.new("RGBA", (cta_w, cta_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(btn)
    bd.rounded_rectangle((0, 0, cta_w - 1, cta_h - 1), radius=cta_h // 2, fill=CRIMSON)
    bd.text((cta_w / 2, cta_h / 2 - 2), cta, font=f_cta, fill=WHITE, anchor="mm")
    canvas.alpha_composite(btn, (cta_x, cta_y))

    print(
        "layout",
        {
            "sub_bottom": sub_y + sub_h,
            "glass": panel,
            "gap_sub_glass": panel_y0 - (sub_y + sub_h),
            "pills": (pills_origin_x, pills_origin_y, col_w, pill_h),
            "cta": (cta_x, cta_y, cta_w, cta_h),
            "gap_glass_cta": cta_y - panel_y1,
            "bottom_pad": SIZE - (cta_y + cta_h),
        },
    )

    return canvas


def save(img: Image.Image) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_OUT.mkdir(parents=True, exist_ok=True)
    hi = img.convert("RGB")
    lo = hi.resize((1024, 1024), Image.Resampling.LANCZOS)
    for dest in (OUT_DIR, LOCAL_OUT):
        hi.save(dest / "layout-card-square-2x.png", "PNG", optimize=True)
        lo.save(dest / "layout-card-square.png", "PNG", optimize=True)
    print("wrote", OUT_DIR / "layout-card-square.png")
    print("display fitted; output 1024 + 2048")


if __name__ == "__main__":
    save(compose())
