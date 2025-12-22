from __future__ import annotations
from PIL import Image, ImageFilter, ImageDraw, ImageFont

from ..constants import CANVAS_W, CANVAS_H, DEFAULT_FONT_PATH, get_provider_font
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
    size = max(1, int(CANVAS_H * font_ratio))  # Ensure minimum size of 1
    from pathlib import Path
    font_file_exists = Path(font_path or DEFAULT_FONT_PATH).exists() if font_path else True
    print(f"[DEBUG MEASURE] Font path: {font_path}, Size: {size}, Exists: {font_file_exists}", flush=True)
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
        font_name = font.getname() if hasattr(font, 'getname') else 'unknown'
        print(f"[DEBUG DRAW] Drawing '{line}' with font {font} (family={font_name}) at ({x}, {y})", flush=True)
        draw.text((x, y), line, font=font, fill=fill)
        y += h + int(CANVAS_H * 0.01)


# -------------------------------------------------------------
# MAIN RENDERER — Crypto / Pragmatic Play Style
# -------------------------------------------------------------
# -------------------------------------------------------------
# MAIN RENDERER — Crypto / Pragmatic Play Style (WITH FINAL ELLIPSE CLIP)
# -------------------------------------------------------------
def render_crypto_card(
    background,
    character,
    title_lines,
    provider,
    font_path=None,
    provider_font_path=None,
    band_color=None,
    provider_logo=None,
    title_image=None,
    blur_enabled=True,
):

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
    # CURVED BAND WITH GRADIENT FADE (two ellipses) - OPTIONAL
    # ---------------------------------------------------------
    if blur_enabled:
        # COLOR DETECTION (main hue)
        # Use manual band_color if provided, otherwise auto-detect
        if band_color is not None:
            r, g, b = band_color
        else:
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
    # TEXT BLOCK (title + provider) — MATCH BIG BASS OUTPUT
    # ---------------------------------------------------------
    text_area_start = int(CANVAS_H * 0.68)
    text_area_end   = int(CANVAS_H * 0.95)
    available_height = text_area_end - text_area_start
    available_width  = int(CANVAS_W * 0.92)

    # Initial ratios
    title_ratio    = 0.15
    provider_ratio = 0.048
    min_gap = int(CANVAS_H * 0.04)

    # Reserve space for provider if present
    min_provider_height = int(CANVAS_H * 0.03) if provider else 0  # ~16px for provider

    # ---------------------------------------------------------
    # 1) TITLE — Fit WIDTH and respect provider space
    # ---------------------------------------------------------
    for _ in range(10):
        title_h, title_w, title_data = measure_text_block(
            title_lines, title_ratio, font_path
        )

        fits_width = title_w <= available_width

        # If there's a provider, ensure title doesn't take too much vertical space
        if provider:
            max_title_height = available_height - min_gap - min_provider_height
            fits_height = title_h <= max_title_height
        else:
            fits_height = True

        if fits_width and fits_height:
            break

        # Scale down based on what doesn't fit
        if not fits_width:
            scale = (available_width / title_w) * 0.92
        else:  # doesn't fit height (provider case)
            scale = (max_title_height / title_h) * 0.92

        title_ratio *= scale

    # Recalculate title
    title_h, title_w, title_data = measure_text_block(
        title_lines, title_ratio, font_path
    )

    # If using title image, calculate its actual height for layout purposes
    actual_title_h = title_h
    if title_image is not None:
        available_width_img = int(CANVAS_W * 0.92)
        available_height_img = int(CANVAS_H * 0.27)
        orig_width, orig_height = title_image.size
        width_scale = available_width_img / orig_width
        height_scale = available_height_img / orig_height
        final_scale = min(width_scale, height_scale)
        actual_title_h = int(orig_height * final_scale)

    # ---------------------------------------------------------
    # 2) PROVIDER — keep sizing/position consistent
    # ---------------------------------------------------------
    prov_data = None
    prov_h = prov_w = 0

    if provider:
        # Provider font: explicit provider_font_path (from UI) wins,
        # otherwise fall back to main title font.
        effective_provider_font_path = provider_font_path or font_path
        provider_font_path = get_provider_font(provider, fallback=effective_provider_font_path)

        # Fixed base ratio for consistency
        provider_ratio = 0.045

        # Measure once with the base ratio
        prov_h, prov_w, prov_data = measure_text_block(
            [provider], provider_ratio, provider_font_path
        )

        # Remaining space to the bottom; anchor provider near bottom with padding
        bottom_padding = int(CANVAS_H * 0.04)
        max_provider_h = max(1, text_area_end - bottom_padding - text_area_start)

        # If it would overflow, shrink a bit (light clamp)
        if prov_w > available_width or prov_h > max_provider_h:
            scale_w = available_width / prov_w if prov_w else 1
            scale_h = max_provider_h / prov_h if prov_h else 1
            scale = min(scale_w, scale_h) * 0.9
            provider_ratio = max(0.03, provider_ratio * scale)
            prov_h, prov_w, prov_data = measure_text_block(
                [provider], provider_ratio, provider_font_path
            )

    # ---------------------------------------------------------
    # FINAL POSITIONING
    # ---------------------------------------------------------
    if provider:
        # Anchor provider near bottom with padding for consistency
        bottom_padding = int(CANVAS_H * 0.04)
        prov_y = text_area_end - bottom_padding - prov_h

        # Space available for title above provider
        available_for_title = prov_y - min_gap - text_area_start
        if available_for_title > 0:
            title_y = text_area_start + max(0, (available_for_title - actual_title_h) // 2)
        else:
            # Fallback: stack title above provider
            total_h = actual_title_h + min_gap + prov_h
            title_y = text_area_start + (available_height - total_h) // 2
            prov_y = title_y + actual_title_h + min_gap
    else:
        title_y = text_area_start + (available_height - actual_title_h) // 2

    # Draw title (image or text)
    if title_image is not None:
        # Use title image with dynamic positioning based on provider height
        from .title_image import render_title_image
        canvas = render_title_image(canvas, title_image, scale=1.0, provider_height=prov_h if provider else 0)

        # If there's a provider, we need to calculate where it goes relative to the title image
        if provider:
            # The title_image renderer centers both, so we need to recalculate provider Y
            # Get the actual image dimensions after scaling
            available_width = int(CANVAS_W * 0.92)
            available_height_constraint = int(CANVAS_H * 0.27)

            orig_width, orig_height = title_image.size
            width_scale = available_width / orig_width
            height_scale = available_height_constraint / orig_height
            final_scale = min(width_scale, height_scale)

            new_height = int(orig_height * final_scale)

            # Calculate where title starts and provider should go
            total_h = new_height + min_gap + prov_h
            title_y_actual = text_area_start + (available_height - total_h) // 2
            prov_y = title_y_actual + new_height + min_gap
    else:
        # Use text title
        draw_text_block(canvas, title_data, title_y, (255, 255, 255, 255))

    # Draw provider (if exists)
    if provider:
        draw_text_block(canvas, prov_data, prov_y, (255, 255, 255, 235))

    # ---------------------------------------------------------
    # PROVIDER LOGO (if enabled)
    # ---------------------------------------------------------
    if provider_logo is not None:
        from ..provider_logo import render_provider_logo

        # Create a minimal config for provider logo rendering
        # We need this to pass positioning/scaling info to render_provider_logo
        cfg = type('obj', (object,), {
            'provider_logo': type('obj', (object,), {
                'position': 'bottom_right',
                'margin': 18,
                'max_width_ratio': 0.25,
                'max_height_ratio': 0.12,
                'opacity': 1.0,
                'invert_for_dark': True
            })()
        })()

        canvas = render_provider_logo(canvas, provider_logo, cfg)

    return canvas