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
    "browser": {
        "label": "Browser Settings",
        "fields": {
            "login": {
                "type": "button",
                "label": "Login to Suno",
                "action": "openLoginBrowser"
            },
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
                    },
                    "disable_gpu": {
                        "default": True,
                        "label": "Disable GPU"
                    },
                    "disable_automation": {
                        "default": True,
                        "label": "Disable Automation Features"
                    }
                }
            },
            "options": {
                "label": "Options",
                "fields": {
                    "delay": {
                        "type": "number",
                        "default": 5,
                        "label": "Page loading delay (seconds)"
                    },
                    "window_size": {
                        "type": "text",
                        "default": "1920,1080",
                        "label": "Window Size"
                    },
                    "debugging_port": {
                        "type": "text",
                        "default": "0",
                        "label": "Remote Debugging Port"
                    },
                    "user_agent": {
                        "type": "text",
                        "default": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                        "label": "User Agent"
                    }
                }
            }
        }
    }
}