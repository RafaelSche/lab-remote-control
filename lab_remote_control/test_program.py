from abc import ABC, abstractmethod
from dataclasses import dataclass
from lab_remote_control.testbench import TestBench, BatteryDABTestBench
from time import sleep
from typing import Union
import json
import logging
import numpy as np
import os
import pandas as pd
import yaml


logger = logging.getLogger(__name__)


class TestProgram(ABC):

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
        param_d = {}
        for k, v in config_d.items():
            if isinstance(v, dict):
                param_d[k] = np.arange(start=float(v['start']),
                                       stop=float(v['stop']),
                                       step=float(v['step']))
            elif isinstance(v, str):
                params = [float(string.strip()) for string in v.split(',')]
                param_d[k] = np.arange(*params)
            else:
                raise TypeError
        return cls(**param_d)

    @abstractmethod
    def step(self, testbench: TestBench):
        pass


@dataclass
class BatteryDABTestProgram(TestProgram):
    phases: Union[list, np.array]
    input_voltage: Union[list, np.array]
    output_voltage: Union[list, np.array]
    sleep_time: float = 1.0

    def step(self, testbench: BatteryDABTestBench):
        for phase in self.phases:
            testbench.test_object.set_phase(phase)
            for volt_in in self.input_voltage:
                testbench.input_supply.voltage.setting = volt_in
                for volt_out in self.output_voltage:
                    testbench.output_supply.voltage.setting = volt_out

                    sleep(self.sleep_time)

                    measurements = {'phase': phase, 'set_input_voltage': volt_in, 'set_output_voltage': volt_out}
                    measurements = dict(measurements, **testbench.power_analyzer.pull_script_vars())
                    yield measurements


class Measurements:

    @classmethod
    def from_csv(cls, path):
        obj = cls(path)
        obj.measurements = pd.read_csv(path)
        return obj

    def __init__(self, save_path='measurements.csv'):
        self.measurements = pd.DataFrame()
        self.save_path = save_path

    def add_row(self, measurement: dict):
        measurement = {k: [v] for k, v in measurement.items()}
        self.measurements = pd.concat([self.measurements, pd.DataFrame.from_dict(measurement)], ignore_index=True)
        self.measurements.reset_index(drop=True)

    def save(self, path=None):
        if not path:
            path = self.save_path
        self.measurements.to_csv(path)
