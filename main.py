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
        msg = command + "".join([' ' + str(bytes(arg), encoding='ascii') for arg in args]) + " " + str(self.__package_index) + self.__command_terminate
        self.__serial.write(bytes(msg, 'ascii'))
        self.__package_index += 1

    def _read(self, count_terminator : int) -> str:
        while True:
            print(self.__serial.read_all())
        # msg = ''
        # for _ in range(count_terminator):
        #     msg += self.__serial.read_until(self.__command_terminate)
        # return msg

    def send_command(self, command : str, *args):
        self._write(command, *args)
        response = self._read(self.__command_count_terminate[command]).split(self.__command_terminate)
        # response = "\r\nscn20 500000000 8\r\n0 2 3 4 69\r\ncomplete\r\n".split(self.__command_terminate)
        try:
            while True:
                response.pop(response.index(''))
        except ValueError:
            pass
        response = [resp.split(" ") for resp in response]
        return response

    def on(self) -> bool:
        command = ArinstCommand.GENERATOR_ON
        response = self.send_command(command)
        return response[-1][0] == "complete" and response[0][0] == command

    def off(self) -> bool:
        command = ArinstCommand.GENERATOR_OFF
        response = self.send_command(command)
        return response[-1][0] == "complete" and response[0][0] == command

    def set_frequency(self, frequency : int) -> bool:
        command = ArinstCommand.GENERATOR_SET_FREQUENCY
        response = self.send_command(command, frequency)
        if len(response) == 3:
            return response[-1][0] == "complete" and response[0][0] == command and response[1][0] == "success"
        else:
            return False
        
    def set_amplitude(self, amplitude : int) -> bool:
        if -15 <= amplitude <= -25:
            command = ArinstCommand.GENERATOR_SET_AMPLITUDE
            amplitude = ((amplitude + 15) * 100) + 10000
            response = self.send_command(command, amplitude)
            return response[-1][0] == "complete" and response[0][0] == command
        else:
            return False

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
                if response[-1][0] == "complete" and response[0][0] == command:
                    return response[1]
        return None


if __name__ == "__main__":
    device = ArinstDevice()
    if device.on():
        print(f'Set amplitude: {device.set_amplitude(-25)}')
        print(f'Set freq: {device.set_frequency(1100000000)}')
        while True:
            print(f'Scan data: {device.get_scan_range()}')    