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
            pass


        class FilePackage(object):
            """
            Package that contains multiplie file objects
            Not sure if I will need this (just make a package a list of file objects?)
            """
            pass


        def getFile(self, file_id, client_id=None):
            """
            Returns a file object of the given file_id
            Supports client specific options if client_id is provided
            """

            request = self.File(file_id)

            if client_id:
                self.configre_for_client(
            return self.File()


        def getFilePackage(self, file_id, client_id=None):
            """
            Returns a file package object (with optional ForClient specialization)
            """
            pass


        def configure_for_client(self, client_id, cursor=None):
            """
            Configures file object for a specific client
            """
            pass
