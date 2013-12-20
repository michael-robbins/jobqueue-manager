

#
#
#
class ConfigManager():
    """
    Parses the JobQueue Manager config file returning a Config() object
    """

    required_config = {
        'MANAGER'  : ['db_type', 'db_host', 'db_port', 'db_name', 'db_user', 'db_file', 'sleep']
        , 'DAEMON' : ['pid_file', 'log_name', 'log_file', 'working_dir', 'umask']
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
    def __init__(self, config_file, logger):
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
