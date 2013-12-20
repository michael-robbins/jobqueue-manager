import subprocess

class SyncManager():
    """
    Handles pushing media files around the various clients
    """

    def __init__(self):
        pass

    def run_in_shell(self):
        pass

    def build_shell_command(self, file_details, client_id, action_id):
        """
        From the given file_details:
        1. From the given action
        """



    def transfer_package(self, package_id, src_client_id, dst_client_id, action_id):
        """
        Transfers a package between clients (or deletes/etc depending on action_id)
        1. bad_src_files = verify_package(package_id, src_client_id)
            1.1. Return False if bad_src_files
        2. bad_dst_files = verify_package(package_id, dst_client_id)
        3. for file_id in ( bad_dst_files || get_package_files(package_id) )
            3.1. if action == 'SYNC':
                3.1.1. transfer_file(file_id, src_client_id, dst_client_id, action_id)
                3.1.2. if not verify_file(file_id, dst_client_id): bad_files.append(file_id)
            3.2. if action == 'DEL':
                3.2.1. delete_file(file_id, dst_client_id)
                3.2.2. if verify_file(file_id, dst_client_id): bad_files.append(file_id)
            3.3. else (Unknown action, bail out here?)
        4. If bad_files: return bad_files
        5. if action == 'SYNC':
            5.1. return verify_package(package_id, dst_client_id)
        6. if action == 'DEL':
            6.1. return not verify_package(package_id, dst_client_id)
        """
        pass

    def transfer_file(self, file_id, src_client_id, dst_client_id):
        """
        Takes a file and performs an action on it (after verifying action needs to be taken)
        1. verify_file(file_id, src_client_id)
        2. verify_file(file_id, dst_client_id)
        3. Take action on file (sync,delete,etc)
            3.1. Sys
        4. verify_file(file_id, dst_client_id)
        """
        pass

    def delete_file(self, file_id, client_id):
        """
        Deletes a file off the client
        1. 
        """
        pass

    def verify_package(self, package_id, client_id):
        """
        Takes a single package and ensures it exists on the client
        1. for file_id in get_package_files(package_id)
            1.1. verify_file(file_id, client_id)
        2. If verify_file returned False add to bad_files set

        Returns: bad_files set
        """
        pass

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
