import os
import sys
import time
import atexit

# Program imports
from lib.logger import Logger
from lib.api import FrontendApiManager
from lib.sync import SyncManager


class JobQueueManager():
    """ Handles the monitoring of the JobQueue and runs jobs """

    def __init__(self, config, verbose, daemon=True):
        """ Parse config file and setup the logging """

        self.config = config
        self.verbose = verbose
        self.daemon = daemon

        self.running = True

        self.logger = Logger(self.config.DAEMON.log_name,
                             self.config.DAEMON.log_dir).get_logger()

        self.pidfile = self.config.DAEMON.pid_file

        self.api_manager = FrontendApiManager(self.config.API, logger=self.logger)
        self.sync_manager = SyncManager(self.api_manager, logger=self.logger)

    def daemonize(self):
        """ Turn this running process into a deamon """
        # Perform first fork
        try:
            pid = os.fork()
            if pid > 0:
                self.logger.error('First fork returned but was >0, exiting')
                sys.exit(1)
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
                self.logger.error('Second fork returned but was >0, exiting')
                sys.exit(1)
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
        self.logger.debug("Written PID of '{0}' into file '{1}'".format(pid, self.pidfile))

    def on_exit(self):
        """ Delete the PID file """
        os.remove(self.pidfile)
        self.logger.debug('Removed the pid file ({0})'.format(self.pidfile))

    def run(self):
        """ Main worker loop """
        while self.running:
            # Loop over the job queue and handle any jobs that we are not processing yet
            job_queue = self.api_manager.get_job_queue()

            if not job_queue:
                self.logger.info('Job queue empty')

            for job in job_queue:
                try:
                    self.sync_manager.handle(job)
                    self.logger.info('Starting job {0}'.format(job['name']))
                except self.sync_manager.AlreadyWorkingOnException:
                    self.logger.debug('Already working on job {0}'.format(job['name']))
                except self.sync_manager.ActionAlreadyWorkingOnException:
                    self.logger.debug("action='{0}' job='{1}' message='action already working on'".format(
                        job['action'], job['name']))

            # Go over all queued jobs and complete any finished ones, report on what jobs we finished off
            for job in self.sync_manager.complete_jobs():
                self.logger.info('Removed finished job {0}'.format(job))

            # Sleep for a set time before checking the queue again
            sleep_time = float(self.config.DAEMON.sleep)
            self.logger.debug('Sleeping for {0} seconds'.format(sleep_time))
            time.sleep(sleep_time)

        if not self.running:
            # Good-ish place to be in
            self.logger.warning('Main loop was stopped (running = False)')
            return True
        else:
            # Bad place to be in
            self.logger.warning('Main loop broke without us saying (running = True)')
            return False

    def start(self):
        """ Start the daemon """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            if not os.path.isdir(os.path.dirname(self.pidfile)):
                print('ERROR: PID folder does not exist: {0}'.format(os.path.dirname(self.pidfile)))
                sys.exit(1)
            pid = None

        if pid:
            # pidfile exists, bail
            message = 'pidfile {0} already exists. Daemon already running?'
            self.logger.error(message.format(self.pidfile))
            sys.exit(1)
        
        # Turn into a daemon if we are told to
        if self.daemon:
            self.daemonize()
            message = 'We are now a daemon, all stdout/stderr redirected'
            self.logger.debug(message)
        else:
            print('INFO: Skipping daemon mode')
            print('INFO: Log file: {0}'.format(self.logger.log_file))

        # Work our magic
        self.run()

        # Finishing up properly
        self.logger.info('Finished successfully, bye bye!')
        return True

    def stop(self):
        """ Stop the daemon, kill off all jobs """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            if not os.path.isdir(os.path.dirname(self.pidfile)):
                message = 'ERROR: PID folder does not exist: {0}'
                print(message.format(os.path.dirname(self.pidfile)))
                sys.exit(1)
            pid = None

        if not pid:
            message = 'pidfile {0} does not exist. Daemon not running?'
            self.logger.error(message.format(self.pidfile))
            sys.exit(1)

        # Go over all queued jobs and close off any finished ones, report on the number we finished off
        for job in self.sync_manager.complete_jobs():
            self.logger.info('Removed finished job {0}'.format(job))

        # Go over all currently running jobs, report on them and then kill them.
        for process in self.sync_manager.processing_queue:
            self.logger.info('Still processing job {0}'.format(process.name))

            # We now kill off the process, upon restart the job should restart again
            self.logger.warning('Killing job {0}'.format(process.name))
            process.terminate()

        self.running = False
