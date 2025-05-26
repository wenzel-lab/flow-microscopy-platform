from flask_socketio import SocketIO

import time
from .api import heaters



def run_threads(socketio: SocketIO):
    
    def run_heaters_emit(socketio):
        while True:
            for heater in heaters.values():
                heater.update()
            heaters_data = {index: heater.data for index, heater in heaters.items()}
            socketio.emit("data", heaters_data, namespace="/cam_strobe/heaters")
            time.sleep(1)

    socketio.start_background_task(lambda: run_heaters_emit(socketio))


def register_socket_events(socketio: SocketIO):
    def handle_heaters_connect():
        print("Client connected to /cam_strobe/heaters namespace")

    socketio.on_event("connect", handle_heaters_connect, namespace="/cam_strobe/heaters")