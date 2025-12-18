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

            # Check for config
            config_path = game_dir / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}

            games.append({
                'path': str(game_dir.relative_to(THUMBNAILS_ROOT)),
                'provider': provider,
                'name': game_name,
                'config': config
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

        config_path = game_dir / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        # Check what assets exist
        assets = {
            'background': (game_dir / "background.png").exists(),
            'char': (game_dir / "char.png").exists(),
            'title': (game_dir / "title.png").exists(),
            'provider': (game_dir / "provider.png").exists(),
        }

        return jsonify({
            'success': True,
            'config': config,
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

        # Apply settings to config
        config_path = game_dir / "config.json"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Force crypto layout
        config['layout'] = 'crypto'

        # Apply blur settings
        if settings.get('blur_enabled'):
            if settings.get('blur_manual_color'):
                config['band_color'] = settings['blur_manual_color']
            else:
                config.pop('band_color', None)
        else:
            config.pop('band_color', None)

        # Apply title settings
        if 'title_image' not in config:
            config['title_image'] = {
                'enabled': False,
                'path': 'title.png',
                'max_width_ratio': 0.7,
                'scale': 1.0
            }
        config['title_image']['enabled'] = settings.get('title_mode') == 'image'

        print(f"DEBUG: Title mode = {settings.get('title_mode')}, title_image enabled = {config['title_image']['enabled']}", flush=True)

        # Apply provider settings
        config['provider_logo'] = config.get('provider_logo', {})
        provider_mode = settings.get('provider_mode', 'text')

        if provider_mode == 'none':
            config['provider_logo']['enabled'] = False
            config['provider_text'] = ""
        elif provider_mode == 'text':
            config['provider_logo']['enabled'] = False
            # Always set provider_text from folder name when text mode is selected
            config['provider_text'] = game_dir.parent.name
        else:  # logo
            config['provider_logo']['enabled'] = True
            config['provider_text'] = ""

        # Apply custom font if provided
        if settings.get('custom_font'):
            # Convert to absolute path to avoid issues with working directory
            font_rel_path = settings['custom_font']
            font_abs_path = (BASE_DIR / font_rel_path).resolve()
            config['font_path'] = str(font_abs_path).replace('\\', '/')

        # Write updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print(f"DEBUG: Config written to {config_path}", flush=True)
        print(f"DEBUG: title_image.enabled = {config.get('title_image', {}).get('enabled')}", flush=True)
        print(f"DEBUG: provider_logo.enabled = {config.get('provider_logo', {}).get('enabled')}", flush=True)
        print(f"DEBUG: provider_text = {config.get('provider_text')}", flush=True)

        # Generate thumbnail
        result_path = generate_thumbnail(game_dir, OUTPUT_DIR)

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

        if not game_paths:
            return jsonify({'success': False, 'error': 'No games selected'}), 400

        results = []
        success_count = 0

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

                # Apply settings (same as single generate)
                config_path = game_dir / "config.json"

                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                config['layout'] = 'crypto'

                if settings.get('blur_enabled'):
                    if settings.get('blur_manual_color'):
                        config['band_color'] = settings['blur_manual_color']
                    else:
                        config.pop('band_color', None)
                else:
                    config.pop('band_color', None)

                config['title_image'] = config.get('title_image', {})
                config['title_image']['enabled'] = settings.get('title_mode') == 'image'

                config['provider_logo'] = config.get('provider_logo', {})
                provider_mode = settings.get('provider_mode', 'text')

                if provider_mode == 'none':
                    config['provider_logo']['enabled'] = False
                    config['provider_text'] = ""
                elif provider_mode == 'text':
                    config['provider_logo']['enabled'] = False
                    # Always set provider_text from folder name when text mode is selected
                    config['provider_text'] = game_dir.parent.name
                else:
                    config['provider_logo']['enabled'] = True
                    config['provider_text'] = ""

                # Apply custom font if provided
                if settings.get('custom_font'):
                    # Convert to absolute path to avoid issues with working directory
                    font_rel_path = settings['custom_font']
                    font_abs_path = (BASE_DIR / font_rel_path).resolve()
                    config['font_path'] = str(font_abs_path).replace('\\', '/')

                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)

                result_path = generate_thumbnail(game_dir, OUTPUT_DIR)

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
