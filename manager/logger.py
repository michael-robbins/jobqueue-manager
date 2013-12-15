import logging
import os

class Logger():
    
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
    log_file = '/tmp/test.log'

    if os.path.exists(log_file):
        os.remove(log_file)

    logger = Logger('test',log_file).get_logger()
    logger.debug('test')
    with open(log_file, 'r') as f:
        print(f.read())

