#!/usr/bin/env python3

import os
import sys

import json
import requests


class ApiManager():
    """ Handles all interactions with the API """

    JSON_HEADER = {'content-type': 'application/json'}
    KEY_VAR = 'api_key={0}'

    def __init__(self, host, key):
        """ Setup the API connection """

        self.host = host
        self.api_key = self.KEY_VAR.format(key)

    @staticmethod
    def build_url(base_url, endpoint, get_vars=None):
        """
        Builds the full URL based off:
        * Base URL
        * Endpoint
        * API Key

            |-  base url  -| |- ep -| |- API Key -|
        Eg. https://base.url/endpoint?apikey=123abc
        """

        url = '{0}/{1}/'.format(base_url, endpoint)

        if get_vars:
            url += '?' + '&'.join(get_vars)

        return url

    # API Operations
    def get(self, endpoint):
        """ Returns a dict() of the endpoint """

        url = self.build_url(self.host, endpoint, [self.api_key])

        data = requests.get(url=url, headers=self.JSON_HEADER).json()

        return data

    def put(self, endpoint, data):
        """ Returns a modified object or None """
        url = self.build_url(self.host, endpoint, [self.api_key])

        return_data = requests.put(url, data=data, headers=self.JSON_HEADER).json()

        return return_data

    def patch(self, endpoint):
        """ Returns a modified field or None """
        url = self.build_url(self.host, endpoint, [self.api_key])

        return url

    def head(self, endpoint):
        """ Returns a dict() of the endpoint """
        url = self.build_url(self.host, endpoint, [self.api_key])

        data = requests.head(url=url, headers=self.JSON_HEADER).json()

        return data


class FrontendApiManager(ApiManager):
    """ Overload the ApiManager with Frontend specific jobs/options/etc """
    # Static definitions of endpoints
    ENDPOINT_JOBS = 'jobs'
    ENDPOINT_PACKAGES = 'packages'
    ENDPOINT_FILES = 'files'
    ENDPOINT_CLIENTS = 'clients'

    def __init__(self, api_config, logger=None):
        """ Instantiate the Frontend specific vars """
        for var in ['host', 'key']:
            if not hasattr(api_config, var):
                message = 'Config file is missing \'{0}\' in the API section'.format(var)
                raise Exception(message)

        ApiManager.__init__(self, api_config.host, api_config.key)

        self.logger = logger

    def get_job_queue(self):
        """ Returns the job queue """
        package_files = self.get(self.ENDPOINT_FILES)
        queue = self.get(self.ENDPOINT_JOBS)

        # Resolve all the Primary Key's to objects
        for job in queue:
            job['package']['package_files'] = list()

            for package_file in package_files:
                if package_file['package'] == job['package']['id']:
                    job['package']['package_files'].append(package_file)

            job['name'] = '{0} - {1}: {2} -> {3}'.format(job['action']
                                                         , job['package']['name']
                                                         , job['source_client']['name']
                                                         , job['destination_client']['name'])
        return queue
