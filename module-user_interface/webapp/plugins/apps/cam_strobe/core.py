import cv2
import threading
import time

import RPi.GPIO as GPIO


from ...utils import load_config, save_config
from ...interfaces.spi_handler import SPIHandler, spi_handler
from ...devices.strobe.core import Strobe, strobe
from ...devices.pi_camera_32.core import pi_camera



class StrobeCam:
    
    DEFAULT_LED_BOARD_PIN = 29

    def __init__(self, strobe_instance: Strobe, background_thread=False, led_board_pin=29):
        self.led_board_pin = led_board_pin
        self.camera = None
        self.thread: threading.Thread = None
        self.strobe = strobe_instance
        
        # self.init_led_pin()
        if background_thread:
            self.start_thread()
        
    def set_camera(self, camera_name):
        if camera_name == "mako":
            from ...devices.mako_camera.core import mako_camera
        elif camera_name == "pi":
            self.camera = pi_camera
            self.init_strobe()
        else:
            raise ValueError("Invalid camera name")

    def init_strobe(self):
        
        # self.camera.set_frame_callback(self.send_led_pulse)
        self.strobe.set_enable(1)
        self.strobe.set_hold(0)


    def start_thread(self):
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):

        for frame in self.camera.generate_frames(config={}):
            if self.strobe_enabled:
                self.send_led_pulse()
            

    def set_timing(self, strobe_period_ns):
        try:
            strobe_period_ns = min(strobe_period_ns, 16_000_000)
            pre_padding_ns, strobe_period_ns, framerate = self._prepare_timing(32, strobe_period_ns, 20_000_000)
            valid, _, _ = self.strobe.set_timing(pre_padding_ns, strobe_period_ns)
            # valid, _, _ = self.strobe.set_timing(84032, strobe_period_ns)
            print("Strobe period set to {}ns".format(strobe_period_ns))
            self.optimize_fps_btn_enabled = True
            if valid:
                self.strobe_enabled = True
            else:
                print("Invalid strobe period")
        except:
            import traceback
            print(traceback.format_exc())

    def _prepare_timing(self, pre_padding_ns, strobe_period_ns, post_padding_ns):
        shutter_speed_us = int((strobe_period_ns + pre_padding_ns + post_padding_ns) / 1000)
        framerate = 1_000_000 / shutter_speed_us
        if framerate > 60:  
            framerate = 60
        # framerate = 10
        self.camera.set_config({"FrameRate": framerate, "ShutterSpeed": shutter_speed_us})

        # Inter-frame period in microseconds
        frame_rate_period_us = int(1000000 / float(framerate))

        # Dead time after frame, before sampling next frame
        strobe_pre_wait_us = frame_rate_period_us - shutter_speed_us

        # How long the strobe is set to wait before triggering
        pre_padding_ns = pre_padding_ns + (1000 * strobe_pre_wait_us)

        return pre_padding_ns, strobe_period_ns, framerate


    def capture_frame(self):
        self.camera.capture_image()
        capture = self.camera.get_capture()
        while capture is None:
            time.sleep(0.1)
            capture = self.camera.get_capture()
        return capture

    def optimize_fps(self):
        get_cam_read_time_us = 10_000
        get_cam_read_time_us_prev = 0
        strobe_post_padding_ns = 1_000_000
        tries = 10
        while abs(get_cam_read_time_us - get_cam_read_time_us_prev) > 1_000:
            get_cam_read_time_us_prev = get_cam_read_time_us
            self._prepare_timing(32, self.strobe_period_ns, strobe_post_padding_ns)
            # print( "strobe wait={}ns, strobe period={}ns, strobe padding={}ns".format( self.strobe_cam.strobe_wait_ns, self.strobe_cam.strobe_period_ns, strobe_post_padding_ns ) )
            _, get_cam_read_time_us = self.strobe.get_cam_read_time()
            # print( "get_cam_read_time_us={}".format( get_cam_read_time_us ) )
            strobe_post_padding_ns = (get_cam_read_time_us + 100) * 1_000

            tries = tries - 1
            if tries <= 0:
                break

    def init_led_pin(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.led_board_pin, GPIO.OUT)
        GPIO.output(self.led_board_pin, GPIO.LOW)

    def send_led_pulse(self):
        GPIO.output(self.led_board_pin, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(self.led_board_pin, GPIO.LOW)

    def close(self):
        self.strobe.set_enable(False)
        self.strobe.set_hold(False)
        self.camera.close()
        del self.thread

strobe_cam = StrobeCam(strobe_instance=strobe, background_thread=False)

# if __name__ == "__main__":
#     PORT_NONE = 0
#     PORT_HEATER1 = 31
#     PORT_HEATER2 = 33
#     PORT_HEATER3 = 32
#     PORT_HEATER4 = 36
#     PORT_STROBE = 24
#     PORT_FLOW = 26

#     spi_handler = SPIHandler(0, 0, 1000000)
#     strobe_cam = StrobeCam(spi_handler, PORT_STROBE, 0.1, "pi", background_thread=True)
#     frame = strobe_cam.capture_frame()
#     cv2.imwrite("/tmp/frame.jpg", cv2.imdecode(frame, cv2.IMREAD_COLOR))

#     strobe_cam.optimize_fps()
#     strobe_cam.close()

#     print("done")

#     exit(0)
