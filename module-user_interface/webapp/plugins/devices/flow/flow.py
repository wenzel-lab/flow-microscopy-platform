import traceback
from ..spi_handler import SPIHandler

class Flow:
    DEVICE_ID = "MICROFLOW"
    STX = 2
    PRESSURE_SHIFT = 3
    PRESSURE_SCALE = 1 << PRESSURE_SHIFT

    PACKET_TYPE_GET_ID = 1
    PACKET_TYPE_SET_PRESSURE_TARGET = 2
    PACKET_TYPE_GET_PRESSURE_TARGET = 3
    PACKET_TYPE_GET_PRESSURE_ACTUAL = 4
    PACKET_TYPE_SET_FLOW_TARGET = 5
    PACKET_TYPE_GET_FLOW_TARGET = 6
    PACKET_TYPE_GET_FLOW_ACTUAL = 7
    PACKET_TYPE_SET_CONTROL_MODE = 8
    PACKET_TYPE_GET_CONTROL_MODE = 9

    NUM_CONTROLLERS = 4

    def __init__(self, spi_handler: SPIHandler, device_port, reply_pause_s):
        self.spi_handler = spi_handler
        self.device_port = device_port
        self.reply_pause_s = reply_pause_s

    def read_bytes(self, bytes_):
        return self.spi_handler.read_bytes(bytes_)
    
    def packet_read(self):
        valid = False
        type_ = None
        self.spi_handler.spi_select_device(self.device_port)
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
        self.spi_handler.spi_select_device(self.device_port)
        self.spi_handler.spi.xfer2(msg)

    def packet_query(self, type_, data):
        try:
            self.spi_handler.spi_lock()
            self.packet_write(type_, data)
            self.spi_handler.pi_wait_s(self.reply_pause_s)
            valid = True
            data_read = []
            type_read = 0x100
            try:
                while valid and (type_read != type_) and (type_read != 0):
                    valid, type_read, data_read = self.packet_read()
            except:
                valid = False
            self.spi_handler.spi_deselect_current()
        except:
            traceback.print_exc()
        finally:
            self.spi_handler.spi_release()

        return valid, data_read
    

    def get_id(self):
        valid, data = self.packet_query(self.PACKET_TYPE_GET_ID, [])
        if valid:
            id = bytes(data[1:-1]).decode("ascii")
            id_valid = (id == self.DEVICE_ID)
            try:
                checksum_okay = data[0] == 0
            except:
                checksum_okay = False
        else:
            id = 0
            id_valid = False
            checksum_okay = False
        return id, id_valid, checksum_okay
    
    def set_pressure_all(self, pressures_mbar):
        data_bytes = []
        for i in range(self.NUM_CONTROLLERS):
            mask = 1 << i
            pressure_fp = int(pressures_mbar[i] * self.PRESSURE_SCALE)
            data_bytes.extend(
                [mask] + list(pressure_fp.to_bytes(2, "little", signed=False))
            )
        valid, data = self.packet_query(
            self.PACKET_TYPE_SET_PRESSURE_TARGET, data_bytes
        )
        return valid and (data[0] == 0)
    

    def set_presure(self, indices, pressures_mbar):
        data_bytes = []
        for i in range(len(indices)):
            mask = 1 << indices[i]
            pressure_fp = int(pressures_mbar[i] * self.PRESSURE_SCALE)
            data_bytes.extend(
                [mask] + list(pressure_fp.to_bytes(2, "little", signed=False))
            )
        valid, data = self.packet_query(
            self.PACKET_TYPE_SET_PRESSURE_TARGET, data_bytes
        )
        return valid and (data[0] == 0)
    
    def set_control_mode(self, indices, control_modes):
        data_bytes = []
        for i in range(len(indices)):
            mask = 1 << indices[i]
            control_mode = control_modes[i]
            data_bytes.extend([mask, control_mode])
        valid, data = self.packet_query(
            self.PACKET_TYPE_SET_CONTROL_MODE, data_bytes
        )
        return valid and (data[0] == 0)
    
    def get_pressure_target(self):
        valid, data = self.packet_query(self.PACKET_TYPE_GET_PRESSURE_TARGET, [])
        count = int((len(data) - 1) / 2)
        pressures_mbar = []
        for i in range(count):
            index = 1 + (i << 1)
            pressure_mbar = (
                int.from_bytes(
                    data[index : index + 2], byteorder="little", signed=False
                )
                / self.PRESSURE_SCALE
            )
            pressures_mbar.extend([pressure_mbar])
        return (valid and (data[0] == 0), pressures_mbar)
    

    def get_pressure_actual(self):
        valid, data = self.packet_query(self.PACKET_TYPE_GET_PRESSURE_ACTUAL, [])
        count = int((len(data) - 1) / 2)
        pressures_mbar = []
        for i in range(count):
            index = 1 + (i << 1)
            pressure_mbar = (
                int.from_bytes(data[index : index + 2], byteorder="little", signed=True)
                / self.PRESSURE_SCALE
            )
            pressures_mbar.extend([pressure_mbar])
        return (valid and (data[0] == 0), pressures_mbar)
    

    def get_flow_actual(self):
        valid, data = self.packet_query(self.PACKET_TYPE_GET_FLOW_ACTUAL, [])
        count = int((len(data) - 1) / 2)
        flows_ul_hr = []
        for i in range(count):
            index = 1 + (i << 1)
            flow_ul_hr = int.from_bytes(
                data[index : index + 2], byteorder="little", signed=True
            )
            flows_ul_hr.extend([flow_ul_hr])
        return (valid and (data[0] == 0), flows_ul_hr)

    def get_control_modes(self):
        valid, data = self.packet_query(self.PACKET_TYPE_GET_CONTROL_MODE, [])
        count = len(data) - 1
        control_modes = []
        for i in range(count):
            index = 1 + i
            control_mode = data[index]
            control_modes.extend([control_mode])
        return (valid and (data[0] == 0), control_modes)
    


