import logging
from flask import Flask, render_template, jsonify, request
from utils.thread_manager import thread_manager
from modules import scraper, prepare, trainer, generator
from modules.settings import settings_manager  # Direct import of settings_manager
from utils.socket_manager import init_socket, socketio
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

# Manuelle Liste der Seiten (URL, Name)
pages = [
    {"url": "home", "name": "Home"},
    {"url": "scrape", "name": "Scrape"},
    {"url": "prepare", "name": "Prepare"},
    {"url": "train", "name": "Train"},
    {"url": "generate", "name": "Generate"},
    {"url": "settings", "name": "Settings"}
]

##########################THREADS##########################
@app.route('/api/threads')
def get_active_threads():
    active_threads = thread_manager.get_active_threads()
    return jsonify(active_threads)

@app.route('/api/stop/<thread_name>')
def stop_thread(thread_name):
    thread_manager.stop_thread(thread_name)
    return jsonify({"status": "stopped"})


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


@app.route('/api/scrape/playlists', methods=['GET', 'POST'])
def api_scrape_playlists():
    success = thread_manager.start_thread(
        'playlist_scraping', 
        scraper.WebScraper(thread_manager.log_queue).scrape_playlists
    )
    return jsonify({"status": "started" if success else "already running"})

@app.route('/api/scrape/songs', methods=['GET', 'POST'])
def api_scrape_songs():
    success = thread_manager.start_thread(
        'song_scraping',
        scraper.WebScraper(thread_manager.log_queue).scrape_songs
    )
    return jsonify({"status": "started" if success else "already running"})


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
    return render_template('content/5-settings.html')



@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'POST':
        data = request.json
        settings_manager.update_setting(
            data['category'],
            data['key'],
            data['value']
        )
        return jsonify({"status": "success"})
    return jsonify(settings_manager.settings)


# Run the app
if __name__ == '__main__':
    logging.info("Server started")
    socketio.run(app, debug=True)