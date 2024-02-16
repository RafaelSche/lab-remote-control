from datetime import datetime
from lab_remote_control.devices.common import Command
from lab_remote_control.devices.supply_load import logger as supply_load_logger
from lab_remote_control.devices.power_analyzer import Script, logger as power_analyzer_logger
from lab_remote_control.testbench import TestBench, logger as testbench_logger
from lab_remote_control.test_program import Measurements, TestProgram, logger as test_program_logger
from time import sleep
import lab_remote_control
import json
import logging
import os
import yaml


testbench_types = {}
for name, type_ in vars(lab_remote_control.testbench).items():
    if isinstance(type_, type):
        if TestBench in type_.mro():
            testbench_types[name] = type_

test_program_types = {}
for name, type_ in vars(lab_remote_control.test_program).items():
    if isinstance(type_, type):
        if TestProgram in type_.mro():
            test_program_types[name] = type_


main_logger = logging.getLogger(__name__)
loggers = [main_logger, supply_load_logger, power_analyzer_logger, testbench_logger, test_program_logger]

for logger in loggers:
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)


class Executor:

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
        type_ = config_d['testbench'].pop('type')
        config_path = config_d['testbench'].pop('path')
        config_d['testbench'] = testbench_types[type_].from_config_file(config_path)

        type_ = config_d['test_program'].pop('type')
        config_path = config_d['test_program'].pop('path')
        config_d['test_program'] = test_program_types[type_].from_config_file(config_path)
        return cls(**config_d)

    def __init__(self, testbench, test_program, measurements=Measurements):
        self.testbench = testbench
        self.test_program = test_program
        self.measurements = measurements()

    def run(self):
        exit_code = 0
        try:
            self.testbench.turn_on()
            start_time, step = datetime.now(), 0
            logger.info('Test Programm started... ')
            for measurement in self.test_program.step(self.testbench):
                self.measurements.add_row(measurement)
                logger.info(f'Step {step} completed; yield: {measurement}, time: {datetime.now() - start_time}')
                step += 1
        except Exception as e:
            logger.error(str(type(e)) + '; ' + str(e))
            exit_code = 1

        finally:
            self.testbench.turn_off()

            #for param_name, params in self.test_program.__dict__.items():
            #    self.measurements.measurements[f'set_{param_name}'] = params[:len(self.measurements.measurements)]
            self.measurements.save()

        return exit_code
