"""
Test script to verify mixed image formats work (JPG background, PNG character, etc.)
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from thumbgen.pipeline import generate_thumbnail

def test_cleomeowtra():
    """Test game with mixed formats: JPG background, PNG character and title."""
    print("=" * 60)
    print("Testing cleomeowtra with mixed image formats...")
    print("=" * 60)

    game_dir = Path("games/cleomeowtra")
    output_dir = Path("output")

    if not game_dir.exists():
        print(f"[X] Game directory not found: {game_dir}")
        return False

    # List files
    print("\nFiles in game directory:")
    for file in sorted(game_dir.iterdir()):
        if file.is_file():
            print(f"  - {file.name}")

    print("\nGenerating thumbnail...")
    try:
        result = generate_thumbnail(game_dir, output_dir)

        if result and result.exists():
            print(f"\n[OK] Thumbnail generated successfully: {result}")
            print(f"[OK] File size: {result.stat().st_size / 1024:.1f} KB")
            return True
        else:
            print("\n[X] Thumbnail generation failed")
            return False

    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n[TEST] Mixed Image Format Test\n")

    success = test_cleomeowtra()

    print("\n" + "=" * 60)
    if success:
        print("[PASS] Mixed format support works!")
        print("\nYou can now use:")
        print("  - background.jpg (or .png, .webp, etc.)")
        print("  - character.jpg (or .png, .webp, etc.)")
        print("  - title.jpg (or .png, .webp, etc.)")
        print("  - provider.jpg (or .png, .webp, etc.)")
        sys.exit(0)
    else:
        print("[FAIL] Test failed")
        sys.exit(1)
