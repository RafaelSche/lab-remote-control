from serial import Serial


class PhaseOutOfRangeError(Exception):
    pass


class DualActiveBridge:

    @classmethod
    def from_serial(cls, serial_args, **kwargs):
        return cls(Serial(**serial_args), **kwargs)

    def __init__(self, client: Serial, PACKET_SIZE=2, RESET_COMMAND=32767, clear_mc_buffer=True):
        """
        Example contruction:
            >>> dab = DualActiveBridge(client=Serial('/dev/ttyUSB0'))
        :param client:
        :param PACKET_SIZE:
        :param RESET_COMMAND:
        :param clear_mc_buffer:
        """
        self.client = client
        self.PACKET_SIZE = PACKET_SIZE
        self.RESET_COMMAND = RESET_COMMAND
        if clear_mc_buffer:
            self.send_clear_FIFO_buffer()

    def __del__(self):
        self.client.close()

    def send_clear_FIFO_buffer(self):
        """
        Wait at least 600 ms before sending another message to microcontroller.
        :return:
        """
        return self.client.write(self.RESET_COMMAND.to_bytes(self.PACKET_SIZE))

    def send_packet(self, value):
        return self.client.write(value.to_bytes(self.PACKET_SIZE))

    def set_phase(self, value: int):
        value = int(value)
        if all([value not in range_ for range_ in [range(1, 180), range(-89, 0)]]):
            raise PhaseOutOfRangeError(f'Current implementation accepts only phase values '
                                       f'in the interval of [0, 179] or [-89, -1]. Got {value}.')
        if value < 0:
            value = 2**(self.PACKET_SIZE * 8) + value
        return self.send_packet(value)
