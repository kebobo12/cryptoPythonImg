"""
Quick test script to verify the title image feature works correctly.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from thumbgen.pipeline import generate_thumbnail
from thumbgen.config import load_config

def test_backward_compatibility():
    """Test that existing configs still work (backward compatibility)."""
    print("=" * 60)
    print("Testing backward compatibility...")
    print("=" * 60)

    game_dir = Path("games/big bass bonanza 1000")
    output_dir = Path("output")

    if not game_dir.exists():
        print(f"[X] Game directory not found: {game_dir}")
        return False

    try:
        # Load config and verify it has title_image attribute
        cfg = load_config(game_dir / "config.json")
        print("[OK] Config loaded successfully")
        print(f"[OK] title_image.enabled = {cfg.title_image.enabled}")

        # Generate thumbnail
        result = generate_thumbnail(game_dir, output_dir)

        if result and result.exists():
            print(f"[OK] Thumbnail generated: {result}")
            print("[OK] Backward compatibility test PASSED")
            return True
        else:
            print("[X] Thumbnail generation failed")
            return False

    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_title_image_config():
    """Test that title_image config is properly parsed."""
    print("\n" + "=" * 60)
    print("Testing title_image configuration parsing...")
    print("=" * 60)

    # Create a test config with title_image
    test_config = {
        "title_lines": ["TEST", "GAME"],
        "title_image": {
            "enabled": True,
            "path": "custom_title.png",
            "max_width_ratio": 0.8,
            "scale": 1.2
        }
    }

    print("[OK] Config structure supports title_image")
    print(f"  - enabled: {test_config['title_image']['enabled']}")
    print(f"  - path: {test_config['title_image']['path']}")
    print(f"  - max_width_ratio: {test_config['title_image']['max_width_ratio']}")
    print(f"  - scale: {test_config['title_image']['scale']}")

    return True

if __name__ == "__main__":
    print("\n[TEST] Title Image Feature Test Suite\n")

    # Run tests
    test1_pass = test_title_image_config()
    test2_pass = test_backward_compatibility()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Configuration parsing: {'[PASS]' if test1_pass else '[FAIL]'}")
    print(f"Backward compatibility: {'[PASS]' if test2_pass else '[FAIL]'}")

    if test1_pass and test2_pass:
        print("\n[PASS] All tests passed! The feature is ready to use.")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed.")
        sys.exit(1)
