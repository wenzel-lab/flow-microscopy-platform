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
    DEFAULT_TRIGGER_GPIO_PIN = 18  # GPIO pin for PIC trigger (configurable)

    def __init__(self, strobe_instance: Strobe, background_thread=False, led_board_pin=29, trigger_gpio_pin=18):
        self.led_board_pin = led_board_pin
        self.trigger_gpio_pin = trigger_gpio_pin
        self.camera = None
        self.thread: threading.Thread = None
        self.strobe = strobe_instance
        self.trigger_mode = "software"  # "software" or "hardware" (if camera XVS available)
        self.strobe_enabled = False
        
        # Initialize GPIO for PIC trigger (software-triggered mode)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_gpio_pin, GPIO.OUT)
        GPIO.output(self.trigger_gpio_pin, GPIO.LOW)
        
        # self.init_led_pin()
        if background_thread:
            self.start_thread()
        
    def set_camera(self, camera_name):
        if camera_name == "mako":
            from ...devices.mako_camera.core import mako_camera
            self.camera = mako_camera
            self.init_strobe()
        elif camera_name == "pi":
            self.camera = pi_camera
            self.init_strobe()
        else:
            raise ValueError("Invalid camera name")

    def init_strobe(self):
        # Configure strobe for hardware trigger mode (PIC will wait for GPIO trigger)
        self.strobe.set_trigger_mode(True)  # Hardware trigger mode (PIC waits for T1G input)
        self.strobe.set_hold(0)
        # Don't enable yet - wait for timing to be set
        
    def frame_callback_trigger(self):
        """
        Frame callback - triggers PIC via GPIO pin.
        This is called on each frame capture (software callback has ~1-5ms jitter,
        but PIC hardware timing is still precise).
        """
        if self.strobe_enabled:
            # Generate short pulse to PIC T1G input (hardware trigger)
            GPIO.output(self.trigger_gpio_pin, GPIO.HIGH)
            time.sleep(0.000001)  # 1us pulse (PIC detects edge)
            GPIO.output(self.trigger_gpio_pin, GPIO.LOW)


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
            
            # For hardware trigger mode, we don't need complex timing calculations
            # Camera is master - just set strobe timing parameters
            wait_ns = 32  # Small delay after trigger before strobe fires
            valid, _, _ = self.strobe.set_timing(wait_ns, strobe_period_ns)
            
            if valid:
                # Set frame callback to trigger PIC on each frame
                if self.camera:
                    self.camera.set_frame_callback(self.frame_callback_trigger)
                
                # Configure camera (simpler - no complex calculations needed)
                shutter_speed_us = int(strobe_period_ns / 1000) + 1000  # Add some margin
                framerate = min(60, int(1_000_000 / shutter_speed_us))
                self.camera.set_config({"FrameRate": framerate, "ShutterSpeed": shutter_speed_us})
                
                # Enable strobe (will wait for GPIO trigger from frame callback)
                self.strobe.set_enable(True)
                self.strobe_enabled = True
                
                print("Strobe period set to {}ns, framerate={}fps".format(strobe_period_ns, framerate))
            else:
                print("Invalid strobe period")
        except:
            import traceback
            print(traceback.format_exc())

    def _prepare_timing(self, pre_padding_ns, strobe_period_ns, post_padding_ns):
        """
        Legacy method - kept for compatibility.
        For hardware trigger mode, timing is simpler (no complex calculations).
        """
        shutter_speed_us = int((strobe_period_ns + pre_padding_ns + post_padding_ns) / 1000)
        framerate = 1_000_000 / shutter_speed_us
        if framerate > 60:  
            framerate = 60
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
