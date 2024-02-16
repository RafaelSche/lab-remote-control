from abc import ABC, abstractmethod
from dataclasses import dataclass, KW_ONLY
from datetime import datetime
from time import sleep
from typing import Optional, Type, Union
import logging
import pyvisa
import time


logger = logging.getLogger(__name__)


class Register(ABC):

    @classmethod
    def from_client(cls, client: pyvisa.resources.MessageBasedResource, event_register=False):
        register = cls()
        if event_register:
            ret = register.query_command_event(client).strip('\n')
        else:
            ret = register.query_command(client).strip('\n')
        register.set_by_int(int(ret))
        return register

    @abstractmethod
    def set_by_bit_string(self, bit_string):
        pass

    def set_by_int(self, int_, register_length=8):
        bit_string = f'{int_:b}'
        if len(bit_string) < register_length:
            additional_bit_count = register_length - len(bit_string)
            bit_string = '0'*additional_bit_count + bit_string
        return self.set_by_bit_string(bit_string)


@dataclass
class EventStatusRegister(Register):  # Short: ESRRegister;
    operation_complete: Optional[bool] = None  # Operation Complete Bit; Short: opc;
    query_error: Optional[bool] = None  # Query Error; Short: qye;
    device_depend_error: Optional[bool] = None  # Device Depend Error; Short: dde;
    execution_error: Optional[bool] = None  # Execution Error; Short: exe;
    command_errors: Optional[bool] = None  # Command Errors; Short: cme;
    power_on: Optional[bool] = None  # Power On; Short: pon;

    def set_by_bit_string(self, bit_string):
        self.operation_complete = bool(int(bit_string[::-1][0]))
        self.query_error = bool(int(bit_string[::-1][2]))
        self.device_depend_error = bool(int(bit_string[::-1][3]))
        self.execution_error = bool(int(bit_string[::-1][4]))
        self.command_errors = bool(int(bit_string[::-1][5]))
        self.power_on = bool(int(bit_string[::-1][7]))

    def properties_to_int(self) -> int:
        int_ = 0
        if self.operation_complete:
            int_ += 1
        if self.query_error:
            int_ += 4
        if self.device_depend_error:
            int_ += 8
        if self.execution_error:
            int_ += 16
        if self.command_errors:
            int_ += 32
        if self.power_on:
            int_ += 128
        return int_

    def __post_init__(self):
        self.set_command = None
        self.query_command = Command('*ESR?')
        self.set_enable_register_command = Command(f'*ESE {self.properties_to_int()}')

    def raise_active_exceptions(self, error_msg):
        if self.query_error:
            raise self.QueryError(error_msg)
        if self.device_depend_error:
            raise self.DeviceDependError(error_msg)
        if self.execution_error:
            raise self.ExecutionError(error_msg)
        if self.command_errors:
            raise self.CommandErrors(error_msg)

    class EventStatusRegisterError(Exception):
        pass

    class QueryError(EventStatusRegisterError):
        pass

    class DeviceDependError(EventStatusRegisterError):
        pass

    class ExecutionError(EventStatusRegisterError):
        pass

    class CommandErrors(EventStatusRegisterError):
        pass


@dataclass
class Command:
    scpi_command: str
    _: KW_ONLY
    raise_exceptions: Optional[bool] = True
    check_operation_complete_bit: Optional[bool] = True
    await_esr_sleep_time: Optional[float] = 0.1
    await_operation_complete_bit_timeout: Optional[float] = 1.0
    ignore_timeout: Optional[bool] = True
    query_delay: Optional[float] = None

    def __post_init__(self):
        self.query = self.scpi_command[-1] == '?'
        self.event_status_register_type: Type["EventStatusRegister"] = EventStatusRegister

    def check_operation_complete(self, *, esr: EventStatusRegister, **kwargs):
        return esr.operation_complete

    def __call__(self, client: pyvisa.resources.MessageBasedResource, *args)\
            -> Union[str, EventStatusRegister, None]:
        try:
            if self.query:
                try:
                    return client.query(self.scpi_command.format(*args))
                except pyvisa.errors.VisaIOError as e:
                    print(str(type(e)), str(e), self.scpi_command.format(*args))
                    esr = self.event_status_register_type.from_client(client)
                    if self.raise_exceptions:
                        # clear error queue to clear the according bit in the Event Status Register
                        error_msg = client.query('SYSTEM:ERROR:ALL?')
                        error_msg += '\n' + self.event_status_register_type.from_client(client).__str__()
                        esr.raise_active_exceptions(error_msg)
            else:
                client.write(self.scpi_command.format(*args))
                operation_complete = False
                cycles = 0
                before = datetime.now()
                while not operation_complete and self.check_operation_complete_bit:
                    cycles += 1
                    logger.info(f'Waiting for operation {self.scpi_command.format(*args)} to complete...')
                    sleep(self.await_esr_sleep_time)
                    esr = self.event_status_register_type.from_client(client)
                    if self.raise_exceptions:
                        # clear error queue to clear the according bit in the Event Status Register
                        error_msg = client.query('SYSTEM:ERROR:ALL?')
                        error_msg += '\n' + self.event_status_register_type.from_client(client).__str__()
                        error_msg += '\n' + self.scpi_command.format(*args)
                        esr.raise_active_exceptions(error_msg)
                    operation_complete = self.check_operation_complete(esr=esr, client=client)
                    if delta := (datetime.now() - before).seconds >= self.await_operation_complete_bit_timeout:
                        if self.ignore_timeout:
                            logger.warning(
                                f'Timeout waiting for operation complete bit. Waited: {delta} sec; {cycles} cycles;')
                            break
                        else:
                            raise TimeoutError
        except (BrokenPipeError, TimeoutError) as e:
            logger.critical(f'{str(type(e))}, {str(e)}\nRecall function... ')
            client.close()
            time.sleep(0.5)
            client.open()
            self.__call__(client, *args)
        try:
            return esr
        except NameError:
            return None


class Instrument(ABC):
    event_status_register_type: Type[EventStatusRegister]

    @classmethod
    def from_visa_resource_name(cls, resource: str, resource_manager=pyvisa.ResourceManager(), **kwargs):
        if resource.startswith('TCPIP') and resource.endswith('SOCKET'):
            return cls(resource_manager.open_resource(resource, read_termination='\n', write_termination='\n'), **kwargs)
        else:
            return cls(resource_manager.open_resource(resource), **kwargs)

    @property
    def event_status_register(self):
        return self.event_status_register_type.from_client(self.client)

    @property
    def error_queue(self):
        return Command('SYSTEM:ERROR:ALL?')(self.client)
