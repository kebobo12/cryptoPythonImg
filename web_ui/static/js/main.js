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
const gameSearch = document.getElementById('game-search');
const openOutputBtn = document.getElementById('open-output-btn');
const openOutputBulkBtn = document.getElementById('open-output-bulk-btn');
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

// Default font controls
const allFontsList = document.getElementById('all-fonts-list');
const defaultFontStatus = document.getElementById('default-font-status');

// Provider modal font list
const providerModalFontsList = document.getElementById('provider-modal-fonts-list');
const providerModalFontStatus = document.getElementById('provider-modal-font-status');

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

// Provider font management elements (standalone modal)
const providerFontProvider = document.getElementById('provider-font-provider');
const providerFontSelect = document.getElementById('provider-font-select');
const saveProviderFontBtn = document.getElementById('save-provider-font-btn');
const providerFontsList = document.getElementById('provider-fonts-list');
const openProviderFontModalBtn = document.getElementById('open-provider-font-modal');
const providerFontModal = document.getElementById('provider-font-modal');
const closeProviderFontModalBtn = document.getElementById('close-provider-font-modal');

// Provider font management elements (Manage Content modal - Fonts tab)
const manageProviderFontProvider = document.getElementById('manage-provider-font-provider');
const manageProviderFontSelect = document.getElementById('manage-provider-font-select');
const manageSaveProviderFontBtn = document.getElementById('manage-save-provider-font-btn');
const manageProviderFontsList = document.getElementById('manage-provider-fonts-list');

// Advanced text controls (single)
const textScale = document.getElementById('text-scale');
const textScaleValue = document.getElementById('text-scale-value');
const textOffset = document.getElementById('text-offset');
const textOffsetValue = document.getElementById('text-offset-value');

// Asset selection elements
const backgroundCheckboxes = document.getElementById('background-checkboxes');
const backgroundSelectGroup = document.getElementById('background-select-group');
const characterCheckboxes = document.getElementById('character-checkboxes');
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

    // Initialize mode based on current URL
    initializeFromURL();

    // Handle browser back/forward buttons
    window.addEventListener('popstate', (event) => {
        const path = window.location.pathname;
        const mode = path === '/single' ? 'single' : 'bulk';
        switchMode(mode, false); // Don't update history when responding to popstate
    });

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

    // Search functionality
    if (gameSearch) {
        gameSearch.addEventListener('input', filterGames);
    }

    // Open output folder button
    if (openOutputBtn) {
        openOutputBtn.addEventListener('click', openOutputFolder);
    }

    // Open output folder button (bulk mode)
    if (openOutputBulkBtn) {
        openOutputBulkBtn.addEventListener('click', openOutputFolder);
    }

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

    // Asset selection controls - checkboxes will have change listeners added dynamically
    // when populated
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

    // Custom dimensions controls
    const bulkCustomDimensions = document.getElementById('bulk-custom-dimensions');
    const bulkCanvasWidth = document.getElementById('bulk-canvas-width');
    const bulkCanvasHeight = document.getElementById('bulk-canvas-height');

    if (bulkCustomDimensions) {
        bulkCustomDimensions.addEventListener('change', function() {
            document.getElementById('bulk-dimensions-controls').style.display =
                this.checked ? 'block' : 'none';
        });
    }

    if (bulkCanvasWidth) {
        bulkCanvasWidth.addEventListener('input', updateAspectRatio);
    }

    if (bulkCanvasHeight) {
        bulkCanvasHeight.addEventListener('input', updateAspectRatio);
    }

    // Generate buttons
    generateBtn.addEventListener('click', generateThumbnail);
    generateBulkBtn.addEventListener('click', generateBulkThumbnails);

    // Bulk controls
    selectAllBtn.addEventListener('click', selectAllGames);
    deselectAllBtn.addEventListener('click', deselectAllGames);
    providerFilter.addEventListener('change', onProviderFilterChange);

    // Provider font management (standalone modal)
    if (saveProviderFontBtn) {
        saveProviderFontBtn.addEventListener('click', saveProviderFont);
    }
    if (openProviderFontModalBtn) {
        openProviderFontModalBtn.addEventListener('click', openProviderFontModal);
    }
    if (closeProviderFontModalBtn) {
        closeProviderFontModalBtn.addEventListener('click', closeProviderFontModal);
    }

    // Close provider font modal when clicking outside
    if (providerFontModal) {
        providerFontModal.addEventListener('click', (e) => {
            if (e.target === providerFontModal) {
                closeProviderFontModal();
            }
        });
    }

    // Default font management - handled via onclick in font list items

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

// Initialize mode from current URL
function initializeFromURL() {
    const path = window.location.pathname;
    const mode = path === '/single' ? 'single' : 'bulk';
    switchMode(mode, false); // Don't update history on initial load
}

// Mode Switching with client-side routing
function switchMode(mode, updateHistory = true) {
    modeBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    if (mode === 'single') {
        singleMode.classList.add('active');
        bulkMode.classList.remove('active');
        if (updateHistory) {
            history.pushState({ mode: 'single' }, '', '/single');
        }
    } else {
        singleMode.classList.remove('active');
        bulkMode.classList.add('active');
        if (allGames.length > 0) {
            populateBulkGamesList();
        }
        if (updateHistory) {
            history.pushState({ mode: 'bulk' }, '', '/bulk');
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

    // Render the all fonts list
    renderAllFontsList();
}

// Populate Provider Font Selects (for standalone Provider Font modal)
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

// Populate Provider Font Selects (for Manage Content modal - Fonts tab)
function populateManageProviderFontSelects() {
    if (!manageProviderFontProvider || !manageProviderFontSelect) return;

    // Populate provider dropdown
    const providers = [...new Set(allGames.map(g => g.provider))].sort();
    manageProviderFontProvider.innerHTML = '<option value="">Select provider...</option>' +
        providers.map(provider =>
            `<option value="${provider}">${provider}</option>`
        ).join('');

    // Populate font dropdown
    manageProviderFontSelect.innerHTML = '<option value="">Select default font...</option>' +
        allFonts.map(font =>
            `<option value="${font.path}">[${font.family}] ${font.name}</option>`
        ).join('');
}

// Render All Fonts List
async function renderAllFontsList() {
    if (!allFontsList) return;

    if (allFonts.length === 0) {
        allFontsList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No fonts available. Upload fonts to get started.</p>';
        return;
    }

    // Get current default font
    let currentDefaultFont = null;
    try {
        const response = await fetch('/api/default-font');
        const data = await response.json();
        if (data.success) {
            currentDefaultFont = data.font_name;
        }
    } catch (error) {
        console.error('Failed to load default font:', error);
    }

    allFontsList.innerHTML = allFonts.map(font => {
        const fontDisplayName = `[${font.family}] ${font.name}`;
        const isDefault = currentDefaultFont && font.name.includes(currentDefaultFont);

        return `
            <div class="provider-font-item">
                <div class="provider-font-info">
                    <div class="provider-font-provider">${font.family}</div>
                    <div class="provider-font-name">${font.name}${isDefault ? ' <strong style="color: #10b981;">(Default)</strong>' : ''}</div>
                </div>
                <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 14px;" onclick="setDefaultFont('${font.path}', '${font.name}')">
                    ${isDefault ? 'Current Default' : 'Set as Default'}
                </button>
            </div>
        `;
    }).join('');
}

// Render Provider Modal Fonts List (for standalone Provider Font modal)
async function renderProviderModalFontsList() {
    if (!providerModalFontsList) return;

    if (allFonts.length === 0) {
        providerModalFontsList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No fonts available. Upload fonts to get started.</p>';
        return;
    }

    // Get current default font
    let currentDefaultFont = null;
    try {
        const response = await fetch('/api/default-font');
        const data = await response.json();
        if (data.success) {
            currentDefaultFont = data.font_name;
        }
    } catch (error) {
        console.error('Failed to load default font:', error);
    }

    providerModalFontsList.innerHTML = allFonts.map(font => {
        const fontDisplayName = `[${font.family}] ${font.name}`;
        const isDefault = currentDefaultFont && font.name.includes(currentDefaultFont);

        return `
            <div class="provider-font-item">
                <div class="provider-font-info">
                    <div class="provider-font-provider">${font.family}</div>
                    <div class="provider-font-name">${font.name}${isDefault ? ' <strong style="color: #10b981;">(Default)</strong>' : ''}</div>
                </div>
                <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 14px;" onclick="setDefaultFontFromProviderModal('${font.path}', '${font.name}')">
                    ${isDefault ? 'Current Default' : 'Set as Default'}
                </button>
            </div>
        `;
    }).join('');
}

// Render Provider Fonts List (for standalone Provider Font modal)
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

// Render Provider Fonts List (for Manage Content modal - Fonts tab)
function renderManageProviderFontsList() {
    if (!manageProviderFontsList) return;

    if (Object.keys(providerFonts).length === 0) {
        manageProviderFontsList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No provider fonts configured</p>';
        return;
    }

    manageProviderFontsList.innerHTML = Object.entries(providerFonts).map(([provider, fontPath]) => {
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

// Save Provider Font (for standalone Provider Font modal)
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

// Save Provider Font (for Manage Content modal - Fonts tab)
async function saveManageProviderFont() {
    const provider = manageProviderFontProvider.value;
    const fontPath = manageProviderFontSelect.value;

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
            renderManageProviderFontsList();
            manageProviderFontProvider.value = '';
            manageProviderFontSelect.value = '';
            alert(data.message);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to save provider font: ' + error.message);
    }
}

async function openProviderFontModal() {
    if (!providerFontModal) return;
    providerFontModal.style.display = 'flex';

    // Populate the font list in the provider modal
    await renderProviderModalFontsList();

    // Populate the provider fonts section dropdowns
    populateProviderFontSelects();

    // Render the list of currently configured provider fonts
    renderProviderFontsList();
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

// Set Default Font (called from Manage Content modal font list)
async function setDefaultFont(fontPath, fontName) {
    if (!fontPath) {
        return;
    }

    try {
        const response = await fetch('/api/default-font', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ font_path: fontPath })
        });

        const data = await response.json();

        if (data.success) {
            defaultFontStatus.textContent = `Default font set to: ${fontName}`;
            defaultFontStatus.style.display = 'block';
            defaultFontStatus.style.color = '#10b981';

            // Re-render the fonts list to update the UI
            await renderAllFontsList();

            // Hide status after 3 seconds
            setTimeout(() => {
                defaultFontStatus.style.display = 'none';
            }, 3000);
        } else {
            defaultFontStatus.textContent = 'Error: ' + data.error;
            defaultFontStatus.style.color = '#ef4444';
            defaultFontStatus.style.display = 'block';
        }
    } catch (error) {
        defaultFontStatus.textContent = 'Failed to save: ' + error.message;
        defaultFontStatus.style.color = '#ef4444';
        defaultFontStatus.style.display = 'block';
    }
}

// Set Default Font (called from Provider Font modal)
async function setDefaultFontFromProviderModal(fontPath, fontName) {
    if (!fontPath) {
        return;
    }

    try {
        const response = await fetch('/api/default-font', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ font_path: fontPath })
        });

        const data = await response.json();

        if (data.success) {
            providerModalFontStatus.textContent = `Default font set to: ${fontName}`;
            providerModalFontStatus.style.display = 'block';
            providerModalFontStatus.style.color = '#10b981';

            // Re-render the fonts list to update the UI
            await renderProviderModalFontsList();

            // Hide status after 3 seconds
            setTimeout(() => {
                providerModalFontStatus.style.display = 'none';
            }, 3000);
        } else {
            providerModalFontStatus.textContent = 'Error: ' + data.error;
            providerModalFontStatus.style.color = '#ef4444';
            providerModalFontStatus.style.display = 'block';
        }
    } catch (error) {
        providerModalFontStatus.textContent = 'Failed to save: ' + error.message;
        providerModalFontStatus.style.color = '#ef4444';
        providerModalFontStatus.style.display = 'block';
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

// Filter Games by Search Query
function filterGames() {
    const searchQuery = gameSearch.value.toLowerCase().trim();

    // Clear current options
    gameSelect.innerHTML = '<option value="">Choose a game...</option>';

    // Filter games
    const filteredGames = allGames.filter(game => {
        const gameName = game.name.toLowerCase();
        const providerName = game.provider.toLowerCase();
        const fullText = `${providerName} ${gameName}`;
        return fullText.includes(searchQuery);
    });

    // Populate with filtered results
    filteredGames.forEach(game => {
        const option = document.createElement('option');
        option.value = game.path;
        option.textContent = `[${game.provider}] ${game.name}`;
        gameSelect.appendChild(option);
    });

    // Show count
    if (searchQuery && filteredGames.length === 0) {
        const option = document.createElement('option');
        option.disabled = true;
        option.textContent = 'No games found';
        gameSelect.appendChild(option);
    }
}

// Open Output Folder
async function openOutputFolder() {
    try {
        const response = await fetch('/api/open-output');
        const data = await response.json();

        if (!data.success) {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to open output folder: ' + error.message);
    }
}

// Game Selection
async function onGameSelect() {
    selectedGamePath = gameSelect.value;

    if (selectedGamePath) {
        const game = allGames.find(g => g.path === selectedGamePath);
        providerName.textContent = game.provider;
        gameName.textContent = game.name;
        gameInfo.style.display = 'block';
        generateBtn.disabled = false;

        // Clear old asset data first to prevent sending wrong filenames
        currentGameAssets = null;

        // Load available assets for this game and WAIT for completion
        await loadGameAssets(selectedGamePath);

        // Trigger initial live preview AFTER assets are loaded (only if we have a background)
        if (currentGameAssets && currentGameAssets.backgrounds && currentGameAssets.backgrounds.length > 0) {
            await updateLivePreview();
        } else {
            // Hide preview if no assets
            previewContainer.style.display = 'none';
        }
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

    // Populate background radio buttons
    if (currentGameAssets.backgrounds && currentGameAssets.backgrounds.length > 0) {
        backgroundCheckboxes.innerHTML = currentGameAssets.backgrounds.map((bg, index) =>
            `<div class="asset-checkbox-item">
                <input type="radio" name="background-choice" id="bg-${index}" value="${bg}" ${index === 0 ? 'checked' : ''}>
                <label for="bg-${index}">${bg}</label>
            </div>`
        ).join('');
        // Add change listeners to all radio buttons
        backgroundCheckboxes.querySelectorAll('input[type="radio"]').forEach(rb => {
            rb.addEventListener('change', debouncedPreview);
        });
        // Add preview tooltips
        backgroundCheckboxes.querySelectorAll('label').forEach((label, index) => {
            const bg = currentGameAssets.backgrounds[index];
            attachPreviewListeners(label, `Backgrounds/${bg}`, bg);
        });
        backgroundSelectGroup.style.display = 'block';
    } else {
        backgroundCheckboxes.innerHTML = '';
        backgroundSelectGroup.style.display = 'none';
    }

    // Populate character radio buttons
    if (currentGameAssets.characters && currentGameAssets.characters.length > 0) {
        characterCheckboxes.innerHTML = currentGameAssets.characters.map((char, index) =>
            `<div class="asset-checkbox-item">
                <input type="radio" name="character-choice" id="char-${index}" value="${char}" ${index === 0 ? 'checked' : ''}>
                <label for="char-${index}">${char}</label>
            </div>`
        ).join('');
        // Add change listeners to all radio buttons
        characterCheckboxes.querySelectorAll('input[type="radio"]').forEach(rb => {
            rb.addEventListener('change', debouncedPreview);
        });
        // Add preview tooltips
        characterCheckboxes.querySelectorAll('label').forEach((label, index) => {
            const char = currentGameAssets.characters[index];
            attachPreviewListeners(label, `Character/${char}`, char);
        });
        characterSelectGroup.style.display = 'block';
    } else {
        characterCheckboxes.innerHTML = '';
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

        // Background selection - get selected radio button
        const selectedBackground = backgroundCheckboxes.querySelector('input[type="radio"]:checked');
        if (selectedBackground) {
            asset_filenames.background = selectedBackground.value;
        }

        // Character selection - get selected radio button
        const selectedCharacter = characterCheckboxes.querySelector('input[type="radio"]:checked');
        if (selectedCharacter) {
            asset_filenames.characters = [selectedCharacter.value];
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

    // Add custom dimensions if enabled
    const customDimensionsCheckbox = document.getElementById('bulk-custom-dimensions');
    if (customDimensionsCheckbox && customDimensionsCheckbox.checked) {
        settings.canvas_width = parseInt(document.getElementById('bulk-canvas-width').value) || 440;
        settings.canvas_height = parseInt(document.getElementById('bulk-canvas-height').value) || 590;
    }

    return settings;
}

// Custom Dimensions Functions
function updateAspectRatio() {
    const width = parseInt(document.getElementById('bulk-canvas-width').value) || 440;
    const height = parseInt(document.getElementById('bulk-canvas-height').value) || 590;
    const ratio = (width / height).toFixed(2);
    const type = ratio > 1 ? 'Landscape' : ratio < 1 ? 'Portrait' : 'Square';
    document.getElementById('bulk-aspect-ratio').textContent = `${ratio}:1 (${type})`;
}

function setBulkDimensions(width, height) {
    document.getElementById('bulk-canvas-width').value = width;
    document.getElementById('bulk-canvas-height').value = height;
    updateAspectRatio();
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
        const response = await fetch('/api/generate-single', {
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
async function switchToSingleModeWithGame(game) {
    // Switch to single mode
    switchMode('single');

    // Find and select the game in the dropdown
    gameSelect.value = game.path;

    // Trigger game selection and wait for it to complete
    await onGameSelect();

    // Scroll to preview after assets load and preview renders
    setTimeout(() => {
        const previewContainer = document.getElementById('preview-container');
        if (previewContainer && previewContainer.style.display !== 'none') {
            previewContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
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

// ===================================================
// Asset Upload & Classification System
// ===================================================

// DOM elements shared with asset upload (in unified modal)
const selectFilesBtn = document.getElementById('select-files-btn');
const assetFilesInput = document.getElementById('asset-files-input');
const dropZone = document.getElementById('drop-zone');
const selectedFilesInfo = document.getElementById('selected-files-info');
const uploadProgress = document.getElementById('upload-progress');
const classificationResults = document.getElementById('classification-results');
const classificationTableBody = document.getElementById('classification-table-body');
const saveClassifiedAssetsBtn = document.getElementById('save-classified-assets-btn');
const cancelUploadBtn = document.getElementById('cancel-upload-btn');
const uploadStatus = document.getElementById('upload-status');

let uploadedFiles = [];
let classificationData = [];

// Event Listeners for asset upload (now in unified modal)

if (selectFilesBtn) {
    selectFilesBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        assetFilesInput.click();
    });
}

if (assetFilesInput) {
    assetFilesInput.addEventListener('change', handleFileSelection);
}

// Drag and Drop handlers
if (dropZone) {
    dropZone.addEventListener('click', () => {
        assetFilesInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');

        const files = Array.from(e.dataTransfer.files).filter(file =>
            file.type.startsWith('image/')
        );

        if (files.length > 0) {
            handleDroppedFiles(files);
        }
    });
}

if (saveClassifiedAssetsBtn) {
    saveClassifiedAssetsBtn.addEventListener('click', saveClassifiedAssets);
}

if (cancelUploadBtn) {
    cancelUploadBtn.addEventListener('click', () => {
        // Reset asset upload area in unified modal
        assetFilesInput.value = '';
        selectedFilesInfo.textContent = '';
        uploadProgress.style.display = 'none';
        classificationResults.style.display = 'none';
        uploadStatus.textContent = '';
        uploadedFiles = [];
        classificationData = [];
        classificationTableBody.innerHTML = '';
    });
}

async function handleFileSelection(event) {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    await processFiles(files);
}

async function handleDroppedFiles(files) {
    await processFiles(files);
}

async function processFiles(files) {
    uploadedFiles = files;
    selectedFilesInfo.textContent = `${files.length} file(s) selected`;

    // Show progress, hide drop zone
    uploadProgress.style.display = 'block';
    classificationResults.style.display = 'none';

    // Upload and analyze
    await uploadAndAnalyzeAssets(files);
}

async function uploadAndAnalyzeAssets(files) {
    try {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        // Get game path from asset target selector (unified modal) or fallback to selected game
        const targetGamePath = assetTargetGame.value || selectedGamePath;
        if (!targetGamePath) {
            uploadStatus.textContent = 'Error: No game selected';
            uploadStatus.style.color = '#ef4444';
            uploadProgress.style.display = 'none';
            return;
        }

        // Extract provider path from selected game path
        const pathParts = targetGamePath.split('/');
        const providerPath = pathParts[0]; // First part is provider

        formData.append('game_path', targetGamePath);
        formData.append('provider_path', providerPath);

        const response = await fetch('/api/upload-assets', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!data.success) {
            uploadStatus.textContent = 'Error: ' + data.error;
            uploadStatus.style.color = '#ef4444';
            uploadProgress.style.display = 'none';
            return;
        }

        // Store classification data
        classificationData = data.results;

        // Hide progress, show results
        uploadProgress.style.display = 'none';
        classificationResults.style.display = 'block';

        // Populate classification table
        populateClassificationTable(data.results);

    } catch (error) {
        uploadStatus.textContent = 'Failed to upload: ' + error.message;
        uploadStatus.style.color = '#ef4444';
        uploadProgress.style.display = 'none';
    }
}

function populateClassificationTable(results) {
    classificationTableBody.innerHTML = '';

    results.forEach((result, index) => {
        const row = document.createElement('tr');

        // Mark low confidence rows
        if (result.requires_manual) {
            row.style.backgroundColor = '#fef2f2';  // Light red
        }

        // Preview thumbnail
        const previewCell = document.createElement('td');
        if (result.thumbnail) {
            const img = document.createElement('img');
            img.src = result.thumbnail;
            img.style.width = '60px';
            img.style.height = '60px';
            img.style.objectFit = 'contain';
            previewCell.appendChild(img);
        }
        row.appendChild(previewCell);

        // Filename
        const filenameCell = document.createElement('td');
        filenameCell.textContent = result.filename;
        row.appendChild(filenameCell);

        // Detected type
        const typeCell = document.createElement('td');
        typeCell.textContent = result.detected_type || 'Unknown';
        if (result.requires_manual) {
            typeCell.style.color = '#dc2626';
            typeCell.style.fontWeight = 'bold';
        }
        row.appendChild(typeCell);

        // Confidence
        const confidenceCell = document.createElement('td');
        if (result.success) {
            confidenceCell.textContent = `${result.confidence.toFixed(0)}%`;
            if (result.requires_manual) {
                confidenceCell.style.color = '#dc2626';
            }
        } else {
            confidenceCell.textContent = 'Error';
            confidenceCell.style.color = '#dc2626';
        }
        row.appendChild(confidenceCell);

        // Override dropdown
        const overrideCell = document.createElement('td');
        const select = document.createElement('select');
        select.className = 'select-input';
        select.dataset.index = index;

        const options = [
            { value: 'background', label: 'Background' },
            { value: 'character', label: 'Character' },
            { value: 'title', label: 'Title' },
            { value: 'logo', label: 'Logo' }
        ];

        options.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.label;
            if (opt.value === result.detected_type) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        select.addEventListener('change', (e) => {
            classificationData[index].detected_type = e.target.value;
            classificationData[index].requires_manual = false;
            // Remove red highlighting
            row.style.backgroundColor = '';
            typeCell.style.color = '';
            typeCell.style.fontWeight = '';
            confidenceCell.style.color = '';
        });

        overrideCell.appendChild(select);
        row.appendChild(overrideCell);

        classificationTableBody.appendChild(row);
    });
}

async function saveClassifiedAssets() {
    // Check for items requiring manual classification
    const unclassified = classificationData.filter(item =>
        item.requires_manual && item.success
    );

    if (unclassified.length > 0) {
        alert(`Please classify ${unclassified.length} item(s) manually before saving`);
        return;
    }

    // Prepare classifications
    const classifications = classificationData
        .filter(item => item.success)
        .map(item => ({
            filename: item.filename,
            temp_filename: item.temp_filename,
            type: item.detected_type
        }));

    if (classifications.length === 0) {
        alert('No valid assets to save');
        return;
    }

    try {
        saveClassifiedAssetsBtn.disabled = true;
        uploadStatus.textContent = 'Saving assets...';
        uploadStatus.style.color = '#3b82f6';

        // Get game path from asset target selector (unified modal)
        const targetGamePath = assetTargetGame.value || selectedGamePath;
        if (!targetGamePath) {
            alert('No game selected');
            return;
        }

        // Extract provider path from selected game path
        const pathParts = targetGamePath.split('/');
        const providerPath = pathParts[0];

        const response = await fetch('/api/save-classified-assets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                game_path: targetGamePath,
                provider_path: providerPath,
                classifications: classifications
            })
        });

        const data = await response.json();

        if (data.success) {
            uploadStatus.textContent = data.message;
            uploadStatus.style.color = '#10b981';

            // Refresh game dropdown immediately
            await loadGames();
            await loadGamesForAssetTab();

            // Reset upload area after success
            setTimeout(() => {
                assetFilesInput.value = '';
                selectedFilesInfo.textContent = '';
                uploadProgress.style.display = 'none';
                classificationResults.style.display = 'none';
                uploadedFiles = [];
                classificationData = [];
                classificationTableBody.innerHTML = '';

                // Refresh asset lists
                loadGameAssets();
            }, 2000);
        } else {
            uploadStatus.textContent = 'Error: ' + (data.errors ? data.errors.join(', ') : data.error);
            uploadStatus.style.color = '#ef4444';
        }

    } catch (error) {
        uploadStatus.textContent = 'Failed to save: ' + error.message;
        uploadStatus.style.color = '#ef4444';
    } finally {
        saveClassifiedAssetsBtn.disabled = false;
    }
}

// ===================================================
// Create New Game System
// ===================================================

// DOM elements for create game modal
// ==================== UNIFIED CONTENT MANAGEMENT MODAL ====================
const manageContentBtn = document.getElementById('manage-content-btn');
const manageContentBulkBtn = document.getElementById('manage-content-bulk-btn');
const manageContentModal = document.getElementById('manage-content-modal');
const closeManageContentModal = document.getElementById('close-manage-content-modal');

// Tab buttons
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');

// Games tab elements
const newProviderSelect = document.getElementById('new-provider-select');
const newProviderToggleBtn = document.getElementById('new-provider-toggle-btn');
const newProviderInputGroup = document.getElementById('new-provider-input-group');
const newProviderName = document.getElementById('new-provider-name');
const newGameName = document.getElementById('new-game-name');
const createGameSubmitBtn = document.getElementById('create-game-submit-btn');
const createGameStatus = document.getElementById('create-game-status');

// Assets tab elements
const assetTargetGame = document.getElementById('asset-target-game');
const assetUploadArea = document.getElementById('asset-upload-area');

// Fonts tab elements
const fontFilesInput = document.getElementById('font-files-input');
const fontDropZone = document.getElementById('font-drop-zone');
const selectFontsBtn = document.getElementById('select-fonts-btn');
const selectedFontsInfo = document.getElementById('selected-fonts-info');
const fontUploadStatus = document.getElementById('font-upload-status');

let isCreatingNewProvider = false;
let currentTab = 'games';

// Event Listeners - Modal
if (manageContentBtn) {
    manageContentBtn.addEventListener('click', () => openManageContentModal('games'));
}

if (manageContentBulkBtn) {
    manageContentBulkBtn.addEventListener('click', () => openManageContentModal('games'));
}

if (closeManageContentModal) {
    closeManageContentModal.addEventListener('click', () => {
        manageContentModal.style.display = 'none';
        resetManageContentModal();
    });
}

// Close manage content modal when clicking outside
if (manageContentModal) {
    manageContentModal.addEventListener('click', (e) => {
        if (e.target === manageContentModal) {
            manageContentModal.style.display = 'none';
            resetManageContentModal();
        }
    });
}

// Provider font management in Manage Content modal
if (manageSaveProviderFontBtn) {
    manageSaveProviderFontBtn.addEventListener('click', saveManageProviderFont);
}

// Tab navigation
tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const targetTab = button.getAttribute('data-tab');
        switchTab(targetTab);
    });
});

// Games tab listeners
if (newProviderToggleBtn) {
    newProviderToggleBtn.addEventListener('click', toggleNewProvider);
}

if (createGameSubmitBtn) {
    createGameSubmitBtn.addEventListener('click', submitCreateGame);
}

// Assets tab listeners
if (assetTargetGame) {
    assetTargetGame.addEventListener('change', () => {
        if (assetTargetGame.value) {
            assetUploadArea.style.display = 'block';
        } else {
            assetUploadArea.style.display = 'none';
        }
    });
}

// Fonts tab listeners
if (selectFontsBtn) {
    selectFontsBtn.addEventListener('click', () => {
        fontFilesInput.click();
    });
}

if (fontFilesInput) {
    fontFilesInput.addEventListener('change', handleFontFilesSelected);
}

if (fontDropZone) {
    fontDropZone.addEventListener('click', () => {
        fontFilesInput.click();
    });

    fontDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        fontDropZone.classList.add('drag-over');
    });

    fontDropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        fontDropZone.classList.remove('drag-over');
    });

    fontDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        fontDropZone.classList.remove('drag-over');

        const files = Array.from(e.dataTransfer.files).filter(file =>
            file.name.endsWith('.ttf') || file.name.endsWith('.otf')
        );

        if (files.length > 0) {
            handleDroppedFonts(files);
        }
    });
}

// ===== Modal Functions =====
async function openManageContentModal(tab = 'games') {
    manageContentModal.style.display = 'flex';
    resetManageContentModal();
    switchTab(tab);

    // Load data for each tab
    await loadProviders();
    await loadGamesForAssetTab();
    await loadFonts(); // For default font dropdown
    await loadProviderFonts(); // For provider fonts

    // Populate fonts list and provider font dropdowns/list in Fonts tab
    await renderAllFontsList();
    populateManageProviderFontSelects();
    renderManageProviderFontsList();
}

function resetManageContentModal() {
    // Reset games tab
    newGameName.value = '';
    newProviderName.value = '';
    isCreatingNewProvider = false;
    newProviderInputGroup.style.display = 'none';
    newProviderToggleBtn.textContent = 'New Provider';
    createGameStatus.textContent = '';

    // Reset assets tab
    assetTargetGame.value = '';
    assetUploadArea.style.display = 'none';
    selectedFilesInfo.textContent = '';
    uploadProgress.style.display = 'none';
    classificationResults.style.display = 'none';
    classificationTableBody.innerHTML = '';

    // Reset fonts tab
    selectedFontsInfo.textContent = '';
    fontUploadStatus.textContent = '';
}

function switchTab(tabName) {
    currentTab = tabName;

    // Update tab buttons
    tabButtons.forEach(btn => {
        if (btn.getAttribute('data-tab') === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update tab content
    tabContents.forEach(content => {
        if (content.id === `tab-${tabName}`) {
            content.classList.add('active');
            content.style.display = 'block';
        } else {
            content.classList.remove('active');
            content.style.display = 'none';
        }
    });
}

async function loadGamesForAssetTab() {
    try {
        const response = await fetch('/api/games');
        const data = await response.json();

        if (data.success && data.games) {
            const options = data.games.map(game =>
                `<option value="${game.path}">${game.provider} - ${game.name}</option>`
            ).join('');
            assetTargetGame.innerHTML = '<option value="">Select a game...</option>' + options;
        }
    } catch (error) {
        console.error('Failed to load games for asset tab:', error);
    }
}

function toggleNewProvider() {
    isCreatingNewProvider = !isCreatingNewProvider;

    if (isCreatingNewProvider) {
        newProviderInputGroup.style.display = 'block';
        newProviderSelect.disabled = true;
        newProviderToggleBtn.textContent = 'Select Existing';
    } else {
        newProviderInputGroup.style.display = 'none';
        newProviderSelect.disabled = false;
        newProviderToggleBtn.textContent = 'New Provider';
    }
}

async function loadProviders() {
    try {
        const response = await fetch('/api/providers');
        const data = await response.json();

        if (data.success) {
            const options = data.providers.map(provider =>
                `<option value="${provider}">${provider}</option>`
            ).join('');
            newProviderSelect.innerHTML = '<option value="">-- Select Provider --</option>' + options;
        }
    } catch (error) {
        console.error('Failed to load providers:', error);
        newProviderSelect.innerHTML = '<option value="">Error loading providers</option>';
    }
}

async function submitCreateGame() {
    const gameName = newGameName.value.trim();

    if (!gameName) {
        alert('Please enter a game name');
        return;
    }

    let providerName;
    if (isCreatingNewProvider) {
        providerName = newProviderName.value.trim();
        if (!providerName) {
            alert('Please enter a provider name');
            return;
        }
    } else {
        providerName = newProviderSelect.value;
        if (!providerName) {
            alert('Please select a provider');
            return;
        }
    }

    try {
        createGameSubmitBtn.disabled = true;
        createGameStatus.textContent = 'Creating game...';
        createGameStatus.style.color = '#3b82f6';

        const response = await fetch('/api/create-game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider: providerName,
                game: gameName
            })
        });

        const data = await response.json();

        if (data.success) {
            createGameStatus.textContent = data.message;
            createGameStatus.style.color = '#10b981';

            // Refresh games list
            setTimeout(async () => {
                await loadGames();

                // Auto-select the new game
                if (data.game_path) {
                    gameSelect.value = data.game_path;
                    await onGameSelect();
                }

                // Switch to assets tab in unified modal
                switchTab('assets');

                // Auto-select the newly created game in assets tab
                assetTargetGame.value = data.game_path;
                assetUploadArea.style.display = 'block';
            }, 1500);
        } else {
            createGameStatus.textContent = 'Error: ' + data.error;
            createGameStatus.style.color = '#ef4444';
        }

    } catch (error) {
        createGameStatus.textContent = 'Failed to create game: ' + error.message;
        createGameStatus.style.color = '#ef4444';
    } finally {
        createGameSubmitBtn.disabled = false;
    }
}

// ===== Font Upload Functions =====
function handleFontFilesSelected(event) {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
        uploadFonts(files);
    }
}

function handleDroppedFonts(files) {
    uploadFonts(files);
}

async function uploadFonts(files) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });

    selectedFontsInfo.textContent = `Uploading ${files.length} font(s)...`;
    selectedFontsInfo.style.color = '#3b82f6';
    fontUploadStatus.textContent = '';

    try {
        const response = await fetch('/api/upload-fonts', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            selectedFontsInfo.textContent = '';
            fontUploadStatus.textContent = data.message;
            fontUploadStatus.style.color = '#10b981';

            // Reload font lists
            await loadFonts();
            await loadProviderFonts();

            // Clear file input
            fontFilesInput.value = '';

            setTimeout(() => {
                fontUploadStatus.textContent = '';
            }, 3000);
        } else {
            fontUploadStatus.textContent = 'Error: ' + (data.error || 'Upload failed');
            fontUploadStatus.style.color = '#ef4444';
            selectedFontsInfo.textContent = '';
        }
    } catch (error) {
        console.error('Font upload error:', error);
        fontUploadStatus.textContent = 'Error: ' + error.message;
        fontUploadStatus.style.color = '#ef4444';
        selectedFontsInfo.textContent = '';
    }
}

// ===== Asset Preview Tooltip =====
let previewTooltip = null;

function createPreviewTooltip() {
    const tooltip = document.createElement('div');
    tooltip.className = 'asset-preview-tooltip';
    tooltip.style.display = 'none';
    document.body.appendChild(tooltip);
    return tooltip;
}

function showAssetPreview(assetPath, filename, event) {
    if (!previewTooltip) {
        previewTooltip = createPreviewTooltip();
        console.log('Created tooltip:', previewTooltip);
    }

    const gamePath = gameSelect.value;
    if (!gamePath) return;

    // Normalize path separators to forward slashes
    const normalizedGamePath = gamePath.replace(/\\/g, '/');
    const normalizedAssetPath = assetPath.replace(/\\/g, '/');

    const previewUrl = `/api/asset-preview?game=${encodeURIComponent(normalizedGamePath)}&asset=${encodeURIComponent(normalizedAssetPath)}`;

    previewTooltip.innerHTML = `
        <img src="${previewUrl}" alt="${filename}" onerror="console.error('Preview failed:', this.src)">
        <div class="filename">${filename}</div>
    `;

    previewTooltip.style.display = 'block';
    console.log('Tooltip display:', previewTooltip.style.display);
    console.log('Tooltip position:', previewTooltip.style.left, previewTooltip.style.top);
    updateTooltipPosition(event);
    console.log('After position update:', previewTooltip.style.left, previewTooltip.style.top);
}

function hideAssetPreview() {
    if (previewTooltip) {
        previewTooltip.style.display = 'none';
    }
}

function updateTooltipPosition(event) {
    if (!previewTooltip) return;

    const tooltipWidth = 300;
    const tooltipHeight = 250;
    const margin = 15;

    let x = event.clientX + margin;
    let y = event.clientY + margin;

    // Keep tooltip within viewport
    if (x + tooltipWidth > window.innerWidth) {
        x = event.clientX - tooltipWidth - margin;
    }

    if (y + tooltipHeight > window.innerHeight) {
        y = event.clientY - tooltipHeight - margin;
    }

    previewTooltip.style.left = x + 'px';
    previewTooltip.style.top = y + 'px';
}

function attachPreviewListeners(label, assetPath, filename) {
    label.addEventListener('mouseenter', (e) => showAssetPreview(assetPath, filename, e));
    label.addEventListener('mousemove', updateTooltipPosition);
    label.addEventListener('mouseleave', hideAssetPreview);
}

// Cache bust 5 - reset dropdown selections on game switch
