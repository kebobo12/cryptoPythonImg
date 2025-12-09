import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from thumbgen.config import load_config

# Test that output filename defaults to folder name
cfg = load_config(Path("games/cleomeowtra/config.json"))
print(f"Output filename: {cfg.output_filename}")
print(f"Expected: cleomeowtra.png")
print(f"Match: {cfg.output_filename == 'cleomeowtra.png'}")
