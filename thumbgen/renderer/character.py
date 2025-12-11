from __future__ import annotations
from typing import Tuple, List
from PIL import Image
from ..constants import (
    CANVAS_W,
    CANVAS_H,
    CHAR_SPACING_RATIO,
    CHAR_MARGIN_RATIO,
    CHAR_MAX_WIDTH_RATIO
)


def render_character(char: Image.Image, height_ratio: float) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Scale character much larger + anchor toward bottom.
    """

    # scale character - make it bigger by using a more generous height ratio
    target_h = int(CANVAS_H * height_ratio * 1.15)  # 15% larger than config
    scale = target_h / char.height
    target_w = int(char.width * scale)

    resized = char.resize((target_w, target_h), Image.LANCZOS)

    # anchor character so it extends to ~85% bottom, leaving room for title at bottom
    bottom_anchor = int(CANVAS_H * 0.85)
    y = bottom_anchor - target_h
    x = (CANVAS_W - target_w) // 2

    return resized, (x, y)


def render_characters(
    characters: List[Image.Image],
    height_ratio: float,
    spacing_ratio: float = CHAR_SPACING_RATIO,
    margin_ratio: float = CHAR_MARGIN_RATIO,
    max_width_ratio: float = CHAR_MAX_WIDTH_RATIO
) -> List[Tuple[Image.Image, Tuple[int, int]]]:
    """
    Render multiple characters with automatic positioning and intelligent spacing.

    Characters are distributed evenly across the canvas with percentage-based spacing.
    Characters maintain their size as the central visual element, allowing overlap if needed.

    Args:
        characters: List of 1-3 character images
        height_ratio: Target height ratio for characters (relative to canvas height)
        spacing_ratio: Spacing between characters as ratio of canvas width (default: 0.05 = 5%)
        margin_ratio: Not used for multi-character (kept for API compatibility)
        max_width_ratio: Not used for multi-character (kept for API compatibility)

    Returns:
        List of (resized_image, (x, y)) tuples
    """
    num_chars = len(characters)
    if num_chars == 0:
        return []

    result = []

    # Calculate target size based on height - characters are the MAIN ELEMENT
    target_size = int(CANVAS_H * height_ratio)

    # Calculate base positioning - anchor characters closer to bottom for better framing
    bottom_anchor = int(CANVAS_H * 0.95)

    # Calculate spacing in pixels
    spacing = int(CANVAS_W * spacing_ratio)

    # First pass: scale all characters to target size (NO auto-scaling down)
    scaled_chars = []
    for char in characters:
        # Scale based on the larger dimension to ensure consistent visual size
        max_dimension = max(char.width, char.height)
        scale = target_size / max_dimension

        target_w = int(char.width * scale)
        target_h = int(char.height * scale)
        resized = char.resize((target_w, target_h), Image.LANCZOS)
        scaled_chars.append((resized, target_w, target_h))

    # Calculate total width with spacing
    total_char_width = sum(w for _, w, _ in scaled_chars)
    total_spacing = spacing * (num_chars - 1) if num_chars > 1 else 0
    total_width = total_char_width + total_spacing

    # If total width exceeds canvas, scale everything down proportionally
    if total_width > CANVAS_W * max_width_ratio:
        scale_down = (CANVAS_W * max_width_ratio) / total_width
        # Re-scale all characters
        new_scaled_chars = []
        for resized, w, h in scaled_chars:
            new_w = int(w * scale_down)
            new_h = int(h * scale_down)
            new_resized = resized.resize((new_w, new_h), Image.LANCZOS)
            new_scaled_chars.append((new_resized, new_w, new_h))
        scaled_chars = new_scaled_chars

        # Recalculate total width
        total_char_width = sum(w for _, w, _ in scaled_chars)
        total_spacing = int(spacing * scale_down) * (num_chars - 1) if num_chars > 1 else 0
        total_width = total_char_width + total_spacing
        spacing = int(spacing * scale_down)

    # Calculate starting X position to center the entire group
    start_x = (CANVAS_W - total_width) // 2

    # Position each character
    current_x = start_x
    for resized, final_w, final_h in scaled_chars:
        # Calculate Y position (same for all)
        y = bottom_anchor - final_h

        # Set X position
        x = current_x

        result.append((resized, (x, y)))

        # Move to next position
        current_x += final_w + spacing

    return result
