import os

SETTINGS = {
    "model": {
        "label": "Model Settings",
        "fields": {
            "name": {
                "type": "text",
                "default": "gpt2",
                "label": "Model Name"
            },
            "epochs": {
                "type": "number",
                "default": 3,
                "label": "Epochs"
            },
            "learning_rate": {
                "type": "number",
                "default": 5e-5,
                "label": "Learning Rate"
            },
            "batch_size": {
                "type": "number",
                "default": 4,
                "label": "Batch Size"
            },
            "max_length": {
                "type": "number",
                "default": 128,
                "label": "Max Length"
            },
            "warmup_steps": {
                "type": "number",
                "default": 500,
                "label": "Warmup Steps"
            },
            "weight_decay": {
                "type": "number",
                "default": 0.01,
                "label": "Weight Decay"
            },
            "gradient_accumulation_steps": {
                "type": "number",
                "default": 4,
                "label": "Gradient Accumulation Steps"
            },
            "logging_steps": {
                "type": "number",
                "default": 100,
                "label": "Logging Steps"
            },
            "save_steps": {
                "type": "number",
                "default": 500,
                "label": "Save Steps"
            },
            "eval_steps": {
                "type": "number",
                "default": 500,
                "label": "Eval Steps"
            }
        }
    },
    "paths": {
        "label": "Path Settings",
        "fields": {
            "songs_dir": {
                "type": "text",
                "default": "songs",
                "label": "Songs Directory"
            },
            "meta_dir": {
                "type": "text",
                "default": "song_meta",
                "label": "Meta Directory"
            },
            "scraped_urls_file": {
                "type": "text",
                "default": "song_meta/urls.json",
                "label": "Scraped URLs File"
            },
            "styles_file": {
                "type": "text",
                "default": "song_meta/all_styles.json",
                "label": "Styles File"
            },
            "song_styles_mapping_file": {
                "type": "text",
                "default": "song_meta/song_styles_mapping.json",
                "label": "Song Styles Mapping File"
            },
            "meta_tags_file": {
                "type": "text",
                "default": "song_meta/all_meta_tags.json",
                "label": "Meta Tags File"
            },
            "song_meta_mapping_file": {
                "type": "text",
                "default": "song_meta/song_meta_mapping.json",
                "label": "Song Meta Mapping File"
            },
            "trainingdata_file": {
                "type": "text",
                "default": "trainingdata.json",
                "label": "Training Data File"
            }
        }
    },
    "scraper": {
        "label": "Scraper Settings",
        "fields": {
            "delay": {
                "type": "number",
                "default": 5,
                "label": "Delay (seconds)"
            },
            "window_size": {
                "type": "text",
                "default": "1920,1080",
                "label": "Window Size"
            },
            "browser_options": {
                "type": "checkbox_group",
                "label": "Browser Options",
                "options": {
                    "headless": {
                        "default": True,
                        "label": "Enable Headless Mode"
                    },
                    "no_sandbox": {
                        "default": True,
                        "label": "No Sandbox"
                    },
                    "dev_shm_usage": {
                        "default": True,
                        "label": "Disable Dev SHM Usage"
                    },
                    "use_login": {
                        "default": False,
                        "label": "Use Login"
                    }
                }
            }
        }
    },
    "login": {
        "label": "Login Settings",
        "fields": {
            "google_email": {
                "type": "email",
                "default": "",
                "label": "Google Email"
            },
            "google_password": {
                "type": "password",
                "default": "",
                "label": "Google Password"
            }
        }
    }
}

# Keep only these core variables
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
#TODO:Alle dateien durchgehen und das laden der Settings durch den settingmanager anpassen
#TODO:Settingsmanager anpassen
#TODO:Layout dynamisch generieren