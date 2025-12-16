from __future__ import annotations
from PIL import Image, ImageFilter, ImageDraw, ImageFont

from ..constants import CANVAS_W, CANVAS_H, DEFAULT_FONT_PATH
from ..utils.images import alpha_composite


# -------------------------------------------------------------
# Background Blur + Fade
# -------------------------------------------------------------
def crypto_blur_background(bg: Image.Image) -> Image.Image:
    bg_ratio = bg.width / bg.height
    canvas_ratio = CANVAS_W / CANVAS_H

    if bg_ratio > canvas_ratio:
        new_h = CANVAS_H
        new_w = int(bg.width * (CANVAS_H / bg.height))
    else:
        new_w = CANVAS_W
        new_h = int(bg.height * (CANVAS_W / bg.width))

    bg_resized = bg.resize((new_w, new_h), Image.LANCZOS).convert("RGBA")

    left = (new_w - CANVAS_W) // 2
    top = (new_h - CANVAS_H) // 2
    bg_cropped = bg_resized.crop((left, top, left + CANVAS_W, top + CANVAS_H))

    fade = Image.new("RGBA", (CANVAS_W, CANVAS_H))
    draw = ImageDraw.Draw(fade)

    for y in range(CANVAS_H):
        alpha = int(80 * (y / CANVAS_H))
        draw.line([(0, y), (CANVAS_W, y)], fill=(0, 0, 0, alpha))

    return Image.alpha_composite(bg_cropped, fade)


# -------------------------------------------------------------
# Dynamic text sizing + metrics
# -------------------------------------------------------------
def measure_text_block(lines, font_ratio, font_path, line_gap_ratio=0.01):
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    size = int(CANVAS_H * font_ratio)
    font = ImageFont.truetype(font_path or DEFAULT_FONT_PATH, size)

    total_height = 0
    max_width = 0
    line_data = []

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        max_width = max(max_width, w)
        total_height += h
        if i < len(lines) - 1:
            total_height += int(CANVAS_H * line_gap_ratio)

        line_data.append((line, font, bbox, w, h))

    return total_height, max_width, line_data


def draw_text_block(canvas, line_data, y_start, fill):
    draw = ImageDraw.Draw(canvas)
    y = y_start

    for line, font, _bbox, w, h in line_data:
        x = (CANVAS_W - w) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += h + int(CANVAS_H * 0.01)


# -------------------------------------------------------------
# MAIN RENDERER — Crypto / Pragmatic Play Style
# -------------------------------------------------------------
# -------------------------------------------------------------
# MAIN RENDERER — Crypto / Pragmatic Play Style (WITH FINAL ELLIPSE CLIP)
# -------------------------------------------------------------
def render_crypto_card(background, character, title_lines, provider, font_path=None):

    canvas = crypto_blur_background(background)

    if not font_path:
        font_path = DEFAULT_FONT_PATH

    # ---------------------------------------------------------
    # CHARACTER (large, center)
    # ---------------------------------------------------------
    max_width = int(CANVAS_W * 0.95)
    max_height = int(CANVAS_H * 0.85)

    width_scale = max_width / character.width
    height_scale = max_height / character.height
    scale = max(width_scale, height_scale)

    w = int(character.width * scale)
    h = int(character.height * scale)

    cx = (CANVAS_W - w) // 2
    cy = int(CANVAS_H * 0.02)

    resized = character.resize((w, h), Image.LANCZOS)

    glow = resized.filter(ImageFilter.GaussianBlur(50))
    glow = glow.point(lambda p: int(p * 0.7))

    alpha_composite(canvas, glow, (cx - 20, cy - 20))
    alpha_composite(canvas, resized, (cx, cy))

    # ---------------------------------------------------------
    # COLOR DETECTION (main hue)
    # ---------------------------------------------------------
    quantized = canvas.quantize(colors=32, method=2)
    quantized_rgb = quantized.convert("RGB")
    small = quantized_rgb.resize((50, 50), Image.LANCZOS)

    detected_color = None
    colors = small.getcolors(2500)

    if colors:
        colors.sort(key=lambda x: x[0], reverse=True)

        for count, col in colors:
            if isinstance(col, tuple):
                r, g, b = col
                avg = (r + g + b) / 3
                variance = abs(r - avg) + abs(g - avg) + abs(b - avg)

                if variance > 30 and (r + g + b) > 100:
                    detected_color = (r, g, b)
                    break

        if detected_color is None:
            for _, col in colors:
                if isinstance(col, tuple):
                    r, g, b = col
                    if 30 < r + g + b < 700:
                        detected_color = (r, g, b)
                        break

    if detected_color is None:
        detected_color = (50, 50, 50)

    r, g, b = detected_color

    # ---------------------------------------------------------
    # CURVED BAND WITH GRADIENT FADE (two ellipses)
    # ---------------------------------------------------------

    # Small ellipse (solid core - almost edge to edge, flatter)
    SMALL_ARC_W = int(CANVAS_W * 1.15)
    SMALL_ARC_H = int(CANVAS_H * 0.315)  # 10% flatter (0.35 * 0.9)

    small_bbox = (
        CANVAS_W // 2 - SMALL_ARC_W // 2,
        int(CANVAS_H - SMALL_ARC_H * 0.7),  # Higher position (was 0.5)
        CANVAS_W // 2 + SMALL_ARC_W // 2,
        int(CANVAS_H + SMALL_ARC_H * 1.3)   # Extends further down
    )

    # Large ellipse (fade extent - reaches title area)
    LARGE_ARC_W = int(CANVAS_W * 1.1)
    LARGE_ARC_H = int(CANVAS_H * 0.65)  # Much taller

    large_bbox = (
        CANVAS_W // 2 - LARGE_ARC_W // 2,
        int(CANVAS_H - LARGE_ARC_H * 0.5),
        CANVAS_W // 2 + LARGE_ARC_W // 2,
        int(CANVAS_H + LARGE_ARC_H * 1.5)
    )

    # Create gradient overlay
    gradient_overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))

    # Layer 1: Solid core (small ellipse) - more opaque
    core_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core_layer)
    core_draw.pieslice(small_bbox, 180, 360, fill=(r, g, b, 255))
    core_blurred = core_layer.filter(ImageFilter.GaussianBlur(25))
    gradient_overlay = Image.alpha_composite(gradient_overlay, core_blurred)

    # Layer 2: Medium fade - more pronounced bleed
    mid_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    mid_draw = ImageDraw.Draw(mid_layer)
    mid_draw.pieslice(large_bbox, 180, 360, fill=(r, g, b, 220))
    mid_blurred = mid_layer.filter(ImageFilter.GaussianBlur(80))  # Increased from 50
    gradient_overlay = Image.alpha_composite(gradient_overlay, mid_blurred)

    # Layer 3: Outer fade - stronger color with bleed
    outer_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    outer_draw = ImageDraw.Draw(outer_layer)
    outer_draw.pieslice(large_bbox, 180, 360, fill=(r, g, b, 240))  # Increased from 200
    outer_blurred = outer_layer.filter(ImageFilter.GaussianBlur(140))
    gradient_overlay = Image.alpha_composite(gradient_overlay, outer_blurred)

    # Composite onto canvas
    canvas = Image.alpha_composite(canvas, gradient_overlay)

    # ---------------------------------------------------------
    # TEXT BLOCK (title + provider) - Rendered AFTER curved fade
    # ---------------------------------------------------------
    text_area_start = int(CANVAS_H * 0.68)
    text_area_end = int(CANVAS_H * 0.95)
    available_height = text_area_end - text_area_start
    available_width = int(CANVAS_W * 0.85)

    title_ratio = 0.15
    provider_ratio = 0.048
    min_gap = int(CANVAS_H * 0.04)

    for _ in range(10):
        title_h, title_w, title_data = measure_text_block(
            title_lines, title_ratio, font_path
        )

        if provider:
            prov_h, prov_w, prov_data = measure_text_block(
                [provider], provider_ratio, font_path
            )
            total_h = title_h + min_gap + prov_h
            max_w = max(title_w, prov_w)
        else:
            total_h = title_h
            max_w = title_w

        if total_h <= available_height and max_w <= available_width:
            break

        if max_w > available_width:
            scale = available_width / max_w
            title_ratio *= scale * 0.85
            provider_ratio *= scale * 0.85

        if total_h > available_height:
            scale = available_height / total_h
            title_ratio *= scale * 0.85
            provider_ratio *= scale * 0.85

        title_ratio = max(title_ratio, 0.05)
        provider_ratio = max(provider_ratio, 0.025)

    title_h, title_w, title_data = measure_text_block(
        title_lines, title_ratio, font_path
    )

    if provider:
        prov_h, prov_w, prov_data = measure_text_block(
            [provider], provider_ratio, font_path
        )
        total_h = title_h + min_gap + prov_h
        title_y = text_area_start + (available_height - total_h) // 2
        prov_y = title_y + title_h + min_gap
    else:
        title_y = text_area_start + (available_height - title_h) // 2

    draw_text_block(canvas, title_data, title_y, (255, 255, 255, 255))

    if provider:
        draw_text_block(canvas, prov_data, prov_y, (255, 255, 255, 235))

    return canvas