from jobqueue_manager.db import DBManager
from jobqueue_manager.sync import SyncManager
from jobqueue_manager.jobs import JobManager

import os
import sys
import time
import atexit
import logging

class JobQueueManagerConfigParser():
    """
    Takes the options provided on the command line and parses them
    """

    def __init__(self, options):
        if options.config_file:
            self.parse_configfile(options.config_file)
        else:
            self.config_file = None

    def parse_configfile(config_file):
        pass


class JobQueueManager():
    """
    Handles the monitoring of the JobQueue and runs jobs
    """
    daemon_redirect_to = '/dev/null'
    daemon_working_dir = '/'
    daemon_umask       = 0
    default_logfile = '/home/michael/logs/media_manager.log'
    default_pidfile = '/run/MediaServer/jobqueuer.pid'

    def __init__(self, options):
        """
        Set PID file and start logging
        """

        self.options = options

        if self.options.pidfile:
            self.pidfile = self.options.pidfile
        else:
            self.pidfile = self.default_pidfile
        
        self.setup_logging('jobqueue_manager')

    def setup_logging(self, title, log_destination=default_logfile):
        """
        Setup the logger
        """
        self.logger = logging.getLogger(title)
        self.logger.setLevel(logging.DEBUG)

        # Create the file log, so channel hander as WE ARE A BLOODY DAEMON!
        fh = logging.FileHandler(log_destination)
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('timestamp="%(asctime)s" name="%(name)s" level="%(levelname)s" message="%(message)s"')

        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.logger.debug('Set up logging')

    def daemonize(self):
        """
        Turn this running process into a deamon
        """

        # Perform first fork
        try:
            pid = os.fork()
            if pid > 0:
                os._exit(0)
            self.logger.debug('First fork worked')
        except OSError as e:
            self.logger.error('First fork failed ({0})'.format(e))
            raise Exception(e)

        # Escape out of where we started
        os.chdir(self.daemon_working_dir)
        os.umask(self.daemon_umask)
        os.setsid()

        # Perform second fork
        try:
            pid = os.fork()
            if pid > 0:
                os._exit(0)
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
        with open(self.pidfile,'w+') as f:
            f.write(pid + '\n')
        self.logger.debug('Written PID file ({0})'.format(self.pidfile))

    def on_exit(self):
        """
        Delete the PID file
        """
        os.remove(self.pidfile)
        self.logger.debug('Removed the pid file ({0})'.format(self.pidfile))

    def run(self):
        """
        Main worker loop
        """
        job_manager = JobManager(options)
        
        while job_manager.isalive():
            job = job_manager.nextjob()

            if job:
                self.logger.debug('Starting job {0}'.format(job.getid()))
                job.report_start()
                job.execute()

                if job.completed():
                    self.logger.debug('Finished job {0}'.format(job.getid()))
                    job.report_complete()
                else:
                    self.logger.debug('Issue with job {0}'.format(job.getid()))
                    job.report_failed()
            
            time.sleep(options.sleep_time)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        # pidfile exists, bail
        if pid:
            message = "pidfile {0} already exist. " + \
                      "Daemon already running?\n"
            self.logger.error(message.format(self.pidfile))
            sys.exit(1)
        
        # Start the daemon
        if not self.daemonize():
            self.logger.error('Unable to create daemon properly, bailing')
            raise Exception('Bad Daemon Creation')

        # Look into resource pools here, potentially multi-thread the process. Eg. multiple instances of run()
        if not self.run():
            raise Exception('Something broke bad')

        self.logger.notice('Finished successfully, bye bye!')

    def stop(self):
        """
        Stop the daemon
        """
        


if __name__ == '__main__':
    jqm = JobQueueManager('/run/MediaServer/jobqueuer.pid')
    jqm.start()
