"""
Migrate old games folder structure to new provider-based structure.

Old: games/GameName/background.png
New: Thumbnails/Provider/GameName/Backgrounds/background.png
"""

import json
import shutil
from pathlib import Path


def get_provider_from_config(game_dir: Path) -> str:
    """Extract provider name from config.json."""
    config_path = game_dir / "config.json"
    if not config_path.exists():
        return "Unknown"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            provider = config.get("provider_text", "Unknown")

            # Normalize provider names
            if not provider or provider.strip() == "":
                return "Unknown"

            # Map common variations
            provider = provider.strip()
            if "hacksaw" in provider.lower():
                return "Hacksaw"
            elif "pragmatic" in provider.lower():
                return "Pragmatic"
            elif "3 oaks" in provider.lower() or "3oaks" in provider.lower():
                return "3Oaks"
            elif "wicked" in provider.lower():
                return "Wicked Games"
            else:
                return provider
    except Exception as e:
        print(f"  Warning: Could not read config for {game_dir.name}: {e}")
        return "Unknown"


def migrate_game(game_dir: Path, thumbnails_root: Path):
    """Migrate a single game to the new structure."""

    # Get provider
    provider = get_provider_from_config(game_dir)
    print(f"\n{game_dir.name} -> Provider: {provider}")

    # Create provider/game directory
    new_game_dir = thumbnails_root / provider / game_dir.name
    new_game_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Created: {new_game_dir}")

    # Move config.json
    old_config = game_dir / "config.json"
    if old_config.exists():
        shutil.copy2(old_config, new_game_dir / "config.json")
        print(f"  Copied: config.json")

    # Migrate backgrounds
    backgrounds_created = False
    for bg_name in ["background.png", "background.jpg", "background.jpeg"]:
        old_bg = game_dir / bg_name
        if old_bg.exists():
            new_bg_folder = new_game_dir / "Backgrounds"
            new_bg_folder.mkdir(exist_ok=True)
            shutil.copy2(old_bg, new_bg_folder / bg_name)
            print(f"  Copied: {bg_name} -> Backgrounds/")
            backgrounds_created = True
            break

    # Migrate characters
    characters_created = False

    # Try numbered characters first (character1, character2, character3)
    for i in range(1, 4):
        for ext in [".png", ".jpg", ".jpeg"]:
            old_char = game_dir / f"character{i}{ext}"
            if old_char.exists():
                new_char_folder = new_game_dir / "Character"
                new_char_folder.mkdir(exist_ok=True)
                shutil.copy2(old_char, new_char_folder / f"character{i}{ext}")
                print(f"  Copied: character{i}{ext} -> Character/")
                characters_created = True

    # If no numbered characters, try single character
    if not characters_created:
        for char_name in ["character.png", "character.jpg", "character.jpeg"]:
            old_char = game_dir / char_name
            if old_char.exists():
                new_char_folder = new_game_dir / "Character"
                new_char_folder.mkdir(exist_ok=True)
                shutil.copy2(old_char, new_char_folder / char_name)
                print(f"  Copied: {char_name} -> Character/")
                characters_created = True
                break

    # Migrate title image if exists
    for title_name in ["title.png", "title.jpg", "title.jpeg"]:
        old_title = game_dir / title_name
        if old_title.exists():
            new_title_folder = new_game_dir / "Title"
            new_title_folder.mkdir(exist_ok=True)
            shutil.copy2(old_title, new_title_folder / title_name)
            print(f"  Copied: {title_name} -> Title/")
            break

    # Migrate provider logo if exists
    for logo_name in ["provider.png", "provider.jpg", "provider.jpeg"]:
        old_logo = game_dir / logo_name
        if old_logo.exists():
            new_logo_folder = new_game_dir / "Provider Logo"
            new_logo_folder.mkdir(exist_ok=True)
            shutil.copy2(old_logo, new_logo_folder / logo_name)
            print(f"  Copied: {logo_name} -> Provider Logo/")
            break


def main():
    """Main migration script."""

    # Paths
    games_root = Path("games")
    thumbnails_root = Path("Thumbnails")

    if not games_root.exists():
        print(f"Error: {games_root} does not exist!")
        return

    print(f"Migrating from: {games_root}")
    print(f"Migrating to:   {thumbnails_root}")
    print("\n" + "="*60)

    # Create Thumbnails root
    thumbnails_root.mkdir(exist_ok=True)

    # Migrate each game
    migrated_count = 0
    for game_dir in sorted(games_root.iterdir()):
        if game_dir.is_dir():
            # Skip test directories
            if "test-" in game_dir.name.lower():
                print(f"\nSkipping test directory: {game_dir.name}")
                continue

            migrate_game(game_dir, thumbnails_root)
            migrated_count += 1

    print("\n" + "="*60)
    print(f"\nMigration complete! Migrated {migrated_count} games.")
    print(f"\nNew structure created in: {thumbnails_root.absolute()}")
    print("\nYou can now:")
    print("  1. Verify the new structure looks correct")
    print("  2. Test with: python -m thumbgen all --games-root Thumbnails")
    print("  3. If everything works, you can delete the old 'games' folder")


if __name__ == "__main__":
    main()
