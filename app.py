from flask import Flask
import os
from utils import *
from vars import *

app = Flask(__name__)

# Eine Liste der Seiten
pages = create_routes(app)


@app.route('/')
def start():
    return render_template('content/home.php', pages=pages)

if __name__ == '__main__':
    app.run(debug=True)
