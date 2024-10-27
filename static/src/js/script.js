// Main initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSocketIO();
    initializeNavigation();
    loadPageSpecificFunctions();
});

// Socket.IO initialization
function initializeSocketIO() {
    const socket = io();
    
    socket.on('log_update', function(data) {
        const terminal = document.getElementById('terminal-output');
        terminal.innerHTML += data.data + '\n';
        terminal.scrollTop = terminal.scrollHeight;
    });

    socket.on('progress_update', function(data) {
        const progressBar = document.getElementById(data.type + '-progress');
        progressBar.value = data.value;
        progressBar.max = data.max;
    });

    socket.on('song_info_update', function(data) {
        document.getElementById('song-url').textContent = data.song_url;
        document.getElementById('playlist-url').textContent = data.playlist_url;
        document.getElementById('song-title').textContent = data.title;
        document.getElementById('song-styles').textContent = data.styles.join(', ');
    });
    
    socket.on('file_updates', function(data) {
        const statusElements = {
            'all_meta_tags.json': 'meta-status',
            'all_styles.json': 'styles-status',
            'song_meta_mapping.json': 'meta-mapping-status',
            'song_styles_mapping.json': 'styles-mapping-status'
        };
        
        for (const file of data.updated_files) {
            if (statusElements[file]) {
                document.getElementById(statusElements[file]).classList.add('uk-card-primary');
                document.getElementById(statusElements[file]).classList.remove('uk-card-secondary');
            }
        }
    });
}

// AJAX Navigation
function initializeNavigation() {
    document.querySelectorAll('a[data-ajax="true"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('href');
            
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                document.getElementById('main-content').innerHTML = html;
                // Update URL without page reload
                history.pushState({}, '', url);
                loadPageSpecificFunctions();
            });
        });
    });
}


// Page-specific function loader
function loadPageSpecificFunctions() {
    // Get current page from URL path
    const path = window.location.pathname;
    const currentPage = path.split('/').pop() || 'home';
    
    // Remove existing event listeners
    removeExistingListeners();
    
    // Load page-specific functions
    switch(currentPage) {
        case 'scrape':
            initScraperControls();
            break;
        case 'prepare':
            initPreparationControls();
            break;
        case 'train':
            initTrainingControls();
            break;
        case 'generate':
            initGenerationControls();
            break;
        case 'settings':
            initSettingsControls();
            break;
    }
}

// Scraper Controls
function initScraperControls() {
    const playlistsBtn = document.getElementById('scrape-playlists');
    const songsBtn = document.getElementById('scrape-songs');
    
    if (playlistsBtn) {
        playlistsBtn.addEventListener('click', function() {
            fetch('/api/scrape/playlists', { method: 'POST' })
                .then(response => response.text())  // Get text first
                .then(text => {
                    try {
                        return JSON.parse(text);  // Try to parse as JSON
                    } catch {
                        return { message: text };  // If not JSON, wrap in object
                    }
                })
                .then(data => console.log('Started playlist scraping:', data));
        });
    }
    
    if (songsBtn) {
        songsBtn.addEventListener('click', function() {
            fetch('/api/scrape/songs', { method: 'POST' })
                .then(response => response.text())
                .then(text => {
                    try {
                        return JSON.parse(text);
                    } catch {
                        return { message: text };
                    }
                })
                .then(data => console.log('Started song scraping:', data));
        });
    }
}

// Preparation Controls
function initPreparationControls() {
    const prepareBtn = document.getElementById('prepare-data');
    if (prepareBtn) {
        prepareBtn.addEventListener('click', function() {
            fetch('/api/prepare', { method: 'POST' })
                .then(response => response.json())
                .then(data => console.log('Started data preparation'));
        });
    }
}

// Training Controls
function initTrainingControls() {
    const startTrainingBtn = document.getElementById('start-training');
    const stopTrainingBtn = document.getElementById('stop-training');
    
    if (startTrainingBtn) {
        startTrainingBtn.addEventListener('click', function() {
            const trainingData = collectTrainingParameters();
            fetch('/api/train/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(trainingData)
            })
            .then(response => response.json())
            .then(data => console.log('Started training'));
        });
    }
    
    if (stopTrainingBtn) {
        stopTrainingBtn.addEventListener('click', function() {
            fetch('/api/train/stop', { method: 'POST' });
        });
    }
}

// Generation Controls
function initGenerationControls() {
    const generateBtn = document.getElementById('generate-lyrics');
    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            const generationData = {
                model: document.getElementById('model-select').value,
                title: document.getElementById('song-title').value,
                style: document.getElementById('style-input').value,
                prompt: document.getElementById('prompt-input').value
            };
            
            fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(generationData)
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('generation-output').textContent = data.lyrics;
            });
        });
    }
}

// Settings Controls
function initSettingsControls() {
    const saveSettingsBtn = document.getElementById('save-settings');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', function() {
            const settings = collectSettingsData();
            fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => console.log('Settings saved'));
        });
    }
}

// Helper Functions
function removeExistingListeners() {
    const buttons = document.querySelectorAll('button[data-initialized]');
    buttons.forEach(button => {
        const clone = button.cloneNode(true);
        button.parentNode.replaceChild(clone, button);
    });
}

function updateProgress(data) {
    const progressBar = document.getElementById(`${data.type}-progress`);
    if (progressBar) {
        progressBar.value = data.value;
        progressBar.max = data.max;
    }
}

function updateSongInfo(data) {
    Object.entries(data).forEach(([key, value]) => {
        const element = document.getElementById(`song-${key}`);
        if (element) {
            element.textContent = Array.isArray(value) ? value.join(', ') : value;
        }
    });
}

function collectTrainingParameters() {
    return {
        epochs: document.getElementById('epochs').value,
        learningRate: document.getElementById('learning-rate').value,
        batchSize: document.getElementById('batch-size').value,
        maxLength: document.getElementById('max-length').value,
        warmupSteps: document.getElementById('warmup-steps').value,
        weightDecay: document.getElementById('weight-decay').value,
        gradientAccumulationSteps: document.getElementById('gradient-accumulation-steps').value
    };
}

function collectSettingsData() {
    return {
        setting1: document.getElementById('setting1').value,
        setting2: document.getElementById('setting2').value
    };
}
