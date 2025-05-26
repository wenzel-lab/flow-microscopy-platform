from flask import Flask, Response
from picamera import PiCamera
import cv2
import os
import io
import time

from typing import Callable, Optional
import numpy as np
from queue import Queue
from threading import Event

class PiCamera32:
    frame_queue = Queue(1)
    cam_running_event = Event()
    capture_flag = Event()
    capture_queue = Queue(1)
    frame_callback: Optional[Callable[[], None]] = None
    cam: PiCamera = None
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        try:
            cam = PiCamera()
        except:
            cam = None
    
    def __init__(self):
        self.config = {
            "size": [
                640,
                480
            ],
            'ExposureTime': 10000,
            'FrameRate': 120,
            'ShutterSpeed': 10000
        }
        self.frame_rate = 120

    def set_frame_callback(self, callback: Optional[Callable[[], None]]):
        self.frame_callback = callback
        
    def list_features(self):
        features = []
        features = [
            {
                "name": "Height",
                "display_name": "Height",
                "tooltip": "Height of the video",
                "description": "Height of the video",
                "type": "int",
                "unit": "pixels",
                "range": (1, 2464),
                "access_mode": (True, True),
                "value": self.config["size"][1]
            },
            {
                "name": "Width",
                "display_name": "Width",
                "tooltip": "Width of the video",
                "description": "Width of the video",
                "type": "int",
                "unit": "pixels",
                "range": (1, 3280),
                "access_mode": (True, True),
                "value": self.config["size"][0]
            },
            {
                "name": "FrameRate",
                "display_name": "Frame Rate",
                "tooltip": "Frame Rate of the video",
                "description": "Frame Rate of the video",
                "type": "int",
                "unit": "fps",
                "range": (1, 206),
                "access_mode": (True, True),
                "value": self.config["FrameRate"]
            },
            {
                "name": "ShutterSpeed",
                "display_name": "Exposure",
                "tooltip": "Frame Rate of the video",
                "description": "Frame Rate of the video",
                "type": "int",
                "unit": "ms",
                "range": (1, 10_000),
                "access_mode": (True, True),
                "value": self.config["ShutterSpeed"]
            },
            {
                "name": "AWSMode",
                "display_name": "Auto White Balance",
                "tooltip": "Auto White Balance",
                "description": "Auto White Balance",
                "type": "bool",
                "access_mode": (True, True),
                "value": True
            },
            {
                "name": "ExposureMode",
                "display_name": "Exposure Mode",
                "tooltip": "Exposure Mode",
                "description": "Exposure Mode",
                "type": "str",
                "access_mode": (True, True),
                "value": "off"
            }

        ]
        return features
    
    def get_current_resolution(self):
        return self.config["size"]

        
    def setup_camera(self, config):
        failed_features = {}
        # try:
        #     self.config = {
        #         "size": [
        #             int(config["width"]),
        #             int(config["height"]),
        #         ]
        #     }
        # except Exception as e:
        #     for key in config:
        #         failed_features[key] = str(e)
        self.cam.resolution = ( 1024, 768 )
        self.cam.awb_mode = 'auto'
        self.cam.exposure_mode = 'off'
        return failed_features

    def generate_frames(self, config=None):
        self.cam_running_event.clear()
        # self.cam.stop()
        # self.cam.configure(self.cam.create_video_configuration(main={"size": self.config["size"]}))
        # self.cam.set_controls({"FrameRate": self.config["FrameRate"]})

        # print(self.cam.controls)
        # self.cam.start()
        self.cam_running_event.set()
        frame_interval = 1.0 / self.config["FrameRate"]
        print(self.config["FrameRate"])
        print(frame_interval)
        while self.cam_running_event.is_set():
            start_time = time.time()
            if self.frame_callback:
                self.frame_callback()
            # frame = self.cam.capture_array()
            stream = io.BytesIO()  # Define stream as an in-memory byte stream
            for _ in self.cam.capture_continuous(stream, 'jpeg', use_video_port=True):
                # print("here")
                stream.seek(0)  # Rewind the stream to the beginning
                data = np.frombuffer(stream.getvalue(), dtype=np.uint8)
                # frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
                # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                stream.truncate(0)  # Clear the stream for the next frame
                break
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            # ret, buffer = cv2.imencode('.jpg', frame)
            buffer = data
            # print(buffer)
            if self.capture_flag.is_set():
                self.capture_queue.put(buffer)
                self.capture_flag.clear()
            yield buffer
            # Ensure frame rate is respected
            elapsed_time = time.time() - start_time
            time.sleep(max(0, frame_interval - elapsed_time))
        self.cam.stop()

    def capture_image(self):
        self.capture_flag.set()

    def get_capture(self) -> np.ndarray:
        return self.capture_queue.get()
    
    def close(self):
        self.cam_running_event.clear()
        self.cam.stop()
        self.cam.close()

    def set_config(self, configs):
        self.cam_running_event.clear()
        formatted_configs = {}
        self.cam.awb_mode = 'auto'
        self.cam.exposure_mode = 'off'
        if "Height" in configs and configs["Height"]:
            self.config["size"][1] = int(configs["Height"])
            del configs["Height"]
        if "Width" in configs and configs["Width"]:
            self.config["size"][0] = int(configs["Width"])
            del configs["Width"]
        self.cam.resolution = (self.config["size"][0], self.config["size"][1])
        if "FrameRate" in configs and configs["FrameRate"]:
            self.config["FrameRate"] = int(configs["FrameRate"])
            del configs["FrameRate"]
        self.cam.framerate = self.config["FrameRate"]
        if "ShutterSpeed" in configs and configs["ShutterSpeed"]:
            self.config["ShutterSpeed"] = int(configs["ShutterSpeed"])
            del configs["ShutterSpeed"]
        self.cam.shutter_speed = self.config["ShutterSpeed"]

        
        
        # self.cam.stop()
        # if "Height" in configs:
        #     self.config["size"][1] = int(configs["Height"])
        #     del configs["Height"]
        # if "Width" in configs:
        #     self.config["size"][0] = int(configs["Width"])
        #     del configs["Width"]

        # for key, value in configs.items():
        #     if type(value) == str and value.isdigit():
        #         value = int(value)
        #         configs[key] = value
        #         self.config[key] = value
        # self.cam.configure(self.cam.create_video_configuration(main={"size": self.config["size"]}))
        # self.cam.set_controls(configs)
        # print(configs)
        # self.cam.start()
        

pi_camera = PiCamera32()