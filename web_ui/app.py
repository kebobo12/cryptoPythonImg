"""
Flask web UI for Thumbnail Generator
Modern, responsive web interface for generating game thumbnails
"""

import sys
import json
import webbrowser
from pathlib import Path
from threading import Timer, Lock
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import io
import base64
from collections import OrderedDict

# Add parent directory to path to import thumbgen
sys.path.insert(0, str(Path(__file__).parent.parent))

from thumbgen import generate_thumbnail
from thumbgen.errors import ThumbgenError
from thumbgen.cli import find_all_game_directories
from thumbgen.loader import load_assets
from thumbgen.config import GameConfig, TitleImageConfig, ProviderLogoConfig
from thumbgen.renderer.crypto_card import render_crypto_card
from thumbgen.constants import DEFAULT_CHARACTER_HEIGHT_RATIO, DEFAULT_FONT_PATH

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Detect paths
if getattr(sys, 'frozen', False):
    # Running as packaged .exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Running in development
    BASE_DIR = Path(__file__).parent.parent

THUMBNAILS_ROOT = BASE_DIR / "Thumbnails"
OUTPUT_DIR = BASE_DIR / "output"
FONTS_DIR = BASE_DIR / "fonts"
PROVIDER_FONTS_FILE = BASE_DIR / "provider_fonts.json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)


def get_available_fonts():
    """Get list of available fonts in the fonts directory."""
    fonts = []

    if not FONTS_DIR.exists():
        return fonts

    # Find all .ttf and .otf files
    for font_file in FONTS_DIR.rglob("*.ttf"):
        rel_path = font_file.relative_to(BASE_DIR)
        fonts.append({
            'path': str(rel_path).replace('\\', '/'),
            'name': font_file.stem,
            'family': font_file.parent.name
        })

    for font_file in FONTS_DIR.rglob("*.otf"):
        rel_path = font_file.relative_to(BASE_DIR)
        fonts.append({
            'path': str(rel_path).replace('\\', '/'),
            'name': font_file.stem,
            'family': font_file.parent.name
        })

    # Sort by family then name
    fonts.sort(key=lambda x: (x['family'], x['name']))

    return fonts


def load_provider_fonts():
    """Load provider font associations from JSON file."""
    if not PROVIDER_FONTS_FILE.exists():
        return {}

    try:
        with open(PROVIDER_FONTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading provider fonts: {e}", flush=True)
        return {}


def save_provider_fonts(provider_fonts):
    """Save provider font associations to JSON file."""
    try:
        with open(PROVIDER_FONTS_FILE, 'w') as f:
            json.dump(provider_fonts, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving provider fonts: {e}", flush=True)
        return False


class LRUCache:
    """Thread-safe LRU cache for preview assets"""
    def __init__(self, max_size=10):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = Lock()

    def get(self, key):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)


# Global preview asset cache
preview_asset_cache = LRUCache(max_size=10)


@app.route('/')
def index():
    """Render main UI page."""
    return render_template('index.html')


@app.route('/api/fonts')
def get_fonts():
    """Get list of all available fonts."""
    try:
        fonts = get_available_fonts()
        return jsonify({'success': True, 'fonts': fonts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/games')
def get_games():
    """Get list of all available games."""
    try:
        game_dirs = find_all_game_directories(THUMBNAILS_ROOT)
        games = []

        for game_dir in game_dirs:
            provider = game_dir.parent.name
            game_name = game_dir.name

            games.append({
                'path': str(game_dir.relative_to(THUMBNAILS_ROOT)),
                'provider': provider,
                'name': game_name
            })

        return jsonify({'success': True, 'games': games})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/game/<path:game_path>')
def get_game_details(game_path):
    """Get details for a specific game."""
    try:
        game_dir = THUMBNAILS_ROOT / game_path

        if not game_dir.exists():
            return jsonify({'success': False, 'error': 'Game not found'}), 404

        # Check what assets exist
        assets = {
            'background': (game_dir / "background.png").exists(),
            'char': (game_dir / "char.png").exists(),
            'title': (game_dir / "title.png").exists(),
            'provider': (game_dir / "provider.png").exists(),
        }

        return jsonify({
            'success': True,
            'assets': assets,
            'provider': game_dir.parent.name,
            'name': game_dir.name
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/game/<path:game_path>/assets')
def get_game_assets(game_path):
    """Get list of all available assets for a game."""
    try:
        # Normalize path separators - split by / and rejoin with Path
        path_parts = game_path.split('/')
        game_dir = THUMBNAILS_ROOT
        for part in path_parts:
            game_dir = game_dir / part

        print(f"[ASSETS] Request for: {game_path}", flush=True)
        print(f"[ASSETS] Full path: {game_dir}", flush=True)
        print(f"[ASSETS] Exists: {game_dir.exists()}", flush=True)

        if not game_dir.exists():
            return jsonify({'success': False, 'error': 'Game not found'}), 404

        # Supported image extensions
        image_exts = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff', '.tif']

        def get_images_in_folder(folder):
            """Get all image files in a folder."""
            if not folder.exists() or not folder.is_dir():
                return []
            images = []
            for ext in image_exts:
                images.extend(folder.glob(f"*{ext}"))
            # Sort case-insensitively to match loader.py behavior
            return sorted([img.name for img in images], key=str.lower)

        # Get backgrounds
        backgrounds = []
        backgrounds_folder = game_dir / "Backgrounds"
        if backgrounds_folder.exists():
            backgrounds = get_images_in_folder(backgrounds_folder)
        else:
            # Old structure - look for background.* in game folder
            for ext in image_exts:
                bg_file = game_dir / f"background{ext}"
                if bg_file.exists():
                    backgrounds.append(bg_file.name)
                    break

        # Get characters
        characters = []
        character_folder = game_dir / "Character"
        if character_folder.exists():
            characters = get_images_in_folder(character_folder)
        else:
            # Old structure - look for character*.* in game folder
            for i in range(1, 10):  # Support up to 9 characters
                found = False
                for ext in image_exts:
                    char_file = game_dir / f"character{i}{ext}"
                    if char_file.exists():
                        characters.append(char_file.name)
                        found = True
                        break
                if not found:
                    break
            # If no numbered, try single character.*
            if not characters:
                for ext in image_exts:
                    char_file = game_dir / f"character{ext}"
                    if char_file.exists():
                        characters.append(char_file.name)
                        break

        # Get titles
        titles = []
        title_folder = game_dir / "Title"
        if title_folder.exists():
            titles = get_images_in_folder(title_folder)
        else:
            for ext in image_exts:
                title_file = game_dir / f"title{ext}"
                if title_file.exists():
                    titles.append(title_file.name)
                    break

        # Get provider logos
        logos = []
        provider_dir = game_dir.parent
        logo_folder = provider_dir / "Provider Logo"
        if logo_folder.exists():
            logos = get_images_in_folder(logo_folder)
        else:
            for ext in image_exts:
                logo_file = game_dir / f"logo{ext}"
                if logo_file.exists():
                    logos.append(logo_file.name)
                    break

        return jsonify({
            'success': True,
            'assets': {
                'backgrounds': backgrounds,
                'characters': characters,
                'titles': titles,
                'logos': logos
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate thumbnail for a game."""
    try:
        data = request.json
        game_path = data.get('game_path')
        settings = data.get('settings', {})

        if not game_path:
            return jsonify({'success': False, 'error': 'No game path provided'}), 400

        game_dir = THUMBNAILS_ROOT / game_path

        if not game_dir.exists():
            return jsonify({'success': False, 'error': 'Game not found'}), 404

        # Apply provider default font for PROVIDER TEXT only (not title),
        # unless a custom font override is specified from the UI.
        provider_name = game_dir.parent.name
        provider_fonts_map = load_provider_fonts()
        if provider_name in provider_fonts_map and not settings.get('provider_font'):
            settings['provider_font'] = provider_fonts_map[provider_name]
            print(f"[PROVIDER FONT] Using provider default for {provider_name}: {settings['provider_font']}", flush=True)
        if settings.get('custom_font'):
            print(f"[PROVIDER FONT] Using custom title font override: {settings.get('custom_font')}", flush=True)

        # Generate thumbnail with settings (no config.json needed)
        result_path = generate_thumbnail(game_dir, OUTPUT_DIR, settings=settings)

        return jsonify({
            'success': True,
            'output_path': str(result_path.relative_to(OUTPUT_DIR)),
            'message': f'Generated: {result_path.name}'
        })

    except ThumbgenError as e:
        import traceback
        print(f"[ERROR] ThumbgenError: {e}", flush=True)
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

    except Exception as e:
        import traceback
        print(f"[ERROR] Exception: {e}", flush=True)
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/preview-live', methods=['POST'])
def preview_live():
    """Generate live preview without saving to disk"""
    try:
        data = request.json
        game_path = data.get('game_path')
        settings = data.get('settings', {})

        if not game_path:
            return jsonify({'success': False, 'error': 'No game path provided'}), 400

        game_dir = THUMBNAILS_ROOT / game_path
        if not game_dir.exists():
            return jsonify({'success': False, 'error': 'Game directory not found'}), 404

        # Check cache for assets (but skip cache if custom assets are selected)
        asset_filenames = settings.get('asset_filenames', {})
        cache_key = game_path if not asset_filenames else None
        cached_assets = preview_asset_cache.get(cache_key) if cache_key else None

        # Provider name from folder
        provider_name = game_dir.parent.name
        provider_text = provider_name if settings.get('provider_mode') == 'text' else ""

        # Apply provider default font for PROVIDER TEXT only (not title),
        # unless a custom font override is specified from the UI.
        provider_fonts_map = load_provider_fonts()
        if provider_name in provider_fonts_map and not settings.get('provider_font'):
            settings['provider_font'] = provider_fonts_map[provider_name]

        # Font selection (TITLE / MAIN TEXT)
        if settings.get('custom_font'):
            font_path = settings['custom_font']
            if not Path(font_path).is_absolute():
                font_path = str((game_dir.parent.parent.parent / font_path).resolve())
        else:
            # Use default font for title text (not provider font)
            font_path = DEFAULT_FONT_PATH

        # Provider font selection (PROVIDER TEXT ONLY)
        provider_font_path = settings.get('provider_font')
        if provider_font_path and not Path(provider_font_path).is_absolute():
            provider_font_path = str((game_dir.parent.parent.parent / provider_font_path).resolve())

        # Create config
        cfg = GameConfig(
            title_lines=[game_dir.name],
            subtitle="",
            provider_text=provider_text,
            output_filename=f"{game_dir.name.lower().replace(' ', '_')}.png",
            character_height_ratio=DEFAULT_CHARACTER_HEIGHT_RATIO,
            font_path=font_path,
            provider_logo=ProviderLogoConfig(
                enabled=settings.get('provider_mode') == 'logo'
            ),
            title_image=TitleImageConfig(
                enabled=settings.get('title_mode') == 'image'
            ),
            layout='crypto',
            band_color=settings.get('blur_manual_color') if settings.get('blur_enabled') and settings.get('blur_manual_color') else None,
        )

        # Load or use cached assets
        if cached_assets is None:
            cached_assets = load_assets(game_dir, cfg, asset_filenames)
            if cache_key:  # Only cache if not using custom asset selections
                preview_asset_cache.set(cache_key, cached_assets)

        # Parse settings
        blur_enabled = settings.get('blur_enabled', True)
        blur_scale = float(settings.get('blur_scale', 1.0))
        text_scale = float(settings.get('text_scale', 1.0))
        text_offset = float(settings.get('text_offset', 0.0))
        band_color = cfg.band_color

        # Render thumbnail in memory
        canvas = render_crypto_card(
            background=cached_assets.background,
            character=cached_assets.characters[0],
            title_lines=cfg.title_lines,
            provider=cfg.provider_text,
            font_path=cfg.font_path,
            provider_font_path=provider_font_path,
            band_color=band_color,
            provider_logo=cached_assets.provider_logo,
            title_image=cached_assets.title_image,
            blur_enabled=blur_enabled,
            blur_scale=blur_scale,
            text_scale=text_scale,
            text_offset=text_offset,
        )

        # Convert to base64
        buffer = io.BytesIO()
        canvas.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        return jsonify({
            'success': True,
            'preview_image': f'data:image/png;base64,{img_base64}'
        })

    except Exception as e:
        import traceback
        print(f"[ERROR] Preview failed: {e}", flush=True)
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-bulk', methods=['POST'])
def generate_bulk():
    """Generate thumbnails for multiple games."""
    try:
        data = request.json
        game_paths = data.get('game_paths', [])
        settings = data.get('settings', {})

        print(f"[BULK GEN] Received settings: {settings}", flush=True)

        if not game_paths:
            return jsonify({'success': False, 'error': 'No games selected'}), 400

        results = []
        success_count = 0
        provider_fonts_map = load_provider_fonts()
        print(f"[BULK GEN] Loaded provider fonts map: {provider_fonts_map}", flush=True)

        for game_path in game_paths:
            try:
                game_dir = THUMBNAILS_ROOT / game_path

                if not game_dir.exists():
                    results.append({
                        'game': game_path,
                        'success': False,
                        'error': 'Game not found'
                    })
                    continue

                # Apply provider default font for PROVIDER TEXT only (not title),
                # unless a provider_font override is already present.
                game_settings = settings.copy()
                provider_name = game_dir.parent.name
                print(f"[BULK GEN] Game: {game_dir.name}, Provider: {provider_name}, Current provider_font: {game_settings.get('provider_font')}", flush=True)
                if provider_name in provider_fonts_map and not game_settings.get('provider_font'):
                    game_settings['provider_font'] = provider_fonts_map[provider_name]
                    print(f"[PROVIDER FONT] {game_dir.name}: Using provider default for {provider_name}: {game_settings['provider_font']}", flush=True)

                # Generate thumbnail with settings (no config.json needed)
                result_path = generate_thumbnail(game_dir, OUTPUT_DIR, settings=game_settings)

                results.append({
                    'game': game_path,
                    'success': True,
                    'output': str(result_path.relative_to(OUTPUT_DIR))
                })
                success_count += 1

            except Exception as e:
                results.append({
                    'game': game_path,
                    'success': False,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'total': len(game_paths),
            'successful': success_count,
            'results': results
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/preview/<path:output_path>')
def get_preview(output_path):
    """Serve generated thumbnail for preview."""
    try:
        file_path = OUTPUT_DIR / output_path

        if not file_path.exists():
            return jsonify({'success': False, 'error': 'File not found'}), 404

        return send_file(file_path, mimetype='image/png')

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/provider-fonts')
def get_provider_fonts():
    """Get all provider font associations."""
    try:
        provider_fonts = load_provider_fonts()
        return jsonify({'success': True, 'provider_fonts': provider_fonts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/provider-fonts', methods=['POST'])
def set_provider_font():
    """Set default font for a provider."""
    try:
        data = request.json
        provider = data.get('provider')
        font_path = data.get('font_path')

        if not provider:
            return jsonify({'success': False, 'error': 'Provider is required'}), 400

        if not font_path:
            return jsonify({'success': False, 'error': 'Font path is required'}), 400

        provider_fonts = load_provider_fonts()
        provider_fonts[provider] = font_path

        if save_provider_fonts(provider_fonts):
            return jsonify({'success': True, 'message': f'Set default font for {provider}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save provider fonts'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/provider-fonts/<provider>', methods=['DELETE'])
def delete_provider_font(provider):
    """Remove default font for a provider."""
    try:
        provider_fonts = load_provider_fonts()

        if provider not in provider_fonts:
            return jsonify({'success': False, 'error': 'Provider not found'}), 404

        del provider_fonts[provider]

        if save_provider_fonts(provider_fonts):
            return jsonify({'success': True, 'message': f'Removed default font for {provider}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save provider fonts'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def open_browser():
    """Open the web browser after a short delay."""
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    # Open browser automatically after 1 second
    Timer(1, open_browser).start()

    # Run Flask app
    print("Starting Thumbnail Generator Web UI...")
    print("Opening browser at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")

    app.run(debug=True, use_reloader=False)
