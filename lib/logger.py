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

        fh = logging.FileHandler(log_destination)
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('timestamp="%(asctime)s" name="%(name)s" ' + \
                'level="%(levelname)s" message="%(message)s"')

        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.logger.debug('Logging is now set up')
        self.logger.info('Log File: {0}'.format(log_destination))

    def get_logger(self):
        return self.logger

if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_Logger()

