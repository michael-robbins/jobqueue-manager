import os
import sys
import subprocess


#
#
#
class SyncManager():
    """
    Handles pushing media files around the various clients
    """
    
    HOST_ADDRESS = 'address'
    HOST_PORT    = 'port'
    HOST_FILE    = 'file'

    #
    #
    #
    def __init__(self, db_manager, logger):
        """
        Setup the DB interactions and logger
        """

        self.logger     = logger
        self.db_manager = db_manager

        self._required_sql = [
                'get_file'
                , 'get_package_parent'
                , 'get_package_children'
                , 'get_package_files'
                , 'get_client_packages'
                , 'get_package_folder'
            ]

        self.SQL = self.db_manager.get_sql_cmds(self._required_sql)



    #
    #
    #
    def get_file(self, client_id, file_id, cursor=None):
        """
        Returns a media_file dict[]
            'package_id' = ID of the media package the file belongs to
            'path' = Fully qualified media file path specific to the client
            'hash' = The hash of the file (should not be different across clients)
            
        As the path could be nested we need to loop through the nesting 
            to discover the fully qualified path
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        # Return a 'media_file' object that contains
        media_file = dict()
        
        (base_path, package_id, rel_path, file_hash) \
                = cursor.execute(self.SQL['get_file'], (client_id, file_id)).fetchone()

        def get_parent_path(package_id):
            """
            Recursively returns the packages folder_name
            for as many parent/child relationships the package_id has
            """
            # Get the folder_name of the current package
            # Get parent_id of current package_id
            # If no parent_id: return folder_name
            # If parent_id: return get_parent_path(parent_id) + '/' + folder_name

            folder_name = cursor.execute(self.SQL['get_package_folder'], str(package_id)).fetchone()
            parent_id   = cursor.execute(self.SQL['get_package_parent'], str(package_id)).fetchone()

            if parent_id:
                return folder_name[0] + get_parent_path(parent_id[0])
            else:
                return folder_name[0]

        media_file['package_id'] = package_id
        media_file['path'] = base_path + get_parent_path(package_id) + rel_path
        media_file['hash'] = file_hash

        return media_file


    #
    #
    #
    def ssh_command(self, dst_details, cmd):
        """
        Executes an SSH command to the remote host and returns the SSH output
        """
        command = [ 'ssh' ]

        if self.HOST_ADDRESS not in dst_details or self.HOST_PORT not in dst_details:
            self.logger.error("Missing address and/or port in dst_details")
            return False

        if self.HOST_PORT in dst_details:
            command.append('-p {0}'.format(dst_details[self.HOST_PORT]))

        command.append(dst_details[self.HOST_ADDRESS])
        command.extend(cmd)

        sshProcess = subprocess.check_output(command)

        return True


    #
    #
    #
    def rsync_file(self, src_details, dst_details):
        """
        Supports sending a file from a [local|remote] host
        to its opposite [remote|local] destination
        """

        command = ['rsync', '-v', '--progress', '--verbose', '--compress']

        if ('address' in src_details or 'port' in src_details) \
                and ('address' in dst_details or 'port' in dst_details):
            self.logger.error("Cannot have both as remote hosts")
            return False

        if self.HOST_PORT in src_details:
            command.append("--rsh='ssh -p{0}'".format(src_details[port]))
        elif self.HOST_PORT in dst_details:
            command.append("--rsh='ssh -p{0}'".format(dst_details[port]))
        else:
            self.logger.warn("Assuming port of 22 for rsync call")

        if self.HOST_ADDRESS in src_details:
            command.append("\"{0}:{1}\"".format(src_details[address], src_details[file]))
        else:
            command.append("\"{0}\"".format(src_details[file]))

        if self.HOST_ADDRESS in dst_details:
            command.append("\"{0}:{1}\"".format(dst_details[address], dst_details[file]))
        else:
            command.append("\"{0}\"".format(dst_details[file]))

        rsyncProcess = subprocess.check_output(command)

        self.logger.debug("RSYNC COMMAND: {0}".format(" ".join(command)))
        self.logger.debug(rsyncProcess)
        return True


    #
    #
    #
    def handle_package(self, package_id, src_client_id, dst_client_id, action_id):
        """
        Transfers a package between clients (or deletes/etc depending on action_id)
        1. bad_src_files = verify_package(package_id, src_client_id)
            1.1. Return False if bad_src_files
        2. bad_dst_files = verify_package(package_id, dst_client_id)
        3. for file_id in ( bad_dst_files || get_package_files(package_id) )
            3.1. if action == 'SYNC':
                3.1.1. result = transfer_file(file_id, src_client_id, dst_client_id, action_id)
            3.2. if action == 'DEL':
                3.2.1. result = delete_file(file_id, dst_client_id)
                3.2.2. if not result: bad_files.append(file_id)
            3.3. else (Unknown action, bail out here?)
        4. If bad_files: return bad_files
        5. if action == 'SYNC':
            5.1. return verify_package(package_id, dst_client_id)
        6. if action == 'DEL':
            6.1. return not verify_package(package_id, dst_client_id)
        """
        pass


    #
    #
    #
    def transfer_file(self, file_id, src_client_id, dst_client_id):
        """
        Takes a file and performs an action on it (after verifying action needs to be taken)
        1. Sync file_id between source and destination
            Find out:
                - Full source path:      create_client_file_path(file_id, src_client_id)
                - Full destination path: create_client_file_path(file_id, dst_client_id)
                - Address details of source (hostname & port)
                - Address details of destination (hostname & port)
        2. return verify_file(file_id, dst_client_id)
        """
        pass


    #
    #
    #
    def delete_file(self, file_id, client_id):
        """
        Deletes a file off the client
        1. if verify_file(file_id, client_id)
            1.1. '/'.join([DST_CLIENT_PATH]
            1.2. Shell out to ssh call to delete remote file
        2. return not verify_file(file_id, dst_client_id)
        """
        pass


    #
    #
    #
    def verify_package(self, package_id, client_id):
        """
        Takes a single package and ensures it exists on the client
        1. for file_id in get_package_files(package_id)
            1.1. verify_file(file_id, client_id)
        2. If verify_file returned False add to bad_files set

        Returns: bad_files set
        """
        pass


    #
    #
    #
    def verify_file(self, file_id, client_id):
        """
        1. file = get_file(client_id, file_id)
        2. Perform remote file existence check
        3. Perform remote hash of file
        4. Return False on missing or hash check fail
        """

        cursor = self.db_manager.get_cursor()

        package_file = get_file(client_id, file_id)
        return True


if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_SyncManager()
    pass
