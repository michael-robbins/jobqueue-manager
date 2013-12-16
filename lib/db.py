#
#
#
class DBManager():
    """
    Generic DB functions in here, will be specialised per DB type (PostgreSQL, MySQL, SQLLite)
    """

    def __init__(self, config, required_opts, logger):
        """
        Set up the connection string details
        """

        self.logger = logger

        for opt in required_opts:
            if opt in config:
                setattr(self, opt, config[opt])
            else:
                self.logger.error('You are missing the following config option: {0}'.format(opt))

    def get_sql_cmds(list_of_cmds):
        """
        return dict() of generic SQL commands
        """
        SQL               = {}
        SQL['all_jobs']   = 'SELECT * FROM job_queue'
        SQL['next_job']   = 'SELECT * FROM job_queue WHERE date_started IS NULL ' + \
                                'AND date_finished IS NULL ORDER BY date_queued ASC LIMIT 1'
        SQL['get_job']    = 'SELECT * FROM job_queue WHERE job_id = ?'
        SQL['delete_job'] = 'DELETE FROM job_queue WHERE job_id = ?'

        SQL['get_archived_job'] = 'SELECT * FROM job_history WHERE job_id = ?'

        return { i: SQL[i] for i in SQL if i in list_of_cmds }


#
#
#
class Postgres_DBManager(DBManager):
    """
    Postgres overload
    """

    import psycopg2

    def __init__(self, config, logger):
        """
        Set any psql specific stuff and bail to parent class
        """

        required_opts = ['db_type', 'db_host', 'db_port', 'db_name', 'db_user']
        DBManager.__init__(self, config, required_opts, logger)

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
    
    def get_sql_cmds(self, list_of_cmds):
        """
        return dict() of PostgreSQL specific commands
        """

        SQL = DBManager.get_sql_cmds(list_of_cmds)

        # Provide any PostgreSQL specific command overrides here
        # SQL['foo'] = 'SELECT * FROM bar'

        SQL['start_job']   = 'UPDATE job_queue SET date_started  = NOW() WHERE job_id = ?'
        SQL['finish_job']  = 'UPDATE job_queue SET date_finished = NOW() WHERE job_id = ?'
        SQL['archive_job'] = 'INSERT INTO job_history VALUES (SELECT *, ? FROM job_queue WHERE job_id = ?'

        return { i: SQL[i] for i in SQL if i in list_of_cmds }


#
#
#
class SQLite3_DBManager(DBManager):
    """
    SQLite3 overload
    """

    def __init__(self, config, logger):
        """
        Set any Sqlite3 specific stuff and bail to parent class
        """

        required_opts = ['db_type', 'db_name', 'db_file']
        DBManager.__init__(self, config, required_opts, logger)


    def get_cursor(self):
        """
        Connect to DB and return cursor
        """

        import sqlite3
        conn = sqlite3.connect(self.db_file)
        conn.isolation_level = None
        return conn.cursor()

    def get_sql_cmds(self, list_of_cmds):
        """
        Return dict() of SQLite3 specific commands
        """

        SQL = DBManager.get_sql_cmds(list_of_cmds)

        # Provide any specific overrides below for SQLite3
        # SQL['foo'] = 'SELECT * FROM bar'

        SQL['start_job']   = 'UPDATE job_queue SET date_started  = DATETIME(\'NOW\') WHERE job_id = ?'
        SQL['finish_job']  = 'UPDATE job_queue SET date_finished = DATETIME(\'NOW\') WHERE job_id = ?'
        SQL['archive_job'] = 'INSERT INTO job_history SELECT *, ? FROM job_queue WHERE job_id = ?'

        return { i: SQL[i] for i in SQL if i in list_of_cmds }


#
#
#
if __name__ == '__main__':

    # Testing
    import os
    from logger import Logger

    log_file = '/tmp/db_test.log'

    if os.path.exists(log_file):
        os.remove(log_file)

    logger = Logger('db_test', log_file).get_logger()

    db_file = '/home/michael/Development/code/jobqueue_manager/manager.db'
    db_manager = SQLite3_DBManager(
            {
                'db_type': 'sqlite3'
                , 'db_name': 'jobmanager'
                , 'db_file': db_file
                }
            , logger)

    db_schema = '/home/michael/Development/code/jobqueue_manager/schema.sqlite3.sql'
    os.system('cat ' + db_schema + ' | sqlite3 ' + db_file)
    print("DEBUG: Reset DB Schema to " + db_schema)

    logger.debug('Opened connection')
    c = db_manager.get_cursor()

    if c:
        SQL = db_manager.get_sql_cmds(['all_jobs'])
        c.execute(SQL['all_jobs'])
        for i,job in enumerate(c.fetchall()):
            print("Job {0}: {1}".format(i,job))
    else:
        print("ERROR: Unable to open cursor")
