import threading
import sys
import cv2
from typing import Callable, Optional
from vimba import (
    Vimba,
    Camera,
    Frame,
    FrameStatus,
    VimbaCameraError,
    VimbaFeatureError,
    intersect_pixel_formats,
    OPENCV_PIXEL_FORMATS,
    COLOR_PIXEL_FORMATS,
    MONO_PIXEL_FORMATS,
    CommandFeature,
)

from vimba.error import VimbaCameraError
import time
import traceback

from queue import Queue
from threading import Event, Thread


class MakoCamera:

    frame_queue = Queue(1)
    cam_running_event = Event()
    capture_flag = Event()
    capture_queue = Queue(1)

    def __init__(self, cam_id: Optional[str] = None):
        self.cam_id = cam_id
        self.frame_callback: Optional[Callable[[], None]] = None
        with Vimba.get_instance():
            self.cam = self.get_camera(self.cam_id)

    def set_frame_callback(self, callback: Optional[Callable[[], None]]):
        self.frame_callback = callback

    def list_features(self):
        features = []
        try:
            with Vimba.get_instance():
                with self.cam:
                    for feature in self.cam.get_all_features():
                        type_ = feature.get_type().__name__
                        access_mode = feature.get_access_mode()
                        feature_dict = {
                            "name": feature.get_name(),
                            "access_mode": access_mode,
                            "display_name": feature.get_display_name(),
                            "tooltip": feature.get_tooltip(),
                            "description": feature.get_description(),
                            "type": type_,
                            "sfnc_namespace": feature.get_sfnc_namespace(),
                            "unit": feature.get_unit(),
                        }
                        if type_ == "EnumFeature":
                            if access_mode[0]:
                                feature_dict["value"] = feature.get()
                            feature_dict["all_entries"] = feature.get_all_entries()
                            feature_dict["available_entries"] = feature.get_available_entries()
                            feature_dict["category"] = feature.get_category()
                            feature_dict["flags"] = feature.get_flags()

                        elif type_ == "FloatFeature":
                            if access_mode[0]:
                                feature_dict["value"] = feature.get()
                            if access_mode[1]:
                                feature_dict["range"] = feature.get_range()
                                feature_dict["increment"] = feature.get_increment()
                        elif type_ == "IntFeature":
                            if access_mode[0]:
                                feature_dict["value"] = feature.get()
                            if access_mode[1]:
                                feature_dict["range"] = feature.get_range()
                                feature_dict["incremen0t"] = feature.get_increment()
                        elif type_ == "StringFeature":
                            if access_mode[0]:
                                feature_dict["value"] = feature.get()
                            # feature_dict['value'] = feature.get()

                        elif type_ == "BoolFeature":
                            if access_mode[0]:
                                feature_dict["value"] = feature.get()
                            # feature_dict['value'] = feature.get()
                        elif type_ == "CommandFeature":
                            if access_mode[0]:
                                feature_dict["value"] = feature.get()
                            feature_dict["flags"] = feature.get_flags()

                        features.append(feature_dict)
                return features
        except VimbaCameraError:
            return []

    def generate_frames(self, config):
        try:
            with Vimba.get_instance():
                with self.cam:
                    self.setup_camera(config)
                    # print(list_features())
                    # cam.start_streaming(handler=frame_handler, buffer_count=1000)
                    self.cam_running_event.set()
                    try:
                        while self.cam_running_event.is_set():
                            if self.frame_callback:
                                self.frame_callback()
                            frame: Frame = self.cam.get_frame()
                            # frame = frame_queue.get()

                            opencv_image = frame.as_opencv_image()

                            _, buffer = cv2.imencode(".jpg", opencv_image)
                            if self.capture_flag.is_set():
                                self.capture_queue.put(buffer)
                                self.capture_flag.clear()
                            yield buffer
                    finally:
                        # self.frame_queue.queue.clear()
                        self.cam.stop_streaming()
        except VimbaCameraError:
            return ""

    def get_camera(self, cam_id: Optional[str] = None) -> Camera:
        try:
            with Vimba.get_instance() as vimba:
                if cam_id:
                    try:
                        return vimba.get_camera_by_id(cam_id)

                    except VimbaCameraError:
                        print("Failed to access Camera '{}'. Abort.".format(cam_id))

                else:
                    cams = vimba.get_all_cameras()
                    if not cams:
                        print("No Cameras accessible. Abort.")

                    return cams[0]
        except:
            return None

    def setup_camera(self, config=None):
        failed_features = {}
        try:
            with Vimba.get_instance() as vimba:
                with self.cam:

                    #     pass
                    for key, value in config.items():
                        try:
                            feature = self.cam.get_feature_by_name(key)
                            access_mode = feature.get_access_mode()
                            if access_mode[1]:
                                # print(feature.get_type())
                                if feature.get_type() == CommandFeature:
                                    continue
                                feature.set(value)
                                print("Set feature: ", key, " to ", value)
                            else:
                                print("Feature ", key, " is read-only")
                        except Exception as e:
                            failed_features[key] = str(e)
                            print("Failed to set feature: ", key)
                            # print(traceback.format_exc())

                    try:
                        self.cam.GVSPAdjustPacketSize.run()

                        while not self.cam.GVSPAdjustPacketSize.is_done():
                            pass

                    except (AttributeError, VimbaFeatureError):
                        pass

                    cv_fmts = intersect_pixel_formats(self.cam.get_pixel_formats(), OPENCV_PIXEL_FORMATS)
                    color_fmts = intersect_pixel_formats(cv_fmts, COLOR_PIXEL_FORMATS)
                    try:
                        if color_fmts:
                            self.cam.set_pixel_format(color_fmts[0])

                        else:
                            mono_fmts = intersect_pixel_formats(cv_fmts, MONO_PIXEL_FORMATS)

                            if mono_fmts:
                                self.cam.set_pixel_format(mono_fmts[0])

                            else:
                                print("Camera does not support a OpenCV compatible format natively. Abort.")
                    except:
                        pass
            return failed_features
        except VimbaCameraError:
            return failed_features

    def capture_image(self):
        self.capture_flag.set()

    def get_capture(self):
        return self.capture_queue.get()
    
    def close(self):
        self.cam_running_event.clear()
        self.cam.stop_streaming()


mako_camera = MakoCamera()
