// Thumbnail Generator Web UI - Main JavaScript

// State
let allGames = [];
let allFonts = [];
let providerFonts = {};
let selectedGamePath = null;
let selectedProvider = '';

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
    blurEnabled.addEventListener('change', toggleBlurOptions);
    blurModeRadios.forEach(radio => {
        radio.addEventListener('change', toggleColorPicker);
    });
    blurColor.addEventListener('input', updateColorPreview);

    // Font controls
    customFontEnabled.addEventListener('change', toggleFontSelect);
    bulkCustomFontEnabled.addEventListener('change', toggleBulkFontSelect);

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

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && providerFontModal && providerFontModal.style.display === 'flex') {
            closeProviderFontModal();
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
        previewContainer.style.display = 'none';
    } else {
        gameInfo.style.display = 'none';
        generateBtn.disabled = true;
    }
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

    // Only set custom_font if checkbox is enabled AND a font is selected
    if (customFontEnabled.checked && fontSelect.value) {
        settings.custom_font = fontSelect.value;
    }
    // Don't send custom_font at all if checkbox is unchecked or no font selected
    // This allows provider defaults to apply

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

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `bulk-game-${game.path}`;
        checkbox.value = game.path;
        checkbox.dataset.provider = game.provider;
        checkbox.addEventListener('change', updateBulkGenerateButton);

        const label = document.createElement('label');
        label.htmlFor = `bulk-game-${game.path}`;
        label.innerHTML = `<span class="game-provider">[${game.provider}]</span> ${game.name}`;

        div.appendChild(checkbox);
        div.appendChild(label);
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
