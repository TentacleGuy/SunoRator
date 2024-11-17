import os

SETTINGS = {
    "model": {
        "label": "Training Settings",
        "fields": {
            "name": {
                "type": "text",
                "default": "gpt2",
                "label": "Model"
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
        "label": "File Settings",
            "fields": {
                "songs_dir": {
                "type": "directory",
                "default": "songs",
                "label": "Songs Directory"
            },
            "meta_dir": {
                "type": "directory",
                "default": "song_meta",
                "label": "Meta Directory"
            },
            "model_dir": {
                "type": "directory",
                "default": "models",
                "label": "Model Directory"
            },
            "output_dir": {
                "type": "directory",
                "default": "output",
                "label": "Output Directory"
            }
        }
    },
    "scraper": {
        "label": "Scraper Settings",
        "fields": {
            "general":{
                "label": "General",
                "fields": {
                    "delay": {
                        "type": "number",
                        "default": 5,
                        "label": "Page loading delay (seconds)"
                    },
                }
            },
            "browser_options": {
                "label": "Browser",
                "fields": {
                    "arguments": {
                        "type": "checkbox_group",
                        "label": "Arguments",
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
                            }
                        }
                    },
                    "use_login": {
                        "type": "checkbox_group",
                        "label": "Options",
                        "options": {
                            "use_login": {
                                "default": False,
                                "label": "Use Login?"
                            }
                        }
                    }
                }
            }
        }
    }
}

import os


def get_constants():
    # Filenames
    URLS_FILE = "urls.json"
    STYLES_FILE = "all_styles.json"
    SONG_STYLES_MAPPING_FILE = "song_styles_mapping.json"
    META_TAGS_FILE = "all_meta_tags.json"
    SONG_META_MAPPING_FILE = "song_meta_mapping.json"
    MODEL_FILE = "gpt2.pt"
    OUTPUT_FILE_TEMPLATE = "{title}.txt"

    # Core variables
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

    return locals()

# Make constants available at module level
globals().update(get_constants())

#TODO:Alle dateien durchgehen und das laden der Settings durch den settingmanager anpassen
#TODO:Settingsmanager anpassen
#TODO:Layout dynamisch generieren