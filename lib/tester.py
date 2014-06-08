import os, sys

class TestManager():
    """
    My dodgy method of testing before I integrate Unit Tests :)
    """

    db_file     = '/home/michael/Development/Projects/jobqueue_manager/manager.db'
    db_schema   = '/home/michael/Development/Projects/jobqueue_manager/schema.sqlite3.sql'
    log_file    = '/tmp/{0}.log'

    config_file = '/home/michael/Development/Projects/jobqueue_manager/test.conf'
    db_extra    = '/home/michael/Development/Projects/jobqueue_manager/test.sqlite3.sql'

    def get_test_logger(self, log_name):
        """
        Returnsa test logger
        """
        from logger import Logger

        log_file = '/tmp/{0}.log'.format(log_name)

        if os.path.exists(log_file):
            os.remove(log_file)

        return Logger(log_name, log_file).get_logger()

    def reset_db_schema(self, db_schema, db_extra, logger=None):
        """
        Resets the SQLite3 DB back to default
        """

        os.system('cat ' + db_schema + ' | sqlite3 ' + self.db_file) # Schema file
        os.system('cat ' + db_extra  + ' | sqlite3 ' + self.db_file) # Test data

        if logger:
            logger.debug('Reset DB Schema to ' + self.db_schema)

    def createTestFile(self, client, package_file, file_contents, logger=None):
        """
        Creates a file on the specified client
        """
        full_path = client.base_path + package_file.relative_path

        try:
            with open(full_path, 'w') as f:
                f.write(file_contents)
        except IOError:
            if logger:
                logger.error('Unable to write test file: {0}'.format(file_name))
            return False
        return True

    def deleteTestFileLocal(local_file):
        os.remove(local_file)

    def deleteTestFileRemote(sync_manager, client, package_file, logger):
        logger.info('About to verify remote file')
        if sync_manager.verifyFile(client, package_file) \
                != sync_manager.VERIFICATION_FULL:
            logger.error('Remote file verification failed')
        else:
            logger.info('Remote file verification worked')

        if sync_manager.delete_file(client, package_file) \
                != sync_manager.PACKAGE_ACTION_WORKED:
            logger.error('Unable to delete remote file: {0}'.format(package_file))
        else:
            logger.info('Deleted remote file: {0}'.format(package_file))
        
        if sync_manager.verifyFile(dst_client, package_file) \
                != sync_manager.VERIFICATION_NONE:
            logger.error('File still exists, remote rm did not work')
        else:
            logger.info("File doesn't exist, all good")

    def dump_log(self, log_file):
        """
        Dumps the test log file
        """
        with open(log_file, 'r') as f:
            print(f.read())

    def test_Logger(self):
        """
        Tests out the Logger (yo dawg, I heard you like loggers)
        """
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

    def test_ConfigManager(self):
        """
        Test the Config Manager
        """
        # Setup
        test_name = 'manager_ConfigManager'
        logger = self.get_test_logger(test_name)

        from config import ConfigManager
        config_manager = ConfigManager(self.config_file)

        # Testing
        config = config_manager.get_config()
        
        required_sections = [ 'DAEMON', 'DB' ]
        for section in required_sections:
            assert getattr(config, section)
            logger.info('Found section {0}'.format(section))
        
        logger.info(dir(config))

        # Print Results
        self.dump_log(self.log_file.format(test_name))

    def test_JobQueueManager(self):
        """
        Test the Job Queue Manager
        """
        # Setup
        test_name = 'manager_JobQueueManager'
        logger = self.get_test_logger(test_name)

        from manager import JobQueueManager
        jqm = JobQueueManager(self.config_file, False, False)

        # Testing
        jqm.start(oneshot=True)

        # Print Results
        self.dump_log(self.log_file.format(test_name))

    def test_FilePackageManager(self):
        """
        Test the File Package Manager
        """
        # Setup
        test_name = 'manager_FilePackageManager'
        logger = self.get_test_logger(test_name)

        from config import ConfigManager
        config = ConfigManager(self.config_file).get_config()

        from db import SQLite3_DBManager
        db_manager = SQLite3_DBManager(config.DB, logger)

        self.reset_db_schema(self.db_schema, self.db_extra, logger)

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

    def test_SyncManager(self):
        """
        Test the Sync Manager
        """
        # Setup
        test_name = 'manager_SyncManager'
        logger = self.get_test_logger(test_name)
        
        import subprocess

        from config import ConfigManager
        config = ConfigManager(self.config_file).get_config()

        from db import SQLite3_DBManager
        db_manager = SQLite3_DBManager(config.DB, logger)

        self.reset_db_schema(self.db_schema, self.db_extra, logger)
        
        from client import ClientManager
        client_manager = ClientManager(db_manager, logger)

        src_client_id = 3
        dst_client_id = 4

        src_client = client_manager.getClient(src_client_id, db_manager.get_cursor())
        dst_client = client_manager.getClient(dst_client_id, db_manager.get_cursor())

        from filepackage import FilePackageManager
        filepackage_manager = FilePackageManager(db_manager, logger)
        
        package_id = 1

        file_package = filepackage_manager.getFilePackage(package_id, db_manager.get_cursor())

        from sync import SyncManager
        sync_manager = SyncManager(db_manager, logger)

        # Testing
        # Test a local SSH command
        try:
            logger.info('Attempting local SSH call')
            sshOutput = sync_manager.sshCommand(src_client, ['ls']).rstrip()
            logger.info(sshOutput.replace('\n',' '))
        except subprocess.CalledProcessError:
            logger.error('Unable to perform local ls')

        # Test a remote SSH command
        try:
            logger.info('Attempting remote SSH call')
            sshOutput = sync_manager.sshCommand(dst_client, ['ls']).rstrip()
            logger.info(sshOutput.replace('\n',' '))
        except subprocess.CalledProcessError:
            logger.error('Unable to perform remote ls')

        # Create an empty file and add the test file
        package_file = filepackage_manager.getEmptyFile()
        package_file.relative_path = 'test.txt'

        local_file_name    = src_client.base_path + package_file.relative_path
        remote_file_name   = dst_client.base_path + package_file.relative_path

        if not self.createTestFile(src_client, package_file, 'test\n', logger):
            logger.error('Failed to create the test file')
            self.dump_log(self.log_file.format(test_name))
            return False
        else:
            logger.info('Created test file: ' + local_file_name)

        # Get the hash of the temporary file
        test_hash = subprocess.check_output(['sha256sum', local_file_name], universal_newlines=True)
        package_file.file_hash = test_hash.split(' ')[0]
        logger.info('Created local hash of: {0}'.format(package_file.file_hash))

        logger.info('About to locally verify file')
        if sync_manager.verifyFile(src_client, package_file) \
                != sync_manager.VERIFICATION_FULL:
            logger.error('Unable to locally verify file')

        # Test transferring the file
        logger.info('About to transfer file')
        if sync_manager.transfer_file(src_client, dst_client, package_file) \
                != sync_manager.PACKAGE_ACTION_WORKED:
            logger.error('Unable to rsync file to remote host')
        else:
            logger.info('Sync worked?')
        logger.info('Double Check: ' + sync_manager.sshCommand(dst_client, ['ls', '/tmp/']).replace('\n',' '))


        # Test fileDiscovery
        # 1. Update the test schema with new file package
        # 2. Create the test file packague
        # 3. Test a verify over it

        # Print Results
        self.dump_log(self.log_file.format(test_name))

if __name__ == '__main__':
    """
    Run through all test_*'s we have created
    """

    tester = TestManager()

    # Run through the test cases we have so far
    tester.test_Logger()
    tester.test_ConfigManager()
    tester.test_DBManager()
    tester.test_JobManager()
    tester.test_JobQueueManager()
    tester.test_ClientManager()
    tester.test_FilePackageManager()
    tester.test_SyncManager()
