from db import DBManager
from sync import SyncManager

import os
import sys
import logging

__daemon_redirect_to = '/dev/null'
__daemon_working_dir = '/'
__daemon_umask       = 0

class JobQueueManager():
    """
    Handles the monitoring of the JobQueue and runs jobs
    """

    def __init__(self):
        # Confirgure logger
        self.logger = None

    def deamonise(self):
        try:
            pid = os.fork()
        except OSError as e:
            self.logger.error('First fork failed ({0})'.format(e))
            raise Exception(e)

        if not pid:
            os.setsid()

            try:
                pid = os.fork()
            except OSError as e:
                self.logger.error('Second fork failed ({0})'.format(e))
                raise Exception(e)

            if not pid:
                self.logger.debug('Second fork worked')
                os.chdir(__daemon_working_dir)
                os.umask(__daemon_umask)
            else:
                self.logger.error('Second fork returned an incorrect PID ({0})'.format(pid))
                os._exit(0)
        else:
            self.logger.error('First fork returned an incorrect PID ({0})'.format(pid))
            os._exit(0)

        import resource
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if maxfd == resource.RLIM_INFINITY:
            maxfd = MAXFD

        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError as e:
                self.logger.warning('File descriptor ({0}) was not open to begin with'.format(fd))
                pass

        return True


if __name__ == '__main__':
    jqm = JobQueueManager()
    jqm.deamonise()
    open('test.log', 'w').write('test\n')

    sys.exit(0)
