let socket = io();;
// Main initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSocketIO();
    initializeTaskManager();
    initializeNavigation();
    loadPageSpecificFunctions();
    initializeLoggingDrawer()

    
Pace.options = {
    startOnPageLoad: true,
    restartOnRequestAfter: false,
    ajax: false
};

Pace.on('done', function() {
    document.body.classList.remove('pace-running');
    document.body.classList.add('pace-done');
});
});

// Socket.IO initialization
function initializeSocketIO() {

    socket.on('log_update', function(data) {
        const terminal = document.getElementById('terminal-output');
        terminal.innerHTML += data.data + '\n';
        terminal.scrollTop = terminal.scrollHeight;
    });

    socket.on('progress_update', function(data) {
        const progressBar = document.getElementById(data.type + '-progress');
        const label = document.querySelector(`label[for="${data.type}-progress"]`);
        
        if (progressBar && progressBar.dataset.chart) {
            const chart = window[progressBar.dataset.chart];
            chart.updateProgress(data.value, data.max);
        }
        
        if (label) {
            label.textContent = data.label;
        }
    });

    socket.on('playlists_updated', function() {
        updateLists();
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
        
        Object.values(statusElements).forEach(elementId => {
            //console.log('Setting red for:', elementId);
            const element = document.getElementById(elementId);
            if (element) {
                element.classList.remove('uk-card-primary');
                element.classList.add('uk-card-secondary');
            }
        });
        
        data.updated_files.forEach(file => {
            if (statusElements[file]) {
                //console.log('Setting green for:', statusElements[file]);
                const element = document.getElementById(statusElements[file]);
                if (element) {
                    element.classList.remove('uk-card-secondary');
                    element.classList.add('uk-card-primary');
                }
            }
        });
    });
    
}

// Taskmanager Initialization
function initializeTaskManager() {
    const socket = io();
    const threadModal = document.getElementById('thread-modal');
    const activeThreadsContainer = document.getElementById('active-threads');
    const template = document.getElementById('task-card-template');

    function updateTasks() {
        fetch('/api/threads')
            .then(response => response.json())
            .then(threads => {
                updateThreadCount(Object.keys(threads).length);
                activeThreadsContainer.innerHTML = '';
                Object.entries(threads).forEach(([name, thread]) => {
                    const card = template.content.cloneNode(true);
                    
                    card.querySelector('.task-name').textContent = name;
                    card.querySelector('.task-status').textContent = `Status: ${thread.status}`;
                    
                    const pauseBtn = card.querySelector('.pause-task');
                    const resumeBtn = card.querySelector('.resume-task');
                    
                    if (thread.status === 'paused') {
                        pauseBtn.style.display = 'none';
                        resumeBtn.style.display = 'inline-block';
                    } else {
                        pauseBtn.style.display = 'inline-block';
                        resumeBtn.style.display = 'none';
                    }

                    pauseBtn.onclick = () => {
                        fetch(`/api/threads/${name}/pause`).then(() => updateTasks());
                    };

                    resumeBtn.onclick = () => {
                        fetch(`/api/threads/${name}/resume`).then(() => updateTasks());
                    };

                    card.querySelector('.stop-task').onclick = () => {
                        fetch(`/api/threads/${name}/stop`).then(() => updateTasks());
                    };

                    activeThreadsContainer.appendChild(card);
                });
            });
    }

    // Listen for thread events
    socket.on('thread_started', updateTasks);
    socket.on('thread_stopped', updateTasks);
    socket.on('thread_status_changed', updateTasks);
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

function initializeDonutCharts(chartIds) {
    chartIds.forEach(id => {
        const chartContainer = document.getElementById(`${id}-progress`);
        if (chartContainer) {
            const chartOptions = {
                height: parseInt(chartContainer.dataset.height || 180),
                colors: JSON.parse(chartContainer.dataset.colors || '["#ee0979"]'),
                gradientColors: JSON.parse(chartContainer.dataset.gradientColors || '["#ffd200"]'),
                label: chartContainer.dataset.labelFormat || `${id} Progress`
            };
            
            const chart = createProgressChart(`#${id}-progress`, chartOptions);
            window[chartContainer.dataset.chart] = chart;
            chart.updateProgress(0);
        }
    });
}
// Scraper Controls
function initScraperControls() {
    const charts = ['overall', 'playlist', 'song'];
    initializeDonutCharts(charts);

    const addUrlBtn = document.getElementById('add-url');
    const urlInput = document.getElementById('url-input');

    // Load collection toggle states
    fetch('/api/collections/status')
    .then(response => response.json())
    .then(data => {
        Object.entries(data).forEach(([collection, enabled]) => {
            const toggle = document.querySelector(`#${collection}-toggle`);
            if (toggle) {
                toggle.checked = enabled;
            }
        });
    });

    if (addUrlBtn) {
        addUrlBtn.addEventListener('click', () => {
            const url = urlInput.value;
            const type = detectUrlType(url);
            if (type) {
                fetch('/api/urls/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, type })
                })
                .then(response => response.json())
                .then(() => {
                    updateUrlLists();
                    urlInput.value = '';
                });
            }
        });
    }

    const scrapingActions = {
        'scrape-collections': '/api/scrape/collections',         // Collect playlists, artists, styles
        'scrape-song-urls': '/api/scrape/song-urls',               // Fetch only song URLs from collections
        'scrape-songs': '/api/scrape/songs'                     // Scrape song details (title, lyrics, etc.)
    };

    // Add collection toggle handlers
    document.querySelectorAll('.collection-toggle').forEach(toggle => {
        toggle.addEventListener('change', function() {
            toggleCollection(this.dataset.collection, this.checked);
        });
    });

    // Add event listeners to buttons for each scraping action
    Object.entries(scrapingActions).forEach(([id, endpoint]) => {
        const button = document.getElementById(id);
        if (button) {
            button.addEventListener('click', () => {
                fetch(endpoint, { method: 'POST' })
                    .then(response => response.text())
                    .then(text => {
                        try {
                            return JSON.parse(text);
                        } catch {
                            return { message: text };
                        }
                    })
                    .then(data => console.log(`Started ${id}:`, data));
            });
        }
    });

    // Initial load of lists and setup of controls
    updateUrlLists();
    initializeCollectionControls();

    // Setup WebSocket listeners for updates
    socket.on('playlists_updated', updateUrlLists);
    socket.on('thread_status_changed', updateUrlLists);
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
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            const displayElement = document.getElementById('display_' + this.id);
            displayElement.value = this.files[0].name;
        });
    });
    document.querySelectorAll('.collection-toggle').forEach(toggle => {
        toggle.addEventListener('change', function() {
            toggleCollection(this.dataset.collection, this.checked);
        });
    });


    // Load current settings when page loads
    fetch('/api/settings')
        .then(response => response.json())
        .then(settings => {
            socket.emit('log_update', { data: 'Loading settings...' });
            document.querySelectorAll('[data-category][data-key]').forEach(input => {
                const category = input.dataset.category;
                const key = input.dataset.key;
                if (settings[category] && settings[category][key] !== undefined) {
                    if (input.type === 'checkbox') {
                        input.checked = settings[category][key];
                    } else {
                        input.value = settings[category][key];
                    }
                    socket.emit('log_update', { data: `Loaded setting: ${category}.${key} = ${settings[category][key]}` });
                }
            });
            socket.emit('log_update', { data: 'Settings loaded successfully' });
        });

    // Save settings button
    const saveSettingsBtn = document.getElementById('save-settings');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', function() {
            const settings = {};
            socket.emit('log_update', { data: 'Collecting settings...' });

            document.querySelectorAll('[data-category][data-key]').forEach(input => {
                const category = input.dataset.category;
                const key = input.dataset.key;

                if (!settings[category]) {
                    settings[category] = {};
                }

                settings[category][key] = input.type === 'checkbox' ? input.checked : input.value;
                socket.emit('log_update', { data: `Setting ${category}.${key} = ${settings[category][key]}` });
            });

            fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                socket.emit('log_update', { data: 'Settings saved successfully' });
            });
        });
    }
    // Reset settings button
    const resetSettingsBtn = document.getElementById('reset-settings');
    if (resetSettingsBtn) {
        resetSettingsBtn.addEventListener('click', function() {
            if (confirm('Reset all settings to default values?')) {
                socket.emit('log_update', { data: 'Resetting settings to defaults...' });
                fetch('/api/settings/reset', { method: 'POST' })
                    .then(response => response.json())
                    .then(() => {
                        socket.emit('log_update', { data: 'Settings reset to defaults' });
                        window.location.reload();
                    });
            }
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

function updateThreadCount(count) {
    const threadCountElement = document.getElementById('thread-count');
    if (threadCountElement) {
        threadCountElement.textContent = count;
    }
}

function createProgressChart(elementId, options = {}) {
    const element = document.querySelector(elementId);
    const displayType = element.dataset.displayType || 'percentage';
    
    let currentValue = 0;
    let maxValue = 0;
    
    const defaultOptions = {
        series: [0],
        height: options.height || 280,
        colors: options.colors || ["#ee0979"],
        gradientColors: options.gradientColors || ['#ffd200']
    };

    const chartOptions = {
        series: [0],
        chart: {
            height: defaultOptions.height,
            type: 'radialBar',
            toolbar: { show: false }
        },
        plotOptions: {
            radialBar: {
                startAngle: -135,
                endAngle: 135,
                hollow: {
                    size: '70%'
                },
                track: {
                    background: 'rgba(0, 0, 0, 0.1)',
                    strokeWidth: '67%'
                },
                dataLabels: {
                    show: true,
                    name: {
                        show: false
                    },
                    value: {
                        show: true,
                        fontSize: '24px',
                        formatter: function() {
                            if (displayType === 'percentage') {
                                const percentage = maxValue > 0 ? Math.round((currentValue / maxValue) * 100) : 0;
                                return `${percentage}%`;
                            }
                            return `${currentValue}/${maxValue || 0}`;
                        }
                    }
                }
            }
        },
        fill: {
            type: 'gradient',
            gradient: {
                shade: 'dark',
                type: 'horizontal',
                gradientToColors: defaultOptions.gradientColors,
                stops: [0, 100]
            }
        },
        colors: defaultOptions.colors
    };

    const chart = new ApexCharts(document.querySelector(elementId), chartOptions);
    chart.render();
    
    return {
        updateProgress: (value, max) => {
            currentValue = value;
            maxValue = max;
            const percentage = max > 0 ? (value / max) * 100 : 0;
            chart.updateSeries([percentage]);
        }
    };
}

function copyLogToClipboard() {
    const logContent = document.getElementById('terminal-output').textContent;
    navigator.clipboard.writeText(logContent)
        .then(() => alert('Log copied to clipboard!'));
}

function initializeThemeSwitcher() {
    const themeInputs = document.querySelectorAll('input[name="theme-options"]');
    
    themeInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.checked) {
                const selectedTheme = this.dataset.theme;
                document.documentElement.setAttribute('data-bs-theme', selectedTheme);
                localStorage.setItem('selectedTheme', selectedTheme);
            }
        });
    });
    
    // Load saved theme
    const savedTheme = localStorage.getItem('selectedTheme') || 'blue-theme';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    
    // Check the corresponding radio button
    const savedThemeInput = document.querySelector(`input[data-theme="${savedTheme}"]`);
    if (savedThemeInput) {
        savedThemeInput.checked = true;
    }
}

function initializeLoggingDrawer(){
    const handle = document.getElementById('logDrawerHandle');
    const minHandle = document.getElementById('logDrawerMinHandle');
    const maxHandle = document.getElementById('logDrawerMaxHandle');
    const drawer = document.getElementById('logDrawer');
    const spacer = document.getElementById('logDrawerSpacer');
    
    handle.addEventListener('click', () => {
        drawer.classList.remove('expanded');
        drawer.classList.remove('minimized');
        spacer.classList.add('normal');
        spacer.classList.remove('minimized');
    });
    minHandle.addEventListener('click', () => {
        drawer.classList.add('minimized');
        drawer.classList.remove('expanded');
        spacer.classList.remove('normal');
        spacer.classList.add('minimized');
    });
    maxHandle.addEventListener('click', () => {
        drawer.classList.add('expanded');
        drawer.classList.remove('minimized');
    });
}

function handleCollectionControls(e) {
    const button = e.target.closest('button');
    if (!button) return;

    const item = button.closest('.list-group-item');
    if (!item) return;

    const url = item.dataset.url;
    if (!url) return;

    e.preventDefault();
    e.stopPropagation();
    button.disabled = true;

    if (button.classList.contains('toggle-status')) {
        fetch(`/api/urls/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const icon = button.querySelector('i');
                icon.classList.toggle('text-success');
                icon.classList.toggle('text-danger');
                updateUrlLists();
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            button.disabled = false;
        });
    } else if (button.classList.contains('reload-url')) {
        fetch('/api/scrape/single-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        })
        .finally(() => {
            button.disabled = false;
        });
    } else if (button.classList.contains('delete-url')) {
        if (confirm('Delete this URL?')) {
            fetch(`/api/urls/delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            })
            .then(() => updateUrlLists())
            .finally(() => {
                button.disabled = false;
            });
        } else {
            button.disabled = false;
        }
    }
}

function initializeCollectionControls() {
    document.removeEventListener('click', handleCollectionControls);
    document.addEventListener('click', handleCollectionControls);
}

function updateLists() {
    fetch('/api/playlists/all')
        .then(response => response.json())
        .then(data => {
            updateListContent('auto-playlists-list', data.auto_playlists);
            updateListContent('manual-playlists-list', data.manual_playlists);
            updateListContent('manual-songs-list', data.manual_songs);
        });
}

function updateListContent(elementId, data) {
    const container = document.getElementById(elementId);
    if (!container) return;

    container.innerHTML = Object.entries(data || {})
        .map(([url, info]) => `
            <div class="list-group-item" data-url="${url}" data-id="${url}">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="flex-grow-1 me-2">
                        ${info.song_urls && info.song_urls.length > 0 ?
                            `<span class="toggle-children" style="cursor: pointer;">▶</span> ` :
                            ''
                        }
                        <strong>${info.title || 'Untitled'} - </strong><small>${url}</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge ${info.processed ? 'bg-success' : 'bg-warning'}">
                            ${info.processed ? 'Processed' : 'Pending'}
                        </span>
                        <div class="item-controls">
                            <button class="btn btn-sm toggle-status" title="Toggle scraping status">
                                <i class="bi bi-circle-fill ${info.enabled ? 'text-success' : 'text-danger'}"></i>
                            </button>
                            <button class="btn btn-sm reload-url" title="Reload this URL">
                                <i class="bi bi-arrow-clockwise"></i>
                            </button>
                            <button class="btn btn-sm delete-url" title="Delete URL">
                                <i class="bi bi-trash text-danger"></i>
                            </button>
                        </div>
                    </div>
                </div>
                ${info.song_urls && info.song_urls.length > 0 ? `
                <div class="item-children" style="display: none; margin-left: 20px;">
                    ${info.song_urls.map(song => `
                        <div class="song-item mt-2 d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${song.title || 'Untitled'}</strong> - <small>${song.url}</small>

                            </div>
                            <div class="d-flex align-items-center gap-2">
                                <span class="badge ${song.processed ? 'bg-success' : 'bg-warning'}">
                                    ${song.processed ? 'Processed' : 'Pending'}
                                </span>
                                <div class="item-controls">
                                    <button class="btn btn-sm toggle-song-status" title="Toggle song scraping status">
                                        <i class="bi bi-circle-fill ${song.enabled ? 'text-success' : 'text-danger'}"></i>
                                    </button>
                                    <button class="btn btn-sm reload-song" title="Reload song data">
                                        <i class="bi bi-arrow-clockwise"></i>
                                    </button>
                                    <button class="btn btn-sm delete-song" title="Delete song">
                                        <i class="bi bi-trash text-danger"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            </div>
        `).join('');

    // Add click handlers for toggles
    container.querySelectorAll('.toggle-children').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const children = this.closest('.list-group-item').querySelector('.item-children');
            const isHidden = children.style.display === 'none';
            children.style.display = isHidden ? 'block' : 'none';
            this.textContent = isHidden ? '▼' : '▶';
        });
    });

    initializeCollectionControls();
}

function detectUrlType(url) {
    if (url.includes('/playlist/')) return 'playlist';
    if (url.includes('/song/')) return 'song';
    if (url.includes('/@')) return 'artist';
    if (url.includes('/style/')) return 'genre';
    return null;
}

function addUrl() {
    const url = document.getElementById('url-input').value;
    const type = detectUrlType(url);
    if (!type) {
        UIkit.notification('Invalid URL format', {status: 'danger'});
        return;
    }

    fetch('/api/urls/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, type })
    }).then(response => response.json())
    .then(data => updateUrlLists());
}

function updateUrlLists() {
    fetch('/api/urls/all')
        .then(response => response.json())
        .then(data => {
            socket.emit('log_update', { data: `Received data: ${JSON.stringify(data)}` });
            // Update each accordion section
            updateListContent('playlists-list', data.playlists);
            updateListContent('songs-list', data.songs);
            updateListContent('artists-list', data.artists);
            updateListContent('styles-list', data.genres);
        });
}

function addListItemEventListeners(container) {
    container.querySelectorAll('.toggle-children').forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            const itemChildren = e.target.closest('.list-item').querySelector('.item-children');
            if (itemChildren) {
                itemChildren.classList.toggle('hidden');
                e.target.textContent = itemChildren.classList.contains('hidden') ? '▶' : '▼';
            }
        });
    });

    container.querySelectorAll('.reload-url').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const url = e.target.closest('.list-item').dataset.url;
            fetch('/api/urls/reload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            }).then(() => updateUrlLists());
        });
    });

    container.querySelectorAll('.delete-url').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const url = e.target.closest('.list-item').dataset.url;
            if (confirm('Are you sure you want to delete this item?')) {
                fetch('/api/urls/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                }).then(() => updateUrlLists());
            }
        });
    });

    container.querySelectorAll('.form-check-input').forEach(toggle => {
        toggle.addEventListener('change', (e) => {
            const url = e.target.closest('.list-item').dataset.url;
            fetch('/api/urls/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    enabled: e.target.checked
                })
            });
        });
    });
}

function handleLoginClick() {
    fetch('/api/browser/open-login', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        socket.emit('log_update', { data: 'Opening login browser...' });
    });
}


function toggleCollection(collection, enabled) {
    fetch('/api/urls/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            type: collection,
            enabled: enabled
        })
    })
    .then(response => response.json())
    .then(data => {
        socket.emit('log_update', { data: `Collection ${collection} ${enabled ? 'enabled' : 'disabled'}` });
        updateUrlLists();
    });
}

