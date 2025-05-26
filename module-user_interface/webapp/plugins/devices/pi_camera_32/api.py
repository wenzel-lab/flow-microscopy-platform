import cv2
import threading
import time


# from .utils import MakoCamera
# from .core import PiCamera
from .core import pi_camera
from ...utils import load_config, save_config, web_frame_generator

from flask import Blueprint, Response, current_app
from flask import render_template, request, jsonify
import json


bp = Blueprint("pi_camera_32", __name__, url_prefix="/pi_camera_32", template_folder="templates")

@bp.route("/get-current-resolution")
def get_current_resolution():
    size = pi_camera.get_current_resolution()
    return jsonify({"height": size[1], "width": size[0]})