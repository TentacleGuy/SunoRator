import json
import os
from config.vars import *

class SettingsManager:
    def __init__(self):
        self.settings_file = "config/settings.json"
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                content = f.read()
                return json.loads(content) if content else self.get_default_settings()
        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_settings()

    def get_settings(self):
        return self.settings

    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_default_settings(self):
        return {
            "model": {
                "name": DEFAULT_MODEL_NAME,
                "epochs": DEFAULT_EPOCHS,
                "learning_rate": DEFAULT_LEARNING_RATE,
                "batch_size": DEFAULT_BATCH_SIZE
            },
            "paths": {
                "songs_dir": SONGS_DIR,
                "meta_dir": SONG_META_DIR
            },
            "scraper": {
                "delay": 5,
                "headless": True
            },
            "login": {
                "google_email": DEFAULT_GOOGLE_EMAIL,
                "google_password": DEFAULT_GOOGLE_PASSWORD
            }
        }

settings_manager = SettingsManager()
