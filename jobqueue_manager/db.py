import sys
import psycopg2


class DBManager():
    """
    Generic DB functions in here, will be specialised per DB type (PostgreSQL, MySQL, SQLLite)
    """

    _default_db_type  = 'psql'
    _default_db_port  = 5432

    _default_connection_string = 'host={0} user={1} dbname={2} port={3}'
    _default_connection_pass   = ' password={0}'

    _required_db_opts = ['db_user', 'db_pass', 'db_host']

    def __init__(self, db_type, db_user, db_pass, db_name, db_host, db_port, logger = None):
        """
        Set up the connection string details
        """

        self.db_type = db_type
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.logger = logger

        for opt in self._required_db_opts:
            if not locals()[opt]:
                self.logger.error('Missing required parameter \'{0}\''.format(opt))
                return False

        self.connection_string = self._default_connection_string.format(
                self.db_host
                , self.db_user
                , self.db_name
                , self.db_port)

        if self.db_pass:
            self.connection_string += self._default_connection_pass.format(self.db_pass)
        
        return self.connect(self.connection_string)

    def connect(self, connection_string):
        """
        Initiate connection to the DB
        """

        try:
            return psycopg2.connect(connection_string)
        except Exception as e:
            self.logger.error('Failed to connect to the DB: {0}'.format(e))
            return None

        return None

if __name__ == '__main__':
    db_manager = DBManager('psql', 'michael', 'test', 'jobmanager', 'skadi', '5432')
