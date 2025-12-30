"""
Flask web UI for Thumbnail Generator
Modern, responsive web interface for generating game thumbnails
"""

import sys
import json
import webbrowser
import subprocess
import platform
import os
from pathlib import Path
from threading import Timer, Lock
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import io
import base64
from collections import OrderedDict

# Add parent directory to path to import thumbgen
sys.path.insert(0, str(Path(__file__).parent.parent))

from thumbgen import generate_thumbnail
from thumbgen.errors import ThumbgenError
from thumbgen.loader import load_assets
from thumbgen.config import GameConfig, TitleImageConfig, ProviderLogoConfig
from thumbgen.renderer.crypto_card import render_crypto_card
from thumbgen.constants import DEFAULT_CHARACTER_HEIGHT_RATIO, DEFAULT_FONT_PATH

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

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

# Ensure required directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
FONTS_DIR.mkdir(exist_ok=True)
THUMBNAILS_ROOT.mkdir(exist_ok=True)


def find_all_game_directories(root: Path):
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
@app.route('/bulk')
@app.route('/single')
def index():
    """Render main UI page - handles both bulk and single modes with client-side routing."""
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


@app.route('/api/open-output')
def open_output_folder():
    """Open the output folder in file explorer."""
    try:
        output_path = OUTPUT_DIR.resolve()

        # Create output folder if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Open folder based on OS
        system = platform.system()
        if system == 'Windows':
            os.startfile(output_path)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', str(output_path)])
        else:  # Linux and others
            subprocess.run(['xdg-open', str(output_path)])

        return jsonify({'success': True})
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


@app.route('/api/asset-preview')
def get_asset_preview():
    """Serve asset image for preview tooltip."""
    try:
        game_path = request.args.get('game', '')
        asset_path = request.args.get('asset', '')

        if not game_path or not asset_path:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        # Normalize game path
        path_parts = game_path.split('/')
        game_dir = THUMBNAILS_ROOT
        for part in path_parts:
            game_dir = game_dir / part

        # Resolve full asset path (normalize path separators)
        asset_path_normalized = asset_path.replace('/', '\\' if '\\' in str(game_dir) else '/')
        full_asset_path = game_dir / asset_path_normalized

        print(f"[PREVIEW] Game path: {game_path}", flush=True)
        print(f"[PREVIEW] Asset path: {asset_path}", flush=True)
        print(f"[PREVIEW] Full path: {full_asset_path}", flush=True)
        print(f"[PREVIEW] Exists: {full_asset_path.exists()}", flush=True)

        if not full_asset_path.exists():
            return jsonify({'success': False, 'error': f'Asset not found: {full_asset_path}'}), 404

        # Serve the image file
        return send_file(str(full_asset_path), mimetype='image/png')

    except Exception as e:
        print(f"[PREVIEW ERROR] {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-single', methods=['POST'])
def generate_single():
    """Generate thumbnail for a single game and save to disk."""
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

        # Validate custom dimensions if provided
        if 'canvas_width' in settings or 'canvas_height' in settings:
            width = settings.get('canvas_width', 440)
            height = settings.get('canvas_height', 590)

            # Validate range
            if not (100 <= width <= 4000) or not (100 <= height <= 4000):
                return jsonify({
                    'success': False,
                    'error': f'Dimensions must be between 100-4000px. Got {width}x{height}'
                }), 400

            settings['canvas_width'] = width
            settings['canvas_height'] = height
            print(f"[BULK GEN] Using custom dimensions: {width}x{height}", flush=True)

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


@app.route('/api/default-font', methods=['GET'])
def get_default_font():
    """Get the current default title font."""
    try:
        from thumbgen.constants import DEFAULT_FONT_PATH
        # Extract just the font filename for display
        font_name = Path(DEFAULT_FONT_PATH).name
        return jsonify({
            'success': True,
            'font_path': DEFAULT_FONT_PATH,
            'font_name': font_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/default-font', methods=['POST'])
def set_default_font():
    """Set the default title font by updating constants.py."""
    try:
        data = request.json
        font_path = data.get('font_path')

        if not font_path:
            return jsonify({'success': False, 'error': 'Font path is required'}), 400

        # Get absolute font path
        if not Path(font_path).is_absolute():
            font_path = str((Path(__file__).parent.parent / font_path).resolve())

        # Verify font file exists
        if not Path(font_path).exists():
            return jsonify({'success': False, 'error': 'Font file not found'}), 404

        # Update constants.py
        constants_file = Path(__file__).parent.parent / 'thumbgen' / 'constants.py'

        with open(constants_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find and replace the DEFAULT_FONT_PATH line
        # Convert absolute path to relative from project root
        project_root = Path(__file__).parent.parent
        try:
            rel_path = Path(font_path).relative_to(project_root)
            font_path_str = str(rel_path).replace('\\', '/')
        except ValueError:
            # If not relative to project root, use absolute path
            font_path_str = str(Path(font_path)).replace('\\', '/')

        # Replace the DEFAULT_FONT_PATH line
        import re
        pattern = r'DEFAULT_FONT_PATH:\s*str\s*=\s*str\(_project_root\s*/\s*"[^"]+"\)'
        replacement = f'DEFAULT_FONT_PATH: str = str(_project_root / "{font_path_str}")'

        new_content = re.sub(pattern, replacement, content)

        # Check if pattern was found (even if replacement is identical)
        if not re.search(pattern, content):
            return jsonify({'success': False, 'error': 'DEFAULT_FONT_PATH not found in constants.py'}), 500

        # Write back to file (even if content is the same, this is a valid operation)
        with open(constants_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Reload the constants module to apply changes immediately
        import importlib
        import thumbgen.constants
        importlib.reload(thumbgen.constants)

        # Update the global DEFAULT_FONT_PATH in this module
        global DEFAULT_FONT_PATH
        from thumbgen.constants import DEFAULT_FONT_PATH

        font_name = Path(font_path).name
        return jsonify({
            'success': True,
            'message': f'Default font set to {font_name} and applied immediately!'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/create-game', methods=['POST'])
def create_game():
    """
    Create a new game directory structure.
    """
    try:
        data = request.json
        provider_name = data.get('provider')
        game_name = data.get('game')

        if not provider_name or not game_name:
            return jsonify({'success': False, 'error': 'Provider and game name required'}), 400

        # Sanitize names
        provider_name = provider_name.strip()
        game_name = game_name.strip()

        if not provider_name or not game_name:
            return jsonify({'success': False, 'error': 'Provider and game name cannot be empty'}), 400

        # Create directory structure
        game_dir = THUMBNAILS_ROOT / provider_name / game_name

        if game_dir.exists():
            return jsonify({'success': False, 'error': f'Game "{game_name}" already exists for provider "{provider_name}"'}), 400

        # Create game directory and standard folders
        game_dir.mkdir(parents=True, exist_ok=True)
        (game_dir / 'Backgrounds').mkdir(exist_ok=True)
        (game_dir / 'Character').mkdir(exist_ok=True)
        (game_dir / 'Title').mkdir(exist_ok=True)

        # Create provider logo folder at provider level if it doesn't exist
        provider_logo_dir = THUMBNAILS_ROOT / provider_name / 'Provider Logo'
        provider_logo_dir.mkdir(exist_ok=True)

        game_path = f"{provider_name}/{game_name}"

        return jsonify({
            'success': True,
            'message': f'Created game "{game_name}" for provider "{provider_name}"',
            'game_path': game_path,
            'provider_path': provider_name
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/providers', methods=['GET'])
def get_providers():
    """
    Get list of all providers (top-level directories in Thumbnails).
    """
    try:
        providers = []
        if THUMBNAILS_ROOT.exists():
            for item in THUMBNAILS_ROOT.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    providers.append(item.name)

        providers.sort()
        return jsonify({
            'success': True,
            'providers': providers
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload-assets', methods=['POST'])
def upload_assets():
    """
    Upload multiple image files and analyze them for asset classification.
    Returns classification results with confidence scores.
    """
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files uploaded'}), 400

        files = request.files.getlist('files')
        game_path = request.form.get('game_path', '')
        provider_path = request.form.get('provider_path', '')

        if not files:
            return jsonify({'success': False, 'error': 'No files selected'}), 400

        # Import detection module
        from thumbgen.asset_detector import detect_asset_type
        from thumbgen.constants import IMAGE_EXTENSIONS

        results = []
        temp_dir = Path(__file__).parent.parent / 'temp_uploads'
        temp_dir.mkdir(exist_ok=True)

        for file in files:
            if file.filename == '':
                continue

            # Check file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in IMAGE_EXTENSIONS:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': f'Unsupported format: {file_ext}',
                    'detected_type': None,
                    'confidence': 0
                })
                continue

            # Save temporarily for analysis
            safe_filename = secure_filename(file.filename)
            temp_path = temp_dir / safe_filename
            file.save(str(temp_path))

            try:
                # Detect asset type
                asset_type, confidence, scores = detect_asset_type(temp_path)

                # Generate thumbnail for preview
                from PIL import Image
                with Image.open(temp_path) as img:
                    # Create thumbnail (max 150x150)
                    img.thumbnail((150, 150))
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    thumbnail_b64 = base64.b64encode(buffer.getvalue()).decode()

                results.append({
                    'filename': file.filename,
                    'temp_filename': safe_filename,
                    'success': True,
                    'detected_type': asset_type,  # None if confidence < 50
                    'confidence': confidence,
                    'scores': {
                        'background': scores.background,
                        'character': scores.character,
                        'title': scores.title,
                        'logo': scores.logo
                    },
                    'thumbnail': f'data:image/png;base64,{thumbnail_b64}',
                    'requires_manual': asset_type is None  # True if confidence < 50
                })

            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e),
                    'detected_type': None,
                    'confidence': 0
                })

        return jsonify({
            'success': True,
            'results': results,
            'game_path': game_path,
            'provider_path': provider_path
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/save-classified-assets', methods=['POST'])
def save_classified_assets():
    """
    Save uploaded files to their classified folders.
    Creates folder structure if needed.
    """
    try:
        data = request.json
        game_path = data.get('game_path', '')
        provider_path = data.get('provider_path', '')
        classifications = data.get('classifications', [])

        if not game_path:
            return jsonify({'success': False, 'error': 'Game path required'}), 400

        if not classifications:
            return jsonify({'success': False, 'error': 'No classifications provided'}), 400

        game_dir = THUMBNAILS_ROOT / game_path
        provider_dir = THUMBNAILS_ROOT / provider_path if provider_path else None
        temp_dir = Path(__file__).parent.parent / 'temp_uploads'

        saved_files = []
        errors = []

        for item in classifications:
            temp_filename = item.get('temp_filename')
            asset_type = item.get('type')
            original_filename = item.get('filename')

            if not temp_filename or not asset_type:
                errors.append(f"Missing data for {original_filename}")
                continue

            temp_path = temp_dir / temp_filename
            if not temp_path.exists():
                errors.append(f"Temporary file not found: {temp_filename}")
                continue

            # Determine target folder based on asset type
            if asset_type == 'background':
                target_dir = game_dir / 'Backgrounds'
            elif asset_type == 'character':
                target_dir = game_dir / 'Character'
            elif asset_type == 'title':
                target_dir = game_dir / 'Title'
            elif asset_type == 'logo':
                if not provider_dir:
                    errors.append(f"Provider path required for logo: {original_filename}")
                    continue
                target_dir = provider_dir / 'Provider Logo'
            else:
                errors.append(f"Invalid asset type '{asset_type}' for {original_filename}")
                continue

            # Create target directory if needed
            target_dir.mkdir(parents=True, exist_ok=True)

            # Handle duplicate filenames
            target_path = target_dir / original_filename
            if target_path.exists():
                # Auto-rename with suffix
                stem = Path(original_filename).stem
                ext = Path(original_filename).suffix
                counter = 1
                while target_path.exists():
                    target_path = target_dir / f"{stem}_{counter}{ext}"
                    counter += 1

            # Move file from temp to target
            import shutil
            shutil.move(str(temp_path), str(target_path))
            saved_files.append({
                'filename': original_filename,
                'type': asset_type,
                'path': str(target_path.relative_to(THUMBNAILS_ROOT))
            })

        # Clean up temp directory
        try:
            if temp_dir.exists():
                for f in temp_dir.glob('*'):
                    f.unlink()
        except Exception:
            pass  # Ignore cleanup errors

        if errors:
            return jsonify({
                'success': False,
                'saved': saved_files,
                'errors': errors
            }), 400

        return jsonify({
            'success': True,
            'saved': saved_files,
            'message': f'Successfully saved {len(saved_files)} file(s)'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload-fonts', methods=['POST'])
def upload_fonts():
    """
    Upload font files (.ttf, .otf) to the fonts directory.
    """
    try:
        files = request.files.getlist('files')

        if not files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400

        fonts_dir = FONTS_ROOT
        fonts_dir.mkdir(parents=True, exist_ok=True)

        uploaded_fonts = []
        errors = []

        for file in files:
            if not file.filename:
                continue

            filename = secure_filename(file.filename)
            ext = Path(filename).suffix.lower()

            # Validate font file extension
            if ext not in ['.ttf', '.otf']:
                errors.append(f"{filename}: Invalid font format (only .ttf and .otf allowed)")
                continue

            # Check if font already exists
            target_path = fonts_dir / filename
            if target_path.exists():
                # Auto-rename with counter
                stem = Path(filename).stem
                counter = 1
                while target_path.exists():
                    target_path = fonts_dir / f"{stem}_{counter}{ext}"
                    counter += 1
                filename = target_path.name

            # Save the font file
            file.save(str(target_path))
            uploaded_fonts.append({
                'filename': filename,
                'path': f'fonts/{filename}'
            })

        if errors:
            return jsonify({
                'success': False if not uploaded_fonts else True,
                'uploaded': uploaded_fonts,
                'errors': errors
            }), 400 if not uploaded_fonts else 200

        return jsonify({
            'success': True,
            'uploaded': uploaded_fonts,
            'message': f'Successfully uploaded {len(uploaded_fonts)} font(s)'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
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
