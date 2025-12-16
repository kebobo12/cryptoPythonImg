import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from thumbgen.pipeline import generate_thumbnail

# Test with new structure
thumbnails_root = Path("Thumbnails")
output_dir = Path("output")

# Test The Count
game_dir = thumbnails_root / "Hacksaw" / "The Count"
print(f"Testing: {game_dir}")
result = generate_thumbnail(game_dir, output_dir)
print(f"Generated: {result}")
