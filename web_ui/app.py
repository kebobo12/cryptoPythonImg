"""
Flask web UI for Thumbnail Generator
Modern, responsive web interface for generating game thumbnails
"""

import sys
import json
import webbrowser
from pathlib import Path
from threading import Timer
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Add parent directory to path to import thumbgen
sys.path.insert(0, str(Path(__file__).parent.parent))

from thumbgen import generate_thumbnail
from thumbgen.errors import ThumbgenError
from thumbgen.cli import find_all_game_directories

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
