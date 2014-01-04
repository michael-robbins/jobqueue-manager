#
#
#
class ConfigManager():
    """
    Parses the JobQueue Manager config file returning a Config() object
    """

    required_config = {
        'MANAGER'  : ['db_type', 'db_name', 'db_user', 'sleep']
        , 'DAEMON' : ['pid_file', 'log_name', 'log_file', 'working_dir', 'umask']
        }

    additional_config = {
        'db_type'  : {
                'sqlite3': ['db_file']
                , 'psql' : ['db_host', 'db_port']
            }
        }

    class ConfigMissingPart(Exception):
        """
        What happens when config_file is missing something
        """

    class ConfigFileMissing(Exception):
        """
        What happens when the config_file is missing
        """


    #
    #
    #
    def __init__(self, config_file):
        """
        Parse config file
        """

        import configparser
        self.config = configparser.ConfigParser()

        try:
            with open(config_file, 'r') as f:
                self.config.read(config_file)
        except IOError as e:
            raise ConfigFileMissing("Something wrong with config_file: " + config_file)

        # Add in the extra 'self.additional_config' parameters if required
        for section in self.required_config:
            for option in self.required_config[section]:
                if option in self.additional_config and option in self.config.options(section)
                    # if the option has extra paramaters based (E.g. DB Type)
                    self.required_config[section].append(
                            self.additional_config[option][self.config[section][option]]
                        )

        # Run through everything (post additional config additions) and check it all exists
        for section in self.required_config:
            if section not in self.config.sections():
                message = "Config File is missing section: " + section
                self.config = None
                raise ConfigMissingPart(message)
            else:
                for option in self.required_config[section]:
                    if option not in self.config.options(section):
                        self.config = None
                        raise ConfigMissingPart("Config file is missing option: " + option)


    #
    #
    #
    def get_config(self):
        """
        Return ConfigParser() object
        """
        if self.config:
            return self.config
        else:
            return None
