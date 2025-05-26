
import os
from flask_socketio import SocketIO

from .core import mako_camera

MODULE_NAME = os.path.basename(os.path.dirname(__file__))
def register_socket(socketio: SocketIO):
    @socketio.on('capture', namespace='/{}'.format(MODULE_NAME))
    def capture():
        mako_camera.capture_image()