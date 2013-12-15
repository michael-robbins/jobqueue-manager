from manager.db import DBManager

from manager.sync import SyncManager
from manager.jobs import JobManager
from manager.logging import Logging

import os
import sys
import time
import atexit
import configparser

#
#
#
class JobQueueManager():
    """
    Handles the monitoring of the JobQueue and runs jobs
    """

    required_config = {
            'MANAGER'  : ['db_type', 'db_host', 'db_port', 'db_name', 'db_user', 'db_file', 'sleep']
            , 'DAEMON' : ['pid_file', 'log_name', 'log_file', 'working_dir', 'umask']
            }


    #
    #
    #
    def __init__(self, config_file, verbose, daemon_mode=True):
        """
        Parse config file and setup the logging
        """

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.verbose=verbose
        self.daemon_mode=daemon_mode

        for section in self.required_config:
            if section not in self.config.sections():
                print('ERROR: Missing config_file section:', section)
            else:
                for option in self.required_config[section]:
                    if option not in self.config.options(section):
                        print('ERROR: Missing Option', option, 'inside section:', section)

        self.logger = Logging(self.config['DAEMON']['log_name']
                    , self.config['DAEMON']['log_file']).get_logger()

        for i in self.config.sections():
            for j in self.config.options(i):
                self.logger.debug('{0}: {1}={2}'.format(i,j,self.config[i][j]))


    #
    #
    #
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
        os.chdir(self.config['DAEMON']['working_dir'])
        os.umask(self.config['DAEMON']['umask'])
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

    #
    #
    #
    def on_exit(self):
        """
        Delete the PID file
        """
        os.remove(self.pidfile)
        self.logger.debug('Removed the pid file ({0})'.format(self.pidfile))

    #
    #
    #
    def run(self):
        """
        Main worker loop
        """
        db_manager  = DBManager(self.config['MANAGER'], self.logger)
        job_manager = JobManager(db_manager.get_cursor(), self.logger)
        
        while job_manager.is_alive():
            job = job_manager.get_next_job()

            if job:
                self.logger.debug('Starting job {0}'.format(job.getid()))
                job.execute()

                if job.completed():
                    self.logger.debug('Finished job {0}'.format(job.getid()))
                    job.report_complete()
                else:
                    self.logger.debug('Issue with job {0}'.format(job.getid()))
                    job.report_failed()
            else:
                self.logger.debug('Job queue is empty.')
            
            sleep_time = float(self.config['MANAGER']['sleep'])
            self.logger.debug('Sleeping for {0}'.format(sleep_time))
            time.sleep(sleep_time)

        if not job_manager.isalive():
            self.logger.debug('job_manager.isalive() is false, exiting')
            return True
        else:
            self.logger.debug('We exited the while loop but are supposedly still alive')
            return False
    #
    #
    #
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
            message = "pidfile {0} already exists. " + \
                      "Daemon already running?\n"
            self.logger.error(message.format(self.pidfile))
            sys.exit(1)
        
        # Turn into a daemon if we are told to
        if self.daemon_mode:
            print('NOTICE: We are about to turn into a daemon, no more stdout!')
            self.daemonize()
            self.logger.debug('We are now a daemon, congrats')
        else:
            print('NOTICE: Skipping daemon mode, all to stdout')

        # Work our magic
        self.run()

        # Finishing up properly
        self.logger.notice('Finished successfully, bye bye!')


    #
    #
    #
    def stop(self):
        """
        Stop the daemon
        """
        # Figure out how to stop a live daemon running
        # Load PID file, kill process?
        # Inject kill command into DB queue?


#
#
#
if __name__ == '__main__':
    """
    Peform some basic checks
    """
    jqm = JobQueueManager()
    jqm.start()
