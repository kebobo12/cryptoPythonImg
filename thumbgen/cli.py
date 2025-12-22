"""
Typer-based CLI interface for the thumbgen system.

Provides commands:
- thumbgen all
- thumbgen one <game>
- thumbgen validate <game>
- thumbgen doctor

All rendering is delegated to the pipeline module.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Optional, List

import typer

from .pipeline import generate_thumbnail
from .config import load_config
from .utils.logging import info, ok, warn, error, heading
from .errors import ThumbgenError, InvalidConfigError, MissingAssetError


app = typer.Typer(add_completion=False, help="Thumbnail generation system.")


# ------------------------------------------------------------
# Shared directory options
# ------------------------------------------------------------

def resolve_dirs(
    games_root: Optional[Path],
    output_dir: Optional[Path]
) -> tuple[Path, Path]:

    root = Path.cwd()

    # Default to Thumbnails if it exists, otherwise games (backward compatibility)
    if games_root is None:
        if (root / "Thumbnails").exists():
            games_root = root / "Thumbnails"
        else:
            games_root = root / "games"

    output_dir = output_dir or (root / "output")

    return games_root, output_dir


def find_all_game_directories(root: Path) -> List[Path]:
    """
    Find all game directories in Provider/Game structure.

    Structure: Thumbnails/Provider/GameName/

    Args:
        root: Root directory to search (Thumbnails/)

    Returns:
        List of Path objects pointing to game directories
    """
    game_dirs = []

    if not root.exists():
        return game_dirs

    # Traverse Provider/Game structure
    for provider_dir in sorted(root.iterdir()):
        if provider_dir.is_dir():
            # Look for game folders inside provider folder
            for game_dir in sorted(provider_dir.iterdir()):
                if game_dir.is_dir():
                    # Skip special folders like "Provider Logo"
                    if game_dir.name.lower() not in ['provider logo', 'assets', '.git']:
                        game_dirs.append(game_dir)

    return game_dirs


# ------------------------------------------------------------
# Command: thumbgen all
# ------------------------------------------------------------

@app.command()
def all(
    games_root: Optional[Path] = typer.Option(
        None,
        help="Directory containing all game folders."
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        help="Directory where output images will be saved."
    ),
    clean: bool = typer.Option(
        False,
        help="Remove output directory before generating."
    ),
):
    """Generate thumbnails for all games in the games directory."""

    games_root, output_dir = resolve_dirs(games_root, output_dir)

    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
        ok("Cleaned output directory.")

    if not games_root.exists():
        error(f"Games root does not exist: {games_root}")
        raise typer.Exit(code=1)

    heading("Generating all thumbnails\n")

    start_time = time.time()
    success_count = 0
    total_count = 0

    # Find all game directories (supports both old and new structure)
    game_dirs = find_all_game_directories(games_root)

    for game_dir in game_dirs:
        total_count += 1
        try:
            generate_thumbnail(game_dir, output_dir)
            success_count += 1
        except ThumbgenError:
            # Already logged — continue to next game
            continue

    elapsed = time.time() - start_time
    ok(f"\nAll thumbnails processed: {success_count}/{total_count} successful in {elapsed:.2f}s")


# ------------------------------------------------------------
# Command: thumbgen one <game>
# ------------------------------------------------------------

@app.command()
def one(
    game: str = typer.Argument(..., help="Name of the game folder."),
    games_root: Optional[Path] = typer.Option(None),
    output_dir: Optional[Path] = typer.Option(None),
):
    """Generate a thumbnail for a single game."""

    games_root, output_dir = resolve_dirs(games_root, output_dir)

    # Try old structure first: games/GameName
    game_dir = games_root / game

    # If not found, search in new structure: Thumbnails/*/GameName
    if not game_dir.exists() or not (game_dir / "config.json").exists():
        all_games = find_all_game_directories(games_root)
        matching = [g for g in all_games if g.name == game]

        if matching:
            game_dir = matching[0]
        else:
            error(f"Game folder not found: {game}")
            raise typer.Exit(code=1)

    heading(f"Generating thumbnail for: {game}\n")

    try:
        generate_thumbnail(game_dir, output_dir)
    except ThumbgenError:
        raise typer.Exit(code=1)


# ------------------------------------------------------------
# Command: thumbgen validate <game>
# ------------------------------------------------------------

@app.command()
def validate(
    game: str = typer.Argument(...),
    games_root: Optional[Path] = typer.Option(None),
):
    """Validate config.json and required assets for a single game."""

    games_root = games_root or (Path.cwd() / "games")
    game_dir = games_root / game

    heading(f"Validating assets for: {game}\n")

    try:
        cfg = load_config(game_dir / "config.json")
        ok("config.json is valid.")
    except InvalidConfigError as exc:
        error(str(exc))
        raise typer.Exit(code=1)

    # required assets
    missing = []
    for asset in ["background.png", "character.png"]:
        if not (game_dir / asset).exists():
            missing.append(asset)

    if missing:
        error(f"Missing required assets: {', '.join(missing)}")
        raise typer.Exit(code=1)

    ok("All required assets are present.")
    info("Provider logo is optional unless enabled in config.")

    ok("\nValidation successful.")


# ------------------------------------------------------------
# Command: thumbgen doctor
# ------------------------------------------------------------

@app.command()
def doctor():
    """Diagnose common environment issues."""

    heading("Thumbgen environment diagnostics\n")

    # Check Pillow installation
    try:
        import PIL
        ok(f"Pillow version: {PIL.__version__}")
    except ImportError:
        error("Pillow is not installed!")
        raise typer.Exit(code=1)

    # Check for common system fonts
    paths = [
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    found = False
    for p in paths:
        if Path(p).exists():
            ok(f"Font detected: {p}")
            found = True

    if not found:
        warn("No standard font detected. You must specify font_path in config.json.")

    ok("\nDoctor check complete.")
