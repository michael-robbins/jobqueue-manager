#
#
#
class JobManager():
    """
    Used to manage jobs and extract info from the JobManager database

    """

    class Job():
        def __init__(self, config_tuple):

            tuple_mapping = ['job_id', 'package_id', 'src_client_id', 'dst_client_id', 'action_id']
            for (i,key) in enumerate(tuple_mapping):
                setattr(self, key, config_tuple[i])

        def getid(self):
            return self.job_id

        def completed(self):
            """
            Place-holder no idea how I'll implement
            """

        def execute(self):
            """
            Place-holder no idea how I'll implement
            """
            pass
    
        def report_start(self):
            """
            Reports back that we have started the job
            """
            pass


        def report_complete(self):
            """
            Reports back that we have finished the job
            """
            pass


        def report_failed(self):
            """
            Reports back that we have failed the job
            """
            pass


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
        return self.Job(self.db.fetchone())


    def get_next_job(self):
        """
        Returns the next job in the queue
        """

        self.db.execute(self.SQL['next_job'])
        return self.Job(self.db.fetchone())




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
        job = job_manager.get_next_job()
        print(job.getid())
