from argparse import ArgumentParser
from lab_remote_control.executor import Executor
from lab_remote_control.test_program import Measurements

parser = ArgumentParser('lab-remote-control')
parser.add_argument('-e, --executor-config-file', dest='executor_config_file')
parser.add_argument('-c', '--continue', dest='continue_', action='store_true', default=False)
args = parser.parse_args()

executor = Executor.from_config_file(args.executor_config_file)
if args.continue_:
    Executor.measurements = Measurements.from_csv(Executor.measurements.save_path)

if __name__ == '__main__':
    executor.run()
