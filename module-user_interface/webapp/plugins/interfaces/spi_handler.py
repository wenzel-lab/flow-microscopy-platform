import spidev
import time
import RPi.GPIO as GPIO
from threading import Lock


class SPIHandler:

    def __init__(self, bus, mode, speed_hz, pin_mode=GPIO.BOARD):
        self.spi = spidev.SpiDev()
        GPIO.setmode(pin_mode)
        self.spi.open(bus, 0)
        self.spi.mode = mode
        self.spi.max_speed_hz = speed_hz
        self.current_device = None
        self.pi_lock = Lock()

    def initialize_port(self, port_number, mode, initial=None, pull_up_down=20):
        if mode == GPIO.OUT:
            if initial is None:
                initial = GPIO.LOW
            GPIO.setup(port_number, mode, initial=initial)
        else:
            GPIO.setup(port_number, mode, pull_up_down=pull_up_down)
        print("Port {} initialized".format(port_number))

    def spi_select_device(self, device):
        if (self.current_device is not None) and (device != self.current_device):
            GPIO.output(self.current_device, GPIO.HIGH)
            self.current_device = None

        if (device is not None) and (device != self.current_device):
            GPIO.output(device, GPIO.LOW)
            self.current_device = device

    def spi_deselect_current(self):
        if self.current_device is not None:
            GPIO.output(self.current_device, GPIO.HIGH)
            self.current_device = None

    def spi_lock(self):
        self.pi_lock.acquire()

    def spi_release(self):
        self.pi_lock.release()

    def pi_wait_s(self, seconds):
        time.sleep(seconds)

    def read_bytes(self, bytes_):
        data = []
        for x in range(bytes_):
            data.extend(self.spi.xfer2([0]))
        return data


spi_handler = SPIHandler(bus=0, mode=2, speed_hz=30_000)


if __name__ == "__main__":
    import traceback
    PORT_NONE = 0
    PORT_HEATER1 = 31
    PORT_HEATER2 = 33
    PORT_HEATER3 = 32
    PORT_HEATER4 = 36
    PORT_STROBE = 24
    PORT_FLOW = 26

    spi_handler = SPIHandler(0, 2, 30_000)
    spi_handler.initialize_port(PORT_STROBE, GPIO.OUT, GPIO.HIGH)
    # spi_handler.initialize_port(PORT_HEATER1, GPIO.OUT, GPIO.HIGH)
    # spi_handler.initialize_port(PORT_HEATER2, GPIO.OUT, GPIO.HIGH)
    # spi_handler.initialize_port(PORT_HEATER3, GPIO.OUT, GPIO.HIGH)
    # spi_handler.initialize_port(PORT_HEATER4, GPIO.OUT, GPIO.HIGH)
    # spi_handler.initialize_port(PORT_FLOW, GPIO.OUT, GPIO.HIGH)
    # spi_handler.spi_select_device(PORT_HEATER1)
    # spi_handler.spi_deselect_current()
    # spi_handler.spi_lock()
    # spi_handler.spi_release()
    # spi_handler.pi_wait_s(0.1)
