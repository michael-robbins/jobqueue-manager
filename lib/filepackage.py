import os
import sys


class FilePackageManager():
        """
        Handles the actual file and file package objects
        Can add files and file packages into the DB
        """

        HOST_USER    = 'user'
        HOST_ADDRESS = 'address'
        HOST_PORT    = 'port'
        HOST_FILE    = 'file'


        def __init__(self, db_mananger, logger):
            """
            Setup the DB interactions and the logger
            """

            self.logger     = logger
            self.db_manager = db_manager

            self._required_sql = [
                    'get_file'
                    , 'get_package_parent'
                    , 'get_package_children'
                    , 'get_file_packages'
                    , 'get_client_packages'
                    , 'get_package_folder'
                    , 'get_client_sync'
                ]

            self.SQL = self.db_manager.get_sql_cmds(self._required_sql)


        class File(object):
            """
            A file object, contains the following attributes
            * file_id
            * package_id
            * rel_path
            * hash
            """
            
            def __init__(self, file_id, cursor):
                """
                Takes the file_id and configures the required attributes
                """
                pass


        class FilePackage(object):
            """
            Package that contains multiplie file objects (in a basic list)
            Contains the following attributes:
            * name
            * folder_name
            * metadata_json
            * media_package_type
            * file_list = list() of files

            Contains the following client specific attributes:
            * hostname
            * port
            * base_path
            """

            def __init__(self, package_id, cursor):
                """
                Takes the package_id and configures the correct attributes
                1. SELECT * FROM media_packages WHERE package_id = package_id
                2. SELECT file_id FROM media_package_files WHERE package_id = package_id
                3. file_list = list()
                4. FOR file_id in cursor.fetchall():
                    - file_list.append(self.File(file_id, cursor))

                * Add in the media_package_type as well to make it fit into the source path.
                """
                pass


            def configure_for_client(self, client_id, cursor):
                """
                Takes the client_id and configures the client specific attributes
                1. SELECT sync_*, base_path FROM clients WHERE client_id = client_id
                """
                pass


        def getFile(self, file_id):
            """
            Returns a file object of the given file_id
            Supports client specific options if client_id is provided
            """

            cursor = self.db_manager.get_cursor()

            request_file = self.File(file_id, cursor)

            if not request_file:
                self.logger.error('Unable to generate file object for id {0}'.format(file_id))
                return None

            return request_file


        def getFilePackage(self, package_id, client_id=None):
            """
            Returns a file package object (with optional ForClient specialization)
            Supports client specific options if client_id is provided
            Note: Client specific options are applied at a file package level
            """

            cursor = self.db_manager.get_cursor()

            request_package = self.FilePackage(package_id, cursor)

            if not request_package:
                self.logger.error('Unable to generate file package for id {0}'.format(package_id))
                return None

            if client_id:
                request_package.configure_for_client(client_id, cursor)

            return request_file


