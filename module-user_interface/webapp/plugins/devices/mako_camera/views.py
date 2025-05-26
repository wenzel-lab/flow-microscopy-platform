import cv2
import threading
from vimba import Vimba
from vimba.feature import FeatureTypes

# from .utils import get_camera, setup_camera, Camera, FrameStatus, Frame, frame_queue, cam_running_event
from .core import mako_camera
from ...utils import load_config, save_config, web_frame_generator

from flask import Blueprint, Response, current_app
from flask import render_template, request, jsonify
import json

from queue import Queue
from threading import Event


bp = Blueprint("mako_camera", __name__, url_prefix="/mako_camera", template_folder="templates")


@bp.route("/get-frame")
def mako_camera_stream():

    config = load_config()
    vimba_config = {}
    if config:
        vimba_config = config.get("plugins", {}).get("devices", {}).get("mako_camera", {})

    return Response(
        web_frame_generator(mako_camera, vimba_config), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@bp.route("/configure", methods=["GET", "POST"])
def configure():
    if request.method == "POST":
        print(request.form.to_dict())
        failed_features = mako_camera.setup_camera(request.form.to_dict())
        features_list = mako_camera.list_features()
        current_values = {
            feature["name"]: str(feature["value"])
            for feature in features_list
            if "value" in feature and feature["name"] not in failed_features
        }
        current_config = load_config()
        current_config["plugins"]["devices"]["mako_camera"] = current_values
        save_config(current_config)
        if failed_features:
            return render_template(
                "mako_camera/configure_camera.html", cam_features=mako_camera.list_features(), failed_features=failed_features
            )

    mako_camera.cam_running_event.clear()
    return render_template("mako_camera/configure_camera.html", cam_features=mako_camera.list_features())


@bp.route("/config-options")
def get_features():

    features = mako_camera.list_features()
    response = Response(response=json.dumps(features, default=str), status=200, mimetype="application/json")
    return response
