import logging
from flask import Flask, render_template, abort
from utils import *
from vars import *


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

@app.route('/')
def start():
    content = render_template('content/0-home.php')
    return render_template('main.php', current_page="home", pages=pages, content=content)

@app.route('/home')
def home():
    content = render_template('content/0-home.php')
    return render_template('main.php', current_page="home", pages=pages, content=content)

@app.route('/scrape')
def scrape():
    content = render_template('content/1-scrape.php')
    return render_template('main.php', current_page="scrape", pages=pages, content=content)

@app.route('/prepare')
def prepare():
    content = render_template('content/2-prepare.php')
    return render_template('main.php', current_page="prepare", pages=pages, content=content)

@app.route('/train')
def train():
    content = render_template('content/3-train.php')
    return render_template('main.php', current_page="train", pages=pages, content=content)

@app.route('/generate')
def generate():
    content = render_template('content/4-generate.php')
    return render_template('main.php', current_page="generate", pages=pages, content=content)

@app.route('/settings')
def settings():
    content = render_template('content/5-settings.php')
    return render_template('main.php', current_page="settings", pages=pages, content=content)

if __name__ == '__main__':
    logging.info("Server started")
    app.run(debug=True)