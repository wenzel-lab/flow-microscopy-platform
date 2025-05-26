import cv2
import RPi.GPIO as GPIO
import threading

# from .utils import get_camera, setup_camera, Camera, FrameStatus, Frame, frame_queue, cam_running_event
from .core import StrobeCam, strobe_cam
from ...interfaces.spi_handler import spi_handler
from ...devices.holder.core import Heater, Holder
from ...utils import load_config, save_config, web_frame_generator

from flask import Blueprint, Response, current_app
from flask_socketio import SocketIO, emit
from flask import render_template, request, jsonify
import json
import os
import datetime
import time

from queue import Queue
from threading import Event, Thread

CAPTURES_PATH = os.path.join(os.path.dirname(__file__), "captures")

# strobe_cam = StrobeCam(spi_handler, strobe_port=24, reply_pause_s=0.1, background_thread=False)
template_folder_path = os.path.join(os.path.dirname(__file__), "templates")
bp = Blueprint("cam_strobe", __name__, url_prefix="/cam_strobe", template_folder=template_folder_path, static_folder="static")

heaters: dict[int, Heater] = {i: Heater(spi_handler, i, getattr(Holder, f"PORT_HEATER{i}")) for i in range(1, 5)}


@bp.route("/camera-type", methods=["GET", "POST"])
def camera_type():
    if request.method == "GET":
        if type(strobe_cam.camera).__name__ == "MakoCamera":
            camera_name = "mako"
        elif type(strobe_cam.camera).__name__ == "PiCamera":
            camera_name = "pi"
        else:
            camera_name = "none"
        return jsonify({"camera_name": camera_name})
    
    elif request.method == "POST":
        data = request.json
        camera_name = data.get("camera_name")
        strobe_cam.set_camera(camera_name)
        return jsonify({"status": "success"})


@bp.route("/get-frame", methods=["GET"])
def get_frame():
    camera = strobe_cam.camera
    config = load_config()
    camera_config = {}
    if config:
        camera_config = config.get("plugins", {}).get("devices", {}).get("pi_camera", {})

    return Response(
        web_frame_generator(camera, camera_config), mimetype="multipart/x-mixed-replace; boundary=frame"
    )       

@bp.route("/list-images", methods=["GET"])
def list_images():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    captures = os.listdir(CAPTURES_PATH)
    captures = list(filter(lambda x: x.endswith(".jpg"), captures))
    captures_with_dates = [
        (capture, datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(CAPTURES_PATH, capture))).strftime("%Y-%m-%d %H:%M:%S"))
        for capture in captures
    ]
    captures_with_dates.sort(key=lambda x: x[1], reverse=True)
    returned_captures = captures_with_dates[(page - 1) * per_page:page * per_page]
    return jsonify(returned_captures)


@bp.route("/capture", methods=["POST"])
def capture():
    frame = strobe_cam.capture_frame()
    frame_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    frame_name = f"{frame_timestamp}.jpg"
    cv2.imwrite(os.path.join(CAPTURES_PATH, frame_name), cv2.imdecode(frame, cv2.IMREAD_COLOR))
    return jsonify({"status": "success", "frame_name": frame_name})


@bp.route("/capture-rename", methods=["POST"])
def capture_rename():
    data = request.json
    old_name = data.get("old_name")
    new_name = data.get("new_name").rsplit(".", maxsplit=1)[0] + ".jpg"
    os.rename(os.path.join(CAPTURES_PATH, old_name), os.path.join(CAPTURES_PATH, new_name))
    return jsonify({"status": "success"})


@bp.route("/camera-config", methods=["GET", "POST"])
def camera_config():
    if request.method == "GET":
        camera = strobe_cam.camera
        features = camera.list_features()
        features = json.dumps(features, default=str)
        features = json.loads(features)
        return jsonify(features)
    elif request.method == "POST":
        data = request.json
        strobe_cam.camera.set_config(data)
        return jsonify({"status": "success"})


@bp.route("/strobe-period", methods=["GET", "POST"])
def strobe_period():
    camera = strobe_cam.camera
    strobe = strobe_cam.strobe
    if request.method == "GET":
        return jsonify({"strobe_period_us": strobe.strobe_period_ns / 1000})
    elif request.method == "POST":
        data = request.json
        strobe_period_ns = int(data.get("strobe_period_us")) * 1000
        strobe_cam.set_timing(strobe_period_ns)
        return jsonify({"status": "success"})
    


@bp.route("/heater-config", methods=["GET", "POST"])
def on_heater(data):
    if request.method == "GET":
        pass

    elif request.method == "POST":
        data = request.json

        if data["cmd"] == "temp_c_target":
            index = data["parameters"]["index"]
            temp_c_target = data["parameters"]["temp_c_target"]
            valid = heaters[index].set_temp(temp_c_target)
        elif data["cmd"] == "pid_enable":
            index = data["parameters"]["index"]
            enabled = data["parameters"]["on"]
            valid = heaters[index].set_pid_running(enabled)
        elif data["cmd"] == "power_limit_pc":
            index = data["parameters"]["index"]
            power_limit_pc = data["parameters"]["power_limit_pc"]
            valid = heaters[index].set_heat_power_limit_pc(power_limit_pc)
        elif data["cmd"] == "autotune":
            index = data["parameters"]["index"]
            enabled = data["parameters"]["on"]
            temp = data["parameters"]["temp"]
            heaters[index].autotune_target_temp = temp
            valid = heaters[index].set_autotune(enabled)
        elif data["cmd"] == "stir":
            index = data["parameters"]["index"]
            enabled = data["parameters"]["on"]
            speed = data["parameters"]["speed"]
            heaters[index].stir_target_speed = speed
            valid = heaters[index].set_stir_running(enabled)

        if index >= 0:
            heaters[index].update()
            heaters_data = {index: heaters[index].data}
            # emit_heaters_data()

