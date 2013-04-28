import sys
import psycopg2


class DBManager():
    """
    Generic DB functions in here, will be specialised per DB type (PostgreSQL, MySQL, SQLLite)
    """

    __default_db_type  = 'PostgreSQL'
    __default_db_port  = 5432

    __default_connection_string = 'host={0} user={1} dbname={2} port={3}'
    __default_connection_pass   = ' password={0}'

    __required_db_opts = ['db_user', 'db_pass', 'db_host']

    def __init__(
            db_type   = __default_db_type
            , db_user = None
            , db_pass = None
            , db_host = None
            , db_port = __default_db_port
            , logger  = None):
        """
        Set up the connection string details
        """

        this.db_type = db_type
        this.db_user = db_user
        this.db_pass = db_pass
        this.db_host = db_host
        this.db_port = db_port
        this.logger = logger

        for opt in __required_db_opts:
            if not locals()[opt]:
                self.logger.error('Missing required parameter \'{0}\''.format(opt))
                return False

        this.connection_string = __default_connection_string.format(
                this.db_host
                , this.db_user
                , this.db_name
                , this.db_port)

        if this.db_pass:
            this.connection_string += __default_connection_pass.format(this.db_pass)
        
        return self.connect(this.connection_string)

    def connect(connection_string):
        """
        Initiate connection to the DB
        """

        try:
            return psycopg2.connect(connection_string)
        except Exception as e:
            self.logger.error('Failed to connect to the DB: {0}'.format(e))
            return None

        return None
