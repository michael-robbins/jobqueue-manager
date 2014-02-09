import os
import sys
import shlex
import subprocess


#
#
#
class SyncManager():
    """
    Handles pushing package files around the various clients
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
        Returns a package_file dict[]
            'package_id' = ID of the package the file belongs to
            'path' = Fully qualified package file path specific to the client
            'hash' = The hash of the file (shouldn't be different across clients)
            'port' = Port of the client
            'address' = Address (host or IP) of the client 
            
        As the path could be nested we need to loop through the nesting 
            to discover the fully qualified path of the file at the client specific location
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        package_file = dict()
        
        (
                package_file[self.HOST_ADDRESS]
                , package_file[self.HOST_PORT]
                , base_path
                , package_file['package_id']
                , rel_path
                , package_file['hash']
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


        package_file[self.HOST_FILE] = base_path + get_parent_path(str(package_file['package_id']))  \
                                                        + rel_path

        return package_file


    #
    #
    #
    def ssh_command(self, package_file, cmd):
        """
        Executes an SSH command to the remote host and returns the SSH output
        Assumes SSH Keys are setup and password-less auth works
        """
        command = [ 'ssh' ]

        if not hasattr(cmd, '__iter__'):
            self.logger.error("Command given must be in a list (iterable), not a string")
            return self.SSH_FAILED

        if self.HOST_ADDRESS not in package_file:
            self.logger.error("Missing address in package_file")
            return self.SSH_FAILED

        if self.HOST_PORT in package_file:
            command.append('-p {0}'.format(package_file[self.HOST_PORT]))

        if self.HOST_USER in package_file:
            command.append(package_file[self.HOST_USER] + '@' + package_file[self.HOST_ADDRESS])
        else:
            command.append(package_file[self.HOST_ADDRESS])

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
    def rsync_file(self, src_package_file, dst_package_file):
        """
        Supports sending a file from a [local|remote] host
        to its opposite [remote|local] destination
        """

        command = ['rsync', '-v', '--progress', '--verbose', '--compress']

        def is_remote(package_file):
            """
            Checks to see if the file host is remote (has address or port)
            """
            if self.HOST_ADDRESS in package_file:
                return True
            elif self.HOST_PORT in package_file:
                return True
            else:
                return False

        if is_remote(src_package_file) and is_remote(dst_package_file):
            self.logger.error("Cannot have both as remote hosts")
            return None

        def is_remote_with_user(package_file):
            """
            Extends is_remote with if we have a user or not as well
            """
            if is_remote(package_file) and self.HOST_USER in package_file:
                return True
            else:
                return False

        if is_remote_with_user(src_package_file) or is_remote_with_user(dst_package_file):
            self.logger.warn("rsync user defaulting to the user it was run as")


        if self.HOST_PORT in src_package_file:
            command.extend(shlex.split("--rsh='ssh -p {0}'".format(src_package_file[self.HOST_PORT])))
        elif self.HOST_PORT in dst_package_file:
            command.extend(shlex.split("--rsh='ssh -p {0}'".format(dst_package_file[self.HOST_PORT])))
        else:
            self.logger.warn("Assuming port of 22 for rsync call")

        # We now have the base part of the command done
        # we process the source and then destination parts
        
        def build_rsync_location(package_file):
            location = ''

            if self.HOST_USER in package_file:
                location += package_file[self.HOST_USER] + '@'

            if self.HOST_ADDRESS in package_file:
                location += package_file[self.HOST_ADDRESS] + ':'

            location += package_file[self.HOST_FILE]

            return location


        for package_file in [src_package_file, dst_package_file]:
            command.append(build_rsync_location(package_file))

        self.logger.debug("RSYNC COMMAND: {0}".format(" ".join(command)))
        rsyncProcess = subprocess.check_output(
                command
                , stderr=subprocess.PIPE
                , universal_newlines=True
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

        src_package_file = get_file(src_client_id, file_id)
        dst_package_file = get_file(dst_client_id, file_id)

        if verify_file(dst_package_file):
            return True

        result = rsync_file(src_package_file, dst_package_file)

        if verify_file(dst_package_file):
            return True
        else:
            self.logger.error('Failed to transfer file {0} from {1} to {2}'.format(
                                file_id, src_client_id, dst_client_id))
            return False


    #
    #
    #
    def delete_package(self, package_id, client_id, cursor=None):
        """
        Takes a single package and deletes it off the client
        1. for file_id in get_package_files(package_id)
            1.1. delete_file(file_id, client_id)
        2. If verify_file returned False add to bad_files set

        Returns: bad_files set
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        bad_files = []

        for file_id in cursor.execute(self.SQL['get_package_files'], package_id).fetchall():
            file_id = file_id[0]

            client_package_file = get_file(client_id, file_id)

            if not client_package_file:
                self.logger.error('Cannot generate package_file for file {0} for client {1}'.format(
                                        file_id, client_id))

            if not delete_file(client_package_file, cursor):
                bad_files.append(file_id)

        return bad_files

    #
    #
    #
    def delete_file(self, client_package_file):
        """
        Deletes a file off the target client
        """

        if not verify_file(client_package_file):
            self.logger.error('Package file is missing or corrupt')

        try:
            self.ssh_command(client_package_file, ['rm', client_package_file[self.HOST_FILE]])
        except subprocess.CalledProcessError:
            self.logger.error('Something went wrong during the remote rm process')

        if verify_file(client_package_file):
            self.logger.error('Package file failed to delete')
            return False

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

        if not cursor:
            cursor = self.db_manager.get_cursor()

        bad_files = []

        for file_id in cursor.execute(self.SQL['get_package_files'], package_id).fetchall():
            file_id = file_id[0]

            client_package_file = get_file(client_id, file_id)

            if not client_package_file:
                self.logger.error('Cannot generate package file for file {0} for client {1}'.format(
                                        file_id, client_id))

            if not verify_file(client_package_file):
                bad_files.append(file_id)

        return bad_files


    #
    #
    #
    def verify_file(self, client_package_file):
        """
        1. package_file = get_file(client_id, file_id)
        2. Perform remote file existence check
        3. Perform remote hash of file
        4. Return False on missing or hash check fail
        """

        try:
            self.ssh_command(client_package_file, ['ls', client_package_file[self.HOST_FILE]])
        except subprocess.CalledProcessError:
            self.logger.error('Missing file {0} on client {1}'.format(
                            client_package_file[self.HOST_FILE]
                            , client_package_file[self.HOST_ADDRESS]
                        ))
            return False

        try:
            sshOutput = self.ssh_command(
                            client_package_file
                            , ['sha256sum', client_package_file[self.HOST_FILE]]
                        )
        except subprocess.CalledProcessError:
            self.logger.error('Unable to perform remote hash for file {0} on client {1}'.format(
                            client_package_file[self.HOST_FILE]
                            , client_package_file[self.HOST_ADDRESS]
                        ))

        remote_hash = sshOutput.rstrip().split(' ')[0]

        if client_package_file['hash'] == remote_hash:
            self.logger.debug('Remote file hash matches')
            return True
        else:
            self.logger.error('File hash mismatch for file {0} on client {1}'.format(
                            client_package_file[self.HOST_FILE]
                            , client_package_file[self.HOST_ADDRESS]))
            return False


if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_SyncManager()
    pass
