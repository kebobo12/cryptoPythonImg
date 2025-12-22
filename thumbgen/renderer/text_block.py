from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
from ..constants import CANVAS_W, CANVAS_H, get_provider_font
from ..utils.text import text_size


def render_text_block(
    canvas: Image.Image,
    title_lines,
    subtitle,
    provider_text,
    font_path,
    provider_font_path: str | None = None,
):
    """
    Draw text inside the blurred band.
    """

    draw = ImageDraw.Draw(canvas)

    # Better typography scaling (TITLE/SUBTITLE)
    title_font = ImageFont.truetype(font_path, int(CANVAS_H * 0.085))
    subtitle_font = ImageFont.truetype(font_path, int(CANVAS_H * 0.055))

    # Provider font: use explicit provider_font_path if supplied (from UI),
    # otherwise fall back to the main title font.
    if provider_text:
        effective_provider_font_path = provider_font_path or font_path
        provider_font_path_resolved = get_provider_font(provider_text, fallback=effective_provider_font_path)
        provider_font = ImageFont.truetype(provider_font_path_resolved, int(CANVAS_H * 0.040))
    else:
        provider_font = None

    lines = []
    for t in title_lines:
        lines.append((t, title_font))
    if subtitle:
        lines.append((subtitle, subtitle_font))
    if provider_text and provider_font:
        lines.append((provider_text, provider_font))

    line_gap = int(CANVAS_H * 0.015)
    sizes = [(txt, font, *text_size(draw, txt, font)) for txt, font in lines]
    total_h = sum(h for _, _, _, h in sizes) + line_gap * (len(sizes) - 1)

    # Vertical placement - position text block at bottom with padding
    bottom_padding = int(CANVAS_H * 0.08)  # 8% padding from bottom
    y = CANVAS_H - total_h - bottom_padding

    for txt, font, w, h in sizes:
        x = (CANVAS_W - w) // 2
        draw.text((x + 2, y + 2), txt, font=font, fill=(0, 0, 0, 160))  # shadow
        draw.text((x, y), txt, font=font, fill=(255, 255, 255, 255))    # main
        y += h + line_gap

    return canvas

def draw_centered_text(canvas, text, y, font_ratio, fill):
    from PIL import ImageDraw, ImageFont
    from ..constants import CANVAS_H, CANVAS_W, DEFAULT_FONT_PATH

    size = int(CANVAS_H * font_ratio)
    font = ImageFont.truetype(DEFAULT_FONT_PATH, size)

    draw = ImageDraw.Draw(canvas)
    w, h = draw.textsize(text, font=font)
    x = (CANVAS_W - w) // 2
    draw.text((x, y), text, font=font, fill=fill)
