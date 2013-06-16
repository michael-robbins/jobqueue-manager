import sys
import psycopg2


class DBManager():
    """
    Generic DB functions in here, will be specialised per DB type (PostgreSQL, MySQL, SQLLite)
    """

    _default_connection_string = 'host={0} user={1} dbname={2} port={3}'
    _default_connection_pass   = ' password={0}'

    _required_db_opts = ['db_type', 'db_host', 'db_port', 'db_name', 'db_user']

    def __init__(self, config, logger=None):
        """
        Set up the connection string details
        """

        self.logger = logger

        for opt in self._required_db_opts:
            setattr(self, opt, config[opt])

        for opt in self._required_db_opts:
            print(eval('self.{0}'.format(opt)))


        for opt in self._required_db_opts:
            if opt not in locals():
                self.logger.error('Missing required parameter \'{0}\''.format(opt))

        self.connection_string = self._default_connection_string.format(
                self.db_host
                , self.db_user
                , self.db_name
                , self.db_port)

        if 'db_pass' in config:
            self.connection_string += self._default_connection_pass.format(config['db_pass'])

    def get_cursor(self):
        """
        Connect to DB and return cursor
        """

        try:
            print (self.connection_string)
            conn = psycopg2.connect(self.connection_string)
            return conn.cursor()
        except Exception as e:
            self.logger.error('Failed to connect to the DB: {0}'.format(e))
            return None
        return None

if __name__ == '__main__':
    db_manager = DBManager('psql', 'michael', 'test', 'jobmanager', 'skadi', '5432')
