import json
import os
from config.vars import *

class SettingsManager:
    def __init__(self):
        self.settings_file = "config/settings.json"
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        self.load_settings()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                content = f.read()
                self.settings = json.loads(content) if content else self.get_defaults()
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = self.get_defaults()
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_defaults(self):
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
            }
        }
    
    def update_setting(self, category, key, value):
        if category in self.settings:
            self.settings[category][key] = value
            self.save_settings()
            return True
        return False

settings_manager = SettingsManager()
