class SyncManager():
    """
    Handles pushing media files around the various clients
    """

    def __init__(self):
        pass

    def run_in_shell(self):
        pass

    def transfer_file(self, source, destination, client, action='push'):
        """
        Takes a file (source & destination) and either:
            * push: Pushes it out to a client from the server (default)
            * pull: Pulls it from the client to the server
        """
        pass

    def verify_remote_file(self, source, destination, client):
        """
        Takes a file (source & destination) and does the following:
            1. Hash the local file
            2. Hash the remote file on the client
            3. Compares hashes and returns the result:
                * True  = match
                * False = non-match
        """
        pass

    def verify_remote_package(self, package, client):
        """
        Takes a single Media Package and ensures it exists on the client:
            * Get list of files from package
            * Check each file exists on the client

            Example:
            for (local_file, remote_file) in MediaPackageManager.get_files(package, client):
                self.verify_remote_file(
                    MediaPackageManager.configure_for_server(local_file
                    , MediaPackageManager.configure_for_client(client_file)
                    , client)
        """
        pass

if __name__ == '__main__':
    sync_manager = SyncManager()
