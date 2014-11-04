#!/usr/bin/env python3

import signal
import argparse

from lib.jobqueue import JobQueueManager
from lib.config import ConfigManager

parser = argparse.ArgumentParser(
    description='Daemon for the Media Server Job Processor'
)

parser.add_argument('-v', '--verbose', action='count', default=0
                    , help='Increases verbosity')
parser.add_argument('-c', '--config',  action='store', dest='config_file', required=True
                    , help='Configuration file for the Job Queue Manager')
parser.add_argument('-d', '--daemon', action='store_true', dest='daemon'
                    , help='Background the Manager')


def main():
    """ Parse the command-line options and configure the Job Queue for use! """

    args = parser.parse_args()
    conf = ConfigManager(args.config_file).get_config()

    manager = JobQueueManager(config=conf, verbose=args.verbose, daemon=args.daemon)

    def stop_manager():
        """ Stop the manager on a CTRL+C """
        manager.stop()

    # Capture the 'Interrupt' signal
    signal.signal(signal.SIGINT, stop_manager)

    manager.start()

if __name__ == '__main__':
    main()
