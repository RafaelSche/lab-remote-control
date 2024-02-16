from dataclasses import dataclass, fields
from lab_remote_control.devices.common import Register, Command, EventStatusRegister, Instrument
from lab_remote_control.devices.dataformats import NR2, NR3
from typing import Literal, Optional
import logging
import pyvisa


logger = logging.getLogger(__name__)


class BasePropertyClass:
    pass


def make_property_class(property_name, short, resp_type=NR2, source_sink='',
                        set_value_=True,
                        measured_value_=True,
                        protection_=True,
                        over_detection_=True,
                        under_detection_=True,
                        limit_low_=True,
                        limit_high_=True,
                        nominal_=True,
                        nominal_min_max_=False,
                        control_speed_=False,
                        alarm_count_=True):
    if source_sink:
        if source_sink[-1] != ':':
            source_sink += ':'

    class PropertyClass(BasePropertyClass):

        def __init__(self, client: pyvisa.resources.MessageBasedResource, command: type = Command):
            self.client = client
            self.Command = command

        if nominal_:
            @property
            def nominal(self):
                return resp_type(self.Command(f'SYSTEM:NOMINAL:{property_name}?')(self.client))

        if nominal_min_max_:
            @property
            def nominal_min(self):
                return resp_type(self.Command(f'SYSTEM:NOMINAL:{property_name}:MINIMUM?')(self.client))

            @property
            def nominal_max(self):
                return resp_type(self.Command(f'SYSTEM:NOMINAL:{property_name}:MAXIMUM?')(self.client))

        if set_value_:
            @property
            def setting(self):
                return resp_type(self.Command(f'{source_sink}{property_name}?')(self.client))

            @setting.setter
            def setting(self, set_value):
                self.Command(f'{source_sink}{property_name} {set_value}')(self.client)

        if measured_value_:
            @property
            def measurement(self):
                return resp_type(self.Command(f'MEASURE:{property_name}:?')(self.client))

        if protection_:
            @property
            def protection(self):
                return resp_type(self.Command(f'{source_sink}{property_name}:PROTECTION?')(self.client))

            @protection.setter
            def protection(self, value):
                self.Command(f'{source_sink}{property_name}:PROTECTION {value}')(self.client)

        if under_detection_:
            @property
            def under_detection(self):
                return resp_type(self.Command(f'SYSTEM:{source_sink}CONFIG:U{short}D?')(self.client))

            @under_detection.setter
            def under_detection(self, value):
                self.Command(f'SYSTEM:{source_sink}CONFIG:U{short}D {value}')(self.client)

            @property
            def under_detection_action(self):
                return self.Command(f'SYSTEM:{source_sink}CONFIG:U{short}D:ACTION?')(self.client).strip('\n')

            @under_detection_action.setter
            def under_detection_action(self, value: Literal['NONE', 'SIGNAL', 'WARNING', 'ALARM']):
                if value not in ['NONE', 'SIGNAL', 'WARNING', 'ALARM']:
                    raise ValueError(f"Value should be 'NONE', 'SIGNAL', 'WARNING' or 'ALARM'. Not {value}")
                self.Command(f'SYSTEM:{source_sink}CONFIG:U{short}D:ACTION {value}')(self.client, value)

        if over_detection_:
            @property
            def over_detection(self):
                return resp_type(self.Command(f'SYSTEM:CONFIG:U{short}D?')(self.client))

            @over_detection.setter
            def over_detection(self, value):
                self.Command(f'SYSTEM:CONFIG:U{short}D {value}')(self.client)

            @property
            def over_detection_action(self):
                return self.Command(f'SYSTEM:CONFIG:U{short}D:ACTION?')(self.client).strip('\n')

            @over_detection_action.setter
            def over_detection_action(self, value: Literal['NONE', 'SIGNAL', 'WARNING', 'ALARM']):
                if value not in ['NONE', 'SIGNAL', 'WARNING', 'ALARM']:
                    raise ValueError(f"Value should be 'NONE', 'SIGNAL', 'WARNING' or 'ALARM'. Not {value}")
                self.Command(f'SYSTEM:CONFIG:U{short}D:ACTION {value}')(self.client)

        if limit_low_:
            @property
            def limit_low(self):
                return resp_type(self.Command(f'{source_sink}{property_name}:LIMIT:LOW?')(self.client))

            @limit_low.setter
            def limit_low(self, value):
                self.Command(f'{source_sink}{property_name}:LIMIT:LOW {value}')(self.client)

        if limit_high_:
            @property
            def limit_high(self):
                return resp_type(self.Command(f'{source_sink}{property_name}:LIMIT:HIGH?')(self.client))

            @limit_high.setter
            def limit_high(self, value):
                self.Command(f'{source_sink}{property_name}:LIMIT:HIGH {value}')(self.client)

        if control_speed_:
            @property
            def control_speed(self):
                return self.Command(f'{source_sink}{property_name}:CONTROL:SPEED?')(self.client).strip('\n')

            @control_speed.setter
            def control_speed(self, value: Literal['FAST', 'SLOW']):
                if value not in ['FAST', 'SLOW']:
                    raise ValueError(f"Value must be 'FAST' or 'SLOW'. Not {value}")
                self.Command(f'{source_sink}{property_name}:CONTROL:SPEED {value}')(self.client)

        if alarm_count_:
            @property
            def alarm_count(self):
                return int(self.Command(f'SYSTEM:ALARM:COUNT:O{property_name}?')(self.client))

        if source_sink == 'SINK':
            @property
            def alarm_count(self):
                return int(self.Command(f'SYSTEM:{source_sink}ALARM:COUNT:O{property_name}?')(self.client))

    return PropertyClass


VoltagePropertyClass = make_property_class('VOLTAGE', 'V', control_speed_=True)
CurrentPropertyClass = make_property_class('CURRENT', 'C')
PowerPropertyClass = make_property_class('POWER', 'P', NR3, under_detection_=False, over_detection_=False,
                                         limit_low_=False)
ResistancePropertyClass = make_property_class('RESISTANCE', 'R',
                                              nominal_=False,
                                              nominal_min_max_=True,
                                              measured_value_=False,
                                              protection_=False,
                                              under_detection_=False,
                                              over_detection_=False,
                                              limit_low_=False,
                                              alarm_count_=False)

SinkCurrentPropertyClass = make_property_class('CURRENT', 'C', source_sink='SINK')
SinkPowerPropertyClass = make_property_class('POWER', 'P', NR3, 'SINK', under_detection_=False, over_detection_=False,
                                             limit_low_=False)
SinkResistancePropertyClass = make_property_class('RESISTANCE', 'R',source_sink='SINK',
                                                  nominal_=False,
                                                  nominal_min_max_=True,
                                                  measured_value_=False,
                                                  protection_=False,
                                                  under_detection_=False,
                                                  over_detection_=False,
                                                  limit_low_=False,
                                                  alarm_count_=False)


@dataclass
class StatusByteRegister(Register):
    SecondQuestionableStatusRegister: Optional[bool] = None  # Short: sec_ques;
    ErrorQueue: Optional[bool] = None  # Short: err;
    QuestionableStatusRegister: Optional[bool] = None  # Short: ques;
    EventStatusRegister: Optional[bool] = None  # Short: esr;
    MasterSummaryStatus: Optional[bool] = None  # Short: mss;
    OperationStatusRegister: Optional[bool] = None  # Short: oper;

    def set_by_bit_string(self, bit_string):
        self.SecondQuestionableStatusRegister = bool(int(bit_string[::-1][0]))
        self.ErrorQueue = bool(int(bit_string[::-1][2]))
        self.QuestionableStatusRegister = bool(int(bit_string[::-1][3]))
        self.EventStatusRegister = bool(int(bit_string[::-1][5]))
        self.MasterSummaryStatus = bool(int(bit_string[::-1][6]))
        self.OperationStatusRegister = bool(int(bit_string[::-1][7]))

    def properties_to_int(self) -> int:
        int_ = 0
        if self.SecondQuestionableStatusRegister:
            int_ += 1
        if self.ErrorQueue:
            int_ += 4
        if self.QuestionableStatusRegister:
            int_ += 8
        if self.EventStatusRegister:
            int_ += 32
        if self.MasterSummaryStatus:
            int_ += 64
        if self.OperationStatusRegister:
            int_ += 128
        return int_

    def __post_init__(self):
        self.set_command = None
        self.query_command = Command('*STB?')
        self.set_sre_command = Command(f'*SRE {self.properties_to_int()}')


@dataclass
class QuestionableStatusRegister(Register):
    over_voltage_protection: Optional[bool] = None
    over_current_protection: Optional[bool] = None
    over_power_protection: Optional[bool] = None
    over_temperature: Optional[bool] = None
    over_voltage_detection: Optional[bool] = None
    under_voltage_detection: Optional[bool] = None
    over_current_detection: Optional[bool] = None
    under_current_detection: Optional[bool] = None
    over_power_detection: Optional[bool] = None
    local: Optional[bool] = None
    remote: Optional[bool] = None
    output_input: Optional[bool] = None
    function: Optional[bool] = None
    power_fail: Optional[bool] = None
    msp: Optional[bool] = None

    def set_by_int(self, int_):
        return super().set_by_int(int_, register_length=15)

    def set_by_bit_string(self, bit_string):
        self.over_voltage_protection = bool(int(bit_string[::-1][0]))
        self.over_current_protection = bool(int(bit_string[::-1][1]))
        self.over_power_protection = bool(int(bit_string[::-1][2]))
        self.over_temperature = bool(int(bit_string[::-1][3]))
        self.over_voltage_detection = bool(int(bit_string[::-1][4]))
        self.under_voltage_detection = bool(int(bit_string[::-1][5]))
        self.over_current_detection = bool(int(bit_string[::-1][6]))
        self.under_current_detection = bool(int(bit_string[::-1][7]))
        self.over_power_detection = bool(int(bit_string[::-1][8]))
        self.local = bool(int(bit_string[::-1][9]))
        self.remote = bool(int(bit_string[::-1][10]))
        self.output_input = bool(int(bit_string[::-1][11]))
        self.function = bool(int(bit_string[::-1][12]))
        self.power_fail = bool(int(bit_string[::-1][13]))
        self.msp = bool(int(bit_string[::-1][14]))

    def properties_to_int(self) -> int:
        property_names = [x.name for x in fields(self)]
        int_ = sum([(2**i)*bool(self.__getattribute__(name)) for i, name in enumerate(property_names)])
        return int_

    def __post_init__(self):
        self.set_command = None
        self.query_command = Command('STATUS:QUESTIONABLE:CONDITION?')
        self.query_command_event = Command('STATUS:QUESTIONABLE?')
        self.set_enable_register_command = Command(f'STATUS:QUESTIONABLE:ENABLE {self.properties_to_int()}')


@dataclass
class OperationStatusRegister(Register):
    rem_sb: Optional[bool] = None
    semi_f47: Optional[bool] = None
    derating: Optional[bool] = None
    connection_timeout: Optional[bool] = None
    constant_voltage: Optional[bool] = None
    constant_current: Optional[bool] = None
    constant_power: Optional[bool] = None
    constant_resistance: Optional[bool] = None
    sink: Optional[bool] = None

    def set_by_int(self, int_):
        return super().set_by_int(int_, register_length=13)

    def set_by_bit_string(self, bit_string):
        self.rem_sb = bool(int(bit_string[::-1][4]))
        self.semi_f47 = bool(int(bit_string[::-1][5]))
        self.derating = bool(int(bit_string[::-1][6]))
        self.connection_timeout = bool(int(bit_string[::-1][7]))
        self.constant_voltage = bool(int(bit_string[::-1][8]))
        self.constant_current = bool(int(bit_string[::-1][9]))
        self.constant_power = bool(int(bit_string[::-1][10]))
        self.constant_resistance = bool(int(bit_string[::-1][11]))
        self.sink = bool(int(bit_string[::-1][12]))

    def properties_to_int(self) -> int:
        property_names = [x.name for x in fields(self)]
        int_ = sum([(2**i)*bool(self.__getattribute__(name)) for i, name in enumerate(property_names, start=4)])
        return int_

    def __post_init__(self):
        self.set_command = None
        self.query_command = Command('STATUS:OPERATION:CONDITION?')
        self.query_command_event = Command('STATUS:OPERATION?')
        self.set_enable_register_command = Command(f'STATUS:OPERATION:ENABLE {self.properties_to_int()}')


class SupplyLoad(Instrument):
    event_status_register_type = EventStatusRegister

    def __init__(self, client: pyvisa.resources.MessageBasedResource, remote=True,
                 clear_errors=True, enable_event_status_register=True, command: type = Command):
        self.client = client
        self.Command = command
        if clear_errors:
            logger.info(f'Error Queue on start: {self.error_queue}')  # clear error queue
            EventStatusRegister.from_client(self.client)  # clear error bits
        if remote:
            self.remote = True
            if enable_event_status_register:
                self.enable_event_status_register()

        self._voltage = VoltagePropertyClass(self.client, command=self.Command)
        self._current = CurrentPropertyClass(self.client, command=self.Command)
        self._power = PowerPropertyClass(self.client, command=self.Command)
        self._resistance = ResistancePropertyClass(self.client, command=self.Command)

    def __del__(self):
        try:
            self.remote = False
            self.client.close()
            del self.client
        except pyvisa.errors.InvalidSession:
            pass

    def remote(self, state: bool):
        if state:
            state = 'ON'
        else:
            state = 'OFF'
        self.Command('SYSTEM:LOCK {}')(self.client, state)

    remote = property(fset=remote)

    def enable_event_status_register(self):
        ese = EventStatusRegister(operation_complete=True,
                                  query_error=True,
                                  device_depend_error=True,
                                  execution_error=True,
                                  command_errors=True)
        ese.set_enable_register_command(self.client)

    def setup_standard_settings(self):
        self.master_slave_mode = False
        self.after_remote = 'AUTO'
        self.resistance_mode = False

    @property
    def status_byte_register(self):
        return StatusByteRegister.from_client(self.client)

    @property
    def questionable_status_register(self):
        return QuestionableStatusRegister.from_client(self.client)

    @property
    def operation_status_register(self):
        return OperationStatusRegister.from_client(self.client)

    @property
    def voltage(self):
        return self._voltage

    @property
    def current(self):
        return self._current

    @property
    def power(self):
        return self._power

    @property
    def resistance(self):
        return self._resistance

    @property
    def master_slave_mode(self):
        return self.Command('SYSTEM:MS:ENABLE?')(self.client).strip('\n')

    @master_slave_mode.setter
    def master_slave_mode(self, value: bool):
        if value:
            self.Command('SYSTEM:MS:ENABLE ON')(self.client)
        else:
            self.Command('SYSTEM:MS:ENABLE OFF')(self.client)

    @property
    def device_class(self):
        return int(self.Command('SYSTEM:DEVICE:CLASS?')(self.client).strip('\n'))

    @property
    def operation_time(self):
        return NR2(self.Command('DIAGNOSTIC:INFORMATION:DEVICE:OTIME?')(self.client))

    @property
    def on_time(self):
        return NR2(self.Command('DIAGNOSTIC:INFORMATION:DEVICE:ONTIME?')(self.client))

    @property
    def off_time(self):
        return NR2(self.Command('DIAGNOSTIC:INFORMATION:DEVICE:OFFTIME?')(self.client))

    @property
    def ampere_hours(self):
        return NR2(self.Command('FETCH:AHOUR?')(self.client))

    @property
    def watt_hours(self):
        return NR3(self.Command('FETCH:WHOUR?')(self.client).strip('\n'))

    @property
    def after_remote(self):
        return self.Command('POWER:STAGE:AFTER:REMOTE?')(self.client).strip('\n').strip('\n')

    @after_remote.setter
    def after_remote(self, value: Literal['AUTO', 'OFF']):
        if value not in ['AUTO', 'OFF']:
            raise ValueError(f"Value must be 'AUTO' or 'OFF'. Not {value}")
        self.Command('POWER:STAGE:AFTER:REMOTE {}')(self.client, value)

    @property
    def user_text(self):
        return self.Command('SYSTEM:CONFIG:USER:TEXT?')(self.client)

    @user_text.setter
    def user_text(self, text: str):
        self.Command('SYSTEM:CONFIG:USER:TEXT {}')(self.client, text)

    @property
    def monitoring_timeout(self):
        return int(self.Command('SYSTEM:COMMUNICATE:MONITORING:TIMEOUT?')(self.client))

    @monitoring_timeout.setter
    def monitoring_timeout(self, value):
        self.Command('SYSTEM:COMMUNICATE:MONITORING:TIMEOUT {}')(self.client, value)

    @property
    def monitoring_action(self):
        value = self.Command('SYSTEM:COMMUNICATE:MONITORING:ACTION?')(self.client).strip('\n')
        if value == 'ON':
            return True
        else:
            return False

    @monitoring_action.setter
    def monitoring_action(self, value:bool):
        if value:
            value = 'ON'
        else:
            value = 'OFF'
        self.Command('SYSTEM:COMMUNICATE:MONITORING:ACTION {}')(self.client, value)

    @property
    def power_fail_alarm_count(self):
        return int(self.Command('SYSTEM:ALARM:COUNT:PFAIL?')(self.client))

    @property
    def after_power_fail(self):
        return self.Command('SYSTEM:ALARM:ACTION:PFAIL?')(self.client).strip('\n')

    @after_power_fail.setter
    def after_power_fail(self, value: Literal['AUTO', 'OFF']):
        if value not in ['AUTO', 'OFF']:
            raise ValueError(f"Value must be 'AUTO' or 'OFF'. Not {value}")
        self.Command('SYSTEM:ALARM:ACTION:PFAIL {}')(self.client, value)

    @property
    def over_temperature_alarm_count(self):
        return int(self.Command('SYSTEM:ALARM:COUNT:OTEMPERATURE:?')(self.client))

    @property
    def after_over_temperature(self):
        return self.Command('SYSTEM:ALARM:ACTION:OTEMPERATURE?')(self.client).strip('\n')

    @after_over_temperature.setter
    def after_over_temperature(self, value: Literal['AUTO', 'OFF']):
        if value not in ['AUTO', 'OFF']:
            raise ValueError(f"Value must be 'AUTO' or 'OFF'. Not {value}")
        self.Command('SYSTEM:ALARM:ACTION:OTEMPERATURE {}')(self.client, value)

    @property
    def resistance_mode(self):
        ret = self.Command('SYSTEM:CONFIG:MODE?')(self.client).strip('\n')
        if ret == 'UIR':
            return True
        else:
            return False

    @resistance_mode.setter
    def resistance_mode(self, value: bool):
        if value:
            value = 'UIR'
        else:
            value = 'UIP'
        self.Command('SYSTEM:CONFIG:MODE {}')(self.client, value)


class Supply(SupplyLoad):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.operation_status_register.sink:
            logger.critical('Supply object connected to sink device.')

    def setup_standard_settings(self):
        super().setup_standard_settings()
        self.output_restore = 'OFF'

    @property
    def output(self):
        state = self.Command('OUTPUT?')(self.client).strip('\n')
        if state == 'ON':
            state = True
        else:
            state = False
        return state

    @output.setter
    def output(self, state: bool):
        if state:
            state = 'ON'
        else:
            state = 'OFF'
        self.Command('OUTPUT {}')(self.client, state)

    @property
    def output_after_remote(self):
        return super().after_remote

    @output_after_remote.setter
    def output_after_remote(self, value: Literal['AUTO', 'OFF']):
        super().after_remote = value

    @property
    def output_restore(self):
        return self.Command('SYSTEM:CONFIG:OUTPUT:RESTORE?')(self.client).strip('\n')

    @output_restore.setter
    def output_restore(self, value: Literal['AUTO', 'OFF']):
        if value not in ['AUTO', 'OFF']:
            raise ValueError(f"Value must be 'AUTO' or 'OFF'. Not {value}")
        self.Command('SYSTEM:CONFIG:OUTPUT:RESTORE {}')(self.client, value)


class Load(SupplyLoad):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if not self.operation_status_register.sink:
        #    logger.critical('Load object connected to supply device.')

    def setup_standard_settings(self):
        super().setup_standard_settings()
        self.input_restore = 'OFF'

    @property
    def input(self):
        state = self.Command('INPUT?')(self.client).strip('\n')
        if state == 'ON':
            state = True
        else:
            state = False
        return state

    @input.setter
    def input(self, state: bool):
        if state:
            state = 'ON'
        else:
            state = 'OFF'
        self.Command('INPUT {}')(self.client, state)

    @property
    def input_after_remote(self):
        return super().after_remote

    @input_after_remote.setter
    def input_after_remote(self, value: Literal['AUTO', 'OFF']):
        super().after_remote = value

    @property
    def input_restore(self):
        return self.Command('SYSTEM:CONFIG:INPUT:RESTORE?')(self.client).strip('\n')

    @input_restore.setter
    def input_restore(self, value: Literal['AUTO', 'OFF']):
        if value not in ['AUTO', 'OFF']:
            raise ValueError(f"Value must be 'AUTO' or 'OFF'. Not {value}")
        self.Command('SYSTEM:CONFIG:INPUT:RESTORE {}')(self.client, value)
