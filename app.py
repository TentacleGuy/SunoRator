from flask import Flask, render_template
import os

app = Flask(__name__)

# Pfad zu den PHP-Dateien im content-Ordner
content_folder = 'templates/content'

# Eine Liste der Seiten
pages = []

# Durchlaufe die Dateien im content-Ordner und erstelle dynamische Routen
for filename in os.listdir(content_folder):
    if filename.endswith('.php'):
        route_name = filename.split('.')[0]  # Name der Datei ohne Erweiterung
        pages.append(route_name)  # Zur Liste der Seiten hinzufügen

        # Funktion zur Erstellung der Route
        def make_route(route):
            return lambda: render_template(f'content/{route}.php', pages=pages)

        # Füge die Route zur Flask-App hinzu
        app.add_url_rule(f'/{route_name}', route_name, make_route(route_name))

@app.route('/')
def home():
    return render_template('content/generate.php', pages=pages)

if __name__ == '__main__':
    app.run(debug=True)
