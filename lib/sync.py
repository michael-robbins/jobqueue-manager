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

    VERIFICATION_FULL    = 'all_there'
    VERIFICATION_PARTIAL = 'kinda_there'
    VERIFICATION_NONE    = 'not_there'

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
                , 'get_file_packages'
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
        Returns a file_package dict[]
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

        file_package = dict()
        
        (
                file_package[self.HOST_ADDRESS]
                , file_package[self.HOST_PORT]
                , base_path
                , file_package['package_id']
                , rel_path
                , file_package['hash']
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


        file_package[self.HOST_FILE] = base_path + get_parent_path(str(file_package['package_id']))  \
                                                        + rel_path

        return file_package


    #
    #
    #
    def ssh_command(self, file_package, cmd):
        """
        Executes an SSH command to the remote host and returns the SSH output
        Assumes SSH Keys are setup and password-less auth works
        """
        command = [ 'ssh' ]

        if not hasattr(cmd, '__iter__'):
            self.logger.error("Command given must be in a list (iterable), not a string")
            return self.SSH_FAILED

        if self.HOST_ADDRESS not in file_package:
            self.logger.error("Missing address in file_package")
            return self.SSH_FAILED

        if self.HOST_PORT in file_package:
            command.append('-p {0}'.format(file_package[self.HOST_PORT]))

        if self.HOST_USER in file_package:
            command.append(file_package[self.HOST_USER] + '@' + file_package[self.HOST_ADDRESS])
        else:
            command.append(file_package[self.HOST_ADDRESS])

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
    def rsync_file(self, src_file_package, dst_file_package):
        """
        Supports sending a file from a [local|remote] host
        to its opposite [remote|local] destination
        """

        command = ['rsync', '-v', '--progress', '--verbose', '--compress']

        def is_remote(file_package):
            """
            Checks to see if the file host is remote (has address or port)
            """
            if self.HOST_ADDRESS in file_package:
                return True
            elif self.HOST_PORT in file_package:
                return True
            else:
                return False

        if is_remote(src_file_package) and is_remote(dst_file_package):
            self.logger.error("Cannot have both as remote hosts")
            return None

        def is_remote_with_user(file_package):
            """
            Extends is_remote with if we have a user or not as well
            """
            if is_remote(file_package) and self.HOST_USER in file_package:
                return True
            else:
                return False

        if is_remote_with_user(src_file_package) or is_remote_with_user(dst_file_package):
            self.logger.warn("rsync user defaulting to the user it was run as")


        if self.HOST_PORT in src_file_package:
            command.extend(shlex.split("--rsh='ssh -p {0}'".format(src_file_package[self.HOST_PORT])))
        elif self.HOST_PORT in dst_file_package:
            command.extend(shlex.split("--rsh='ssh -p {0}'".format(dst_file_package[self.HOST_PORT])))
        else:
            self.logger.warn("Assuming port of 22 for rsync call")

        # We now have the base part of the command done
        # we process the source and then destination parts
        
        def build_rsync_location(file_package):
            location = ''

            if self.HOST_USER in file_package:
                location += file_package[self.HOST_USER] + '@'

            if self.HOST_ADDRESS in file_package:
                location += file_package[self.HOST_ADDRESS] + ':'

            location += file_package[self.HOST_FILE]

            return location


        for file_package in [src_file_package, dst_file_package]:
            command.append(build_rsync_location(file_package))

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
    def handle_package(self, package_id, src_client_id, dst_client_id, action_id, cursor=None):
        """
        Transfers a package between clients (or deletes/etc depending on action_id)
        1. bad_src_files = verify_package(package_id, src_client_id)
            1.1. Return False if bad_src_files
        2. bad_dst_files = verify_package(package_id, dst_client_id)
        3. for file_id in ( bad_dst_files || get_file_packages(package_id) )
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

        if not cursor:
            cursor = self.db_manager.get_cursor()

        self.logger.debug("{0} package {1} from {2} to {3}".format(action_id, package_id,
                                src_client_id, dst_client_id ))

        if action_id == 1: # Sync
            if verify_package(package_id, src_client_id) != self.VERIFICATION_FULL:
                self.logger.error('Source package is incomplete or corrupt')
                return False

            if verify_package(package_id, dst_client_id) == self.VERIFICATION_FULL:
                self.logger.error('Destination package exists already...')
                return False

            if transfer_package(package_id, src_client_id, dst_client_id):
                self.logger.info('Completed package transfer')
            else:
                self.logger.error('Failed package verification')

            if verify_package(package_id, client_id) == self.VERIFICATION_FULL:
                self.logger.info('Completed package verification')
                return True
            else:
                self.logger.error('Failed package verification')
                return False

        if action_id == 2: # Delete
            if verify_package(package_id, dst_client_id) != self.VERIFICATION_FULL:
                self.logger.error('Destination package is not complete, skipping')
                return False
            else:
                self.logger.debug('Destination package is in a good condition to delete')

            if delete_package(package_id, dst_client_id):
                self.logger.info('Package deletion completed')
            else:
                self.logger.error('Package deletion failed')

            if verify_package(package_id, dst_client_id) != self.VERIFICATION_NONE:
                self.logger.error('Package verification failed')
            else:
                self.logger.debug('Package verification worked')

        if action_id == 3: # Reindex
            pass # Not implemented yet


    #
    #
    #
    def transfer_package(self, package_id, src_client_id, dst_client_id, cursor=None):
        """
        Wrapper around transfer_file
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        bad_transfers = []

        for file_id in cursor.execute(self.sql['get_file_packages'], package_id).fetchall():
            file_id = file_id[0]

            src_file_package = get_file(src_client_id, file_id)
            dst_file_package = get_file(dst_client_id, file_id)

            if not transfer_file(src_file_package, dst_file_package):
                bad_transfers.append(file_id)

        if verify_package(package_id, dst_client_id):
            self.logger.info('Transfer of package worked')
            return True
        else:
            self.logger.error('Transfer of package failed')
            self.logger.error('Failed file_id\'s were: ' + ' '.join(bad_transfers))
            return False


    #
    #
    #
    def transfer_file(self, src_file_package, dst_file_packge):
        """
        Takes a file and rsyncs from src->dst (after verifying action needs to be taken)
        """

        if verify_file(dst_file_package):
            self.logger.debug('File already exists, skipping transfer')
            return True

        rsyncResult = rsync_file(src_file_package, dst_file_package)

        if verify_file(dst_file_package):
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
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        bad_files = []

        for file_id in cursor.execute(self.sql['get_file_packages'], package_id).fetchall():
            file_id = file_id[0]

            file_package = get_file(client_id, file_id)

            if not delete_file(file_package, cursor):
                bad_files.append(file_id)

        if bad_files:
            self.logger.error('Unable to delete file_id\'s: ' + ' '.join(bad_files))
            return False
        else:
            self.logger.debug('Deleted packge {0} off client {1}'.format(package_id, client_id))
            return True


    #
    #
    #
    def delete_file(self, file_package):
        """
        Deletes a file off the target client
        """

        if not verify_file(file_package):
            self.logger.error('File package is missing or corrupt')

        try:
            self.ssh_command(file_package, ['rm', file_package[self.HOST_FILE]])
        except subprocess.CalledProcessError:
            self.logger.error('Something went wrong during the remote rm process')

        if verify_file(file_package):
            self.logger.error('File package {0} failed to delete off {1}'.format(
                            file_package[self.HOST_FILE], file_package[self.HOST_ADDRESS]))
            return False

        return True


    #
    #
    #
    def verify_package(self, package_id, client_id, cursor=None):
        """
        Takes a single package and ensures it exists on the client
        1. for file_id in get_file_packages(package_id)
            1.1. verify_file(file_id, client_id)
        2. If verify_file returned False add to bad_files set

        Returns: bad_files set
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        bad_files  = []

        count = 0
        for file_id in cursor.execute(self.sql['get_file_packages'], package_id).fetchall():
            count += 1
            file_id = file_id[0]

            file_package = get_file(client_id, file_id)

            if verify_file(file_package) == self.VERIFICATION_NONE:
                bad_files.append(file_id)

        if bad_files and (len(bad_files) == count or len(bad_files) > count):
            return self.VERIFICATION_NONE
        elif bad_files and len(bad_files) < count:
            return self.VERIFICATION_PARTIAL
        else bad_files:
            return self.VERIFICATION_FULL


    #
    #
    #
    def verify_file(self, file_package):
        """
        1. file_package = get_file(client_id, file_id)
        2. Perform remote file existence check
        3. Perform remote hash of file
        4. Return False on missing or hash check fail
        """

        try:
            self.ssh_command(file_package, ['ls', file_package[self.HOST_FILE]])
        except subprocess.CalledProcessError:
            self.logger.error('Missing file {0} on client {1}'.format(
                            file_package[self.HOST_FILE]
                            , file_package[self.HOST_ADDRESS]
                        ))
            return self.VERIFICATION_NONE

        try:
            sshOutput = self.ssh_command(
                            file_package
                            , ['sha256sum', file_package[self.HOST_FILE]]
                        )
        except subprocess.CalledProcessError:
            self.logger.error('Unable to perform remote hash for file {0} on client {1}'.format(
                            file_package[self.HOST_FILE]
                            , file_package[self.HOST_ADDRESS]
                        ))

        remote_hash = sshOutput.rstrip().split(' ')[0]

        if file_package['hash'] == remote_hash:
            self.logger.debug('Remote file hash matches')
            return self.VERIFICATION_FULL
        else:
            self.logger.error('File hash mismatch for file {0} on client {1}'.format(
                            file_package[self.HOST_FILE]
                            , file_package[self.HOST_ADDRESS]))
            return self.VERIFICATION_NONE


if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_SyncManager()
