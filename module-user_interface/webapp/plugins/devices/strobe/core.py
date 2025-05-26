import traceback
import RPi.GPIO as GPIO
from ...interfaces.spi_handler import SPIHandler, spi_handler


class Strobe:
    STX = 2
    DEFAULT_PORT = 24
    DEFAULT_REPLY_PAUSE_S = 0.1

    def __init__(self, spi_handler: SPIHandler, device_port: int = 24, reply_pause_s: float = 0.1):
        self._spi_handler = spi_handler
        self._device_port = device_port
        self._reply_pause_s = reply_pause_s
        self._spi_handler.initialize_port(device_port, GPIO.OUT, GPIO.HIGH)
        self._enabled = False
        self._hold = False
        self._strobe_period_ns = 0
        self._cam_read_time_us = 0

    @property
    def enabled(self):
        return self._enabled
    
    @property
    def hold(self):
        return self._hold
    
    @property
    def strobe_period_ns(self):
        return self._strobe_period_ns
    
    @property
    def cam_read_time_us(self):
        return self._cam_read_time_us      

    def read_bytes(self, bytes_):
        return self._spi_handler.read_bytes(bytes_)

    def packet_read(self):
        valid = False
        type_ = None
        self._spi_handler.spi_select_device(self._device_port)
        data = self.read_bytes(1)
        if data[0] == self.STX:
            data.extend(self.read_bytes(2))
            size = data[1]
            type_ = data[2]
            data.extend(self.read_bytes(size - 3))
            checksum = sum(data) & 0xFF
            if checksum == 0:
                data = data[3 : (size - 1)]
                valid = True
        if not valid:
            data = []
        return valid, type_, data

    def packet_write(self, type_, data):
        msg = [2, len(data) + 4, type_] + data
        checksum = (-(sum(msg) & 0xFF)) & 0xFF
        msg.append(checksum)
        self._spi_handler.spi_select_device(self._device_port)
        self._spi_handler.spi.xfer2(msg)

    def packet_query(self, type_, data):
        valid = False
        data_read = []

        try:
            self._spi_handler.spi_lock()
            self.packet_write(type_, data)
            self._spi_handler.pi_wait_s(self._reply_pause_s)
            valid = True
            type_read = 0x100
            try:
                while valid and (type_read != type_) and (type_read != 0):
                    valid, type_read, data_read = self.packet_read()
            except:
                print(traceback.format_exc())
                valid = False
            self._spi_handler.spi_deselect_current()
        except:
            traceback.print_exc()
        finally:
            self._spi_handler.spi_release()

        return valid, data_read

    def set_enable(self, enable):
        enabled = 1 if enable else 0
        valid, data = self.packet_query(1, [enabled])
        self._enabled = valid and (data[0] == 0)
        return self._enabled

    def set_timing(self, wait_ns, period_ns):
        wait_ns_bytes = list(wait_ns.to_bytes(4, "little", signed=False))
        period_ns_bytes = list(period_ns.to_bytes(4, "little", signed=False))
        valid, data = self.packet_query(2, wait_ns_bytes + period_ns_bytes)
        actual_wait_ns = int.from_bytes(data[1:5], byteorder="little", signed=False)
        actual_period_ns = int.from_bytes(data[5:9], byteorder="little", signed=False)
        print("data={}, wait={}, period={}, wait_bytes={}".format(data, actual_wait_ns, actual_period_ns, data[1:5]))
        if valid and (data[0] == 0):
            self._strobe_period_ns = actual_period_ns
        return ((valid and (data[0] == 0)), actual_wait_ns, actual_period_ns)

    def set_hold(self, hold):
        valid, data = self.packet_query(3, [1 if hold else 0])
        self._hold = valid and (data[0] == 0)
        return self._hold

    def get_cam_read_time(self):
        valid, data = self.packet_query(4, [])
        cam_read_time_us = int.from_bytes(data[1:3], byteorder="little", signed=False)
        if valid and (data[0] == 0):
            self._cam_read_time_us = cam_read_time_us
        return (valid and (data[0] == 0), cam_read_time_us)

strobe = Strobe(spi_handler, Strobe.DEFAULT_PORT, Strobe.DEFAULT_REPLY_PAUSE_S)