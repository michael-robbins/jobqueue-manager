# System imports
import os
import sys
import time
import atexit

# Program imports
import db
from logger import Logger
from jobs   import JobManager
from config import ConfigManager

class JobQueueManager():
    """
    Handles the monitoring of the JobQueue and runs jobs
    """

    def __init__(self, config, verbose, daemon_mode=True):
        """
        Parse config file and setup the logging
        """
        
        self.config  = config
        self.verbose = verbose
        self.daemon_mode = daemon_mode

        self.logger = Logger(self.config.DAEMON.log_name
                    , self.config.DAEMON.log_file).get_logger()

        self.pidfile = self.config.DAEMON.pid_file

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
        os.chdir(self.config.DAEMON.working_dir)
        os.umask(self.config.DAEMON.umask)
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
        self.logger.debug('Written PID of ({0}) into file ({1})'.format(pid,self.pidfile))

    def on_exit(self):
        """
        Delete the PID file
        """

        os.remove(self.pidfile)
        self.logger.debug('Removed the pid file ({0})'.format(self.pidfile))

    def run(self, oneshot=False):
        """
        Main worker loop
        """

        if self.config.DB.db_type == 'psql':
            db_manager = db.Postgres_DBManager(self.config.DB, self.logger)
        elif self.config.DB.db_type == 'sqlite3':
            db_manager = db.SQLite3_DBManager(self.config.DB, self.logger)
        else:
            db_manager = None
            self.logger.error('Unsupport db_type in the config file')
            sys.exit(1)

        job_manager = JobManager(db_manager, self.logger)
        
        while job_manager.is_alive():
            # Figure out how to thow the job off to a separate thread here...
            # Another fork? Or perhaps a threading class
            job = job_manager.get_next_job()

            if job:
                self.logger.info('Starting job {0}'.format(job.job_id))
                job.execute()
            else:
                self.logger.info('Job queue is empty.')
            
            if oneshot:
                break

            sleep_time = float(self.config.DAEMON.sleep)
            self.logger.debug('Sleeping for {0}'.format(sleep_time))
            time.sleep(sleep_time)

        if not job_manager.is_alive():
            self.logger.info('job_manager.isalive() is false, exiting')
            return True
        else:
            self.logger.error('We exited the while loop but are supposedly still alive')
            return False

    def start(self, oneshot=False):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile,'r') as pf:
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
        if self.daemon_mode:
            print('INFO: We are about to turn into a daemon, no more stdout!')
            self.daemonize()
            self.logger.debug('We are now a daemon, congrats')
        else:
            print('INFO: Skipping daemon mode')
            print('INFO: Log file: ' + self.config.DAEMON.log_file)

        # Work our magic
        self.run(oneshot)

        # Finishing up properly
        self.logger.info('Finished successfully, bye bye!')

    def stop(self):
        """
        Stop the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            if not os.path.isdir(os.path.dirname(self.pidfile)):
                print('ERROR: PID folder does not exist: {0}'.format(os.path.dirname(self.pidfile)))
                sys.exit(1)
            pid = None

        if not pid:
            message="pidfile {0} does not exist. " + \
                    "Daemon not running?"
            self.logger.error(message.format(pidfile))
            sys.exit(1)
        
        # Figure out how to stop a live daemon running
        # Kill the pid?
        # Inject kill command into DB queue?

if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_JobQueueManager()
