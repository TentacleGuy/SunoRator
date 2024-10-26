import logging
from flask import Flask, render_template, jsonify, request
from utils.thread_manager import thread_manager
from modules import scraper, prepare, trainer, generator, settings
from utils.utils import *
from config.vars import *

app = Flask(__name__)

# Manuelle Liste der Seiten (URL, Name)
pages = [
    {"url": "home", "name": "Home"},
    {"url": "scrape", "name": "Scrape"},
    {"url": "prepare", "name": "Prepare"},
    {"url": "train", "name": "Train"},
    {"url": "generate", "name": "Generate"},
    {"url": "settings", "name": "Settings"}
]

@app.route('/api/threads')
def get_threads():
    active_threads = thread_manager.get_active_threads()
    return jsonify({name: thread.name for name, thread in active_threads.items()})

@app.route('/api/stop_thread/<thread_name>')
def stop_thread(thread_name):
    thread_manager.stop_thread(thread_name)
    return jsonify({"status": "success"})

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'POST':
        data = request.json
        settings.settings_manager.update_setting(
            data['category'],
            data['key'],
            data['value']
        )
        return jsonify({"status": "success"})
    return jsonify(settings.settings_manager.settings)

@app.route('/')
def start():
    content = render_template('content/0-home.html')
    return render_template('main.html', current_page="home", pages=pages, content=content)

@app.route('/home')
def home():
    content = render_template('content/0-home.html')
    return render_template('main.html', current_page="home", pages=pages, content=content)

@app.route('/scrape')
def scrape():
    content = render_template('content/1-scrape.html')
    return render_template('main.html', current_page="scrape", pages=pages, content=content)

@app.route('/prepare')
def prepare():
    content = render_template('content/2-prepare.html')
    return render_template('main.html', current_page="prepare", pages=pages, content=content)

@app.route('/train')
def train():
    content = render_template('content/3-train.html')
    return render_template('main.html', current_page="train", pages=pages, content=content)

@app.route('/generate')
def generate():
    content = render_template('content/4-generate.html')
    return render_template('main.html', current_page="generate", pages=pages, content=content)

@app.route('/settings')
def settings():
    content = render_template('content/5-settings.html')
    return render_template('main.html', current_page="settings", pages=pages, content=content)

if __name__ == '__main__':
    logging.info("Server started")
    app.run(debug=True)