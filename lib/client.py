import os
import sys

class ClientManager():
    """
    Handles the client interactions
    """

    def __init__(self, db_manager, logger):
        """
        Setup the DB interactions and logger
        We just use the db_manager to get the correct SQL
        The rest will be provided to the child classes as cursors from the calling class
        """

        self.logger = logger

        self.SQL = db_manager.get_sql_cmds()

    class Client():
        """
        Client object, contains the following attributes:
        * hostname
        * port
        * username
        * base_path
        """

        def __init__(self, client_id, required_sql, cursor):
            """
            Takes the client_id and configures the required attributes
            """

            self.SQL = required_sql

            cursor.execute(self.SQL['get_client_for_sync'], str(client_id))

            (
                self.hostname
                , self.port
                , self.username
                , self.base_path
                , self.max_download
                , self.max_upload
            ) = cursor.fetchone()

        def __str__(self):
            """
            Returns a pretty string representing the client
            """

            if not self.hostname:
                return 'localhost'

            string = ''

            if self.username:
                string += self.username + '@'

            string += self.hostname

            if self.port:
                string += ':{0}'.format(self.port)

            return string


    def getClient(self, client_id, cursor):
        """
        Returns a client object of the given client_id
        """

        request_client = self.Client(client_id, self.SQL, cursor)

        if not request_client:
            self.logger.error('Unable to generate client object for client_id {0}'.format(client_id))
            return None

        return request_client


if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_ClientManager()
