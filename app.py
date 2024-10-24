from flask import Flask, render_template
from flask_socketio import SocketIO
import io
from utils import create_routes
from vars import root_folder, content_folder
import logging

app = Flask(__name__)
socketio = SocketIO(app)

# Create a string stream to capture logs
log_stream = io.StringIO()

# Configure logging to write to the string stream
logging.basicConfig(stream=log_stream, level=logging.INFO)

# Eine Liste der Seiten
pages = create_routes(app)


@app.route('/')
def start():
    return render_template('content/0-home.php', pages=pages)

def get_log_contents():
    return log_stream.getvalue()

# Emit logs to the client
def emit_logs():
    socketio.emit('log_update', {'data': get_log_contents()})

if __name__ == '__main__':
    logging.info("Server started")
    socketio.run(app, debug=True)
