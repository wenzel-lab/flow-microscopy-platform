import cv2
import RPi.GPIO as GPIO
import threading

# from .utils import get_camera, setup_camera, Camera, FrameStatus, Frame, frame_queue, cam_running_event
from .core import StrobeCam, strobe_cam
from ...interfaces.spi_handler import spi_handler
from ...utils import load_config, save_config, web_frame_generator

from flask import Blueprint, Response, current_app
from flask import render_template, request, jsonify
import json
import os
import datetime

from queue import Queue
from threading import Event

CAPTURES_PATH = os.path.join(os.path.dirname(__file__), "captures")


template_folder_path = os.path.join(os.path.dirname(__file__), "templates")
bp = Blueprint("cam_strobe", __name__, url_prefix="/cam_strobe", template_folder=template_folder_path, static_folder="static")


@bp.route("", methods=["GET"])
def main_view():
    if type(strobe_cam.camera).__name__ == "MakoCamera":
        camera_name = "mako"
    elif type(strobe_cam.camera).__name__ == "PiCamera":
        camera_name = "pi"
    else:
        camera_name = "none"
    return render_template("main.html", camera_name=camera_name)


@bp.route("image/<image_name>", methods=["GET"])
def get_image(image_name):
    with open(os.path.join(CAPTURES_PATH, image_name), "rb") as f:
        return Response(f.read(), mimetype="image/jpeg")

