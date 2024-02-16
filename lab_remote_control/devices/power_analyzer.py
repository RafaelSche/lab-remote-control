from dataclasses import dataclass
from datetime import datetime
from lab_remote_control.devices.common import Command, EventStatusRegister, Instrument
from typing import Literal, Optional, Union
import logging
import pyvisa


logger = logging.getLogger(__name__)


@dataclass
class Script:
    source_code: str

    @classmethod
    def from_file(cls, path):
        with open(path) as f:
            source_code = f.read()
        return cls(source_code)

    def __post_init__(self):
        self.vars: list[str] = []
        for line in self.source_code.splitlines():
            if '=' in line:
                self.vars.append(line.split('=')[0].strip(' '))
        if len(self.vars) >= 64:
            raise self.VariablesStorageFullError('Power Analyzer cannot store more than 64 Variables')

    class VariablesStorageFullError(Exception):
        pass


@dataclass
class PowerAnalyzerEventStatusRegister(EventStatusRegister):
    request_control: Optional[bool] = None
    user_request: Optional[bool] = None

    def set_by_bit_string(self, bit_string):
        super().set_by_bit_string(bit_string)
        self.request_control = bool(int(bit_string[::-1][1]))
        self.user_request = bool(int(bit_string[::-1][6]))

    def properties_to_int(self) -> int:
        int_ = super().properties_to_int()
        if self.request_control:
            int_ += 2
        if self.user_request:
            int_ += 64
        return int_


@dataclass
class PowerAnalyzerCommand(Command):

    def __init__(self, scpi_command: str, check_operation_complete_bit=False, *args, **kwargs):
        super(PowerAnalyzerCommand, self).__init__(scpi_command, check_operation_complete_bit=False, *args, **kwargs)

    def check_operation_complete(self, *, client: pyvisa.Resource, **kwargs):
        return bool(int(client.query('*OPC?')))

    def __post_init__(self):
        super(PowerAnalyzerCommand, self).__post_init__()
        self.event_status_register_type = PowerAnalyzerEventStatusRegister
        if '?' in self.scpi_command:
            self.query = True


class PowerAnalyzer(Instrument):
    event_status_register_type = PowerAnalyzerEventStatusRegister

    def __init__(self, client: pyvisa.resources.MessageBasedResource, clear=True):
        self.client = client
        self._script: Optional[Script] = None
        if clear:
            self.clear()

    def reset(self):
        return PowerAnalyzerCommand('*RST')(self.client)

    def clear(self):
        return PowerAnalyzerCommand('*CLS')(self.client)

    @property
    def zlang(self):
        return PowerAnalyzerCommand('*ZLANG?')(self.client).strip('"')

    @zlang.setter
    def zlang(self, language: Literal['SCPI', 'SHORT']):
        PowerAnalyzerCommand('*ZLANG {}')(self.client, language)

    @property
    def operation_complete(self):
        return bool(int(PowerAnalyzerCommand('*OPC?')(self.client)))

    def script_from_file(self, path):
        self.script = Script.from_file(path)

    script_from_file = property(fset=script_from_file)

    @property
    def script(self) -> Script:
        script = ''
        script += PowerAnalyzerCommand(':SENSE:SCRIPT:LISTING?')(self.client)
        while True:
            try:
                script += '\n' + self.client.read()
            except pyvisa.errors.VisaIOError:
                break
        self._script = Script(script.strip('"').strip("'"))
        return self._script

    @script.setter
    def script(self, script: Script):
        self._script = script
        PowerAnalyzerCommand(':SENSE:SCRIPT:LISTING "{}"')(self.client, script.source_code)

    def pull_script_vars(self, include_cycle_timestamp=False) -> dict[str, Union[float, datetime]]:
        if not self._script:
            script = self.script
        else:
            script = self._script
        scpi_command = f':READ:SCRIPT:RESULT? (0:{len(script.vars)-1})'
        if include_cycle_timestamp:
            scpi_command = ':READ:SLOTS:DEC:TIMESTAMPCYCLE?;' + scpi_command
        resp = PowerAnalyzerCommand(scpi_command)(self.client)
        if include_cycle_timestamp:
            timestamp, resp = resp.split(';')
            timestamp = datetime.strptime(timestamp.split('.')[0], '%Y:%m:%dD%H:%M:%S')
        results = {var: float(value) for var, value in zip(script.vars, resp.split(','))}
        if include_cycle_timestamp:
            results['timestamp'] = timestamp
        return results

    @property
    def cycle_time(self) -> float:
        return float(PowerAnalyzerCommand(':SENSE:SWEEP:TIME?')(self.client))

    @cycle_time.setter
    def cycle_time(self, time: float):
        PowerAnalyzerCommand(':SENSE:SWEEP:TIME {}')(self.client, time)

    @property
    def cycle_mode(self):
        return PowerAnalyzerCommand(':SENSE:SWEEP:MODE?')(self.client)

    @cycle_mode.setter
    def cycle_mode(self, mode: int):
        PowerAnalyzerCommand(':SENSE:SWEEP:MODE {}')(self.client, mode)

    def go_to_local(self):
        return PowerAnalyzerCommand(':GTL')(self.client)

    def __del__(self):
        try:
            self.go_to_local()
            self.client.close()
            del self.client
        except pyvisa.errors.InvalidSession:
            pass
