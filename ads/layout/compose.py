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


def draw_pill(
    canvas: Image.Image,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    min_w: int,
    pad_x: int = 40,
    pad_y: int = 22,
) -> tuple[int, int]:
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = dummy.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w = max(min_w, tw + pad_x * 2)
    h = th + pad_y * 2
    x, y = xy
    pill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle(
        (1, 1, w - 2, h - 2),
        radius=h // 2,
        fill=(6, 10, 22, 155),
        outline=CYAN_LINE,
        width=3,
    )
    pd.text((w / 2, h / 2 - 1), text, font=fnt, fill=WHITE, anchor="mm")
    canvas.alpha_composite(pill, (x, y))
    return w, h


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
    tracking_display = -0.035

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

    sub_y = rule_y + 56
    draw_tracked(
        draw,
        (left, sub_y),
        "СОВРЕМЕННЫЙ ДИЗАЙН  ·  FIGMA → КОД",
        f_sub,
        CYAN,
        tracking=0.055,
    )

    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    pad_x, pad_y = 40, 22
    gap_x, gap_y = 18, 18
    col_ws = [0, 0]
    pill_h = 0
    for left_t, right_t in PILLS:
        for col, t in enumerate((left_t, right_t)):
            bbox = dummy.textbbox((0, 0), t, font=f_pill)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            col_ws[col] = max(col_ws[col], tw + pad_x * 2)
            pill_h = max(pill_h, th + pad_y * 2)

    inner_w = col_ws[0] + gap_x + col_ws[1]
    inner_h = pill_h * 3 + gap_y * 2
    panel_pad_x, panel_pad_y = 34, 30
    pills_origin_x = left + 6
    pills_origin_y = sub_y + int(f_sub.size * 1.35)

    cta = "Консультация бесплатно"
    cta_bbox = dummy.textbbox((0, 0), cta, font=f_cta)
    cta_tw, cta_th = cta_bbox[2] - cta_bbox[0], cta_bbox[3] - cta_bbox[1]
    cta_h = cta_th + 36
    cta_w = cta_tw + 88
    bottom_pad = 56
    cta_x = left
    cta_y = SIZE - bottom_pad - cta_h

    # Glass hugs the pills, then stretches down toward the CTA so the footer
    # has weight without covering the orb on the far right.
    panel = (
        pills_origin_x - panel_pad_x,
        pills_origin_y - panel_pad_y,
        min(pills_origin_x + inner_w + panel_pad_x, int(SIZE * 0.74)),
        min(cta_y - 24, pills_origin_y + inner_h + panel_pad_y + 120),
    )

    glass = make_glass(canvas, panel, radius=48, tint=(5, 9, 22, 64), blur=22)
    canvas.alpha_composite(glass, (panel[0], panel[1]))

    cy = pills_origin_y
    for left_t, right_t in PILLS:
        draw_pill(canvas, (pills_origin_x, cy), left_t, f_pill, min_w=col_ws[0], pad_x=pad_x, pad_y=pad_y)
        draw_pill(
            canvas,
            (pills_origin_x + col_ws[0] + gap_x, cy),
            right_t,
            f_pill,
            min_w=col_ws[1],
            pad_x=pad_x,
            pad_y=pad_y,
        )
        cy += pill_h + gap_y

    glow = Image.new("RGBA", (cta_w + 90, cta_h + 90), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(
        (20, 20, cta_w + 69, cta_h + 69),
        radius=cta_h // 2 + 12,
        fill=(252, 28, 70, 80),
    )
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(24)), (cta_x - 45, cta_y - 45))

    btn = Image.new("RGBA", (cta_w, cta_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(btn)
    bd.rounded_rectangle((0, 0, cta_w - 1, cta_h - 1), radius=cta_h // 2, fill=CRIMSON)
    bd.text((cta_w / 2, cta_h / 2 - 2), cta, font=f_cta, fill=WHITE, anchor="mm")
    canvas.alpha_composite(btn, (cta_x, cta_y))

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
