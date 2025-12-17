"""
Asset loading utilities for thumbgen.

This module handles:
- Loading validated game configuration
- Loading required images (background, character)
- Loading optional provider logo
- Loading fonts with graceful fallback

All file-system access and error checking is centralized here, making the
rendering pipeline clean and testable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageFont

from .config import GameConfig
from .errors import (
    MissingAssetError,
    FontLoadError,
    ProviderLogoError,
)


# ------------------------------------------------------------
# Image loading
# ------------------------------------------------------------

# Supported image extensions (order matters - PNG first as most common)
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff', '.tif']


def find_first_image_in_folder(folder: Path) -> Optional[Path]:
    """
    Find the first image file in a folder (alphabetically).

    Args:
        folder: Path to a folder containing images

    Returns:
        Path to the first image found, or None if folder doesn't exist or has no images.

    Example:
        find_first_image_in_folder(Path("Thumbnails/Provider/Game/Backgrounds"))
        # Returns: Path("Thumbnails/Provider/Game/Backgrounds/bg1.png") if that's the first alphabetically
    """
    if not folder.exists() or not folder.is_dir():
        return None

    # Get all image files in the folder, sorted alphabetically
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(folder.glob(f"*{ext}"))

    if not image_files:
        return None

    # Sort and return first
    return sorted(image_files)[0]


def find_image_file(base_path: Path) -> Optional[Path]:
    """
    Find an image file with any supported extension.

    Args:
        base_path: Path without extension (e.g., "games/mygame/background")

    Returns:
        Path to the found image file, or None if not found.

    Example:
        find_image_file(Path("games/mygame/background"))
        # Returns: Path("games/mygame/background.jpg") if that exists
    """
    # First, check if the exact path exists (user specified full filename)
    if base_path.exists():
        return base_path

    # Get the directory and base name
    parent = base_path.parent
    stem = base_path.stem if base_path.suffix else base_path.name

    # Try each extension
    for ext in IMAGE_EXTENSIONS:
        candidate = parent / f"{stem}{ext}"
        if candidate.exists():
            return candidate

    return None


def load_image(path: Path, required: bool = True) -> Optional[Image.Image]:
    """
    Load an image from disk and convert it to RGBA.
    Auto-detects image format from extensions: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

    Args:
        path: The path to an image file (with or without extension).
        required: Whether missing file should raise an error.

    Returns:
        Image.Image or None if optional and missing.

    Raises:
        MissingAssetError: If required and file does not exist.
    """
    # Try to find the image with any supported extension
    found_path = find_image_file(path)

    if not found_path:
        if required:
            raise MissingAssetError(f"Missing required image: {path} (tried: {', '.join(IMAGE_EXTENSIONS)})")
        return None

    try:
        img = Image.open(found_path).convert("RGBA")
        return img
    except Exception as exc:
        raise MissingAssetError(f"Failed to load image {found_path}: {exc}") from exc


def load_background(game_dir: Path) -> Image.Image:
    """
    Load background image from the game directory.
    Supports both old structure (background.png) and new structure (Backgrounds/ folder).
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF
    """
    # Try new structure first: Backgrounds/ folder
    backgrounds_folder = game_dir / "Backgrounds"
    if backgrounds_folder.exists() and backgrounds_folder.is_dir():
        found = find_first_image_in_folder(backgrounds_folder)
        if found:
            return load_image(found, required=True)

    # Fallback to old structure: background.png
    return load_image(game_dir / "background", required=True)


def load_character(game_dir: Path) -> Image.Image:
    """
    Load character image from the game directory.
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF
    """
    return load_image(game_dir / "character", required=True)


def load_characters(game_dir: Path) -> list[Image.Image]:
    """
    Load multiple character images.
    Supports both old structure (character1.png, character2.png) and new structure (Character/ folder).
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

    Returns:
        List of character images (1-3 characters)
    """
    characters = []

    # Try new structure first: Character/ folder
    character_folder = game_dir / "Character"
    if character_folder.exists() and character_folder.is_dir():
        # Get all images from Character folder, sorted alphabetically
        image_files = []
        for ext in IMAGE_EXTENSIONS:
            image_files.extend(character_folder.glob(f"*{ext}"))

        if image_files:
            # Sort and load up to 3 characters
            for img_path in sorted(image_files)[:3]:
                img = load_image(img_path, required=False)
                if img:
                    characters.append(img)

            if characters:
                return characters

    # Fallback to old structure: character1, character2, character3...
    for i in range(1, 4):  # Support up to 3 characters
        char_path = game_dir / f"character{i}"
        img = load_image(char_path, required=False)
        if img:
            characters.append(img)
        else:
            break  # Stop at first missing numbered character

    # If no numbered characters found, fall back to single character.png
    if not characters:
        characters.append(load_character(game_dir))

    return characters


def load_provider_logo(game_dir: Path, cfg: GameConfig) -> Optional[Image.Image]:
    """
    Load provider logo if enabled in configuration.

    New structure: Looks in provider folder (Thumbnails/Provider/Provider Logo/)
    Old structure: Looks in game folder (game_dir/provider.png)

    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

    Args:
        game_dir: Directory containing the game
        cfg: GameConfig object

    Returns:
        Optional Image.Image

    Raises:
        ProviderLogoError: If loading fails unexpectedly.
    """
    if not cfg.provider_logo.enabled:
        return None

    # Try new structure first: Provider Logo/ folder at provider level
    # game_dir = Thumbnails/Provider/Game
    # provider_dir = Thumbnails/Provider
    provider_dir = game_dir.parent
    provider_logo_folder = provider_dir / "Provider Logo"

    if provider_logo_folder.exists() and provider_logo_folder.is_dir():
        found = find_first_image_in_folder(provider_logo_folder)
        if found:
            try:
                return Image.open(found).convert("RGBA")
            except Exception as exc:
                raise ProviderLogoError(f"Failed to load provider logo {found}: {exc}") from exc

    # Fallback to old structure: provider.png in game folder
    logo_base = game_dir / Path(cfg.provider_logo.path).stem
    logo_path = find_image_file(logo_base)

    if not logo_path:
        # If no base match, try the exact path from config
        logo_path = game_dir / cfg.provider_logo.path
        if not logo_path.exists():
            # Missing provider logo is NOT fatal — fallback to provider_text
            return None

    try:
        return Image.open(logo_path).convert("RGBA")
    except Exception as exc:
        raise ProviderLogoError(f"Failed to load provider logo {logo_path}: {exc}") from exc


def load_title_image(game_dir: Path, cfg: GameConfig) -> Optional[Image.Image]:
    """
    Load title image if enabled in configuration.
    Supports both old structure (title.png) and new structure (Title/ folder).
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

    Args:
        game_dir: Directory containing title image
        cfg: GameConfig object

    Returns:
        Optional Image.Image (always converted to RGBA)

    Raises:
        MissingAssetError: If enabled but file doesn't exist or can't be loaded.
    """
    if not cfg.title_image.enabled:
        return None

    # Try new structure first: Title/ folder
    title_folder = game_dir / "Title"
    if title_folder.exists() and title_folder.is_dir():
        found = find_first_image_in_folder(title_folder)
        if found:
            try:
                img = Image.open(found)
                return img.convert("RGBA")
            except Exception as exc:
                raise MissingAssetError(f"Failed to load title image {found}: {exc}") from exc

    # Fallback to old structure: title.png or path from config
    title_base = game_dir / Path(cfg.title_image.path).stem
    title_path = find_image_file(title_base)

    if not title_path:
        # If no base match, try the exact path from config
        title_path = game_dir / cfg.title_image.path
        if not title_path.exists():
            # Missing title image is NOT fatal — fallback to text title
            return None

    try:
        img = Image.open(title_path)
        # Convert to RGBA to ensure transparency support
        # Works with PNG, JPG, WEBP, BMP, GIF, TIFF, etc.
        return img.convert("RGBA")
    except Exception as exc:
        raise MissingAssetError(f"Failed to load title image {title_path}: {exc}") from exc


# ------------------------------------------------------------
# Font loading
# ------------------------------------------------------------

def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Load a TrueType font.

    Args:
        font_path: Path to .ttf file.
        size: Font size in pixels.

    Returns:
        Loaded TrueTypeFont.

    Raises:
        FontLoadError: If font cannot be loaded.
    """
    try:
        return ImageFont.truetype(font_path, size=size)
    except Exception as exc:
        raise FontLoadError(f"Failed to load font '{font_path}': {exc}") from exc


# ------------------------------------------------------------
# Unified asset bundle
# ------------------------------------------------------------

class LoadedAssets:
    """
    Bundles all game assets after loading from disk.

    Attributes:
        background: Background image.
        character: Character image with transparency (deprecated, use characters).
        characters: List of character images (1-3).
        provider_logo: Optional provider logo.
        title_image: Optional title image to use instead of text.
    """
    def __init__(
        self,
        background: Image.Image,
        character: Image.Image,
        characters: list[Image.Image],
        provider_logo: Optional[Image.Image],
        title_image: Optional[Image.Image],
    ) -> None:
        self.background = background
        self.character = character  # Keep for backward compatibility
        self.characters = characters
        self.provider_logo = provider_logo
        self.title_image = title_image


def load_assets(game_dir: Path, cfg: GameConfig) -> LoadedAssets:
    """
    Load all image assets for a game in one call.

    Args:
        game_dir: Path to game directory
        cfg: Validated GameConfig

    Returns:
        LoadedAssets: container object with images
    """
    background = load_background(game_dir)
    characters = load_characters(game_dir)
    provider_logo = load_provider_logo(game_dir, cfg)
    title_image = load_title_image(game_dir, cfg)

    return LoadedAssets(
        background=background,
        character=characters[0],  # For backward compatibility
        characters=characters,
        provider_logo=provider_logo,
        title_image=title_image,
    )
