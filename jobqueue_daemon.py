#!/usr/bin/env python3

import argparse
from lib.manager import JobQueueManager

parser = argparse.ArgumentParser(
        description='Daemon for the Media Server Job Processor'
)

parser.add_argument('-v', '--verbose', action='count', default=0
        , help='Increases verbosity')
parser.add_argument('-c', '--config',  action='store', dest='config_file', required=True
        , help='Configuration file for the Job Queue Manager')
parser.add_argument('--daemon', action='store_true'
        , help='Start the Manager as a daemon')

#
#
#
def main():
    """
    Parse the command-line options and configure the Job Queuer for use!
    """

    options = parser.parse_args()

    manager = JobQueueManager(
            options.config_file
            , options.verbose
            , options.daemon
    )

    return manager.run()

if __name__ == '__main__':
    main()
