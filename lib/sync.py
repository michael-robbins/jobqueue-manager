import os
import sys
import shlex
import subprocess


#
#
#
class SyncManager():
    """
    Handles pushing media files around the various clients
    """
    
    HOST_USER    = 'user'
    HOST_ADDRESS = 'address'
    HOST_PORT    = 'port'
    HOST_FILE    = 'file'

    SSH_WORKED   = 'ssh_worked'
    SSH_FAILED   = 'ssh_failed'

    RSYNC_WORKED = 'rsync_worked'
    RSYNC_FAILED = 'rsync_failed'

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
                , 'get_client_sync'
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
        
        (       media_file[self.HOST_ADDRESS] \
                , media_file[self.HOST_PORT]  \
                , base_path                   \
                , media_file['package_id']    \
                , rel_path                    \
                , media_file['hash']          \
        ) = cursor.execute(self.SQL['get_file'], (client_id, file_id)).fetchone()

        def get_parent_path(package_id):
            """
            Recursively returns the packages folder_name
            for as many parent/child relationships the package_id has
            """
            folder_name = cursor.execute(self.SQL['get_package_folder'], package_id).fetchone()
            parent_id   = cursor.execute(self.SQL['get_package_parent'], package_id).fetchone()

            if parent_id:
                return folder_name[0] + get_parent_path(parent_id[0])
            else:
                return folder_name[0]


        media_file[self.HOST_FILE] = base_path + get_parent_path(str(media_file['package_id']))  \
                                                        + rel_path

        return media_file


    #
    #
    #
    def ssh_command(self, dst_details, cmd):
        """
        Executes an SSH command to the remote host and returns the SSH output
        Assumes SSH Keys are setup and password-less auth works
        """
        command = [ 'ssh' ]

        if not hasattr(cmd, '__iter__'):
            self.logger.error("Command given must be in a list (iterable), not a string")
            return self.SSH_FAILED

        if self.HOST_ADDRESS not in dst_details:
            self.logger.error("Missing address in dst_details")
            return self.SSH_FAILED

        if self.HOST_PORT in dst_details:
            command.append('-p {0}'.format(dst_details[self.HOST_PORT]))

        if self.HOST_USER in dst_details:
            command.append(dst_details[self.HOST_USER] + '@' + dst_details[self.HOST_ADDRESS])
        else:
            command.append(dst_details[self.HOST_ADDRESS])

        command.extend(cmd)

        self.logger.debug("SSH COMMAND: {0}".format(" ".join(command)))
        sshProcess = subprocess.check_output(
                command
                , stderr=subprocess.PIPE
                , universal_newlines=True
            )

        return sshProcess


    #
    #
    #
    def rsync_file(self, src_details, dst_details):
        """
        Supports sending a file from a [local|remote] host
        to its opposite [remote|local] destination
        """

        command = ['rsync', '-v', '--progress', '--verbose', '--compress']

        def is_remote_location(details):
            if self.HOST_ADDRESS in details:
                return True
            elif self.HOST_PORT in details:
                return True
            else:
                return False

        if is_remote_location(src_details) and is_remote_location(dst_details):
            self.logger.error("Cannot have both as remote hosts")
            return None

        if (self.HOST_ADDRESS in src_details and self.HOST_USER not in src_details) \
                or (self.HOST_ADDRESS in dst_details and self.HOST_USER not in dst_details):
            self.logger.warn("rsync user defaulting to the user it was run as")

        if self.HOST_PORT in src_details:
            command.extend(shlex.split("--rsh='ssh -p {0}'".format(src_details[self.HOST_PORT])))
        elif self.HOST_PORT in dst_details:
            command.extend(shlex.split("--rsh='ssh -p {0}'".format(dst_details[self.HOST_PORT])))
        else:
            self.logger.warn("Assuming port of 22 for rsync call")

        # We now have the base part of the command done
        # we process the source and then destination parts
        
        def build_rsync_location(details):
            part = ''
            remote = False

            if self.HOST_USER in details:
                remote = True
                part += details[self.HOST_USER] + '@'

            if self.HOST_ADDRESS in details:
                remote = True
                part += details[self.HOST_ADDRESS] + ':'

            part += details[self.HOST_FILE]

            return part


        for i in [src_details, dst_details]:
            command.append(build_rsync_location(i))

        self.logger.debug("RSYNC COMMAND: {0}".format(" ".join(command)))
        rsyncProcess = subprocess.check_output(
                command
                , stderr=subprocess.PIPE
            )

        return rsyncProcess


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
        Takes a file and rsyncs from src->dst (after verifying action needs to be taken)
        """

        src_file = get_file(src_client_id, file_id)
        dst_file = get_file(dst_client_id, file_id)

        if verify_file(dst_file):
            return True

        result = rsync_file(src_file, dst_file)

        if verify_file(dst_file):
            return True
        else:
            self.logger.error('Failed to transfer file {0} from {1} to {2}'.format(
                                file_id, src_client_id, dst_client_id))
            return False

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

        src_file = get_file(client_id, file_id)

        attempts = 0
        while verify_file(src_file):
            if attempts > 5:
                self.logger("Unable to delete file, please investigate")
                return False
            ssh_command(src_file, ['rm', src_file[self.HOST_FILE]])
            attempts += 1

        return True


    #
    #
    #
    def verify_package(self, package_id, client_id, cursor=None):
        """
        Takes a single package and ensures it exists on the client
        1. for file_id in get_package_files(package_id)
            1.1. verify_file(file_id, client_id)
        2. If verify_file returned False add to bad_files set

        Returns: bad_files set
        """
        bad_files = []

        for file_id in cursor.execute(self.SQL['get_package_files'], package_id).fetchall()
            file_id = file_id[0]

            src_file = get_file(client_id, file_id)

            if not verify_file(src_file):
                bad_files.append(file_id)

        return bad_files


    #
    #
    #
    def verify_file(self, file_id, client_id, cursor=None):
        """
        1. file = get_file(client_id, file_id)
        2. Perform remote file existence check
        3. Perform remote hash of file
        4. Return False on missing or hash check fail
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        package_file = get_file(client_id, file_id)
        return True


if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_SyncManager()
    pass
