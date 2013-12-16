#
#
#
class JobManager():
    """
    Used to manage jobs and extract info from the JobManager database

    """

    def __init__(self, db_manager, logger):
        """
        Sets up the DB and the logger
        """

        self._required_sql = [ 'all_jobs', 'next_job', 'get_job', 'start_job', 'finish_job' ]

        self.logger = logger

        self.db = db_manager.get_cursor()
        self.SQL = db_manager.get_sql_cmds(self._required_sql) # Get implementation specific SQL

        for opt in self._required_sql:
            if opt not in self.SQL:
                self.logger.error('You are missing the following SQL command: {0}'.format(opt))


    def is_alive(self):
        """
        Tells the daemon to keep going or not
        """

        # For the time being, we will leave this as 'always on'
        return True


    def get_job(self, job_id):
        """
        Returns the details of the given job_id
        """

        self.db.execute(self.SQL['get_job'].format(job_id))
        return self.db.fetchone()


    def get_next_job(self):
        """
        Returns the next job in the queue
        """

        self.db.execute(self.SQL['next_job'])
        return self.db.fetchone()


    def report_start(self, job_id):
        """
        Reports back that we have started the given job_id
        """

        pass


    def report_complete(self, job_id):
        """
        Reports back that we have finished the given job_id
        """

        pass


    def report_failed(self, job_id):
        """
        Reports back that we have failed the given job_id
        """

        pass


#
#
#
if __name__ == '__main__':

    # Testing
    import os
    from logger import Logger
    from db import SQLite3_DBManager 

    log_file = '/tmp/jobs_test.log'

    if os.path.exists(log_file):
        os.remove(log_file)

    logger = Logger('jobs_test', log_file).get_logger()

    db_manager = SQLite3_DBManager(
            {
                'db_type': 'sqlite3'
                , 'db_name': 'jobmanager'
                , 'db_file': '/home/michael/Development/code/jobqueue_manager/manager.db'
                }
            , logger)

    job_manager = JobManager( db_manager, logger )

    if job_manager.is_alive():
        print(job_manager.get_next_job())
