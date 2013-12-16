#
#
#
class JobManager():
    """
    Used to manage jobs and extract info from the JobManager database

    """

    class Job():

        from sync import SyncManager


        def __init__(self, db_manager, config_tuple):
            """
            Setup the object by setattr'ing the fields into attributes
            Setup the DB side of things
            Setup the SyncManager
            """
            
            self.tuple_mapping = [
                    'job_id'
                    , 'package_id'
                    , 'src_client_id'
                    , 'dst_client_id'
                    , 'action_id'
                    , 'date_queued'
                    , 'date_started'
                    , 'date_finished'
                    , 'outcome'
                ]

            for (i,key) in enumerate(self.tuple_mapping):
                try:
                    setattr(self, key, str(config_tuple[i]))
                except IndexError:
                    setattr(self, key, '')

            self.syncer = self.SyncManager()

            self._required_sql = [ 
                    'get_job'
                    , 'get_archived_job'
                    , 'start_job'
                    , 'finish_job'
                    , 'archive_job'
                    , 'delete_job'
                ]

            self.db_manager = db_manager
            self.db  = db_manager.get_cursor()
            self.SQL = db_manager.get_sql_cmds(self._required_sql) # Get implementation specific SQL

        def __str__(self):
            """
            Return object as a good looking string ;)
            """

            good_looking_attributes = [ 
                    "{0}='{1}'".format(key,getattr(self,key)) for key in self.tuple_mapping
                ]

            return " ".join(good_looking_attributes)

        def reload_job(self, archived=False):
            """
            Reloads the job (get latest datetime fields)
            """

            if archived:
                row = self.db.execute(self.SQL['get_archived_job'], self.job_id).fetchone()
            else:
                row = self.db.execute(self.SQL['get_job'], self.job_id).fetchone()

            self.__init__(self.db_manager, row)

        def get_id(self):
            """
            Get the... id?
            """
            return self.job_id

        def completed(self):
            """
            We save the PID of the process handling the job into the Job table
            * Verify the PID is not running
            * Execute a verify of the dst_client_id, package_id and action_id
                - dst_client_id to know where to check
                - package_id to know what to check
                - action_id to know how to check (package should/shouldn't exist, etc)
            * If verify succeeds we return True else False
            """
            pass

        def execute(self):
            """
            Execute Job:
            * Run SyncManager over the job
            """
            pass
    
        def report_started(self):
            """
            Reports back that we have started the job
            """
            self.db.execute( self.SQL['start_job'], (self.job_id) )
            self.reload_job()

        def report_complete(self):
            """
            Reports back that we have finished the job
            """
            self.db.execute( self.SQL['finish_job'], (self.job_id) )
            self.db.execute( self.SQL['archive_job'], ('Complete', self.job_id) )
            self.db.execute( self.SQL['delete_job'], (self.job_id) )
            self.reload_job(archived=True)

        def report_failed(self):
            """
            Reports back that we have failed the job
            """
            self.db.execute( self.SQL['finish_job'], (self.job_id) )
            self.db.execute( self.SQL['archive_job'], ('Failed', self.job_id) )
            self.db.execute( self.SQL['delete_job'], (self.job_id) )
            self.reload_job(archived=True)


    def __init__(self, db_manager, logger):
        """
        Sets up the DB and the logger
        """

        self._required_sql = [ 'all_jobs', 'next_job', 'get_job' ]

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

    def get_jobs(self):
        """
        Returns a list of all available Jobs
        """

        self.db.execute(self.SQL['all_jobs'])
        return [ self.Job(db_manager, i) for i in self.db.fetchall() if i ]

    def get_job(self, job_id):
        """
        Returns a Job of the given job_id
        """

        self.db.execute(self.SQL['get_job'], job_id )
        row = self.db.fetchone()
        return self.Job(db_manager, row) if row else None

    def get_next_job(self):
        """
        Returns the next Job in the queue
        """

        self.db.execute(self.SQL['next_job'])
        row = self.db.fetchone()
        return self.Job(db_manager, row) if row else None


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

    job_manager = JobManager( db_manager, logger )

    if job_manager.is_alive():
        job = job_manager.get_next_job()

        if job:
            print( "INFO: Before: ", end=''); print( job )

            job.report_started()
            print( "INFO: Started: ", end=''); print( job )

            job.report_complete()
            print( "INFO: Complete: ", end=''); print( job )

        job = job_manager.get_next_job()

        if job:
            print(job)
        else:
            print("INFO: No More Jobs!")
