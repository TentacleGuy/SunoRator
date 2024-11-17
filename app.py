import logging
from flask import Flask, render_template, jsonify, request
from utils.thread_manager import thread_manager
from modules import scraper, prepare, trainer, generator
from utils.settings_manager import settings_manager  # Direct import of settings_manager
from utils.socket_manager import socketio
from utils.utils import *
from config.vars import *

app = Flask(__name__)
socketio.init_app(app)

# Add WebSocket handler for logging
def handle_connect():
    def emit_logs():
        while True:
            message = thread_manager.log_queue.get()
            socketio.emit('log_update', {'data': message})
    
    thread_manager.start_thread('log_emitter', emit_logs)

##########################THREADS##########################
@app.route('/api/threads')
def get_active_threads():
    active_threads = thread_manager.get_active_threads()
    # The thread manager now returns a dictionary with the correct format
    return jsonify(active_threads)

@app.route('/api/threads')

@app.route('/api/threads/<thread_name>/stop')
def stop_thread(thread_name):
    thread_manager.stop_thread(thread_name)
    return jsonify({"status": "stopped"})

@app.route('/api/threads/<thread_name>/pause')
def pause_thread(thread_name):
    thread_manager.pause_thread(thread_name)
    return jsonify({"status": "paused"})

@app.route('/api/threads/<thread_name>/resume')
def resume_thread(thread_name):
    thread_manager.resume_thread(thread_name)
    return jsonify({"status": "resumed"})

##########################HOME##########################
@app.route('/')
def start():
    return render_template('main.html', 
                            current_page="home", 
                            pages=pages, 
                            content=render_template('content/0-home.html'))


@app.route('/home')
def home():
    return render_template('content/0-home.html')

##########################SCRAPE##########################
@app.route('/scrape')
def scrape():
    return render_template('content/1-scrape.html')  # Return only content

@app.route('/api/scrape/collections', methods=['POST'])
def api_scrape_collections():
    success = thread_manager.start_thread(
        'collection_scraping',
        scraper.WebScraper(thread_manager.log_queue).scrape_collections
    )
    return jsonify({"status": "started" if success else "already running"})

@app.route('/api/scrape/song-urls', methods=['POST'])
def api_scrape_song_urls():
    success = thread_manager.start_thread(
        'song_url_scraping',
        scraper.WebScraper(thread_manager.log_queue).scrape_song_urls
    )
    return jsonify({"status": "started" if success else "already running"})

@app.route('/api/collections/<collection_id>', methods=['DELETE'])
def delete_collection(collection_id):
    data = get_playlist_data()
    for collection_type in ['playlists', 'artists', 'genres']:
        if collection_id in data[collection_type]:
            del data[collection_type][collection_id]
            save_playlist_data(data)
            return jsonify({"status": "success"})
    return jsonify({"status": "not found"}), 404

@app.route('/api/collections/<collection_id>/toggle', methods=['POST'])
def toggle_collection(collection_id):
    data = get_playlist_data()
    for collection_type in ['playlists', 'artists', 'genres']:
        if collection_id in data[collection_type]:
            data[collection_type][collection_id]['enabled'] = not data[collection_type][collection_id].get('enabled', True)
            save_playlist_data(data)
            return jsonify({"status": "success"})
    return jsonify({"status": "not found"}), 404


@app.route('/api/scrape/songs', methods=['GET', 'POST'])
def api_scrape_songs():
    success = thread_manager.start_thread(
        'song_scraping',
        scraper.WebScraper(thread_manager.log_queue).scrape_songs
    )
    return jsonify({"status": "started" if success else "already running"})

@app.route('/api/playlists/manual', methods=['POST'])
def add_manual_playlist():
    data = request.json
    playlist_url = data['url']
    # Create scraper instance with log queue
    scraper_instance = scraper.WebScraper(thread_manager.log_queue)
    success = scraper_instance.add_manual_playlist(playlist_url)
    return jsonify({"success": success})

@app.route('/api/playlists/all')
def get_all_playlists():
    """Return all playlist data including auto, manual playlists and manual songs"""
    playlists = get_playlist_data()
    return jsonify(playlists)

@app.route('/api/songs/manual', methods=['POST'])
def add_manual_song():
    data = request.json
    song_url = data['url']
    # Create scraper instance with log queue
    scraper_instance = scraper.WebScraper(thread_manager.log_queue)
    success = scraper_instance.add_manual_song(song_url)
    return jsonify({"success": success})

@app.route('/api/scrape/single-url', methods=['POST'])
def scrape_single_url():
    url = request.json.get('url')
    success = thread_manager.start_thread(
        f'scrape_{url}',
        lambda stop_event, log_queue, pause_event:
            scraper.WebScraper(thread_manager.log_queue).scrape_single_url(stop_event, log_queue, pause_event, url)
    )
    return jsonify({"status": "started" if success else "already running"})
@app.route('/api/urls/all', methods=['GET'])
def get_all_urls():
    data = load_json(SCRAPED_URLS_FILE)
    if not isinstance(data, dict):
        data = {
            "playlists": {},
            "artists": {},
            "genres": {},
            "songs": {}
        }
    return jsonify(data)

@app.route('/api/urls/toggle', methods=['POST'])
def toggle_url():
    data = request.json
    url = data.get('url')
    playlists = get_playlist_data()

    # Find the correct collection type for this URL
    for collection_type in ['playlists', 'artists', 'genres', 'songs']:
        if url in playlists[collection_type]:
            playlists[collection_type][url]['enabled'] = not playlists[collection_type][url].get('enabled', True)
            save_playlist_data(playlists)
            return jsonify({
                "success": True,
                "enabled": playlists[collection_type][url]['enabled']
            })

    return jsonify({"success": False}), 404

@app.route('/api/urls/delete', methods=['POST'])
def delete_url():
    data = request.json
    url = data.get('url')
    playlists = get_playlist_data()
    for collection in playlists.values():
        if url in collection:
            del collection[url]
    save_playlist_data(playlists)
    return jsonify({"success": True})


@app.route('/api/urls/add', methods=['POST'])
def add_url():
    data = request.get_json()
    url = data.get('url')
    url_type = data.get('type')
    success = add_url_to_collection(url, url_type)
    return jsonify({'success': success})

##########################PREPARE##########################
@app.route('/prepare')
def prepare():
    return render_template('content/2-prepare.html')

@app.route('/api/prepare')
def api_prepare():
    thread_manager.start_thread('prepare', prepare.start_preparation)
    return jsonify({"status": "started"})

#########################TRAIN##########################
@app.route('/train')
def train():
    return render_template('content/3-train.html')

@app.route('/api/train/start')
def api_train_start():
    thread_manager.start_thread('trainer', trainer.start_training)
    return jsonify({"status": "started"})

#########################GENERATE##########################
@app.route('/generate')
def generate():
    return render_template('content/4-generate.html')


@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json
    result = generator.generate_lyrics(data)
    return jsonify({"lyrics": result})

#########################SETTINGS##########################
@app.route('/settings')
def settings():
    settings_html = settings_manager.generate_settings_html()
    return render_template('content/5-settings.html', settings_content=settings_html)

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'POST':
        data = request.json
        settings_manager.update_settings(data)
        return jsonify({"status": "success"})
    return jsonify(settings_manager.settings)

@app.route('/api/settings/reset', methods=['POST'])
def reset_settings():
    settings_manager.settings = settings_manager.get_default_settings()
    settings_manager.save_settings()
    return jsonify({"status": "success"})

@app.route('/api/file-picker', methods=['POST'])
def file_picker():
    data = request.json
    if data['type'] == 'directory':
        # Handle directory selection
        directory = request.files['directory']
        # Process directory
    else:
        # Handle file selection
        file = request.files['file']
        # Process file
    return jsonify({"path": selected_path})



# Run the app
if __name__ == '__main__':
    logging.info("Server started")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    

#TODO: ThreadManager in Modal erstellen.
#Threads pausieren, stoppen, und fortfahren.
#Informationen zu den threads anzeigen
