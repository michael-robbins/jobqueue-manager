import os
import logging


class Logger():
    """
    Has the following levels (in increasing importance):
    Logger.debug()
    Logger.info()
    Logger.warning()
    Logger.error()
    Logger.critical()
    """

    def __init__(self, title, log_destination):
        """
        Setup the logger
        """
        self.logger = logging.getLogger(title)
        self.logger.setLevel(logging.DEBUG)

        # If it's a relative path add it onto the scripts working directory
        if log_destination.startswith('.'):
            log_destination = os.path.join(os.path.dirname(os.path.realpath(__file__)), log_destination)

        # os.path.normpath strips out the crap
        log_destination = os.path.normpath(os.path.join(log_destination, '{0}.log'.format(title)))

        self.logger.log_file = log_destination
        fh = logging.FileHandler(log_destination)
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('timestamp="%(asctime)s" name="%(name)s" ' +
                                      'level="%(levelname)s" message="%(message)s"')

        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.logger.debug('Logging is now set up')
        self.logger.info('Log File: {0}'.format(log_destination))

    def get_logger(self):
        return self.logger
