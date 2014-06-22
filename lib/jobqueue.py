# System imports
import os
import sys
import time
import atexit

# Program imports
from logger import Logger
from config import ConfigManager
from sync import SyncManager
from api import ApiManager


class JobQueueManager():
    """
    Handles the monitoring of the JobQueue and runs jobs
    """

    def __init__(self, config, verbose, daemon=True):
        """
        Parse config file and setup the logging
        """

        self.config = config
        self.verbose = verbose
        self.daemon = daemon

        self.logger = Logger(self.config.DAEMON.log_name,
                             self.config.DAEMON.log_file).get_logger()

        self.pidfile = self.config.DAEMON.pid_file

        self.api_manager = ApiManager(self.config.API, self.logger)
        self.sync_manager = SyncManager(self.api_manager, self.logger)

    def daemonize(self):
        """
        Turn this running process into a deamon
        """

        # Perform first fork
        try:
            pid = os.fork()
            if pid > 0:
                os.exit(0)
            self.logger.debug('First fork worked')
        except OSError as e:
            self.logger.error('First fork failed ({0})'.format(e))
            raise Exception(e)

        # Escape out of where we started
        os.chdir(self.config.DAEMON.working_dir)
        os.umask(self.config.DAEMON.umask)
        os.setsid()

        # Perform second fork
        try:
            pid = os.fork()
            if pid > 0:
                os.exit(0)
        except OSError as e:
            self.logger.error('Second fork failed ({0})'.format(e))
            raise Exception(e)

        # Close off the stdXXX
        self.logger.debug('Closing file descriptors')
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Register the pid file deletion
        atexit.register(self.on_exit)

        # Write the PID to file
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write(pid + '\n')
        self.logger.debug('Written PID of ({0}) into file ({1})'.format(pid, self.pidfile))

    def on_exit(self):
        """
        Delete the PID file
        """

        os.remove(self.pidfile)
        self.logger.debug('Removed the pid file ({0})'.format(self.pidfile))

    def run(self, one_shot=False):
        """
        Main worker loop
        """

        while True:
            # Figure out how to thow the job off to a separate thread here...
            # Another fork? Or perhaps a threading class
            job_queue = self.api_manager.get(self.api_manager.endpoints.JOBS)

            if not job_queue:
                self.logger.info('Job queue is empty')
            else:
                for job in job_queue:
                    if not self.sync_manager.working_on(job):
                        message = 'Starting job {0}'.format(job.job_id)
                        self.logger.info(message)
                        self.sync_manager.handle(job)
                    else:
                        message = 'Already working on {0}'.format(job.job_id)
                        self.logger.info(message)

            if one_shot:
                message = 'Breaking out of job loop due to one_shot'
                self.logger.warning(message)
                break

            sleep_time = float(self.config.DAEMON.sleep)
            self.logger.debug('Sleeping for {0}'.format(sleep_time))
            time.sleep(sleep_time)

        self.logger.error('Exiting run()')

    def start(self, one_shot=False):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            if not os.path.isdir(os.path.dirname(self.pidfile)):
                print('ERROR: PID folder does not exist: {0}'.format(os.path.dirname(self.pidfile)))
                sys.exit(1)
            pid = None

        # pidfile exists, bail
        if pid:
            message = "pidfile {0} already exists. " + \
                      "Daemon already running?\n"
            self.logger.error(message.format(self.pidfile))
            sys.exit(1)
        
        # Turn into a daemon if we are told to
        if self.daemon:
            self.daemonize()
            message = 'We are now a daemon, all stdout/stderr redirected'
            self.logger.debug(message)
        else:
            print('INFO: Skipping daemon mode')
            print('INFO: Log file: ' + self.config.DAEMON.log_file)

        # Work our magic
        self.run(one_shot)

        # Finishing up properly
        self.logger.info('Finished successfully, bye bye!')

    def stop(self):
        """
        Stop the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            if not os.path.isdir(os.path.dirname(self.pidfile)):
                message = 'ERROR: PID folder does not exist: {0}'.format(os.path.dirname(self.pidfile))
                print(message)
                sys.exit(1)
            pid = None

        if not pid:
            message = "pidfile {0} does not exist. Daemon not running?"
            self.logger.error(message.format(self.pidfile))
            sys.exit(1)
        
        # Figure out how to stop a live daemon running
        # Kill the pid?
        # Inject kill command into DB queue?

if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_JobQueueManager()
