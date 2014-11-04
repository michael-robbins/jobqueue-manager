import os
import subprocess
import multiprocessing


class SyncManager():
    """
    Handles pushing package files around the various clients
    """

    # Hacky way of doing constants, is there a better way?
    SSH_WORKED = 'ssh_worked'
    SSH_FAILED = 'ssh_failed'

    RSYNC_WORKED = 'rsync_worked'
    RSYNC_FAILED = 'rsync_failed'

    VERIFICATION_FULL = 'all_there'
    VERIFICATION_PARTIAL = 'kinda_there'
    VERIFICATION_NONE = 'not_there'

    PACKAGE_ACTION_FAILED = 'nope'
    PACKAGE_ACTION_WORKED = 'yep'

    REMOTE_PROG_HASH = 'sha256sum'
    REMOTE_PROG_LS = 'ls'
    REMOTE_PROG_RM = 'rm'

    def __init__(self, api_manager, logger):
        """ Setup the API interactions and logger """

        self.api_manager = api_manager
        self.logger = logger
        self.job_queue = list()
        self.processing_queue = list()

    class AlreadyWorkingOnException(Exception):
        """ The job we have been given is already being worked on """
        pass

    class ActionAlreadyWorkingOnException(Exception):
        """ The job action is already being worked on """
        pass

    @staticmethod
    def shell_out(command):
        """ Generic method to shell out to the OS """
        process = subprocess.check_output(command, stderr=subprocess.PIPE, universal_newlines=True)
        return process

    def ssh_command(self, client, cmd):
        """
        Executes an SSH command to the remote host and returns the SSH output
        Assumes SSH Keys are setup and password-less auth works
        """
        # If the cmd isn't iterable we bail
        if not hasattr(cmd, '__iter__'):
            self.logger.error("Command given must be iterable")
            return self.SSH_FAILED

        # Test if the client is local, if so shell out without building the ssh part
        if not client['host_hostname'] and not client['host_port'] and not client['host_username']:
            self.logger.debug("Client is local, just shelling out without ssh")
            self.logger.debug("LOCAL COMMAND: {0}".format(" ".join(cmd)))
            return self.shell_out(cmd)

        # Client is remote, build the SSH command
        command = ['ssh']

        if client['host_port']:
            command.append('-p {0}'.format(client['host_port']))

        if client['host_username']:
            command.append(client['host_username'] + '@' + client['host_hostname'])
        else:
            command.append(client['host_hostname'])

        command.extend(cmd)

        self.logger.debug("SSH COMMAND: {0}".format(' '.join(command)))
        return self.shell_out(command)

    def rsync_file(self, src_client, dst_client, package_file):
        """
        Supports sending a file from a [local|remote] host
        to its respective [remote|local] destination
        This assumes that [src|dst]_file is the fully qualified file path
        """

        # Check that we don't have both as a 'remote' client
        if 'host_hostname' in src_client and 'host_hostname' in dst_client:
            self.logger.error('Cannot have both as remote hosts')
            return self.RSYNC_FAILED

        # Check to ensure at least one client is 'remote'
        if 'host_hostname' not in src_client and 'host_hostname' not in dst_client:
            self.logger.error('At least one client needs to be a remote client')
            return self.RSYNC_FAILED

        # Report if we are defaulting to the default user
        if ('host_hostname' in src_client and 'host_username' not in src_client) \
                or ('host_hostname' in dst_client and 'host_username' not in dst_client):
            self.logger.debug("rsync user defaulting to the username '{0}'".format(os.getlogin()))

        # Build the rsync command
        command = ['rsync']

        # Turn this into a variable maybe?
        command.extend(['--progress', '--verbose', '--compress'])

        # Extend the rsync command with the port of the remote user
        if src_client['host_hostname'] and src_client['host_port']:
            command.append('--rsh=ssh -p {0}'.format(src_client['host_port']))
        elif dst_client['host_hostname'] and dst_client['host_port']:
            command.append('--rsh=ssh -p {0}'.format(dst_client['host_port']))
        else:
            self.logger.debug('Assuming port for 22 for rsync call')

        # Extend the rsync command with the bandwidth limit (bwlimit)
        if src_client['max_upload']:
            if dst_client['max_download']:
                if src_client['max_upload'] > dst_client['max_download']:
                    max_sync = dst_client['max_download']
                else:
                    max_sync = src_client['max_upload']
            else:
                max_sync = src_client['max_upload']
        else:
            max_sync = 0

        # Only append if we have a value > 0
        if max_sync:
            command.append('--bwlimit={0}'.format(max_sync))

        # We now have the base part of the command done
        # we process the source and then destination parts
        def build_rsync_location(local_client, file_path):
            """ Takes a client and a file path """
            location = ''

            if local_client['host_username']:
                location += local_client['host_username'] + '@'

            if local_client['host_hostname']:
                location += local_client['host_hostname'] + ':'

            location += local_client['base_path'] + file_path

            return location

        for client in [src_client, dst_client]:
            command.append(build_rsync_location(client, package_file['relative_path']))

        self.logger.debug('RSYNC COMMAND: {0}'.format(' '.join(command)))

        return self.shell_out(command)

    def handle_packages(self, job_id, packages, src_client, dst_client, action):
        """ Wrapper around handle_package allowing multiple packages to be worked on """
        results = []
        self.logger.debug('Working on multiple packages')

        for package in packages:
            # Build up a list of (package, result) tuples
            results.append((package, self.handle_package(job_id, package, src_client, dst_client, action)))

        return results

    def handle_package(self, job_id, package, src_client, dst_client, action):
        """ Transfers a package between clients (or deletes/etc depending on action) """
        self.logger.debug("{0}'ing package {1} from {2} to {3}".format(action, package['name'], src_client['name'],
                                                                       dst_client['name']))
        self.api_manager.update_job_state(job_id, 'PROG')
        outcome = None

        if action == 'SYNC':
            if self.verify_package(src_client, package) == self.VERIFICATION_FULL:
                if self.verify_package(dst_client, package) != self.VERIFICATION_FULL:
                    outcome = self.transfer_package(src_client, dst_client, package)
                else:
                    self.logger.error('Destination package exists already, returning that it worked')
                    outcome = self.PACKAGE_ACTION_WORKED
            else:
                self.logger.error('Source package is incomplete or corrupt, bailing')
                outcome = self.PACKAGE_ACTION_FAILED

        elif action == 'DEL':
            if self.verify_package(dst_client, package) == self.VERIFICATION_FULL:
                self.logger.debug('Destination package is in a good condition to delete')
                outcome = self.delete_package(dst_client, package)
            else:
                self.logger.error('Destination package is not complete, skipping')
                outcome = self.PACKAGE_ACTION_FAILED

        elif action == 'INDEX':
            outcome = self.verify_package(dst_client, package)

        if outcome == self.PACKAGE_ACTION_WORKED:
            return self.api_manager.update_job_state(job_id, 'COMP')
        else:
            return self.api_manager.update_job_state(job_id, 'FAIL')

    def transfer_package(self, src_client, dst_client, file_package):
        """ Wrapper around transfer_file """
        bad_transfers = []

        for package_file in file_package['package_files']:
            if self.transfer_file(src_client, dst_client, package_file) != self.PACKAGE_ACTION_WORKED:
                bad_transfers.append(package_file)

        if self.verify_package(dst_client, file_package) == (self.VERIFICATION_FULL, list()):
            self.logger.info('Transfer of package worked')
            return self.PACKAGE_ACTION_WORKED
        else:
            self.logger.error('Transfer of package failed')
            self.logger.error('Failed file_id\'s were: ' + ' '.join(bad_transfers))
            return self.PACKAGE_ACTION_FAILED

    def transfer_file(self, src_client, dst_client, package_file):
        """ Takes a file and rsyncs from src->dst (after verifying action needs to be taken) """
        if self.verify_file(dst_client, package_file) == self.VERIFICATION_FULL:
            self.logger.debug('File already exists, skipping transfer')
            return self.PACKAGE_ACTION_WORKED

        try:
            self.rsync_file(src_client, dst_client, package_file)
        except subprocess.CalledProcessError:
            self.logger.error('Rsync failed to send the file properly')

        if self.verify_file(dst_client, package_file) == self.VERIFICATION_FULL:
            return self.PACKAGE_ACTION_WORKED
        else:
            message = 'Failed to transfer file {0} from {1} to {2}'.format(package_file, src_client, dst_client)
            self.logger.error(message)
            return self.PACKAGE_ACTION_FAILED

    def delete_package(self, client, file_package):
        """ Takes a single package and deletes it off the client """
        bad_files = list()

        for package_file in file_package['package_files']:
            if self.delete_file(client, package_file) == self.PACKAGE_ACTION_FAILED:
                bad_files.append(package_file)

        if bad_files:
            self.logger.error('Unable to delete file\'s: ' + ' '.join(bad_files))
            return self.PACKAGE_ACTION_FAILED
        else:
            self.logger.debug('Deleted package {0} off client {1}'.format(file_package, client))
            return self.PACKAGE_ACTION_WORKED

    def delete_file(self, client, package_file):
        """ Deletes a file off the target client """

        if self.verify_file(client, package_file) != self.VERIFICATION_FULL:
            self.logger.error('File package is missing or corrupt')

        full_path = client['base_path'] + package_file['relative_path']

        try:
            self.ssh_command(client, [self.REMOTE_PROG_RM, full_path])
        except subprocess.CalledProcessError:
            self.logger.error('Something went wrong during the remote rm process')

        if self.verify_file(client, package_file) == self.VERIFICATION_FULL:
            self.logger.error('File package {0} failed to delete off {1}'.format(package_file, client))
            return self.PACKAGE_ACTION_FAILED

        return self.PACKAGE_ACTION_WORKED

    def verify_package(self, client, package):
        """
        Takes a single package and ensures it exists on the given client
        Also updates the API in regards to the outcome
        """

        bad_files = list()

        for package_file in package['package_files']:
            if self.verify_file(client, package_file) == self.VERIFICATION_FULL:
                self.api_manager.associate_client_with_file(client['id'], package_file['id'], True)
            else:
                self.api_manager.associate_client_with_file(client['id'], package_file['id'], False)
                bad_files.append(package_file)

        if bad_files:
            self.api_manager.associate_client_with_package(client['id'], package['id'], False)
            if len(bad_files) > len(package['package_files']):
                message = 'More bad files ({0}) than files in package ({1})?'.format(len(bad_files),
                                                                                     len(package['package_files']))
                self.logger.error(message)
                return self.VERIFICATION_NONE
            if len(bad_files) == len(package['package_files']):
                return self.VERIFICATION_NONE
            else:
                return self.VERIFICATION_PARTIAL
        else:
            self.api_manager.associate_client_with_package(client['id'], package['id'], True)
            return self.VERIFICATION_FULL

    def verify_file(self, client, package_file):
        """
        Ensures that the given file:
        1. Exists on the client
        2. Matches the hash
        3. Returns the result
        """
        full_path = client['base_path'] + package_file['relative_path']

        # Verify the file exists at all
        try:
            self.ssh_command(client, [self.REMOTE_PROG_LS, full_path])
        except subprocess.CalledProcessError:
            self.logger.error('Missing file {0} on client {1}'.format(package_file, client))
            return self.VERIFICATION_NONE

        # Verify the remote hash against the one we have
        try:
            ssh_output = self.ssh_command(client, [self.REMOTE_PROG_HASH, full_path])
        except subprocess.CalledProcessError:
            self.logger.error('Unable to perform remote hash for file {0} on client {1}'.format(package_file, client))
            return self.VERIFICATION_NONE

        # $> file_hash file.name.ext
        remote_hash = ssh_output.rstrip().split(' ')[0]

        if package_file['file_hash'] == remote_hash:
            self.logger.debug('File hash matches for {0}'.format(package_file))
            return self.VERIFICATION_FULL
        else:
            self.logger.error('File hash mismatch for file {0} on client {1}'.format(package_file, client))
            return self.VERIFICATION_NONE

    def handle(self, job):
        """ Queues the job internally """
        for process in self.processing_queue:
            if process.name == job:
                raise self.AlreadyWorkingOnException

        for process in self.processing_queue:
            if job['action'] in process.name:
                raise self.ActionAlreadyWorkingOnException

        function_args = (job['id'], job['package'], job['source_client'], job['destination_client'], job['action'])
        p = multiprocessing.Process(target=self.handle_package, args=function_args, name=job['name'])
        p.start()

        self.processing_queue.append(p)

    def complete_jobs(self):
        """ Loop through all the jobs and report back the jobs that we removed """
        removed_processes = list()

        for process in self.processing_queue:
            if not process.is_alive():
                # Process outcome will have been reported from within the process itself
                # Join it to ensure it's finished and remove it from the processing queue
                self.logger.debug("Joining process {0} to ensure it's dead".format(process.name))
                try:
                    process.join(timeout=5)
                    self.processing_queue.remove(process)
                    removed_processes.append(process.name)
                except multiprocessing.TimeoutError as e:
                    self.logger.warn('Process isn\'t alive but didn\'t join in time...')

        # Report on the number of processed
        return removed_processes