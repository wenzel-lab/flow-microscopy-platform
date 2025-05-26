import traceback
import time
import RPi.GPIO as GPIO
from ...interfaces.spi_handler import SPIHandler


class Holder:
    DEVICE_ID = "SAMPLE_HOLDER"
    STX = 2
    PRESSURE_SHIFT = 3
    TEMP_SCALE = 100
    PRESSURE_SCALE = 1 << PRESSURE_SHIFT
    PACKET_TYPE_GET_ID = 1
    PACKET_TYPE_TEMP_SET_TARGET = 2
    PACKET_TYPE_TEMP_GET_TARGET = 3
    PACKET_TYPE_TEMP_GET_ACTUAL = 4
    PACKET_TYPE_PID_SET_COEFFS = 5
    PACKET_TYPE_PID_GET_COEFFS = 6
    PACKET_TYPE_PID_SET_RUNNING = 7
    PACKET_TYPE_PID_GET_STATUS = 8
    PACKET_TYPE_AUTOTUNE_SET_RUNNING = 9
    PACKET_TYPE_AUTOTUNE_GET_RUNNING = 10
    PACKET_TYPE_AUTOTUNE_GET_STATUS = 11
    PACKET_TYPE_STIR_SET_RUNNING = 12
    PACKET_TYPE_STIR_GET_STATUS = 13
    PACKET_TYPE_STIR_SPEED_GET_ACTUAL = 14
    PACKET_TYPE_HEAT_POWER_LIMIT_SET = 15
    PACKET_TYPE_HEAT_POWER_LIMIT_GET = 16
    PORT_HEATER1 = 31
    PORT_HEATER2 = 33
    PORT_HEATER3 = 32
    PORT_HEATER4 = 36

    def __init__(self, spi_handler: SPIHandler, device_port, reply_pause_s):
        self.spi_handler = spi_handler
        self.spi_handler.initialize_port(device_port, GPIO.OUT, GPIO.HIGH)
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
        valid = False
        data_read = []
        try:
            self.spi_handler.spi_lock()
            self.packet_write(type_, data)
            self.spi_handler.pi_wait_s(self.reply_pause_s)
            valid = True
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
            id_valid = id == self.DEVICE_ID
            try:
                checksum_okay = data[0] == 0
            except:
                checksum_okay = False

        else:
            id = 0
            id_valid = False
            checksum_okay = False

        return (valid and checksum_okay, id, id_valid)

    def get_temp_target(self):
        valid, data = self.packet_query(self.PACKET_TYPE_TEMP_GET_TARGET, [])
        if valid:
            temp = int.from_bytes(data, byteorder="big", signed=True) / self.TEMP_SCALE
            try:
                checksum_okay = data[0] == 0
            except:
                checksum_okay = False
        else:
            temp = 0
            checksum_okay = False

        return (valid and checksum_okay, temp)

    def set_pid_coeffs(self, pid_p, pid_i, pid_d):
        pid_p_bytes = list(pid_p.to_bytes(4, "big", signed=True))
        pid_i_bytes = list(pid_i.to_bytes(4, "big", signed=True))
        pid_d_bytes = list(pid_d.to_bytes(4, "big", signed=True))
        valid, data = self.packet_query(self.PACKET_TYPE_PID_SET_COEFFS, pid_p_bytes + pid_i_bytes + pid_d_bytes)
        return valid and (data[0] == 0)

    def get_pid_coeffs(self):
        valid, data = self.packet_query(self.PACKET_TYPE_PID_GET_COEFFS, [])
        if valid:
            pid_p = int.from_bytes(data[1:5], byteorder="big", signed=True)
            pid_i = int.from_bytes(data[5:9], byteorder="big", signed=True)
            pid_d = int.from_bytes(data[9:13], byteorder="big", signed=True)
        else:
            pid_p = 0
            pid_i = 0
            pid_d = 0
        return (valid and (data[0] == 0), pid_p, pid_i, pid_d)

    def set_pid_running(self, running, temp):
        running_bytes = list(running.to_bytes(1, "big", signed=False))
        temp_bytes = list(int(temp * self.TEMP_SCALE).to_bytes(2, "big", signed=True))
        valid, data = self.packet_query(self.PACKET_TYPE_PID_SET_RUNNING, running_bytes + temp_bytes)
        return valid and (data[0] == 0)

    def set_pid_temp(self, temp):
        temp_bytes = list(int(temp * self.TEMP_SCALE).to_bytes(2, "big", signed=True))
        valid, data = self.packet_query(self.PACKET_TYPE_TEMP_SET_TARGET, temp_bytes)
        return valid and (data[0] == 0)

    def get_pid_status(self):
        valid, data = self.packet_query(self.PACKET_TYPE_PID_GET_STATUS, [])
        if valid:
            pid_status = data[1]
            pid_error = data[2]
        else:
            pid_status = 0
            pid_error = 0
        return valid and (data[0] == 0), pid_status, pid_error

    def get_temp_actual(self):
        valid, data = self.packet_query(self.PACKET_TYPE_TEMP_GET_ACTUAL, [])
        if valid:
            temp = int.from_bytes(data, byteorder="big", signed=True) / self.TEMP_SCALE
            try:
                checksum_okay = data[0] == 0
            except:
                checksum_okay = False
        else:
            temp = 0
            checksum_okay = False

        return (valid and checksum_okay, temp)

    def set_autotune_running(self, running, temp_c):
        running_bytes = list(running.to_bytes(1, "big", signed=False))
        temp_bytes = list(int(temp_c * self.TEMP_SCALE).to_bytes(2, "big", signed=True))
        valid, data = self.packet_query(self.PACKET_TYPE_AUTOTUNE_SET_RUNNING, running_bytes + temp_bytes)
        return valid and (data[0] == 0)

    def get_autotune_running(self):
        valid, data = self.packet_query(self.PACKET_TYPE_AUTOTUNE_GET_RUNNING, [])
        if valid:
            running = data[1]
        else:
            running = 0
        return valid and (data[0] == 0), running

    def get_autotune_status(self):
        valid, data = self.packet_query(self.PACKET_TYPE_AUTOTUNE_GET_STATUS, [])
        if valid:
            status = data[1]
            failed = data[2]
        else:
            status = 0
            failed = 0
        return valid and (data[0] == 0), status, failed

    def set_stir_running(self, running, stir_speed):
        running_bytes = list(running.to_bytes(1, "big", signed=False))
        speed_bytes = list(stir_speed.to_bytes(2, "big", signed=False))
        valid, data = self.packet_query(self.PACKET_TYPE_STIR_SET_RUNNING, running_bytes + speed_bytes)
        return valid and (data[0] == 0)

    def get_stir_status(self):
        valid, data = self.packet_query(self.PACKET_TYPE_STIR_GET_STATUS, [])
        if valid:
            status = data[1]
        else:
            status = 0
        return valid and (data[0] == 0), status

    def get_stir_speed_actual(self):
        valid, data = self.packet_query(self.PACKET_TYPE_STIR_SPEED_GET_ACTUAL, [])
        if valid:
            speed = int.from_bytes(data[1:3], byteorder="big", signed=False)
        else:
            speed = 0
        return valid and (data[0] == 0), speed

    def set_heat_power_limit(self, limit):
        limit_bytes = list(limit.to_bytes(1, "big", signed=False))
        valid, data = self.packet_query(self.PACKET_TYPE_HEAT_POWER_LIMIT_SET, limit_bytes)
        return valid and (data[0] == 0)

    def get_heat_power_limit_pc(self):
        valid, data = self.packet_query(self.PACKET_TYPE_HEAT_POWER_LIMIT_GET, [])
        if valid:
            limit = data[1]
        else:
            limit = 0
        return valid and (data[0] == 0), limit

    def set_heat_power_limit_pc(self, power_limit_pc):
        send_bytes = list(power_limit_pc.to_bytes(1, "little", signed=False))
        valid, data = self.packet_query(self.PACKET_TYPE_HEAT_POWER_LIMIT_SET, send_bytes)
        return valid and (data[0] == 0)


class Heater:
    pid_status_str = ["Unconfigured", "Idle", "Heating", "Suspended", "Error"]

    autotune_status_str = ["None", "Running", "Aborted", "Finished", "Failed"]

    INIT_TRIES = 3

    def __init__(self, spi_handler, heater_num, port):
        self.holder = Holder(spi_handler, port, 0.05)
        self.autotuning = False
        self.pid_enabled = False
        self.stir_enabled = False
        self.autotune_target_temp = 50.0
        self.stir_target_speed = 20
        self.temp_c_actual = 0
        self.status_text = ""
        self.autotune_status_text = ""
        self.temp_text = ""
        self.stir_speed_text = ""

        for i in range(self.INIT_TRIES):
            valid, id, id_valid = self.holder.get_id()
            if valid:
                break
        #      else:
        #        time.sleep( 0.1 )
        print("Heater {} ID OK:{}".format(heater_num, valid))
        self.enabled = valid and id_valid

        self.temp_c_target = self.get_temp_target()
        valid, self.heat_power_limit_pc = self.holder.get_heat_power_limit_pc()

    @property
    def data(self):
        return {
            "status_text": self.status_text,
            "autotune_status_text": self.autotune_status_text,
            "temp_text": self.temp_text,
            "stir_speed_text": self.stir_speed_text,
            "temp_c_actual": self.temp_c_actual,
            "temp_c_target": self.temp_c_target,
            "heat_power_limit_pc": self.heat_power_limit_pc,
            "pid_enabled": self.pid_enabled,
            "stir_enabled": self.stir_enabled,
            "autotuning": self.autotuning,
        }

    def get_temp_target(self):
        valid, temp_c_target = self.holder.get_temp_target()
        if valid:
            temp_c_target = round(temp_c_target, 2)
        self.temp_c_target = temp_c_target
        return temp_c_target

    def set_temp(self, temp):
        try:
            temp = round(float(temp), 2)
            self.holder.set_pid_temp(temp)
            self.temp_c_target = self.get_temp_target()
        except:
            pass

    def set_heat_power_limit_pc(self, power_limit_pc):
        try:
            limit_pc = int(power_limit_pc)
            valid = self.holder.set_heat_power_limit_pc(limit_pc)
            valid, power_limit_pc = self.holder.get_heat_power_limit_pc()
            if valid:
                self.heat_power_limit_pc = power_limit_pc
        except:
            pass

    def set_autotune(self, autotuning):
        try:
            temp = round(float(self.autotune_target_temp), 2)
            # autotuning = 0 if self.autotuning else 1
            self.holder.set_autotune_running(autotuning, temp)
        except:
            pass

    def set_pid_running(self, run):
        try:
            # run = 0 if self.pid_enabled else 1
            # temp = round( float( self.temp_target_box.value ), 2 )
            # self.holder.set_pid_running( run, temp )

            # TODO: Define temp
            self.holder.set_pid_running(run, temp)
            # self.temp_c_target = self.get_temp_target()
        except:
            pass

    def set_stir_running(self, run):
        try:
            # run = 0 if self.stir_enabled else 1
            stir_speed_rps = int(self.stir_target_speed)
            self.holder.set_stir_running(run, stir_speed_rps)
        except:
            pass

    def update(self):
        if not self.enabled:
            self.status_text = "Offline"
        else:
            valid, pid_status, pid_error = self.holder.get_pid_status()
            okay = valid
            valid, temp_c = self.holder.get_temp_actual()
            if valid:
                self.temp_c_actual = round(temp_c, 2)
            okay = okay and valid
            valid, autotune_status, autotune_fail = self.holder.get_autotune_status()
            okay = okay and valid
            valid, stir_status = self.holder.get_stir_status()
            okay = okay and valid
            valid, stir_speed_actual_rps = self.holder.get_stir_speed_actual()
            okay = okay and valid

            self.autotuning = autotune_status == 1
            self.autotune_status = autotune_status

            if not okay:
                self.status_text = "Connection Error"
            elif self.autotuning:
                self.status_text = "Autotuning"
            else:
                if pid_status == 4:
                    if pid_error == 2:
                        self.status_text = "No Sensor"
                    else:
                        self.status_text = f"Error: {pid_error}"
                else:
                    try:
                        self.status_text = f"{self.pid_status_str[pid_status]}"
                    except:
                        pass

            try:
                self.temp_text = f"{round(self.temp_c_actual, 2)} / { round(self.temp_c_target, 2)}"
                self.stir_speed_text = f"{stir_speed_actual_rps} RPS"
            except:
                pass

            self.pid_enabled = pid_status == 2
            self.stir_enabled = stir_status == 2

        try:
            self.autotune_status_text = "{}".format(self.autotune_status_str[autotune_status])
        except:
            pass
