from flask import Flask, blueprints
import importlib
import os
from .main import bp as main_blueprint
from flask_socketio import SocketIO

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

devices_plugins = [
    # "mako_camera",
    "pi_camera_32",
    "strobe"
]
apps_plugins = [
    "cam_strobe"
]

interfaces_plugins = [
    "spi_handler"
]

def create_app():
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*")
    app.config["socketio"] = socketio
    app.config["DATA_PATH"] = DATA_PATH
    app.template_folder = 'templates'
    app.static_folder = 'static'
    # Configuration settings
    # app.config.from_object('config.Config')
    for plugin in interfaces_plugins:
        module = importlib.import_module(f"webapp.plugins.interfaces.{plugin}")

    app.register_blueprint(main_blueprint)

    api_blueprints = blueprints.Blueprint("api", __name__, url_prefix="/api")

    for plugin in devices_plugins:
        module = importlib.import_module(f"webapp.plugins.devices.{plugin}")
        if hasattr(module, "api_bp"):
            api_blueprints.register_blueprint(module.api_bp)
        if hasattr(module, "views_bp"):
            app.register_blueprint(module.views_bp)

    for plugin in apps_plugins:
        module = importlib.import_module(f"webapp.plugins.apps.{plugin}")
        if hasattr(module, "api_bp"):
            api_blueprints.register_blueprint(module.api_bp)
        if hasattr(module, "views_bp"):
            app.register_blueprint(module.views_bp)
        if hasattr(module, "sockets_core"):
            module.sockets_core.register_socket_events(socketio)
            module.sockets_core.run_threads(socketio)

    app.register_blueprint(api_blueprints)
    return app