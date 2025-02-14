// Main initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSocketIO();
    initializeTaskManager();
    initializeNavigation();
    loadPageSpecificFunctions();
    initializeLoggingDrawer()
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
        const label = document.querySelector(`label[for="${data.type}-progress"]`);
        
        if (progressBar && progressBar.dataset.chart) {
            const chart = window[progressBar.dataset.chart];
            chart.updateProgress(data.value, data.max);
        }
        
        if (label) {
            label.textContent = data.label;
        }
    });

    socket.on('song_info_update', function(data) {
        document.getElementById('song-url').textContent = data.song_url;
        document.getElementById('playlist-url').textContent = data.playlist_url;
        document.getElementById('song-title').textContent = data.title;
        document.getElementById('song-styles').textContent = data.styles.join(', ');
    });

    socket.on('file_updates', function(data) {
        //console.log('File updates received:', data);
        
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
    const playlistsBtn = document.getElementById('scrape-playlists');
    const songsBtn = document.getElementById('scrape-songs');
    const charts = ['overall', 'playlist', 'song'];
   
    initializeDonutCharts(charts);
    
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

    function initScraperControls() {
        // Existing scraper controls...
        
        // Add URL management
        const urlInput = document.getElementById('url-input');
        const urlType = document.getElementById('url-type');
        const addUrlBtn = document.getElementById('add-url');
        
        function loadUrls() {
            fetch('/api/urls/playlists')
                .then(response => response.json())
                .then(data => {
                    updateUrlDisplay('auto-playlists-content', data.auto);
                    updateUrlDisplay('manual-playlists-content', data.manual);
                });
                
            fetch('/api/urls/songs')
                .then(response => response.json())
                .then(songs => {
                    updateSongDisplay('manual-songs-content', songs);
                });
        }
        
        function updateUrlDisplay(containerId, playlists) {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            
            Object.entries(playlists).forEach(([playlistUrl, data]) => {
                const playlistDiv = document.createElement('div');
                playlistDiv.className = 'playlist-item';
                playlistDiv.innerHTML = `
                    <div class="playlist-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
                        <i class="material-icons">playlist_play</i>
                        <span>${playlistUrl}</span>
                    </div>
                    <div class="song-list hidden">
                        ${data.song_urls.map(url => `
                            <div class="song-item">
                                <i class="material-icons">music_note</i>
                                <span>${url}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
                container.appendChild(playlistDiv);
            });
        }
        
        function updateSongDisplay(containerId, songs) {
            const container = document.getElementById(containerId);
            container.innerHTML = songs.map(url => `
                <div class="song-item">
                    <i class="material-icons">music_note</i>
                    <span>${url}</span>
                </div>
            `).join('');
        }
        
        if (addUrlBtn) {
            addUrlBtn.addEventListener('click', () => {
                const url = urlInput.value.trim();
                const type = urlType.value;
                
                if (url) {
                    fetch('/api/urls/add', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, type })
                    })
                    .then(() => {
                        urlInput.value = '';
                        loadUrls();
                    });
                }
            });
            
            // Initial load
            loadUrls();
        }
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
    const expandHandle = document.getElementById('logDrawerExpandHandle');
    const normalHandle = document.getElementById('logDrawerNormalHandle');
    const minHandle = document.getElementById('logDrawerMinHandle');
    const drawer = document.getElementById('logDrawer');
    
    normalHandle.addEventListener('click', () => {
        drawer.classList.remove('expanded')
        drawer.classList.remove('minimized');
    });
    expandHandle.addEventListener('click', () => {
        drawer.classList.remove('minimized')
        drawer.classList.add('expanded');

    });
    minHandle.addEventListener('click', () => {
        drawer.classList.remove('expanded')
        drawer.classList.add('minimized');
    });
}

