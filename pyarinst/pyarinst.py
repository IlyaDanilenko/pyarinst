from serial import Serial

class ArinstCommand:
    GENERATOR_ON = "gon"
    GENERATOR_OFF = "gof"
    GENERATOR_SET_FREQUENCY = "scf"
    GENERATOR_SET_AMPLITUDE = "sga"
    SCAN_RANGE = "scn20"
    SCAN_RANGE_TRACKING = "scn22"

class ArinstDevice:
    def __init__(self, device='/dev/ttyACM0', baudrate=115200):
        self.__serial = Serial(port = device, baudrate = baudrate)
        self.__command_terminate = '\r\n'
        self.__package_index = 0
        self.__command_count_terminate = {
            ArinstCommand.GENERATOR_ON: 2,
            ArinstCommand.GENERATOR_OFF: 2,
            ArinstCommand.GENERATOR_SET_FREQUENCY: 3,
            ArinstCommand.GENERATOR_SET_AMPLITUDE: 2,
            ArinstCommand.SCAN_RANGE: 4,
            ArinstCommand.SCAN_RANGE_TRACKING: 4
        }

    def _write(self, command : str, *args):
        msg = command + "".join([f' {arg}' for arg in args]) + " " + str(self.__package_index) + self.__command_terminate
        self.__serial.write(bytes(msg, 'ascii'))
        self.__package_index += 1

    def _read(self, command : str) -> str:
        msg = b''
        for _ in range(self.__command_count_terminate[command]):
            msg += self.__serial.read_until(bytes(self.__command_terminate, 'ascii'))

        self.__serial.reset_input_buffer()
        self.__serial.reset_output_buffer()
        return msg

    def send_command(self, command : str, *args):
        self._write(command, *args)
        response = self._read(command)
        response = response.split(bytes(self.__command_terminate, 'ascii'))
        try:
            while True:
                response.pop(response.index(b''))
        except ValueError:
            pass
        response = [resp.split(b' ') for resp in response]
        return response

    def on(self) -> bool:
        command = ArinstCommand.GENERATOR_ON
        response = self.send_command(command)
        return response[-1][0] == b"complete" and str(response[0][0], 'ascii') == command

    def off(self) -> bool:
        command = ArinstCommand.GENERATOR_OFF
        response = self.send_command(command)
        return response[-1][0] == b"complete" and str(response[0][0], 'ascii') == command

    def set_frequency(self, frequency : int) -> bool:
        command = ArinstCommand.GENERATOR_SET_FREQUENCY
        response = self.send_command(command, frequency)
        if len(response) == 3:
            return response[-1][0] == b"complete" and str(response[0][0], 'ascii') == command and str(response[1][0], 'ascii') == "success"
        else:
            return False
        
    def set_amplitude(self, amplitude : int) -> bool:
        if -15 <= amplitude <= -25:
            command = ArinstCommand.GENERATOR_SET_AMPLITUDE
            amplitude = ((amplitude + 15) * 100) + 10000
            response = self.send_command(command, amplitude)
            return response[-1][0] == b"complete" and str(response[0][0], 'ascii') == command
        else:
            return False

    def __decode_data(self, response, attenuation):
        amplitudes = []
        for i in range(0, len(response), 2):
            first = int.from_bytes(response[i:i + 1], byteorder='little')
            second = int.from_bytes(response[i + 2:i + 3], byteorder='little')
            val = first << 8 | second
            data = val & 0b000011111111111
            amplitudes.append((800.0 - data)/10.0 - attenuation)
        return amplitudes

    def get_scan_range(self, start = 1500000000, stop = 1700000000, step = 1000000, attenuation = 0, tracking = False):
        if -30 <= attenuation <= 0:
            command = None
            if tracking:
                command = ArinstCommand.SCAN_RANGE_TRACKING
            else:
                command = ArinstCommand.SCAN_RANGE
            attenuation = (attenuation * 100) + 10000
            response = self.send_command(command, start, stop, step, 200, 20, 10700000, attenuation)
            if len(response) == 3:
                if response[-1][0] == b"complete" and str(response[0][0], 'ascii') == command:
                    return self.__decode_data(response[1][0][0:-2], attenuation)
        return None