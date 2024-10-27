from flask_socketio import SocketIO, emit

socketio = SocketIO()


@socketio.on('connect')
def handle_connect():
    emit('log_update', {'data': 'Client connected'})
    
def init_socket(app):
    socketio.init_app(app)
    return socketio
