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


bp = Blueprint("pi_camera", __name__, url_prefix="/pi_camera", template_folder="templates")

