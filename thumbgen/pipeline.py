"""
Improved full thumbnail-generation pipeline for thumbgen.
Produces high-quality casino-style promo card thumbnails.

Key improvements:
- Better background composition with upward bias toward sky
- Larger, better-anchored character placement
- Shorter and darker blur band (modern style)
- Better typography scaling
- Clean provider logo placement after text
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from PIL import Image
from PIL import Image, ImageFilter, ImageDraw

from .config import GameConfig, load_config
from .loader import load_assets
from .errors import ProcessingError
from .utils.logging import ok, error, heading
from .utils.images import alpha_composite, save_png
from .renderer.background import render_background
from .renderer.character import render_character, render_characters
from .renderer.band import render_bottom_band
from .renderer.text_block import render_text_block
from .renderer.title_image import render_title_image
from .provider_logo import render_provider_logo
from .constants import CANVAS_W, CANVAS_H


def generate_thumbnail(game_dir: Path, output_dir: Path) -> Optional[Path]:
    start_time = time.time()

    try:
        cfg_path = game_dir / "config.json"
        cfg: GameConfig = load_config(cfg_path)

        assets = load_assets(game_dir, cfg)
        output_dir.mkdir(parents=True, exist_ok=True)

        # --------------------------------------------------------
        # LAYOUT SWITCHING
        # --------------------------------------------------------
        layout = getattr(cfg, "layout", "default")

        # CRYPTO MODE - Single character with text overlay
        if layout == "crypto":
            from .renderer.crypto_card import render_crypto_card

            canvas = render_crypto_card(
                background=assets.background,
                character=assets.characters[0],
                title_lines=cfg.title_lines,
                provider=cfg.provider_text,
                font_path=cfg.font_path
            )

            out_path = output_dir / cfg.output_filename
            save_png(canvas, out_path)
            ok(f"{game_dir.name} -> {out_path} (crypto mode)")
            return out_path

        # DUAL MODE - Two characters with title banner
        if layout == "dual" and len(assets.characters) >= 2:
            from .renderer.dual_card import render_dual_card

            if not assets.title_image:
                raise ProcessingError("Dual layout requires title_image to be enabled")

            canvas = render_dual_card(
                background=assets.background,
                char1=assets.characters[0],
                char2=assets.characters[1],
                title_image=assets.title_image
            )

            out_path = output_dir / cfg.output_filename
            save_png(canvas, out_path)
            ok(f"{game_dir.name} -> {out_path} (dual mode)")
            return out_path

        # --------------------------------------------------------
        # DEFAULT / CLASSIC RENDERING PIPELINE
        # --------------------------------------------------------
        canvas: Image.Image = render_background(assets.background)

        # ---- Pyramid layout (Cleocatra, 3 characters) ----
        if len(assets.characters) == 3:

            # 1) PYRAMID - very large, dominant background element
            pyramid = assets.characters[1]
            pyramid_target_h = int(CANVAS_H * 0.95)  # Much larger pyramid
            scale = pyramid_target_h / pyramid.height
            pyramid_w = int(pyramid.width * scale)
            pyramid_h = pyramid_target_h
            pyramid_resized = pyramid.resize((pyramid_w, pyramid_h), Image.LANCZOS)

            pyramid_center_y = int(CANVAS_H * 0.38)  # Slightly higher
            pyramid_x = (CANVAS_W - pyramid_w) // 2
            pyramid_y = pyramid_center_y - (pyramid_h // 2)
            alpha_composite(canvas, pyramid_resized, (pyramid_x, pyramid_y))

            # Pyramid Glow - stronger and larger for dramatic effect
            glow = pyramid_resized.filter(ImageFilter.GaussianBlur(48))
            glow = glow.point(lambda p: int(p * 0.85))
            alpha_composite(canvas, glow, (pyramid_x - 25, pyramid_y - 25))

            # 2) CATS - much smaller, positioned in front
            left_cat = assets.characters[0]
            right_cat = assets.characters[2]

            cat_target_h = int(CANVAS_H * 0.42)  # Much smaller cats

            scale_l = cat_target_h / left_cat.height
            left_w = int(left_cat.width * scale_l)
            left_h = cat_target_h
            left_resized = left_cat.resize((left_w, left_h), Image.LANCZOS)

            scale_r = cat_target_h / right_cat.height
            right_w = int(right_cat.width * scale_r)
            right_h = cat_target_h
            right_resized = right_cat.resize((right_w, right_h), Image.LANCZOS)

            cats_center_y = int(CANVAS_H * 0.58)  # Lower cats
            left_center_x = int(CANVAS_W * 0.30)  # More spread out
            right_center_x = int(CANVAS_W * 0.70)

            left_x = left_center_x - left_w // 2
            right_x = right_center_x - right_w // 2
            left_y = cats_center_y - left_h // 2
            right_y = cats_center_y - right_h // 2

            alpha_composite(canvas, left_resized, (left_x, left_y))
            alpha_composite(canvas, right_resized, (right_x, right_y))

        else:
            # Standard side-by-side for 1–2 characters
            rendered_chars = render_characters(assets.characters, cfg.character_height_ratio)

            # Render ALL characters first (including character 1)
            for char_img, (char_x, char_y) in rendered_chars:
                alpha_composite(canvas, char_img, (char_x, char_y))

        # --------------------------------------------------------
        # TITLE - Rendered AFTER characters so it appears on top
        # --------------------------------------------------------
        if cfg.title_image.enabled and assets.title_image:
            canvas = render_title_image(
                canvas=canvas,
                title_img=assets.title_image,
                max_width_ratio=cfg.title_image.max_width_ratio,
                scale=cfg.title_image.scale,
            )
        else:
            if assets.provider_logo:
                cfg.provider_text = ""

            canvas = render_text_block(
                canvas=canvas,
                title_lines=cfg.title_lines,
                subtitle=cfg.subtitle,
                provider_text=cfg.provider_text,
                font_path=cfg.font_path,
            )

        # Provider logo
        if cfg.provider_logo.enabled and assets.provider_logo:
            canvas = render_provider_logo(canvas, assets.provider_logo, cfg)

        # Save
        out_path = output_dir / cfg.output_filename
        save_png(canvas, out_path)
        ok(f"{game_dir.name} -> {out_path}")
        return out_path

    except Exception as exc:
        error(f"Failed generating {game_dir.name}: {exc}")
        raise ProcessingError(str(exc)) from exc
   