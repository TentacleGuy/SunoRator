document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('a[data-ajax="true"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const url = this.getAttribute('href');
            
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    document.getElementById('main-content').innerHTML = html;
                })
                .catch(error => console.error('Error loading content:', error));
                console.log(url);
        });
    });

    const socket = io();
    const terminalOutput =  document.getElementById('terminal-output');
    const progressBars = {
        overall: document.getElementById('overall-progress'),
        playlist: document.getElementById('playlist-progress'),
        song: document.getElementById('song-progress')
    };

    // WebSocket logging
    socket.on('log_update', function(msg) {
        if (terminalOutput) {
            terminalOutput.innerHTML += msg.data + '\n';
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
    });

    socket.on('progress_update', function(data) {
        const bar = progressBars[data.type];
        if (bar) {
            bar.value = data.value;
            bar.max = data.max;
        }
    });

    socket.on('song_info_update', function(data) {
        updateSongInfo(data);
    });

    
    function updateSongInfo(data) {
        document.getElementById('song-url').textContent = data.song_url || '';
        document.getElementById('playlist-url').textContent = data.playlist_url || '';
        document.getElementById('song-title').textContent = data.title || '';
        document.getElementById('song-styles').textContent = data.styles?.join(', ') || '';
    }
        // Handle scraper controls
    if (document.getElementById('scrape-playlists')) {
        initScraperControls();
    }
    
    // Handle preparation controls
    if (document.getElementById('prepare-data')) {
        initPreparationControls();
    }
    
    // Handle training controls
    if (document.getElementById('start-training')) {
        initTrainingControls();
    }
    
    // Handle generation controls
    if (document.getElementById('generate-lyrics')) {
        initGenerationControls();
    }



    function initScraperControls() {
        document.getElementById('scrape-playlists')?.addEventListener('click', function() {
            fetch('/api/scrape/playlists')
                .then(response => response.json())
                .then(data => {
                    console.log('Started playlist scraping');
                });
        });
    
        document.getElementById('scrape-songs')?.addEventListener('click', function() {
            fetch('/api/scrape/songs')
                .then(response => response.json())
                .then(data => {
                    console.log('Started song scraping');
                });
        });
    }
    
    function initPreparationControls() {
        document.getElementById('prepare-data')?.addEventListener('click', function() {
            fetch('/api/prepare')
                .then(response => response.json())
                .then(data => {
                    console.log('Started data preparation');
                });
        });
    }
    
    function initTrainingControls() {
        document.getElementById('start-training')?.addEventListener('click', function() {
            fetch('/api/train/start')
                .then(response => response.json())
                .then(data => {
                    console.log('Started training');
                });
        });
    }
    
    function initGenerationControls() {
        document.getElementById('generate-lyrics')?.addEventListener('click', function() {
            const data = {
                model: document.getElementById('generator-model').value,
                title: document.getElementById('song-title').value,
                style: document.getElementById('style-tags').value,
                prompt: document.getElementById('generation-prompt').value
            };
            
            fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('generation-output').textContent = data.lyrics;
            });
        });
    }



    // Scraper controls
    document.querySelector('#scrape-playlists')?.addEventListener('click', function() {
        fetch('/api/scrape/playlists')
            .then(response => response.json())
            .then(data => console.log('Started playlist scraping'));
    });

    document.querySelector('#scrape-songs')?.addEventListener('click', function() {
        fetch('/api/scrape/songs')
            .then(response => response.json())
            .then(data => console.log('Started song scraping'));
    });

    // Preparation controls
    document.querySelector('#prepare-data')?.addEventListener('click', function() {
        fetch('/api/prepare')
            .then(response => response.json())
            .then(data => console.log('Started data preparation'));
    });

    // Training controls
    document.querySelector('#start-training')?.addEventListener('click', function() {
        fetch('/api/train/start')
            .then(response => response.json())
            .then(data => console.log('Started training'));
    });

    // Generation controls
    document.querySelector('#generate-lyrics')?.addEventListener('click', function() {
        const data = {
            model: document.querySelector('#generator-model').value,
            title: document.querySelector('#song-title').value,
            style: document.querySelector('#style-tags').value,
            prompt: document.querySelector('#generation-prompt').value
        };
        
        fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            document.querySelector('#generation-output').textContent = data.lyrics;
        });
    });
    
    // Load current settings
    fetch('/api/settings')
    .then(response => response.json())
    .then(settings => {
        Object.entries(settings).forEach(([category, values]) => {
            Object.entries(values).forEach(([key, value]) => {
                const element = document.querySelector(`[data-category="${category}"][data-key="${key}"]`);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = value;
                    } else {
                        element.value = value;
                    }
                }
            });
        });
    });

    // Save settings
    document.getElementById('save-settings').addEventListener('click', function() {
        const settings = {};
        document.querySelectorAll('[data-category][data-key]').forEach(element => {
            const category = element.dataset.category;
            const key = element.dataset.key;
            const value = element.type === 'checkbox' ? element.checked : element.value;
            
            if (!settings[category]) settings[category] = {};
            settings[category][key] = value;
        });

        fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        })
        .then(() => UIkit.notification({
            message: 'Settings saved successfully!',
            status: 'success'
        }));
    });

    // Reset settings
    document.getElementById('reset-settings').addEventListener('click', function() {
        if (confirm('Reset all settings to defaults?')) {
            fetch('/api/settings/reset')
                .then(response => response.json())
                .then(settings => {
                    location.reload();
                });
        }
    });
});

