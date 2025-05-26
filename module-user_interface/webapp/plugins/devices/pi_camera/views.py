import cv2
import threading
import time


# from .utils import MakoCamera
from .core import pi_camera

from ...utils import load_config, save_config, web_frame_generator

from flask import Blueprint, Response, current_app
from flask import render_template, request, jsonify
import json


bp = Blueprint("pi_camera", __name__, url_prefix="/pi_camera", template_folder="templates")



@bp.route("/get-frame")
def pi_camera_stream():

    config = load_config()
    vimba_config = {}
    if config:
        vimba_config = config.get("plugins", {}).get("devices", {}).get("pi_camera", {})
    return Response(web_frame_generator(pi_camera, vimba_config), mimetype="multipart/x-mixed-replace; boundary=frame")


@bp.route("/configure", methods=["GET", "POST"])
def configure():
    if request.method == "POST":
        print(request.form.to_dict())
        failed_features = pi_camera.setup_camera(request.form.to_dict())
        features_list = pi_camera.list_features()
        current_values = {feature["name"]: str(feature["value"]) for feature in features_list if "value" in feature and feature["name"] not in failed_features}
        current_config = load_config()
        current_config["plugins"]["devices"]["pi_camera"] = current_values
        save_config(current_config)
        if failed_features:
            return render_template(
                "pi_camera/configure_camera.html", cam_features=pi_camera.list_features(), failed_features=failed_features
            )


    pi_camera.cam_running_event.clear()
    return render_template("pi_camera/configure_camera.html", cam_features=pi_camera.list_features())


@bp.route("/config-options")
def features():
    features = pi_camera.list_features()
    response = Response(response=json.dumps(features, default=str), status=200, mimetype="application/json")
    return response


@bp.route("/capture")
def capture():
    pi_camera.capture_image()
    return Response(response="Capture initiated", status=200, mimetype="text/plain")

@bp.route("/get-capture")
def get_capture():
    image = pi_camera.get_capture()
    bytes_image = image.tobytes()
    return Response(bytes_image, mimetype="image/jpeg")
