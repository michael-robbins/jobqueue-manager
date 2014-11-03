#!/usr/bin/env python3

import json
import requests


class ApiManager():
    """ Handles all interactions with the API """
    JSON_HEADER = {'content-type': 'application/json'}
    DEFAULT_HEADER = dict().update(JSON_HEADER)
    DEFAULT_PARAMS = dict()

    def __init__(self, host):
        """ Setup the API connection """
        self.host = host

    # API Operations
    def get(self, endpoint, params=DEFAULT_PARAMS, headers=DEFAULT_HEADER):
        """ Returns a dict() of the endpoint """
        url = '/'.join([self.host, endpoint, ''])
        return requests.get(url=url, params=params, headers=headers).json()

    def post(self, endpoint, data, params=DEFAULT_PARAMS, headers=DEFAULT_HEADER):
        """ Returns a modified object or None """
        url = '/'.join([self.host, endpoint, ''])
        return requests.post(url=url, params=params, data=json.dumps(data), headers=headers).json()

    def patch(self, endpoint, data, params=DEFAULT_PARAMS, headers=DEFAULT_HEADER):
        """ Returns a modified field or None """
        url = '/'.join([self.host, endpoint, ''])
        return requests.patch(url=url, params=params, data=json.dumps(data), headers=headers).json()

    def head(self, endpoint, params=DEFAULT_PARAMS, header=DEFAULT_HEADER):
        """ Returns a dict() of the endpoint """
        url = '/'.join([self.host, endpoint, ''])
        return requests.head(url=url, params=params, headers=header).json()


class FrontendApiManager(ApiManager):
    """ Overload the ApiManager with Frontend specific jobs/options/etc """
    # Static definitions of endpoints
    ENDPOINT_JOBS = 'jobs'
    ENDPOINT_PACKAGES = 'packages'
    ENDPOINT_FILES = 'files'
    ENDPOINT_CLIENTS = 'clients'

    ENDPOINT_PACKAGEAVAILABILITY = 'packageavailability'
    ENDPOINT_PACKAGEFILEAVAILABILITY = 'fileavailability'

    def __init__(self, api_config, logger=None):
        """ Instantiate the Frontend specific vars """
        for var in ['host', 'key']:
            if not hasattr(api_config, var):
                message = 'Config file is missing \'{0}\' in the API section'.format(var)
                raise Exception(message)

        ApiManager.__init__(self, api_config.host)

        self.logger = logger
        self.DEFAULT_PARAMS['api_key'] = api_config.key

    def get_job_queue(self):
        """ Returns the job queue """
        queue = self.get(self.ENDPOINT_JOBS)

        # Add in the package's files
        for job in queue:
            job['package']['package_files'] = list()

            params = dict(self.DEFAULT_PARAMS)
            params.update({'package': job['package']['id']})

            for package_file in self.get(self.ENDPOINT_FILES, params=params):
                job['package']['package_files'].append(package_file)

            job['name'] = '{action} - {package}: {source} -> {destination}'.format(
                action=job['action'],
                package=job['package']['name'],
                source=job['source_client']['name'],
                destination=job['destination_client']['name'])

        return queue

    def associate_client_with_package(self, client_id, package_id, available):
        """
        For the given client_id and package_id
        We tie the client to the package
        """
        # Get all packages that are already tied to the client
        params = dict(self.DEFAULT_PARAMS)
        params.update({'client': client_id, 'package': package_id})
        client_package_instance = self.get(self.ENDPOINT_PACKAGEAVAILABILITY, params=params)

        data = {'availability': available}

        if client_package_instance:
            # This package is already tied to the client, just update it's availability
            endpoint = '/'.join([self.ENDPOINT_PACKAGEAVAILABILITY, client_package_instance['id']])
            return self.patch(endpoint, data, params=self.DEFAULT_PARAMS)
        else:
            # This package isn't tied to the client, insert a new entry
            data['client'] = client_id
            data['package'] = package_id
            return self.post(self.ENDPOINT_PACKAGEAVAILABILITY, data, params=self.DEFAULT_PARAMS)

    def associate_client_with_file(self, client_id, package_file_id, availability):
        """
        For the given client_id and file_id
        We tie the client to the package file
        """
        # Get all files that are already tied to the client
        params = dict(self.DEFAULT_PARAMS)
        params.update({'client': client_id, 'package_file': package_file_id})
        client_package_file_instance = self.get(self.ENDPOINT_PACKAGEFILEAVAILABILITY)

        data = {'availability': availability}

        if client_package_file_instance:
            # This package file is already tied to the client, just update it's availability
            endpoint = '/'.join([self.ENDPOINT_PACKAGEFILEAVAILABILITY, client_package_file_instance['id']])
            return self.patch(endpoint, data, params=self.DEFAULT_PARAMS)
        else:
            # This package file isn't tied to the client, insert a new entry
            data['client'] = client_id
            data['package_file'] = package_file_id
            return self.post(self.ENDPOINT_PACKAGEFILEAVAILABILITY, data, params=self.DEFAULT_PARAMS)

    def update_job(self, job_id, state):
        """
        For the given job_id, update it's state to what's provided
        """
        pass