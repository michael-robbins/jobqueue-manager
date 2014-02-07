import subprocess


#
#
#
class SyncManager():
    """
    Handles pushing media files around the various clients
    """

    #
    #
    #
    def __init__(self):
        pass


    #
    #
    #
    def rsync_file(self, src_details, dst_details):
        """
        Supports sending a file from a [local|remote] source to its opposite [remote|local] destination

        src_details[address] = 'files.source.com'
        src_details[port]    = '8080'
        src_details[file]    = '/path/to/source/file'

        dst_details[address] = 'files.destination.com'
        dst_details[port]    = '8080'
        dst_details[file]    = '/path/to/destination/file'

        subprocess call to:
            rsync
                --verbose
                --partial
                --compress
                --rsh='ssh -p'+dst_details[port]
                src_details[file]
                dst_details[address]:dst_details[file]
        """
        command = ['rsync', '-v', '--progress', '--verbose', '--compress']

        if ('address' in src_details or 'port' in src_details)
                and ('address' in dst_details or 'port' in dst_details):
            print "ERROR: Cannot have both as remote hosts"
            return False

        if 'port' in src_details:
            command.append("--rsh='ssh -p{0}'".format(src_details[port]))
        elif 'port' in dst_details:
            command.append("--rsh='ssh -p{0}'".format(dst_details[port]))
        else:
            print "WARNING: Assuming port of 22 for rsync call"

        if 'address' in src_details:
            command.append("\"{0}:{1}\"".format(src_details[address], src_details[file]))
        else:
            command.append("\"{0}\"".format(src_details[file]))

        if 'address' in dst_details:
            command.append("\"{0}:{1}\"".format(dst_details[address], dst_details[file]))
        else:
            command.append("\"{0}\"".format(dst_details[file]))

        print("DEBUG: RSYNC COMMAND: {0}".format(" ".join(command)))


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
        1. file = get_file(file_id)
        2. Perform remote file existence check
        3. Perform remote hash of file
        4. Return False on missing or hash check fail
        """
        pass


if __name__ == '__main__':
    #from tester import TestManager
    #tester = TestManager()
    #tester.test_SyncManager()
    pass
