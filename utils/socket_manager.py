from flask_socketio import SocketIO

socketio = SocketIO()

def init_socket(app):
    socketio.init_app(app)
    return socketio
