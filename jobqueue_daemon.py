#!/usr/bin/env python3

import argparse
from jobqueue_manager.manager import JobQueueManager
from jobqueue_manager.manager import JobQueueManagerConfigParser

parser = argparse.ArgumentParser(
        description='Daemon for the Media Server Job Processor'
)

parser.add_argument('-v', '--verbose', action='count', default=0
        , help='Increases verbosity (max 3)')
parser.add_argument('-c', '--config',  action='store', dest='config_file'
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
            JobQueueManagerConfigParser(options.config_file)
            , options.verbose
            , options.daemon
    )

    return manager.run()

if __name__ == '__main__':
    main()
