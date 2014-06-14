import os
import sys
import subprocess

class SyncManager():
    """
    Handles pushing package files around the various clients
    """
    
    SSH_WORKED   = 'ssh_worked'
    SSH_FAILED   = 'ssh_failed'

    RSYNC_WORKED = 'rsync_worked'
    RSYNC_FAILED = 'rsync_failed'

    VERIFICATION_FULL    = 'all_there'
    VERIFICATION_PARTIAL = 'kinda_there'
    VERIFICATION_NONE    = 'not_there'

    PACKAGE_ACTION_FAILED = 'nope'
    PACKAGE_ACTION_WORKED = 'yep'

    REMOTE_PROG_HASH = 'sha256sum'
    REMOTE_PROG_LS   = 'ls'
    REMOTE_PROG_RM   = 'rm'

    def __init__(self, db_manager, logger):
        """
        Setup the DB interactions and logger
        """
        self.logger      = logger
        self.db_manager  = db_manager

    def shellOut(self, command):
        """
        Generic method to shell out to the OS
        """

        process = subprocess.check_output(
                command
                , stderr=subprocess.PIPE
                , universal_newlines=True
            )

        return process

    def sshCommand(self, client, cmd):
        """
        Executes an SSH command to the remote host and returns the SSH output
        Assumes SSH Keys are setup and password-less auth works
        """

        command = [ 'ssh' ]

        # If the object isn't iterable we bail
        if not hasattr(cmd, '__iter__'):
            self.logger.error("Command given must be in a list (iterable), not a string")
            return self.SSH_FAILED

        if not client.hostname and not client.port and not client.username:
            self.logger.debug("Client is local, just shelling out without ssh")
            self.logger.debug("LOCAL COMMAND: {0}".format(" ".join(cmd)))
            return self.shellOut(cmd)

        if client.port:
            command.append('-p {0}'.format(client.port))

        if client.username:
            command.append(client.username + '@' + client.hostname)
        else:
            command.append(client.hostname)

        command.extend(cmd)

        self.logger.debug("SSH COMMAND: {0}".format(" ".join(command)))

        return self.shellOut(command)

    def rsyncFile(self, src_client, dst_client, package_file):
        """
        Supports sending a file from a [local|remote] host
        to its respective [remote|local] destination
        This assumes that [src|dst]_file is the fully qualified file path
        """

        command = ['rsync'] 

        # Turn this into a variable maybe?
        command.extend(['--progress', '--verbose', '--compress'])

        # Check that we dont have both as a 'remote' client
        if src_client.hostname and dst_client.hostname:
            self.logger.error("Cannot have both as remote hosts")
            return self.RSYNC_FAILED

        # Check to ensure at least one client is 'remote'
        if not src_client.hostname and not dst_client.hostname:
            self.logger.error("At least one client needs to be a remote client")
            return self.RSYNC_FAILED

        # Report if we are defaulting to the default user
        if (src_client.hostname and not src_client.username) \
                    or (dst_client.hostname and not dst_client.username):
            self.logger.debug("rsync user defaulting to the username '{0}'".format(os.getlogin()))

        # Extend the rsync command with the port of the remote user
        if (src_client.hostname and src_client.port):
            command.append('--rsh=ssh -p {0}'.format(src_client.port))
        elif (dst_client.hostname and dst_client.port):
            command.append('--rsh=ssh -p {0}'.format(dst_client.port))
        else:
            self.logger.debug("Assuming port for 22 for rsync call")

        # Extend the rsync command with the bwlimit
        if src_client.max_upload:
            if dst_client.max_download:
                if src_client.max_upload > dst_client.max_download:
                    max_sync = dst_client.max_download
                else:
                    max_sync = src_client.max_upload
            else:
                max_sync = src_client.max_upload
        else:
            max_sync = None

        # We get the number of current jobs and divide the max_sync by that
        if max_sync:
            num_jobs = len(self.job_manager.get_jobs())
            command.append('--bwlimit={0}'.format(max_sync/num_jobs))

        # We now have the base part of the command done
        # we process the source and then destination parts
        
        def build_rsync_location(client, file_path):
            """
            Takes a client and a file_object
            """
            location = ''

            if client.username:
                location += client.username + '@'

            if client.hostname:
                location += client.hostname + ':'

            location += client.base_path + file_path

            return location

        for client in [src_client, dst_client]:
            command.append(build_rsync_location(client, package_file.relative_path))

        self.logger.debug("RSYNC COMMAND: {0}".format(" ".join(command)))

        return self.shellOut(command)

    def handlePackage(self, package_id, src_client_id, dst_client_id, action_id, cursor=None):
        """
        Transfers a package between clients (or deletes/etc depending on action_id)
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        self.logger.debug("{0}'ing package {1} from {2} to {3}".format(action_id, package_id,
                                src_client_id, dst_client_id ))

        src_client   = self.client_manager.getClient(src_client_id, cursor)
        dst_client   = self.client_manager.getClient(dst_client_id, cursor)
        file_package = self.filepackage_manager.getFilePackage(package_id, cursor)

        if action_id == 1: # Sync
            if verifyPackage(src_client, file_package) != self.VERIFICATION_FULL:
                self.logger.error('Source package is incomplete or corrupt, bailing')
                return self.PACKAGE_ACTION_FAILED
            else:
                self.logger.info('Source package is verified')

            if verifyPackage(dst_client, file_package) == self.VERIFICATION_FULL:
                self.logger.error('Destination package exists already, returning that it worked')
                return self.PACKAGE_ACTION_WORKED
            else:
                self.logger.info("Destination is missing the package (or part of it)")

            if transferPackage(src_client, dst_client, file_package) == self.PACKAGE_ACTION_WORKED:
                self.logger.info('Completed package transfer')
                return self.PACKAGE_ACTION_WORKED
            else:
                self.logger.error('Failed package verification')
                return self.PACKAGE_ACTION_FAILED

        if action_id == 2: # Delete
            if verifyPackage(dst_client, file_package) != self.VERIFICATION_FULL:
                self.logger.error('Destination package is not complete, skipping')
                return self.PACKAGE_ACTION_FAILED
            else:
                self.logger.debug('Destination package is in a good condition to delete')

            if delete_package(dst_client, file_package):
                self.logger.info('Package deletion completed')
                return self.PACKAGE_ACTION_WORKED
            else:
                self.logger.error('Package deletion failed')
                return self.PACKAGE_ACTION_FAILED

        if action_id == 3: # Reindex (discoverPackages)
            return discoverFilePackage(dst_client, package_id) == self.PACKAGE_ACTION_WORKED:

    def transferPackage(self, src_client, dst_client, file_package, cursor=None):
        """
        Wrapper around transfer_file
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        bad_transfers = []

        for package_file in file_package.file_list:
            if transfer_file(src_client, dst_client, package_file) != self.PACKAGE_ACTION_WORKED:
                bad_transfers.append(package_file)

        if verifyPackage(dst_client, file_package):
            self.logger.info('Transfer of package worked')
            return self.PACKAGE_ACTION_WORKED
        else:
            self.logger.error('Transfer of package failed')
            self.logger.error('Failed file_id\'s were: ' + ' '.join(bad_transfers))
            return self.PACKAGE_ACTION_FAILED


    def transfer_file(self, src_client, dst_client, package_file):
        """
        Takes a file and rsyncs from src->dst (after verifying action needs to be taken)
        """

        if self.verifyFile(dst_client, package_file) == self.VERIFICATION_FULL:
            self.logger.debug('File already exists, skipping transfer')
            return self.PACKAGE_ACTION_WORKED

        try:
            rsyncResult = self.rsyncFile(src_client, dst_client, package_file)
        except subprocess.CalledProcessError as e:
            self.logger.error('Rsync failed to send the file properly')

        if self.verifyFile(dst_client, package_file) == self.VERIFICATION_FULL:
            return self.PACKAGE_ACTION_WORKED
        else:
            self.logger.error('Failed to transfer file {0} from {1} to {2}'.format(
                                package_file, src_client, dst_client))
            return self.PACKAGE_ACTION_FAILED

    def delete_package(self, client, file_package, cursor=None):
        """
        Takes a single package and deletes it off the client
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        bad_files = []

        for package_file in file_package.file_list:
            if delete_file(client, package_file) == self.PACKAGE_ACTION_FAILED:
                bad_files.append(package_file)

        if bad_files:
            self.logger.error('Unable to delete file\'s: ' + ' '.join(bad_files))
            return self.PACKAGE_ACTION_FAILED
        else:
            self.logger.debug('Deleted packge {0} off client {1}'.format(file_package, client))
            return self.PACKAGE_ACTION_WORKED

    def delete_file(self, client, package_file):
        """
        Deletes a file off the target client
        """

        if self.verifyFile(client, package_file) != self.VERIFICATION_FULL:
            self.logger.error('File package is missing or corrupt')

        full_path = client.base_path + package_file.relative_path

        try:
            self.sshCommand(client, [self.REMOTE_PROG_RM, full_path])
        except subprocess.CalledProcessError:
            self.logger.error('Something went wrong during the remote rm process')

        if self.verifyFile(client, package_file) == self.VERIFICATION_FULL:
            self.logger.error('File package {0} failed to delete off {1}'.format(
                            package_file, client))
            return self.PACKAGE_ACTION_FAILED

        return self.PACKAGE_ACTION_WORKED

    def verifyPackage(self, client, file_package, cursor=None):
        """
        Takes a single package and ensures it exists on the given client
        """

        if not cursor:
            cursor = self.db_manager.get_cursor()

        bad_files  = []

        for package_file in file_package.file_list:
            if self.verifyFile(client, package_file) == self.VERIFICATION_NONE:
                bad_files.append(package_file)

        if bad_files:
            if len(bad_files) >= len(file_package.file_list):
                return self.VERIFICATION_NONE
            else:
                return self.VERIFICATION_PARTIAL
        else:
            return self.VERIFICATION_FULL

    def verifyFile(self, client, package_file):
        """
        Ensures that the given file:
        1. Exists on the client
        2. Matches the hash
        """

        full_path = client.base_path + package_file.relative_path

        # Verify the file exists at all
        try:
            self.sshCommand(client, [self.REMOTE_PROG_LS, full_path])
        except subprocess.CalledProcessError:
            self.logger.error('Missing file {0} on client {1}'.format(
                            package_file
                            , client
                        ))
            return self.VERIFICATION_NONE

        # Verify the remote hash against the one we have
        try:
            sshOutput = self.sshCommand(
                            client
                            , [self.REMOTE_PROG_HASH, full_path]
                        )
        except subprocess.CalledProcessError:
            self.logger.error('Unable to perform remote hash for file {0} on client {1}'.format(
                            package_file
                            , client
                        ))
            return self.VERIFICATION_NONE

        remote_hash = sshOutput.rstrip().split(' ')[0]

        if package_file.file_hash == remote_hash:
            self.logger.debug('File hash matches for {0}'.format(package_file))
            return self.VERIFICATION_FULL
        else:
            self.logger.error('File hash mismatch for file {0} on client {1}'.format(
                            package_file
                            , client))
            return self.VERIFICATION_NONE

    def discoverFilePackage(self, client, filepackage_ids=list()):
        """
        Given a client and an (optional) list of file_package id's
        We attempt to verify each package on the client
        If a verify returns a self.VERIFICATION_FULL we then associate the client to that package
        """

        full_verify = 0
        part_verify = 0
        none_verify = 0

        if not filepackage_ids:
            filepackage_ids = filepackage_mananger.getAllFilePackageIds(self.db_manager.get_cursor())

        for filepackage_id in filepackage_ids:
            file_package = self.filepackage_manager.getFilePackage(filepackage_id)

            result_code = self.verifyPackage(client, file_package)

            if result_code == self.VERIFICATION_FULL:
                client.associateFilePackage(filepackage_id, self.VERIFICATION_FULL)
                self.logger.info('Associating filepackage_id {0}'
                                    + 'with client {1}'.format(filepackage_id, client))
                full_verify += 1

            elif result_code == self.VERIFICATION_PARTIAL:
                client.associateFilePackage(filepackage_id, self.VERIFICATION_PARTIAL)
                self.logger.info('Partially associating filepackage_id {0}'
                                    + 'with client {1}'.format(filepackage_id, client))
                part_verify += 1

            else:
                self.logger.info('Not associating filepackage_id {0}'
                                    + 'with client {1}'.format(filepackage_id, client))
                none_verify += 1

        self.logger.info('Filepackage discovery over')
        self.logger.info('total={0} full={1} partial={2} none={3}'.format(
                            len(filepackage_ids)
                            , full_verify
                            , part_verify
                            , none_verify))

        if (full_verify + part_verify) == len(filepackage_ids):
            self.logger.info('We fully/partially verified all requested packages')
            return self.PACKAGE_ACTION_WORKED
        elif full_verify > 0:
            self.logger.warning('We verified some packages')
            return self.PACKAGE_ACTION_WORKED
        else:
            self.logger.error('There were requested packages that failed to verify')
            return self.PACKAGE_ACTION_FAILED

if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_SyncManager()
