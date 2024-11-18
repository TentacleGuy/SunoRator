import json
from config.settings import SETTINGS
from config.vars import *

class SettingsManager:
    def __init__(self):
        self.settings_file = "config/settings.json"
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                stored_settings = json.loads(f.read()) if f.read() else {}
        except (FileNotFoundError, json.JSONDecodeError):
            stored_settings = {}

        settings = {}

        # Initialize with nested structure from SETTINGS
        for category, config in SETTINGS.items():
            settings[category] = {}
            for field_name, field_config in config['fields'].items():
                if field_config.get('type') == 'button':
                    continue
                elif 'fields' in field_config:
                    settings[category][field_name] = {}
                    for sub_field, sub_config in field_config['fields'].items():
                        settings[category][field_name][sub_field] = sub_config['default']
                elif 'options' in field_config:
                    settings[category][field_name] = {}
                    for option_name, option_config in field_config['options'].items():
                        settings[category][field_name][option_name] = option_config['default']
                else:
                    settings[category][field_name] = field_config['default']

        # Update with stored values
        if stored_settings:
            for category in settings:
                if category in stored_settings:
                    settings[category].update(stored_settings[category])

        return settings

    def get_settings(self, keys=None):
        if keys is None:
            return self.settings

        if isinstance(keys, str):
            keys = [keys]

        result = {}
        for key in keys:
            if key in self.settings:
                result[key] = self.settings[key]
            else:
                # Handle nested fields recursively
                category_settings = {}
                category_config = SETTINGS[key]

                def process_fields(fields, prefix=''):
                    field_dict = {}
                    for field_name, field_config in fields.items():
                        if 'fields' in field_config:
                            field_dict.update(process_fields(field_config['fields'], f"{prefix}{field_name}."))
                        elif 'options' in field_config:
                            for option_name, option_config in field_config['options'].items():
                                field_dict[f"{prefix}{field_name}.{option_name}"] = option_config['default']
                        else:
                            field_dict[f"{prefix}{field_name}"] = field_config.get('default')
                    return field_dict

                result[key] = process_fields(category_config['fields'])

        return result[keys[0]] if len(keys) == 1 else result

    def update_settings(self, new_settings):
        # Convert flat structure to nested for scraper settings
        if 'scraper' in new_settings:
            scraper_settings = {}
            for key, value in new_settings['scraper'].items():
                parts = key.split('.')
                current = scraper_settings
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            new_settings['scraper'] = scraper_settings

        # Update settings with nested structure
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
                    <div class="accordion-body p-4">
                            {self._generate_fields(category, config['fields'])}
                    </div>
                </div>
            </div>
            '''
        html += '</div>'
        return html

    def _generate_fields(self, category, fields, parent_key=''):
        html = '<div class="row g-4">'
        current_settings = self.settings.get(category, {})

        if all('type' in field_config and 'default' in field_config for field_config in fields.values()):
            for field_name, field_config in fields.items():
                current_key = f"{parent_key}.{field_name}" if parent_key else field_name
                value = current_settings.get(field_name, field_config['default'])
                html += f'''
                    <div class="col-md-4">
                        <label class="form-label">{field_config['label']}</label>
                        <input class="form-control" type="{field_config['type']}"
                               id="{current_key}" data-category="{category}" 
                               data-key="{current_key}"
                               value="{value}">
                    </div>
                '''
        else:
            for field_name, field_config in fields.items():
                current_key = f"{parent_key}.{field_name}" if parent_key else field_name
                nested_settings = current_settings.get(field_name, {})

                if 'type' in field_config and field_config['type'] == 'button':
                    html += f'''
                        <div class="col-md-4">
                            <button class="btn btn-primary w-100" 
                                    onclick="handleLoginClick()"
                                    data-action="{field_config['action']}">
                                {field_config['label']}
                            </button>
                        </div>
                    '''
                elif 'fields' in field_config:
                    html += f'''
                        <div class="col-md-4">
                            <div class="border rounded p-3">
                                <h6 class="mb-3">{field_config['label']}</h6>
                                <div class="row">
                                    <div class="col-12">
                                        {self._generate_nested_fields(category, field_config['fields'], current_key, nested_settings)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    '''
                elif 'options' in field_config:
                    html += f'''
                        <div class="col-md-4">
                            <div class="border rounded p-3">
                                <h6 class="mb-3">{field_config['label']}</h6>
                                {self._generate_checkbox_group(category, current_key, field_config['options'], nested_settings)}
                            </div>
                        </div>
                    '''

        html += '</div>'
        return html

    def _generate_nested_fields(self, category, fields, parent_key, current_values):
        html = ''
        for field_name, field_config in fields.items():
            current_key = f"{parent_key}.{field_name}"
            value = current_values.get(field_name, field_config['default'])
            html += f'''
                <div class="mb-3">
                    <label class="form-label">{field_config['label']}</label>
                    <input class="form-control" type="{field_config['type']}"
                           id="{current_key}" data-category="{category}" 
                           data-key="{current_key}"
                           value="{value}">
                </div>
            '''
        return html

    def _generate_checkbox_group(self, category, group_name, options, current_values=None):
        html = '<div class="d-flex flex-column gap-2">'
        current_values = current_values or {}

        for option_name, option_config in options.items():
            checked = current_values.get(option_name, option_config['default'])
            html += f'''
            <div class="form-check">
                <input class="form-check-input" type="checkbox" 
                       id="{option_name}" data-category="{category}" 
                       data-key="{group_name}.{option_name}"
                       {"checked" if checked else ""}>
                <label class="form-check-label" for="{option_name}">
                    {option_config['label']}
                </label>
            </div>
            '''
        html += '</div>'
        return html



settings_manager = SettingsManager()
