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
        self.config = api_config

    def perform_request(self):
        pass

    def build_url(self, endpoint):
        pass

    # API Operations
    def get(self, endpoint):
        """
        Returns a dict() of the endpoint
        """
        pass

    def put(self, endpoint):
        """
        Returns a modified object or None
        """
        pass

    def patch(self, endpoint):
        """
        Returns a modified field or None
        """
        pass

    def head(self, endpoint):
        """
        Returns a dict() of the endpoint
        """
        pass
