import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from thumbgen.pipeline import generate_thumbnail

# Test with new structure on Desktop
desktop = Path("C:/Users/PC/Desktop")
game_dir = desktop / "Thumbnails/Pragmatic/Sweet Bonanza"
output_dir = Path("output")

print(f"Looking for: {game_dir}")
print(f"Exists: {game_dir.exists()}")

if game_dir.exists():
    # List what's in the folder
    print(f"\nContents of {game_dir}:")
    for item in sorted(game_dir.iterdir()):
        print(f"  - {item.name}")

    # Try to generate thumbnail
    print(f"\nTesting new structure: {game_dir}")
    result = generate_thumbnail(game_dir, output_dir)
    print(f"Generated: {result}")
else:
    print(f"\nGame directory not found: {game_dir}")
    print("Please ensure the Thumbnails folder structure is set up")
