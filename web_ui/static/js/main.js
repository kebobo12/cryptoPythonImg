// Thumbnail Generator Web UI - Main JavaScript

// State
let allGames = [];
let allFonts = [];
let providerFonts = {};
let selectedGamePath = null;
let selectedProvider = '';

// Live preview state
let previewDebounceTimer = null;
let previewInProgress = false;
const DEBOUNCE_DELAY = 200; // milliseconds

// Asset selection state
let currentGameAssets = null;

// DOM Elements
const modeBtns = document.querySelectorAll('.mode-btn');
const singleMode = document.getElementById('single-mode');
const bulkMode = document.getElementById('bulk-mode');
const gameSelect = document.getElementById('game-select');
const gameInfo = document.getElementById('game-info');
const providerName = document.getElementById('provider-name');
const gameName = document.getElementById('game-name');
const generateBtn = document.getElementById('generate-btn');
const singleStatus = document.getElementById('single-status');
const previewContainer = document.getElementById('preview-container');
const previewImage = document.getElementById('preview-image');

// Font controls
const customFontEnabled = document.getElementById('custom-font-enabled');
const fontSelectContainer = document.getElementById('font-select-container');
const fontSelect = document.getElementById('font-select');

const bulkCustomFontEnabled = document.getElementById('bulk-custom-font-enabled');
const bulkFontSelectContainer = document.getElementById('bulk-font-select-container');
const bulkFontSelect = document.getElementById('bulk-font-select');

// Blur controls
const blurEnabled = document.getElementById('blur-enabled');
const blurOptions = document.getElementById('blur-options');
const blurModeRadios = document.querySelectorAll('input[name="blur-mode"]');
const colorPickerGroup = document.getElementById('color-picker-group');
const blurColor = document.getElementById('blur-color');
const colorPreview = document.getElementById('color-preview');
const blurScale = document.getElementById('blur-scale');
const blurScaleValue = document.getElementById('blur-scale-value');

// Bulk mode elements
const providerFilter = document.getElementById('provider-filter');
const bulkGamesList = document.getElementById('bulk-games-list');
const selectAllBtn = document.getElementById('select-all-btn');
const deselectAllBtn = document.getElementById('deselect-all-btn');
const generateBulkBtn = document.getElementById('generate-bulk-btn');
const bulkStatus = document.getElementById('bulk-status');
const bulkProgress = document.getElementById('bulk-progress');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

const bulkBlurEnabled = document.getElementById('bulk-blur-enabled');
const bulkBlurOptions = document.getElementById('bulk-blur-options');
const bulkBlurModeRadios = document.querySelectorAll('input[name="bulk-blur-mode"]');
const bulkColorPickerGroup = document.getElementById('bulk-color-picker-group');
const bulkBlurColor = document.getElementById('bulk-blur-color');

// Provider font management elements (modal)
const providerFontProvider = document.getElementById('provider-font-provider');
const providerFontSelect = document.getElementById('provider-font-select');
const saveProviderFontBtn = document.getElementById('save-provider-font-btn');
const providerFontsList = document.getElementById('provider-fonts-list');
const openProviderFontModalBtn = document.getElementById('open-provider-font-modal');
const providerFontModal = document.getElementById('provider-font-modal');
const closeProviderFontModalBtn = document.getElementById('close-provider-font-modal');

// Advanced text controls (single)
const textScale = document.getElementById('text-scale');
const textScaleValue = document.getElementById('text-scale-value');
const textOffset = document.getElementById('text-offset');
const textOffsetValue = document.getElementById('text-offset-value');

// Asset selection elements
const backgroundSelect = document.getElementById('background-select');
const backgroundSelectGroup = document.getElementById('background-select-group');
const characterSelect = document.getElementById('character-select');
const characterSelectGroup = document.getElementById('character-select-group');
const titleSelect = document.getElementById('title-select');
const titleSelectGroup = document.getElementById('title-select-group');
const logoSelect = document.getElementById('logo-select');
const logoSelectGroup = document.getElementById('logo-select-group');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadGames();
    loadFonts();
    loadProviderFonts();
    setupEventListeners();

    // Initialize UI state
    toggleBlurOptions();
    toggleColorPicker();
    toggleBulkBlurOptions();
    toggleBulkColorPicker();
    toggleFontSelect();
    toggleBulkFontSelect();
    updateTextScaleValue();
    updateTextOffsetValue();
    updateBlurScaleValue();
});

// Event Listeners
function setupEventListeners() {
    // Mode switching
    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => switchMode(btn.dataset.mode));
    });

    // Game selection
    gameSelect.addEventListener('change', onGameSelect);

    // Blur controls
    blurEnabled.addEventListener('change', () => {
        toggleBlurOptions();
        debouncedPreview();
    });
    blurModeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            toggleColorPicker();
            debouncedPreview();
        });
    });
    blurColor.addEventListener('input', () => {
        updateColorPreview();
        debouncedPreview();
    });
    if (blurScale) {
        blurScale.addEventListener('input', () => {
            updateBlurScaleValue();
            debouncedPreview();
        });
    }

    // Advanced text sliders
    if (textScale) {
        textScale.addEventListener('input', () => {
            updateTextScaleValue();
            debouncedPreview();
        });
    }
    if (textOffset) {
        textOffset.addEventListener('input', () => {
            updateTextOffsetValue();
            debouncedPreview();
        });
    }

    // Title/provider mode radios - add live preview and toggle asset selectors
    document.querySelectorAll('input[name="title-mode"]').forEach(radio => {
        radio.addEventListener('change', () => {
            updateAssetSelectorVisibility();
            debouncedPreview();
        });
    });
    document.querySelectorAll('input[name="provider-mode"]').forEach(radio => {
        radio.addEventListener('change', () => {
            updateAssetSelectorVisibility();
            debouncedPreview();
        });
    });

    // Font controls
    customFontEnabled.addEventListener('change', () => {
        toggleFontSelect();
        debouncedPreview();
    });
    if (fontSelect) {
        fontSelect.addEventListener('change', debouncedPreview);
    }
    bulkCustomFontEnabled.addEventListener('change', toggleBulkFontSelect);

    // Asset selection controls - trigger live preview on change
    if (backgroundSelect) {
        backgroundSelect.addEventListener('change', debouncedPreview);
    }
    if (characterSelect) {
        characterSelect.addEventListener('change', debouncedPreview);
    }
    if (titleSelect) {
        titleSelect.addEventListener('change', debouncedPreview);
    }
    if (logoSelect) {
        logoSelect.addEventListener('change', debouncedPreview);
    }

    // Bulk blur controls
    bulkBlurEnabled.addEventListener('change', toggleBulkBlurOptions);
    bulkBlurModeRadios.forEach(radio => {
        radio.addEventListener('change', toggleBulkColorPicker);
    });

    // Generate buttons
    generateBtn.addEventListener('click', generateThumbnail);
    generateBulkBtn.addEventListener('click', generateBulkThumbnails);

    // Bulk controls
    selectAllBtn.addEventListener('click', selectAllGames);
    deselectAllBtn.addEventListener('click', deselectAllGames);
    providerFilter.addEventListener('change', onProviderFilterChange);

    // Provider font management
    if (saveProviderFontBtn) {
        saveProviderFontBtn.addEventListener('click', saveProviderFont);
    }
    if (openProviderFontModalBtn) {
        openProviderFontModalBtn.addEventListener('click', openProviderFontModal);
    }
    if (closeProviderFontModalBtn) {
        closeProviderFontModalBtn.addEventListener('click', closeProviderFontModal);
    }

    // Close modal when clicking outside content
    if (providerFontModal) {
        providerFontModal.addEventListener('click', (e) => {
            if (e.target === providerFontModal) {
                closeProviderFontModal();
            }
        });
    }

    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (providerFontModal && providerFontModal.style.display === 'flex') {
                closeProviderFontModal();
            }
        }
    });
}

// Mode Switching
function switchMode(mode) {
    modeBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    if (mode === 'single') {
        singleMode.classList.add('active');
        bulkMode.classList.remove('active');
    } else {
        singleMode.classList.remove('active');
        bulkMode.classList.add('active');
        if (allGames.length > 0) {
            populateBulkGamesList();
        }
    }
}

// Load Games
async function loadGames() {
    try {
        const response = await fetch('/api/games');
        const data = await response.json();

        if (data.success) {
            allGames = data.games;
            populateGameSelect();
            populateProviderFilter();
            // Populate bulk games list on initial load since bulk mode is default
            populateBulkGamesList();
        } else {
            showStatus('error', data.error, singleStatus);
        }
    } catch (error) {
        showStatus('error', 'Failed to load games: ' + error.message, singleStatus);
    }
}

// Load Fonts
async function loadFonts() {
    try {
        const response = await fetch('/api/fonts');
        const data = await response.json();

        if (data.success) {
            allFonts = data.fonts;
            populateFontSelects();
            populateProviderFontSelects();
        } else {
            console.error('Failed to load fonts:', data.error);
        }
    } catch (error) {
        console.error('Failed to load fonts:', error.message);
    }
}

// Load Provider Fonts
async function loadProviderFonts() {
    try {
        const response = await fetch('/api/provider-fonts');
        const data = await response.json();

        if (data.success) {
            providerFonts = data.provider_fonts;
            renderProviderFontsList();
        } else {
            console.error('Failed to load provider fonts:', data.error);
        }
    } catch (error) {
        console.error('Failed to load provider fonts:', error.message);
    }
}

// Populate Font Selects
function populateFontSelects() {
    const options = '<option value="">Use default font</option>' +
        allFonts.map(font =>
            `<option value="${font.path}">[${font.family}] ${font.name}</option>`
        ).join('');

    fontSelect.innerHTML = options;
    bulkFontSelect.innerHTML = options;
}

// Populate Provider Font Selects (for management)
function populateProviderFontSelects() {
    // Populate provider dropdown
    const providers = [...new Set(allGames.map(g => g.provider))].sort();
    providerFontProvider.innerHTML = '<option value="">Select provider...</option>' +
        providers.map(provider =>
            `<option value="${provider}">${provider}</option>`
        ).join('');

    // Populate font dropdown
    providerFontSelect.innerHTML = '<option value="">Select default font...</option>' +
        allFonts.map(font =>
            `<option value="${font.path}">[${font.family}] ${font.name}</option>`
        ).join('');
}

// Render Provider Fonts List
function renderProviderFontsList() {
    if (!providerFontsList) return;

    if (Object.keys(providerFonts).length === 0) {
        providerFontsList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No provider fonts configured</p>';
        return;
    }

    providerFontsList.innerHTML = Object.entries(providerFonts).map(([provider, fontPath]) => {
        const font = allFonts.find(f => f.path === fontPath);
        const fontName = font ? `[${font.family}] ${font.name}` : fontPath;

        return `
            <div class="provider-font-item">
                <div class="provider-font-info">
                    <div class="provider-font-provider">${provider}</div>
                    <div class="provider-font-name">${fontName}</div>
                </div>
                <button class="btn-remove" onclick="removeProviderFont('${provider}')">Remove</button>
            </div>
        `;
    }).join('');
}

// Save Provider Font
async function saveProviderFont() {
    const provider = providerFontProvider.value;
    const fontPath = providerFontSelect.value;

    if (!provider) {
        alert('Please select a provider');
        return;
    }

    if (!fontPath) {
        alert('Please select a font');
        return;
    }

    try {
        const response = await fetch('/api/provider-fonts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider: provider,
                font_path: fontPath
            })
        });

        const data = await response.json();

        if (data.success) {
            providerFonts[provider] = fontPath;
            renderProviderFontsList();
            providerFontProvider.value = '';
            providerFontSelect.value = '';
            alert(data.message);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to save provider font: ' + error.message);
    }
}

function openProviderFontModal() {
    if (!providerFontModal) return;
    providerFontModal.style.display = 'flex';
}

function closeProviderFontModal() {
    if (!providerFontModal) return;
    providerFontModal.style.display = 'none';
}

// Remove Provider Font
async function removeProviderFont(provider) {
    if (!confirm(`Remove default font for ${provider}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/provider-fonts/${encodeURIComponent(provider)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            delete providerFonts[provider];
            renderProviderFontsList();
            alert(data.message);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to remove provider font: ' + error.message);
    }
}

// Populate Game Dropdown
function populateGameSelect() {
    gameSelect.innerHTML = '<option value="">Choose a game...</option>';

    allGames.forEach(game => {
        const option = document.createElement('option');
        option.value = game.path;
        option.textContent = `[${game.provider}] ${game.name}`;
        gameSelect.appendChild(option);
    });
}

// Game Selection
function onGameSelect() {
    selectedGamePath = gameSelect.value;

    if (selectedGamePath) {
        const game = allGames.find(g => g.path === selectedGamePath);
        providerName.textContent = game.provider;
        gameName.textContent = game.name;
        gameInfo.style.display = 'block';
        generateBtn.disabled = false;

        // Load available assets for this game
        loadGameAssets(selectedGamePath);

        // Trigger initial live preview
        updateLivePreview();
    } else {
        gameInfo.style.display = 'none';
        generateBtn.disabled = true;
        previewContainer.style.display = 'none';
    }
}

// Load Game Assets
async function loadGameAssets(gamePath) {
    try {
        const response = await fetch(`/api/game/${gamePath}/assets`);
        const data = await response.json();

        if (data.success) {
            currentGameAssets = data.assets;
            populateAssetSelectors();
        } else {
            console.error('Failed to load game assets:', data.error);
        }
    } catch (error) {
        console.error('Failed to load game assets:', error);
    }
}

// Populate Asset Selectors
function populateAssetSelectors() {
    if (!currentGameAssets) return;

    // Populate background selector
    if (currentGameAssets.backgrounds && currentGameAssets.backgrounds.length > 0) {
        backgroundSelect.innerHTML = currentGameAssets.backgrounds.map(bg =>
            `<option value="${bg}">${bg}</option>`
        ).join('');
        // Ensure first option is selected
        backgroundSelect.selectedIndex = 0;
        backgroundSelectGroup.style.display = 'block';
    } else {
        backgroundSelect.innerHTML = '';
        backgroundSelectGroup.style.display = 'none';
    }

    // Populate character selector (single selection dropdown)
    if (currentGameAssets.characters && currentGameAssets.characters.length > 0) {
        characterSelect.innerHTML = currentGameAssets.characters.map(char =>
            `<option value="${char}">${char}</option>`
        ).join('');
        // Ensure first option is selected
        characterSelect.selectedIndex = 0;
        characterSelectGroup.style.display = 'block';
    } else {
        characterSelect.innerHTML = '';
        characterSelectGroup.style.display = 'none';
    }

    // Populate title selector
    if (currentGameAssets.titles && currentGameAssets.titles.length > 0) {
        titleSelect.innerHTML = currentGameAssets.titles.map(title =>
            `<option value="${title}">${title}</option>`
        ).join('');
        // Ensure first option is selected
        titleSelect.selectedIndex = 0;
    } else {
        titleSelect.innerHTML = '';
    }

    // Populate logo selector
    if (currentGameAssets.logos && currentGameAssets.logos.length > 0) {
        logoSelect.innerHTML = currentGameAssets.logos.map(logo =>
            `<option value="${logo}">${logo}</option>`
        ).join('');
        // Ensure first option is selected
        logoSelect.selectedIndex = 0;
    } else {
        logoSelect.innerHTML = '';
    }

    // Update visibility based on mode and available assets
    updateAssetSelectorVisibility();
}

// Update visibility of asset selectors based on mode and available options
function updateAssetSelectorVisibility() {
    if (!currentGameAssets) return;

    // Title selector - show only if in image mode AND multiple titles available
    const titleMode = document.querySelector('input[name="title-mode"]:checked')?.value;
    const hasTitles = currentGameAssets.titles && currentGameAssets.titles.length > 1;
    titleSelectGroup.style.display = (titleMode === 'image' && hasTitles) ? 'block' : 'none';

    // Logo selector - show only if in logo mode AND multiple logos available
    const providerMode = document.querySelector('input[name="provider-mode"]:checked')?.value;
    const hasLogos = currentGameAssets.logos && currentGameAssets.logos.length > 1;
    logoSelectGroup.style.display = (providerMode === 'logo' && hasLogos) ? 'block' : 'none';
}

// Blur Options Toggle
function toggleBlurOptions() {
    blurOptions.style.display = blurEnabled.checked ? 'block' : 'none';
}

function toggleColorPicker() {
    const manual = document.querySelector('input[name="blur-mode"][value="manual"]').checked;
    colorPickerGroup.style.display = manual ? 'flex' : 'none';
}

function updateColorPreview() {
    const color = blurColor.value;
    colorPreview.textContent = color;
    colorPreview.style.backgroundColor = color;
    colorPreview.style.color = getContrastColor(color);
}

function toggleBulkBlurOptions() {
    bulkBlurOptions.style.display = bulkBlurEnabled.checked ? 'block' : 'none';
}

function toggleBulkColorPicker() {
    const manual = document.querySelector('input[name="bulk-blur-mode"][value="manual"]').checked;
    bulkColorPickerGroup.style.display = manual ? 'flex' : 'none';
}

function toggleFontSelect() {
    fontSelectContainer.style.display = customFontEnabled.checked ? 'block' : 'none';
}

function toggleBulkFontSelect() {
    bulkFontSelectContainer.style.display = bulkCustomFontEnabled.checked ? 'block' : 'none';
}

function updateTextScaleValue() {
    if (!textScaleValue || !textScale) return;
    textScaleValue.textContent = `${parseFloat(textScale.value).toFixed(2)}x`;
}

function updateTextOffsetValue() {
    if (!textOffsetValue || !textOffset) return;
    textOffsetValue.textContent = `${parseFloat(textOffset.value).toFixed(2)}`;
}

function updateBlurScaleValue() {
    if (!blurScaleValue || !blurScale) return;
    blurScaleValue.textContent = `${parseFloat(blurScale.value).toFixed(2)}x`;
}

// Get Settings
function getSettings() {
    const blurMode = document.querySelector('input[name="blur-mode"]:checked').value;
    const titleMode = document.querySelector('input[name="title-mode"]:checked').value;
    const providerMode = document.querySelector('input[name="provider-mode"]:checked').value;

    const settings = {
        blur_enabled: blurEnabled.checked,
        title_mode: titleMode,
        provider_mode: providerMode
    };

    if (blurEnabled.checked && blurMode === 'manual') {
        const hex = blurColor.value;
        settings.blur_manual_color = hexToRgb(hex);
    }

    // Advanced text/blur controls (single)
    if (textScale) settings.text_scale = parseFloat(textScale.value) || 1;
    if (textOffset) settings.text_offset = parseFloat(textOffset.value) || 0;
    if (blurScale) settings.blur_scale = parseFloat(blurScale.value) || 1;

    // Only set custom_font if checkbox is enabled AND a font is selected
    if (customFontEnabled.checked && fontSelect.value) {
        settings.custom_font = fontSelect.value;
    }
    // Don't send custom_font at all if checkbox is unchecked or no font selected
    // This allows provider defaults to apply

    // Asset selections
    if (currentGameAssets) {
        const asset_filenames = {};

        // Background selection
        if (backgroundSelect.value) {
            asset_filenames.background = backgroundSelect.value;
        }

        // Character selection (single dropdown)
        if (characterSelect.value) {
            asset_filenames.characters = [characterSelect.value];
        }

        // Title selection
        if (titleSelect.value) {
            asset_filenames.title = titleSelect.value;
        }

        // Logo selection
        if (logoSelect.value) {
            asset_filenames.logo = logoSelect.value;
        }

        // Only include asset_filenames if any selections were made
        if (Object.keys(asset_filenames).length > 0) {
            settings.asset_filenames = asset_filenames;
        }
    }

    console.log('Settings being sent:', settings);
    return settings;
}

function getBulkSettings() {
    const blurMode = document.querySelector('input[name="bulk-blur-mode"]:checked').value;
    const titleMode = document.querySelector('input[name="bulk-title-mode"]:checked').value;
    const providerMode = document.querySelector('input[name="bulk-provider-mode"]:checked').value;

    const settings = {
        blur_enabled: bulkBlurEnabled.checked,
        title_mode: titleMode,
        provider_mode: providerMode
    };

    if (bulkBlurEnabled.checked && blurMode === 'manual') {
        const hex = bulkBlurColor.value;
        settings.blur_manual_color = hexToRgb(hex);
    }

    // Only set custom_font if checkbox is enabled AND a font is selected
    if (bulkCustomFontEnabled.checked && bulkFontSelect.value) {
        settings.custom_font = bulkFontSelect.value;
    }
    // Don't send custom_font at all if checkbox is unchecked or no font selected
    // This allows provider defaults to apply

    return settings;
}

// Live Preview Functions
function debouncedPreview() {
    clearTimeout(previewDebounceTimer);

    previewDebounceTimer = setTimeout(() => {
        if (!previewInProgress && selectedGamePath) {
            updateLivePreview();
        }
    }, DEBOUNCE_DELAY);
}

async function updateLivePreview() {
    if (!selectedGamePath) return;

    previewInProgress = true;
    previewContainer.classList.add('updating');

    try {
        const response = await fetch('/api/preview-live', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                game_path: selectedGamePath,
                settings: getSettings()
            })
        });

        const data = await response.json();

        if (data.success) {
            previewImage.src = data.preview_image;
            previewContainer.style.display = 'block';
        } else {
            console.error('Preview failed:', data.error);
        }
    } catch (error) {
        console.error('Live preview error:', error);
        // Fallback: preview will update on Generate button click
    } finally {
        previewInProgress = false;
        previewContainer.classList.remove('updating');
    }
}

// Generate Thumbnail
async function generateThumbnail() {
    if (!selectedGamePath) return;

    generateBtn.disabled = true;
    showStatus('info', 'Generating thumbnail...', singleStatus);
    previewContainer.style.display = 'none';

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                game_path: selectedGamePath,
                settings: getSettings()
            })
        });

        const data = await response.json();

        if (data.success) {
            showStatus('success', data.message, singleStatus);
            // Show preview
            previewImage.src = `/api/preview/${data.output_path}?t=${Date.now()}`;
            previewContainer.style.display = 'block';
        } else {
            showStatus('error', data.error, singleStatus);
        }
    } catch (error) {
        showStatus('error', 'Failed to generate thumbnail: ' + error.message, singleStatus);
    } finally {
        generateBtn.disabled = false;
    }
}

// Provider Filter
function populateProviderFilter() {
    const providers = [...new Set(allGames.map(g => g.provider))].sort();

    providerFilter.innerHTML = '<option value="">All Providers</option>';
    providers.forEach(provider => {
        const option = document.createElement('option');
        option.value = provider;
        option.textContent = provider;
        providerFilter.appendChild(option);
    });
}

function onProviderFilterChange() {
    selectedProvider = providerFilter.value;
    populateBulkGamesList();

    // Auto-select all games when filtering by provider
    if (selectedProvider) {
        selectAllGames();
    }
}

// Bulk Mode
function populateBulkGamesList() {
    bulkGamesList.innerHTML = '';

    const filteredGames = selectedProvider
        ? allGames.filter(g => g.provider === selectedProvider)
        : allGames;

    filteredGames.forEach(game => {
        const div = document.createElement('div');
        div.className = 'game-checkbox';

        // Checkbox and label container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'game-checkbox-content';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `bulk-game-${game.path}`;
        checkbox.value = game.path;
        checkbox.dataset.provider = game.provider;
        checkbox.addEventListener('change', updateBulkGenerateButton);

        const label = document.createElement('label');
        label.htmlFor = `bulk-game-${game.path}`;
        label.innerHTML = `<span class="game-provider">[${game.provider}]</span> ${game.name}`;

        contentDiv.appendChild(checkbox);
        contentDiv.appendChild(label);

        // Edit button
        const editBtn = document.createElement('button');
        editBtn.className = 'edit-game-btn';
        editBtn.textContent = 'Edit';
        editBtn.onclick = (e) => {
            e.stopPropagation(); // Prevent checkbox toggle
            switchToSingleModeWithGame(game);
        };

        div.appendChild(contentDiv);
        div.appendChild(editBtn);
        bulkGamesList.appendChild(div);
    });

    updateBulkGenerateButton();
}

function selectAllGames() {
    const checkboxes = bulkGamesList.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = true);
    updateBulkGenerateButton();
}

function deselectAllGames() {
    const checkboxes = bulkGamesList.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);
    updateBulkGenerateButton();
}

function updateBulkGenerateButton() {
    const checkboxes = bulkGamesList.querySelectorAll('input[type="checkbox"]:checked');
    generateBulkBtn.disabled = checkboxes.length === 0;
}

async function generateBulkThumbnails() {
    const checkboxes = bulkGamesList.querySelectorAll('input[type="checkbox"]:checked');
    const gamePaths = Array.from(checkboxes).map(cb => cb.value);

    if (gamePaths.length === 0) return;

    generateBulkBtn.disabled = true;
    selectAllBtn.disabled = true;
    deselectAllBtn.disabled = true;
    bulkProgress.style.display = 'block';
    showStatus('info', 'Processing games...', bulkStatus);

    try {
        const response = await fetch('/api/generate-bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                game_paths: gamePaths,
                settings: getBulkSettings()
            })
        });

        const data = await response.json();

        if (data.success) {
            progressFill.style.width = '100%';
            progressText.textContent = '100%';

            const message = `Complete! ${data.successful}/${data.total} thumbnails generated successfully`;
            showStatus('success', message, bulkStatus);

            // Show detailed results
            const failedGames = data.results.filter(r => !r.success);
            if (failedGames.length > 0) {
                console.log('Failed games:', failedGames);
            }
        } else {
            showStatus('error', data.error, bulkStatus);
        }
    } catch (error) {
        showStatus('error', 'Failed to generate thumbnails: ' + error.message, bulkStatus);
    } finally {
        setTimeout(() => {
            bulkProgress.style.display = 'none';
            progressFill.style.width = '0%';
            progressText.textContent = '0%';
        }, 2000);

        generateBulkBtn.disabled = false;
        selectAllBtn.disabled = false;
        deselectAllBtn.disabled = false;
    }
}

// Switch to single mode with game selected
function switchToSingleModeWithGame(game) {
    // Switch to single mode
    switchMode('single');

    // Find and select the game in the dropdown
    gameSelect.value = game.path;

    // Trigger game selection
    onGameSelect();

    // Scroll to preview after a short delay (wait for preview to render)
    setTimeout(() => {
        const previewContainer = document.getElementById('preview-container');
        if (previewContainer && previewContainer.style.display !== 'none') {
            previewContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 300);
}

// Utility Functions
function showStatus(type, message, element) {
    element.className = `status ${type}`;
    element.textContent = message;
    element.style.display = 'block';

    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            if (type === 'success') {
                element.style.display = 'none';
            }
        }, 5000);
    }
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16)
    ] : null;
}

function getContrastColor(hexColor) {
    const rgb = hexToRgb(hexColor);
    if (!rgb) return '#ffffff';

    const brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000;
    return brightness > 128 ? '#000000' : '#ffffff';
}
// Cache bust 5 - reset dropdown selections on game switch
