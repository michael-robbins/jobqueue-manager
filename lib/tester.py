

class TestManager():
    """
    My dodgy method of testing before I integrate Unit Tests :)
    """

    config_file = '/home/michael/Development/Projects/jobqueue_manager/test.conf'
    db_file     = '/home/michael/Development/Projects/jobqueue_manager/manager.db'
    db_schema   = '/home/michael/Development/Projects/jobqueue_manager/schema.sqlite3.sql'
    log_file    = '/tmp/{0}.log'


    def get_test_logger(self, log_name):
        import os
        from logger import Logger

        log_file = '/tmp/{0}.log'.format(log_name)

        if os.path.exists(log_file):
            os.remove(log_file)

        return Logger(log_name, log_file).get_logger()


    def reset_db_schema(self, db_schema, logger=None):
        import os
        os.system('cat ' + db_schema + ' | sqlite3 ' + self.db_file)

        if logger:
            logger.debug('Reset DB Schema to ' + self.db_schema)


    def dump_log(self, log_file):
        with open(log_file, 'r') as f:
            print(f.read())


    def test_Logger(self):
        # Setup
        test_name = 'manager_Logger'
        logger = self.get_test_logger(test_name)

        # Testing
        logger.error('ERROR')
        logger.warning('WARNING')
        logger.info('INFO')
        logger.debug('DEBUG')

        try:
            logger.zomg('ZOMG')
            raise Exception("logger.zomg should not exist")
        except Exception:
            pass

        # Print Results
        self.dump_log(self.log_file.format(test_name))


    def test_DBManager(self):
        # Setup
        test_name = 'manager_DBManager'
        logger = self.get_test_logger(test_name)

        from config import ConfigManager
        config = ConfigManager(self.config_file).get_config()

        from db import SQLite3_DBManager
        db_manager = SQLite3_DBManager(config['MANAGER'], logger)

        self.reset_db_schema(self.db_schema, logger)

        # Testing
        logger.debug('Opened connection and reset schema')
        cursor = db_manager.get_cursor()

        if cursor:
            SQL = db_manager.get_sql_cmds(['all_jobs'])
            cursor.execute(SQL['all_jobs'])
            for i,job in enumerate(cursor.fetchall()):
                logger.info("Job {0}: {1}".format(i,job))
        else:
            logger.error("Unable to open cursor")

        # Print Results
        self.dump_log(self.log_file.format(test_name))


    def test_JobManager(self):
        # Setup
        test_name = 'manager_JobManager'
        logger = self.get_test_logger(test_name)

        from config import ConfigManager
        config = ConfigManager(self.config_file).get_config()

        from db import SQLite3_DBManager
        db_manager = SQLite3_DBManager(config['MANAGER'], logger)

        self.reset_db_schema(self.db_schema, logger)

        from jobs import JobManager
        job_manager = JobManager(db_manager, logger)

        # Testing
        if job_manager.is_alive():
            job = job_manager.get_next_job()

            if job:
                logger.info('Before:'    + str(job))
                job.report_started()
                logger.info('Started: '  + str(job))
                job.report_complete()
                logger.info('Complete: ' + str(job))

            job = job_manager.get_next_job()

            if job:
                logger.info('Next: ' + str(job))
            else:
                logger.info('No more jobs!')

        # Print Results
        self.dump_log(self.log_file.format(test_name))


    def test_JobQueueManager(self):
        # Setup
        test_name = 'manager_JobQueueManager'
        logger = self.get_test_logger(test_name)

        from manager import JobQueueManager
        jqm = JobQueueManager(self.config_file, False, False)

        # Testing
        jqm.start(oneshot=True)

        # Print Results
        self.dump_log(self.log_file.format(test_name))


    def test_SyncManager(self):
        # Setup
        test_name = 'manager_SyncManager'
        logger = self.get_test_logger(test_name)

        from config import ConfigManager
        config = ConfigManager(self.config_file).get_config()

        from db import SQLite3_DBManager
        db_manager = SQLite3_DBManager(config['MANAGER'], logger)

        self.reset_db_schema(self.db_schema, logger)

        from sync import SyncManager
        sm = SyncManager(db_manager, logger)

        package_id = 1
        client_id  = 1

        # Test an SSH command
        client_details = dict()
        client_details['address'] = 'olympus.dalmura.com.au'
        client_details['port'] = '9999'
        client_details['user'] = 'michael'

        sshoutput = sm.ssh_command(client_details, ['ls', '-l']).rstrip()
        logger.info(sshoutput)

        # Generate our temporary file
        import os
        import subprocess
        test_file = '/tmp/test.txt'
        try:
            with open(test_file, 'w') as f:
                f.write('test\n')
        except IOError:
            logger.error('Unable to write test file')

        # Get it's hash
        test_hash = subprocess.check_output(['sha256sum', test_file], universal_newlines=True)
        test_hash = test_hash.split(' ')[0]

        # Test the rsync command
        dst_details = dict()
        dst_details['address'] = 'olympus.dalmura.com.au'
        dst_details['port'] = '9999'
        dst_details['user'] = 'michael'
        dst_details['file'] = test_file
        dst_details['hash'] = test_hash

        src_details = dict()
        src_details['file'] = test_file

        rsyncOutput = sm.rsync_file(src_details, dst_details)
        logger.info(rsyncOutput)

        try:
            sshOutput = sm.ssh_command(dst_details, ['ls', '-l', test_file]).rstrip()
            logger.info(sshOutput)
        except subprocess.CalledProcessError:
            logger.error('remote rsyncd file does not exist')

        # Remotely verify the file
        if sm.verify_file(dst_details):
            logger.info('Remote file verification worked')
        else:
            logger.error('Remote file verification failed')

        # Remove the temp remote file
        os.remove(test_file)
        sshOutput = sm.ssh_command(dst_details, ['rm', test_file])
        logger.info(sshOutput)
        
        file_exists = True
        try:
            sshOutput = sm.ssh_command(dst_details, ['ls', '-l', test_file])
            logger.info(sshOutput)
        except subprocess.CalledProcessError:
            file_exists = False

        if file_exists:
            logger.error('File still exists, remote rm did not work')

        # Test 
        # Print Results
        self.dump_log(self.log_file.format(test_name))


    def test_ClientManager(self):
        # Setup
        test_name = 'manager_ClientManager'
        logger = self.get_test_logger(test_name)

        from config import ConfigManager
        config = ConfigManager(self.config_file).get_config()

        from db import SQLite3_DBManager
        db_manager = SQLite3_DBManager(config['MANAGER'], logger)

        self.reset_db_schema(self.db_schema, logger)

        from client import ClientManager
        client_manager = ClientManager(db_manager, logger)

        # Testing
        client_id = 1
        client = client_manager.getClient(client_id, db_manager.get_cursor())

        if not client:
            logger.info('Error obtaining client')

        attributes = [ 'sync_hostname', 'sync_port', 'sync_user', 'base_path' ]
        answers    = [ 'atlas', '22', 'test', '/data/media/' ]

        for attribute, answer in zip(attributes, answers):
            logger.info("{0}='{1}'".format(attribute,getattr(client, attribute)))
            assert str(getattr(client, attribute)) == answer

        # Print Results
        self.dump_log(self.log_file.format(test_name))


    def test_FilePackageManager(self):
        # Setup
        test_name = 'manager_FilePackageManager'
        logger = self.get_test_logger(test_name)

        from config import ConfigManager
        config = ConfigManager(self.config_file).get_config()

        from db import SQLite3_DBManager
        db_manager = SQLite3_DBManager(config['MANAGER'], logger)

        self.reset_db_schema(self.db_schema, logger)

        from filepackage import FilePackageManager
        filepackage_manager = FilePackageManager(db_manager, logger)

        # Testing
        package_id = 1
        test_package = filepackage_manager.getFilePackage(package_id, db_manager.get_cursor())

        if not test_package:
            logger.error('Unable to generate FilePackage object')

        attributes = [ 'package_id', 'name', 'folder_name', 'package_type_name' ]
        answers    = [ 
                        str(package_id)
                        , 'Movie 1'
                        , 'Movie 1 (2009)/'
                        , 'Movie'
                     ]


        # Check the package is fine
        for attribute, answer in zip(attributes, answers):
            logger.info("{0}='{1}'".format(attribute,getattr(test_package, attribute)))
            assert str(getattr(test_package, attribute)) == answer

        # Assert the package has a file_list
        assert getattr(test_package, 'file_list')

        file_attributes = [ 'file_id', 'package_id', 'relative_path', 'file_hash' ]

        # Loop through the file list asserting all files have all their required attributes
        for test_file in test_package.file_list:
            for attribute in file_attributes:
                logger.info("{0}='{1}'".format(attribute,getattr(test_file, attribute)))
                assert getattr(test_file, attribute)

        # Print Results
        self.dump_log(self.log_file.format(test_name))


if __name__ == '__main__':
    """
    Run through all test_*'s we have created
    """

    tester = TestManager()

    # Run through the test cases we have so far
    tester.test_Logger()
    tester.test_DBManager()
    tester.test_JobManager()
    tester.test_JobQueueManager()
    #tester.test_SyncManager() # Removed until I figure this out
    tester.test_ClientManager()
    tester.test_FilePackageManager()
