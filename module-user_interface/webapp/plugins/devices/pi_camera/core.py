from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import os
import time

from typing import Callable, Optional
import numpy as np
from queue import Queue
from threading import Event

class PiCamera:
    frame_queue = Queue(1)
    cam_running_event = Event()
    capture_flag = Event()
    capture_queue = Queue(1)
    frame_callback: Optional[Callable[[], None]] = None
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        try:
            cam = Picamera2()
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
        }
        self.frame_rate = 120

    def set_frame_callback(self, callback: Optional[Callable[[], None]]):
        self.frame_callback = callback
        
    def list_features(self):
        features = [
            
        ]
        # features = [
        #     {
        #         "name": "Height",
        #         "display_name": "Height",
        #         "tooltip": "Height of the video",
        #         "description": "Height of the video",
        #         "type": "int",
        #         "unit": "pixels",
        #         "range": (1, 2464),
        #         "access_mode": (True, True),
        #         "value": self.config["size"][1]
        #     },
        #     {
        #         "name": "Width",
        #         "display_name": "Width",
        #         "tooltip": "Width of the video",
        #         "description": "Width of the video",
        #         "type": "int",
        #         "unit": "pixels",
        #         "range": (1, 3280),
        #         "access_mode": (True, True),
        #         "value": self.config["size"][0]
        #     },
        #     {
        #         "name": "FrameRate",
        #         "display_name": "Frame Rate",
        #         "tooltip": "Frame Rate of the video",
        #         "description": "Frame Rate of the video",
        #         "type": "int",
        #         "unit": "fps",
        #         "range": (1, 206),
        #         "access_mode": (True, True),
        #         "value": self.frame_rate
        #     },
        #     {
        #         "name": "ExposureTime",
        #         "display_name": "Exposure",
        #         "tooltip": "Frame Rate of the video",
        #         "description": "Frame Rate of the video",
        #         "type": "int",
        #         "unit": "fps",
        #         "range": (1, 10_000),
        #         "access_mode": (True, True),
        #         "value": self.frame_rate
        #     }

        # ]
        return features
        
    def setup_camera(self, config):
        failed_features = {}
        try:
            self.config = {
                "size": [
                    int(config["width"]),
                    int(config["height"]),
                ]
            }
        except Exception as e:
            for key in config:
                failed_features[key] = str(e)
        return failed_features

    def generate_frames(self, config=None):
        self.cam_running_event.clear()
        self.cam.stop()
        self.cam.configure(self.cam.create_video_configuration(main={"size": self.config["size"]}))
        self.cam.set_controls({"FrameRate": self.config["FrameRate"]})

        print(self.cam.controls)
        self.cam.start()
        self.cam_running_event.set()
        frame_interval = 1.0 / self.config["FrameRate"]
        print(self.config["FrameRate"])
        print(frame_interval)
        while self.cam_running_event.is_set():
            start_time = time.time()
            if self.frame_callback:
                self.frame_callback()
            frame = self.cam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            ret, buffer = cv2.imencode('.jpg', frame)
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

    def get_capture(self) -> np.ndarray[np.uint8]:
        return self.capture_queue.get()
    
    def close(self):
        self.cam_running_event.clear()
        self.cam.stop()
        self.cam.close()

    def set_config(self, configs):
        self.cam_running_event.clear()
        self.cam.stop()
        if "Height" in configs:
            self.config["size"][1] = int(configs["Height"])
            del configs["Height"]
        if "Width" in configs:
            self.config["size"][0] = int(configs["Width"])
            del configs["Width"]

        for key, value in configs.items():
            if type(value) == str and value.isdigit():
                value = int(value)
                configs[key] = value
                self.config[key] = value
        self.cam.configure(self.cam.create_video_configuration(main={"size": self.config["size"]}))
        self.cam.set_controls(configs)
        print(configs)
        # self.cam.start()
        

pi_camera = PiCamera()