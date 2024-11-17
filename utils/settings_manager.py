import json
import os
from config.vars import SETTINGS


class SettingsManager:
    def __init__(self):
        self.settings_file = "config/settings.json"
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                content = f.read()
                stored_settings = json.loads(content) if content else {}
        except (FileNotFoundError, json.JSONDecodeError):
            stored_settings = {}

        # Initialize with defaults and update with stored values
        settings = {}
        for category, config in SETTINGS.items():
            settings[category] = {}
            for field_name, field_config in config['fields'].items():
                if isinstance(field_config, dict) and 'type' in field_config:
                    if field_config['type'] == 'checkbox_group':
                        settings[category][field_name] = {
                            option_name: option_config['default']
                            for option_name, option_config in field_config['options'].items()
                        }
                    else:
                        settings[category][field_name] = field_config['default']

            # Update with stored values if they exist
            if category in stored_settings:
                settings[category].update(stored_settings[category])

        return settings

    def get_settings(self, keys=None):
        """
        Get settings for specific categories or all settings if no keys provided
        Returns flattened settings structure
        """
        if keys is None:
            return self.settings

        if isinstance(keys, str):
            keys = [keys]

        result = {}
        for key in keys:
            if key in self.settings:
                result[key] = self.settings[key]
            else:
                # Get defaults from SETTINGS structure and flatten them
                result[key] = {
                    field_name: field_config['default']
                    for field_name, field_config in SETTINGS[key]['fields'].items()
                }

        return result[keys[0]] if len(keys) == 1 else result

    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_default_settings(self):
        defaults = {}
        for category, config in SETTINGS.items():
            defaults[category] = {}
            for field_name, field_config in config['fields'].items():
                if field_config['type'] == 'checkbox_group':
                    defaults[category][field_name] = {}
                    for option_name, option_config in field_config['options'].items():
                        defaults[category][field_name][option_name] = option_config['default']
                else:
                    defaults[category][field_name] = field_config['default']
        return defaults

    def generate_settings_html(self):
        html = '<div class="accordion" id="settingsAccordion">'

        for category, config in SETTINGS.items():
            html += f'''
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button" type="button" data-bs-toggle="collapse" 
                            data-bs-target="#{category}Collapse">
                        {config['label']}
                    </button>
                </h2>
                <div id="{category}Collapse" class="accordion-collapse collapse show" 
                     data-bs-parent="#settingsAccordion">
                    <div class="card-body">
                        <div class="row g-3">
                            {self._generate_fields(category, config['fields'])}
                        </div>
                    </div>
                </div>
            </div>
            '''

        html += '</div>'
        return html

    def _generate_fields(self, category, fields, parent_key=''):
        html = ''
        for field_name, field_config in fields.items():
            current_key = f"{parent_key}.{field_name}" if parent_key else field_name

            if 'fields' in field_config:
                # This is a nested group
                html += f'''
                <div class="col-12">
                    <div class="border rounded p-3 mb-3">
                        <label class="form-label">{field_config['label']}</label>
                        <div class="row g-3">
                            {self._generate_fields(category, field_config['fields'], current_key)}
                        </div>
                    </div>
                </div>
                '''
            elif 'options' in field_config:
                # This is a checkbox group
                html += f'''
                <div class="col-12">
                    <div class="border rounded p-3">
                        <label class="form-label">{field_config['label']}</label>
                        {self._generate_checkbox_group(category, current_key, field_config['options'])}
                    </div>
                </div>
                '''
            elif field_config['type'] in ['file', 'directory']:
                html += f'''
                        <div class="col-md-4">
                            <label class="form-label">{field_config['label']}</label>
                            <div class="input-group">
                                <input class="form-control" type="text" 
                                       id="display_{current_key}" 
                                       value="{field_config['default']}" 
                                       readonly>
                                <input type="file" 
                                       id="{current_key}" 
                                       data-category="{category}" 
                                       data-key="{current_key}"
                                       class="d-none"
                                       {' webkitdirectory directory' if field_config['type'] == 'directory' else ''}>
                                <button class="btn btn-outline-secondary" type="button" 
                                        onclick="document.getElementById('{current_key}').click()">
                                    <i class="bi bi-folder"></i>
                                </button>
                            </div>
                        </div>
                        '''
            else:
                # Regular input field
                html += f'''
                <div class="col-md-4">
                    <label class="form-label">{field_config['label']}</label>
                    <input class="form-control" type="{field_config['type']}"
                           id="{current_key}" data-category="{category}" 
                           data-key="{current_key}">
                </div>
                '''
        return html

    def _generate_checkbox_group(self, category, group_name, options):
        html = '<div class="d-flex flex-column gap-2">'
        for option_name, option_config in options.items():
            html += f'''
            <div class="form-check">
                <input class="form-check-input" type="checkbox" 
                       id="{option_name}" data-category="{category}" 
                       data-key="{group_name}.{option_name}">
                <label class="form-check-label" for="{option_name}">
                    {option_config['label']}
                </label>
            </div>
            '''
        html += '</div>'
        return html

settings_manager = SettingsManager()
