from __future__ import annotations
from PIL import Image

from ..constants import CANVAS_W, CANVAS_H
from ..utils.images import alpha_composite


def get_content_bbox(img):
    """
    Get bounding box of non-transparent content in an image.
    Returns (left, top, right, bottom) of visible pixels.
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Get alpha channel
    alpha = img.split()[3]

    # Find bounding box of non-transparent pixels
    bbox = alpha.getbbox()

    if bbox:
        return bbox
    else:
        # If completely transparent (shouldn't happen), return full image
        return (0, 0, img.width, img.height)


def render_dual_card(background, char1, char2, title_image):
    """
    Zeus vs Hades style - two characters side by side with title banner in center.

    Args:
        background: Background image
        char1: Left character
        char2: Right character
        title_image: Title banner image to place in center

    Returns:
        Composed canvas with both characters and title
    """
    # 1) Background - keep sharp and clear
    bg_ratio = background.width / background.height
    canvas_ratio = CANVAS_W / CANVAS_H

    if bg_ratio > canvas_ratio:
        new_h = CANVAS_H
        new_w = int(background.width * (CANVAS_H / background.height))
    else:
        new_w = CANVAS_W
        new_h = int(background.height * (CANVAS_W / background.width))

    bg_resized = background.resize((new_w, new_h), Image.LANCZOS).convert("RGBA")
    left = (new_w - CANVAS_W) // 2
    top = (new_h - CANVAS_H) // 2
    canvas = bg_resized.crop((left, top, left + CANVAS_W, top + CANVAS_H))

    # 2) Characters - CONSISTENT POSITIONING (crop transparent edges first)
    # Step 1: Crop transparent edges from both characters
    bbox1 = get_content_bbox(char1)
    char1_cropped = char1.crop(bbox1)

    bbox2 = get_content_bbox(char2)
    char2_cropped = char2.crop(bbox2)

    # Step 2: Scale both characters to consistent height (52% of canvas)
    char_target_h = int(CANVAS_H * 0.52)

    # Left character
    scale_l = char_target_h / char1_cropped.height
    left_w = int(char1_cropped.width * scale_l)
    left_h = char_target_h
    left_resized = char1_cropped.resize((left_w, left_h), Image.LANCZOS)

    # Right character
    scale_r = char_target_h / char2_cropped.height
    right_w = int(char2_cropped.width * scale_r)
    right_h = char_target_h
    right_resized = char2_cropped.resize((right_w, right_h), Image.LANCZOS)

    # Step 3: Position characters at FIXED percentages (consistent across all games)
    # Left character: centered at 30% from left
    left_center_x = int(CANVAS_W * 0.30)
    left_x = left_center_x - (left_w // 2)

    # Right character: centered at 70% from left
    right_center_x = int(CANVAS_W * 0.70)
    right_x = right_center_x - (right_w // 2)

    # Step 4: Top-align both characters
    char_y = int(CANVAS_H * 0.15)  # 15% from top

    # Composite characters
    alpha_composite(canvas, left_resized, (left_x, char_y))
    alpha_composite(canvas, right_resized, (right_x, char_y))

    # 3) Title banner - positioned at reference Y=345px (58.5% on 590px canvas)
    # Layered ON TOP of characters
    title_target_w = int(CANVAS_W * 0.85)  # 85% width
    scale_t = title_target_w / title_image.width
    title_w = title_target_w
    title_h = int(title_image.height * scale_t)
    title_resized = title_image.resize((title_w, title_h), Image.LANCZOS)

    # Position title at reference Y position, centered horizontally
    title_center_y = int(CANVAS_H * 0.585)  # 345px on 590px canvas
    title_x = (CANVAS_W - title_w) // 2
    title_y = title_center_y - (title_h // 2)

    alpha_composite(canvas, title_resized, (title_x, title_y))

    return canvas
