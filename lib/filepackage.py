import os
import sys


class FilePackageManager():
        """
        Handles the actual file and file package objects
        Can add files and file packages into the DB
        """

        def __init__(self, db_manager, logger):
            """
            Setup the DB interactions and the logger
            We just use the db_manager to get the correct SQL
            The rest will be provided to the child classes as cursors from the calling class
            """

            self.logger = logger

            self._required_sql = [
                    'get_file_for_sync'
                    , 'get_package_for_sync'
                    , 'get_package_parent'
                    , 'get_package_children'
                    , 'get_file_packages'
                    , 'get_package_folder'
                    , 'get_package_files'
                ]

            self.SQL = db_manager.get_sql_cmds(self._required_sql)


        class FilePackage(object):
            """
            Package that contains multiplie file objects (in a basic list)
            Contains the following attributes:
            * name
            * folder_name
            * package_type_name
            * file_list = list() of files

            This class encapsulates the File object
            (as you shouldn't be dealing with File objects directly)
            """

            class File(object):
                """
                A file object, contains the following attributes
                * file_id
                * package_id
                * relative_path
                * file_hash
                """
                
                def __init__(self, file_id, required_sql, cursor):
                    """
                    Takes the file_id and configures the required attributes
                    """

                    self.file_id = file_id
                    self.SQL     = required_sql

                    cursor.execute(self.SQL['get_file_for_sync'], str(file_id))

                    (
                        self.package_id
                        , self.relative_path
                        , self.file_hash
                    ) = cursor.fetchone()

                def __str__(self):
                    """
                    Returns a pretty string representation of the file
                    """
                    return self.relative_path


            def __init__(self, package_id, required_sql, cursor):
                """
                Takes the package_id and configures the correct attributes
                """

                self.package_id = package_id
                self.SQL = required_sql

                cursor.execute(self.SQL['get_package_for_sync'], str(package_id))

                (
                    self.name
                    , self.package_type_name
                ) = cursor.fetchone()

                self.folder_name = self.getParentPath(package_id, cursor)

                self.file_list = []

                cursor.execute(self.SQL['get_package_files'], str(package_id))

                # Double check that passing through the cursor to the File class
                #     doesn't screw up the cursor in this scope
                for file_id in cursor.fetchall():
                    self.file_list.append(self.File(file_id[0], self.SQL, cursor)) # <-- This cursor

            def __str__(self):
                """
                Returns a pretty string representation of the file package
                """
                return self.name


            def getFile(self, file_id, cursor):
                """
                Returns a file object of the given file_id
                """

                request_file = self.File(file_id, self.SQL, cursor)

                if not request_file:
                    self.logger.error('Unable to generate file object for id {0}'.format(file_id))
                    return None

                return request_file


            def getParentPath(self, package_id, cursor):
                """
                Recursively returns the packages folder_name
                for as many parent/child relationships the package_id has
                """
                folder_name = cursor.execute(self.SQL['get_package_folder'], str(package_id)).fetchone()
                parent_id   = cursor.execute(self.SQL['get_package_parent'], str(package_id)).fetchone()

                if parent_id:
                    return folder_name[0] + self.getParentPath(parent_id[0])
                else:
                    return folder_name[0]


        def getFilePackage(self, package_id, cursor):
            """
            Returns a file package object
            """

            request_package = self.FilePackage(package_id, self.SQL, cursor)

            if not request_package:
                self.logger.error('Unable to generate file package for id {0}'.format(package_id))
                return None

            return request_package


if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_FilePackageManager()
