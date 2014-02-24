import os
import sys


#
#
#
class FilePackageManager():
        """
        Handles the actual file and file package objects
        Can add files and file packages into the DB
        """

        class File(object):
            """
            A file object, contains the following attributes
            * file_id
            * package_id
            * rel_path
            * hash
            """
            pass

            def configure_for_client(client_id):
                """
                Configures file object for a specific client
                """
                pass


        class FilePackage(object):
            """
            Package that contains multiplie file objects
            Not sure if I will need this (just make a package a list of file objects?)
            """
            pass

            def configure_for_client(client_id):
                """
                Configures a file package for a specific client
                """
                pass

        def getFile(file_id, client_id=None):
            """
            Returns a file object of the given file_id
            Supports client specific options if client_id is provided
            """
            pass

        def getFilePackage(file_id, client_id=None):
            """
            Returns a file package object (with optional ForClient specialization)
            """
