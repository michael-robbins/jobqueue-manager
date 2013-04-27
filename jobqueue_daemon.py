#!/usr/bin/env python3

import argparse
from manager import JobQueueManager
from manager import JobQueueManagerConfigParser

#
#
#
parser = argparse.ArgumentParser(
        description='Daemon for the Media Server Job Processor'
)

parser.add_argument('-v', '--verbose', action='count', default=0
        , help='Increases verbosity (max 3)')
parser.add_argument('-c', '--connection-string', dest='conn', required=True
        , help='Connection String: user@host/db')

#
#
#
def main():
    """
    Parse the command-line options and configure the Job Queuer for use!
    """

    options = parser.parse_args()
    print(options)

    daemon = JobQueueManager(
            JobQueueManagerConfigParser(options)
    )

if __name__ == '__main__':
    main()
