import sys
import psycopg2


class DBManager():
    """
    Generic DB functions in here, will be specialised per DB type (PostgreSQL, MySQL, SQLLite)
    """

    _required_db_opts = ['db_type', 'db_host', 'db_port', 'db_name', 'db_user']

    def __init__(self, config, logger=None):
        """
        Set up the connection string details
        """

        self.logger = logger

        for opt in self._required_db_opts:
            if opt in config:
                setattr(self, opt, config[opt])
            else:
                self.logger.error('You are missing the following config option: {0}'.format(opt))


class Postgres_DBManager(DBManager):
    """
    Postgres overload
    """

    self.connected = False

    def __init__(self, config, logger=None):
        """
        Set any psql specific stuff and bail to parent class
        """
        pass

    def get_cursor(self):
        """
        Connect to DB and return cursor
        """

        try:
            print (self.connection_string)
            conn = psycopg2.connect(self.connection_string)
            self.connected = True
            return conn.cursor()
        except Exception as e:
            self.logger.error('Failed to connect to the DB: {0}'.format(e))
            return None
        return None

if __name__ == '__main__':
    db_manager = DBManager('psql', 'michael', 'test', 'jobmanager', 'skadi', '5432')
