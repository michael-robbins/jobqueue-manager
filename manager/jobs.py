class JobManager():
    """
    Used to manage jobs and extract info from the JobManager database
    """
    SQL                 = {}
    SQL['all_jobs']     = 'SELECT * FROM job_queue'
    SQL['next_job']     = 'SELECT * FROM get_next_job()'
    SQL['next_job']     = 'SELECT * FROM job_queue WHERE date_started IS NULL ' + \
                            'and date_completed IS NULL ORDER BY date_queued asc LIMIT 1'
    SQL['get_job']      = 'SELECT * FROM job_queue WHERE job_id = {0}'
    SQL['start_job']    = 'UPDATE job_queue SET date_started = NOW() WHERE job_id = {0}'
    SQL['finish_job']   = 'UPDATE job_queue SET date_completed = NOW() WHERE job_id = {0}'

    def __init__(self, db, logger):
        """
        Sets up the DB and the logger
        """
        self.db = db
        self.logger = logger

        self.logger.debug('Entered Job Manager')

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

if __name__ == '__main__':
    db_options['host'] = 'titan'
    db_options['name'] = 'jobqueue_manager'
    db_options['port'] = '5432'
    db_options['user'] = 'michael'
    db_options['pass'] = ''

    import logging

    logger = logging.getLogger('JobManager')
    logger.setLevel(logging.DEBUG)
    
    fh = logging.FileHandler(fh = logging.FileHandler(log_destination))
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('timestamp="%(asctime)s" name="%(name)s" level="%(levelname)s" message="%(message)s"')
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    job_manager = JobManager(db_options, logger)