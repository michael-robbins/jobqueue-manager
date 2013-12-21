#
#
#
class JobManager():
    """
    Used to manage jobs and extract info from the JobManager database
    """

    #
    #
    #
    class Job():

        from sync import SyncManager

        #
        #
        #
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
                    , 'pid'
                    , 'outcome'
                ]

            if 'outcome' in config_tuple:
                # Only jobs that have finished executing (and have been archived) have an outcome
                self.archived = True
            else:
                self.archived = False


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
            self.SQL = db_manager.get_sql_cmds(self._required_sql) # Get implementation specific SQL


        #
        #
        #
        def __str__(self):
            """
            Return object as a good looking string ;)
            """

            return " ".join(
                    [ "{0}='{1}'".format(key,getattr(self,key)) for key in self.tuple_mapping ]
                )


        #
        #
        #
        def reload_job(self, archived=False):
            """
            Reloads the job (get latest datetime fields)
            """

            cursor = self.db_manager.get_cursor()
            if archived:
                row = cursor.execute(self.SQL['get_archived_job'], self.job_id).fetchone()
            else:
                row = cursor.execute(self.SQL['get_job'], self.job_id).fetchone()

            self.__init__(self.db_manager, row)


        #
        #
        #
        def execute(self):
            """
            Execute Job (this function should be forked correctly from manager):
            * Save the PID of this process
            * Run SyncManager over the job
            * Return what SyncManager reports
            """

            self.report_started() # We do this here as we are within the forked context
            result = self.syncer.handle_package(
                            self.package_id
                            , self.src_client_id
                            , self.dst_client_id
                            , self.action_id
                        )

            if result:
                self.report_complete()
            else:
                self.report_failed()


        #
        #
        #
        def report_started(self):
            """
            Reports back that we have started the job
            """

            import os
            cursor = self.db_manager.get_cursor()
            cursor.execute( self.SQL['start_job'], (os.getpid(), self.job_id) )
            self.reload_job()


        #
        #
        #
        def report_complete(self):
            """
            Reports back that we have finished the job
            """

            cursor = self.db_manager.get_cursor()
            cursor.execute( self.SQL['finish_job'], (self.job_id) )
            cursor.execute( self.SQL['archive_job'], ('Complete', self.job_id) )
            cursor.execute( self.SQL['delete_job'], (self.job_id) )
            self.reload_job(archived=True)


        #
        #
        #
        def report_failed(self):
            """
            Reports back that we have failed the job
            """

            cursor = self.db_manager.get_cursor()
            cursor.execute( self.SQL['finish_job'], (self.job_id) )
            cursor.execute( self.SQL['archive_job'], ('Failed', self.job_id) )
            cursor.execute( self.SQL['delete_job'], (self.job_id) )
            self.reload_job(archived=True)


    #
    #
    #
    def __init__(self, db_manager, logger):
        """
        Sets up the DB and the logger
        """

        self._required_sql = [ 'all_jobs', 'next_job', 'get_job' ]

        self.logger = logger

        self.db_manager = db_manager
        self.SQL = db_manager.get_sql_cmds(self._required_sql) # Get implementation specific SQL

        for opt in self._required_sql:
            if opt not in self.SQL:
                self.logger.error('You are missing the following SQL command: {0}'.format(opt))


    #
    #
    #
    def is_alive(self):
        """
        Tells the daemon to keep going or not
        """

        # For the time being, we will leave this as 'always on'
        return True


    #
    #
    #
    def get_jobs(self):
        """
        Returns a list of all available Jobs
        """

        cursor = self.db_manager.get_cursor()
        cursor.execute(self.SQL['all_jobs'])
        return [ self.Job(self.db_manager, i) for i in cursor.fetchall() if i ]


    #
    #
    #
    def get_job(self, job_id):
        """
        Returns a Job of the given job_id
        """

        cursor = self.db_manager.get_cursor()
        cursor.execute(self.SQL['get_job'], job_id )
        row = cursor.fetchone()
        return self.Job(self.db_manager, row) if row else None


    #
    #
    #
    def get_next_job(self):
        """
        Returns the next Job in the queue
        """

        cursor = self.db_manager.get_cursor()
        cursor.execute(self.SQL['next_job'])
        row = cursor.fetchone()
        return self.Job(self.db_manager, row) if row else None


#
#
#
if __name__ == '__main__':
    """
    Testing if run interactively
    """
    from tester import TestManager
    tester = TestManager()
    tester.test_JobManager()
