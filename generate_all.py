import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from thumbgen.cli import find_all_game_directories
from thumbgen.pipeline import generate_thumbnail
from thumbgen.errors import ThumbgenError

# Use new Thumbnails folder
thumbnails_root = Path("Thumbnails")
output_dir = Path("output")

print(f"Generating thumbnails from: {thumbnails_root}")
print(f"Output directory: {output_dir}\n")

# Find all games
game_dirs = find_all_game_directories(thumbnails_root)

print(f"Found {len(game_dirs)} games:\n")

success_count = 0
for game_dir in game_dirs:
    provider = game_dir.parent.name
    game_name = game_dir.name

    print(f"[{provider}] {game_name}...")

    try:
        result = generate_thumbnail(game_dir, output_dir)
        print(f"  OK - Generated: {result.name}\n")
        success_count += 1
    except ThumbgenError as e:
        print(f"  ERROR - Failed: {e}\n")

print(f"\n{'='*60}")
print(f"Complete! {success_count}/{len(game_dirs)} thumbnails generated successfully")
print(f"Output directory: {output_dir.absolute()}")
