from __future__ import annotations
from PIL import Image, ImageFilter, ImageDraw, ImageFont

from ..constants import CANVAS_W, CANVAS_H, DEFAULT_FONT_PATH, get_provider_font
from ..utils.images import alpha_composite


# -------------------------------------------------------------
# Background Blur + Fade
# -------------------------------------------------------------
def crypto_blur_background(bg: Image.Image, canvas_w: int = None, canvas_h: int = None) -> Image.Image:
    if canvas_w is None:
        canvas_w = CANVAS_W
    if canvas_h is None:
        canvas_h = CANVAS_H

    bg_ratio = bg.width / bg.height
    canvas_ratio = canvas_w / canvas_h

    if bg_ratio > canvas_ratio:
        new_h = canvas_h
        new_w = int(bg.width * (canvas_h / bg.height))
    else:
        new_w = canvas_w
        new_h = int(bg.height * (canvas_w / bg.width))

    bg_resized = bg.resize((new_w, new_h), Image.BICUBIC).convert("RGBA")

    # Force symmetric crop to avoid LANCZOS half-pixel seams
    dx = new_w - canvas_w
    dy = new_h - canvas_h

    left = dx // 2
    top = dy // 2

    # Compensate for odd pixels to eliminate vertical line artifacts
    if dx % 2 != 0:
        left += 1
    if dy % 2 != 0:
        top += 1

    bg_cropped = bg_resized.crop((left, top, left + canvas_w, top + canvas_h))

    fade = Image.new("RGBA", (canvas_w, canvas_h))
    draw = ImageDraw.Draw(fade)

    for y in range(canvas_h):
        alpha = int(80 * (y / canvas_h))
        draw.line([(0, y), (canvas_w - 1, y)], fill=(0, 0, 0, alpha))

    return Image.alpha_composite(bg_cropped, fade)


# -------------------------------------------------------------
# Dynamic text sizing + metrics
# -------------------------------------------------------------
def measure_text_block(lines, font_ratio, font_path, canvas_h, line_gap_ratio=0.01):
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    size = max(1, int(canvas_h * font_ratio))  # Ensure minimum size of 1
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
            total_height += int(canvas_h * line_gap_ratio)

        line_data.append((line, font, bbox, w, h))

    return total_height, max_width, line_data


def draw_text_block(canvas, line_data, y_start, fill, canvas_width, canvas_height):
    draw = ImageDraw.Draw(canvas)
    y = y_start

    for line, font, _bbox, w, h in line_data:
        x = (canvas_width - w) // 2
        font_name = font.getname() if hasattr(font, 'getname') else 'unknown'
        print(f"[DEBUG DRAW] Drawing '{line}' with font {font} (family={font_name}) at ({x}, {y})", flush=True)
        draw.text((x, y), line, font=font, fill=fill)
        y += h + int(canvas_height * 0.01)


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
    blur_scale: float = 1.0,
    text_scale: float = 1.0,
    text_offset: float = 0.0,
    canvas_width: int = None,
    canvas_height: int = None,
):
    # Use defaults if not provided
    if canvas_width is None:
        canvas_width = CANVAS_W
    if canvas_height is None:
        canvas_height = CANVAS_H

    canvas = crypto_blur_background(background, canvas_width, canvas_height)

    if not font_path:
        font_path = DEFAULT_FONT_PATH

    # ---------------------------------------------------------
    # CHARACTER (large, center)
    # ---------------------------------------------------------
    max_width = int(canvas_width * 0.95)
    max_height = int(canvas_height * 0.85)

    width_scale = max_width / character.width
    height_scale = max_height / character.height
    scale = max(width_scale, height_scale)

    w = int(character.width * scale)
    h = int(character.height * scale)

    cx = (canvas_width - w) // 2
    cy = int(canvas_height * 0.02)

    resized = character.resize((w, h), Image.LANCZOS)

    # Create glow with proper boundary handling
    # Add padding for blur to prevent edge artifacts
    blur_radius = 50
    padding = blur_radius * 2  # Extra space for blur

    # Create padded canvas for glow
    padded_w = w + padding * 2
    padded_h = h + padding * 2
    glow_padded = Image.new("RGBA", (padded_w, padded_h), (0, 0, 0, 0))
    glow_padded.alpha_composite(resized, dest=(padding, padding))

    # Apply blur on padded image
    glow_blurred = glow_padded.filter(ImageFilter.GaussianBlur(blur_radius))
    glow_blurred = glow_blurred.point(lambda p: int(p * 0.7))

    # Composite glow with offset, using safe clipping
    glow_x = cx - 20 - padding
    glow_y = cy - 20 - padding
    alpha_composite(canvas, glow_blurred, (glow_x, glow_y))

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

        # Apply blur_scale to intensities (clamped)
        intensity_scale = max(0.3, min(2.0, blur_scale))

        # Small ellipse (solid core - almost edge to edge, flatter)
        SMALL_ARC_W = int(canvas_width * 1.15)
        SMALL_ARC_H = int(canvas_height * 0.315)  # 10% flatter (0.35 * 0.9)

        small_bbox = (
            canvas_width // 2 - SMALL_ARC_W // 2,
            int(canvas_height - SMALL_ARC_H * 0.7),  # Higher position (was 0.5)
            canvas_width // 2 + SMALL_ARC_W // 2,
            int(canvas_height + SMALL_ARC_H * 1.3)   # Extends further down
        )

        # Large ellipse (fade extent - reaches title area)
        LARGE_ARC_W = int(canvas_width * 1.1)
        LARGE_ARC_H = int(canvas_height * 0.65)  # Much taller

        large_bbox = (
            canvas_width // 2 - LARGE_ARC_W // 2,
            int(canvas_height - LARGE_ARC_H * 0.5),
            canvas_width // 2 + LARGE_ARC_W // 2,
            int(canvas_height + LARGE_ARC_H * 1.5)
        )

        # Create gradient overlay
        gradient_overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))

        # Layer 1: Solid core (small ellipse) - more opaque
        core_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        core_draw = ImageDraw.Draw(core_layer)
        core_draw.pieslice(small_bbox, 180, 360, fill=(r, g, b, int(255 * intensity_scale)))
        core_blurred = core_layer.filter(ImageFilter.GaussianBlur(25))
        gradient_overlay = Image.alpha_composite(gradient_overlay, core_blurred)

        # Layer 2: Medium fade - more pronounced bleed
        mid_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        mid_draw = ImageDraw.Draw(mid_layer)
        mid_draw.pieslice(large_bbox, 180, 360, fill=(r, g, b, int(220 * intensity_scale)))
        mid_blurred = mid_layer.filter(ImageFilter.GaussianBlur(80))  # Increased from 50
        gradient_overlay = Image.alpha_composite(gradient_overlay, mid_blurred)

        # Layer 3: Outer fade - stronger color with bleed
        outer_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        outer_draw = ImageDraw.Draw(outer_layer)
        outer_draw.pieslice(large_bbox, 180, 360, fill=(r, g, b, int(240 * intensity_scale)))  # Increased from 200
        outer_blurred = outer_layer.filter(ImageFilter.GaussianBlur(140))
        gradient_overlay = Image.alpha_composite(gradient_overlay, outer_blurred)

        # Composite onto canvas
        canvas = Image.alpha_composite(canvas, gradient_overlay)

    # ---------------------------------------------------------
    # TEXT BLOCK (title + provider)
    # ---------------------------------------------------------
    text_area_start = int(canvas_height * 0.68)
    text_area_end   = int(canvas_height * 0.95)
    available_height = text_area_end - text_area_start
    available_width  = int(canvas_width * 0.92)

    # Initial ratios
    title_ratio    = 0.15 * text_scale
    provider_ratio = 0.045 * text_scale
    min_gap = int(canvas_height * 0.04)

    # Reserve space for provider if present
    min_provider_height = int(canvas_height * 0.03) if provider else 0  # ~16px for provider

    # ---------------------------------------------------------
    # 1) TITLE — Fit WIDTH and respect provider space
    # ---------------------------------------------------------
    for _ in range(10):
        title_h, title_w, title_data = measure_text_block(
            title_lines, title_ratio, font_path, canvas_height
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
        title_lines, title_ratio, font_path, canvas_height
    )

    # If using title image, calculate its actual height for layout purposes
    actual_title_h = title_h
    if title_image is not None:
        available_width_img = int(canvas_width * 0.92)
        available_height_img = int(canvas_height * 0.27)
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
            [provider], provider_ratio, provider_font_path, canvas_height
        )

        # Remaining space to the bottom; anchor provider near bottom with padding
        bottom_padding = int(canvas_height * 0.04)
        max_provider_h = max(1, text_area_end - bottom_padding - text_area_start)

        # If it would overflow, shrink a bit (light clamp)
        if prov_w > available_width or prov_h > max_provider_h:
            scale_w = available_width / prov_w if prov_w else 1
            scale_h = max_provider_h / prov_h if prov_h else 1
            scale = min(scale_w, scale_h) * 0.9
            provider_ratio = max(0.03, provider_ratio * scale)
            prov_h, prov_w, prov_data = measure_text_block(
                [provider], provider_ratio, provider_font_path, canvas_height
            )

    # ---------------------------------------------------------
    # FINAL POSITIONING
    # ---------------------------------------------------------
    if provider:
        # Anchor provider near bottom with padding for consistency
        bottom_padding = int(canvas_height * 0.04)
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
    else:
        # Use text title
        draw_text_block(canvas, title_data, title_y, (255, 255, 255, 255), canvas_width, canvas_height)

    # Draw provider (if exists)
    if provider:
        # Apply optional vertical offset (text_offset is ratio of canvas height)
        prov_y_with_offset = prov_y + int(text_offset * canvas_height)
        title_y = title_y + int(text_offset * canvas_height)
        draw_text_block(canvas, prov_data, prov_y_with_offset, (255, 255, 255, 235), canvas_width, canvas_height)

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

def safe_alpha_composite(dst, src, pos):
    tmp = Image.new("RGBA", dst.size, (0, 0, 0, 0))
    tmp.paste(src, pos)
    return Image.alpha_composite(dst, tmp)
