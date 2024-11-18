import os
root_folder = os.path.dirname(os.path.abspath(__file__))
content_folder = 'templates/content'
pages = [
    {"name": "home", "icon": "home"},
    {"name": "scrape", "icon": "download"},
    {"name": "prepare", "icon": "settings_suggest"},
    {"name": "train", "icon": "school"},
    {"name": "generate", "icon": "auto_awesome"},
    {"name": "settings", "icon": "settings"}
]
EXPECTED_KEYS = {
    "title": ["title", "songtitle", "name"],
    "lyrics": ["lyrics", "text", "songtext"],
    "styles": ["styles", "genre", "genres", "style"],
    "metatags": ["metatags", "tags", "meta"],
    "language": ["language", "lang", "sprache"]
}


# Ordner für die Song-JSON-Dateien
SONGS_DIR = "songs"
SONG_META_DIR = "song_meta"  # Neuer Ordner für die JSON-Dateien
USERDATA_DIR = "chrome_user_data"

# JSON Datei Pfade im Ordner 'song_meta'
SCRAPED_URLS_FILE = f"{SONG_META_DIR}/urls.json"
STYLES_FILE = f"{SONG_META_DIR}/all_styles.json"
SONG_STYLES_MAPPING_FILE = f"{SONG_META_DIR}/song_styles_mapping.json"
META_TAGS_FILE = f"{SONG_META_DIR}/all_meta_tags.json"
SONG_META_MAPPING_FILE = f"{SONG_META_DIR}/song_meta_mapping.json"
