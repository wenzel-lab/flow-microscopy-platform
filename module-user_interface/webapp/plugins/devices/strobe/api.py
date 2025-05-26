import cv2
import RPi.GPIO as GPIO
import threading

# from .utils import get_camera, setup_camera, Camera, FrameStatus, Frame, frame_queue, cam_running_event
from ...interfaces.spi_handler import spi_handler
from ...utils import load_config, save_config, web_frame_generator
from .core import Strobe, strobe

from flask import Blueprint, Response, current_app
from flask import render_template, request, jsonify
import json
import os
import datetime

from queue import Queue
from threading import Event

CAPTURES_PATH = os.path.join(os.path.dirname(__file__), "captures")

template_folder_path = os.path.join(os.path.dirname(__file__), "templates")
bp = Blueprint("strobe", __name__, url_prefix="/strobe", template_folder=template_folder_path, static_folder="static")



@bp.route("/strobe-period", methods=["GET", "POST"])
def strobe_period():
    if request.method == "GET":
        return jsonify({"strobe_period_us": strobe.strobe_period_ns / 1000})
    elif request.method == "POST":
        data = request.json
        strobe_period_ns = int(data.get("strobe_period_us")) * 1000
        strobe.set_timing(84032, strobe_period_ns)
        return jsonify({"status": "success"})

@bp.route("/enable-strobe", methods=["POST"])
def strobe_enable():
    data = request.json
    enable = data.get("strobe_enable")
    # strobe.init_led_pin()
    strobe.set_enable(enable)
    return jsonify({"status": "success"})