#!/usr/bin/env python3

import os
import sys

import json
import requests


class ApiManager():
    """
    Handles all interactions with the API
    """

    JSON_HEADER = {'content-type': 'application/json'}
    KEY_VAR = 'api_key={0}'

    # Static definitions of endpoints?
    JOBS = 'jobs'

    def __init__(self, api_config, logger):
        """
        Setup the API connection & logger
        """

        self.logger = logger

        for var in ['host', 'key']:
            if hasattr(api_config, var):
                setattr(self, var, getattr(api_config, var))
            else:
                message = 'Config file is missing \'{0}\' in the API section'.format(var)
                raise Exception(message)

    def build_url(self, endpoint):
        """
        Builds the full URL based off:
        * Base URL
        * Endpoint
        * API Key

            |-  base url  -| |- ep -| |- API Key -|
        Eg. https://base.url/endpoint?apikey=123abc
        """

        url = '{0}/{1}'.format(self.host, endpoint)

        api_key = self.KEY_VAR.format(self.key)

        return url + '?' + '&'.join([api_key])


    ##################
    # API Operations #
    ##################

    def get(self, endpoint):
        """
        Returns a dict() of the endpoint
        """
        url = self.build_url(endpoint)

        data = requests.get(url=url, headers=self.JSON_HEADER).json()

        return data

    def put(self, endpoint, data):
        """
        Returns a modified object or None
        """
        url = self.build_url(endpoint)

        return_data = requests.put(url, data=data)

        return return_data

    def patch(self, endpoint):
        """
        Returns a modified field or None
        """
        url = self.build_url(endpoint)

        return url

    def head(self, endpoint):
        """
        Returns a dict() of the endpoint
        """
        url = self.build_url(endpoint)

        data = requests.head(url=url, headers=self.JSON_HEADER).json()

        return data
