from abc import ABC, abstractmethod
from lab_remote_control.devices.common import Command, Instrument
from lab_remote_control.devices.supply_load import Supply, Load, BasePropertyClass
from lab_remote_control.devices.power_analyzer import PowerAnalyzer
from lab_remote_control.devices.dab import DualActiveBridge
import json
import logging
import os
import yaml


logger = logging.getLogger(__name__)


class TestBench(ABC):

    @classmethod
    def from_config_file(cls, path):
        with open(path) as f:
            if os.path.splitext(path)[-1] == '.json':
                settings = json.load(f)
            elif os.path.splitext(path)[-1] == '.yml' or os.path.splitext(path)[-1] == '.yaml':
                settings = yaml.load(f, Loader=yaml.FullLoader)
            else:
                class FileTypeInvalid(Exception):
                    pass

                raise FileTypeInvalid(f'file must be json or yaml: {path}')

        return cls.from_dict(settings)

    @classmethod
    def from_dict(cls, config_d):
        return cls(**config_d)

    @abstractmethod
    def __init__(self):
        pass

    def log_idns(self):
        for device_label, device in self.__dict__.items():
            if isinstance(device, Instrument):
                logger.info(f"{device_label}: {str(device.client.query('*IDN?'))}")

    def set_from_file(self, path):
        with open(path) as f:
            if os.path.splitext(path)[-1] == '.json':
                settings = json.load(f)
            elif os.path.splitext(path)[-1] == '.yml' or os.path.splitext(path)[-1] == '.yaml':
                settings = yaml.load(f, Loader=yaml.FullLoader)
            else:
                class FileTypeInvalid(Exception):
                    pass
                raise FileTypeInvalid(f'file must be json or yaml: {path}')

        return self.set_properties(settings)

    def set_properties(self, settings: dict):
        for device_label, device_settings in settings.items():
            for property_name, property_settings in device_settings.items():
                device = getattr(self, device_label)
                try:
                    property_ = getattr(device, property_name)
                except AttributeError:
                    property_ = None
                if isinstance(property_, BasePropertyClass):
                    for subproperty_name, value in property_settings.items():
                        setattr(property_, subproperty_name, value)
                else:
                    setattr(device, property_name, property_settings)

    @abstractmethod
    def turn_on(self):
        pass

    @abstractmethod
    def turn_off(self):
        pass


class BatteryDABTestBench(TestBench):

    def __init__(self, input_supply, load, output_supply, power_analyzer, test_object, properties=None, log_idns=True):
        logger.info('Establishing connections to devices...')
        logger.info('Connection to input_supply... ')
        self.input_supply = Supply.from_visa_resource_name(**input_supply)
        logger.info('Connection to load... ')

        def command(*args, **kwargs):
            return Command(*args, **kwargs, check_operation_complete_bit=False)
        self.load = Load.from_visa_resource_name(**load, clear_errors=False, enable_event_status_register=False, command=command)

        logger.info('Connection to output_supply... ')
        self.output_supply = Supply.from_visa_resource_name(**output_supply)
        logger.info('Connection to power_analyzer... ')
        self.power_analyzer = PowerAnalyzer.from_visa_resource_name(**power_analyzer)
        logger.info('Connection to DAB... ')
        self.test_object = DualActiveBridge.from_serial(test_object)
        if log_idns:
            self.log_idns()
        if properties:
            self.set_from_file(properties)

    def turn_on(self):
        self.load.input, self.output_supply.output, self.input_supply.output = True, True, True

    def turn_off(self):
        self.input_supply.output, self.input_supply.output, self.load.input = False, False, False
