import sys

class ConfigManager():
    """
    Parses the JobQueue Manager config file returning a Config() object
    """

    DAEMON = 'DAEMON';
    DB     = 'DB';

    default_config = {
        DAEMON : ['pid_file', 'log_name', 'log_file', 'working_dir', 'umask', 'sleep']
        , DB   : ['db_type', 'db_name', 'db_user']
        }

    additional_config = {
        'db_type'  : {
                'sqlite3': ['db_file']
                , 'psql' : ['db_host', 'db_port']
            }
        }

    class Config():
        """
        Holds all the configuration sections
        """
        pass

    class Section():
        """
        Holds the configuration objects for a specific section
        """
        pass

    def __init__(self, config_file):
        """
        Parse config file and build a Config object
        """

        import configparser
        self.config_parser = configparser.ConfigParser()
       
        self.config = ConfigManager.Config()

        try:
            with open(config_file, 'r') as f:
                self.config_parser.read(config_file)
        except IOError as e:
            print("ERROR: Something is wrong with the config file: {0}".format(config_file))
            sys.exit(1)

        # Add in the extra 'self.additional_config' parameters if required
        for section in self.default_config:
            for option in self.default_config[section]:
                if option in self.additional_config and option in self.config_parser.options(section):
                    # if the option has extra paramaters based (E.g. DB Type)
                    for i in self.additional_config[option][self.config_parser[section][option]]:
                        self.default_config[section].append(i)

        # Run through everything (post additional config additions) and check it all exists
        for section in self.default_config:
            if section not in self.config_parser.sections():
                message = "Config File is missing section: " + section
                print("ERROR: The config file is missing the seciont: {0}".format(section))
                sys.exit(1)
            else:
                setattr(self.config, section, ConfigManager.Section())
                for option in self.default_config[section]:
                    if option not in self.config_parser.options(section):
                        print("ERROR: Missing config {0} option {1}".format(section, option))
                        sys.exit(1)
                    else:
                        setattr(
                                getattr(self.config, section)
                                , option
                                , self.config_parser[section][option])

    def get_config(self):
        """
        Return ConfigParser() object
        """
        if self.config:
            return self.config
        else:
            return None

if __name__ == '__main__':
    from tester import TestManager
    tester = TestManager()
    tester.test_ConfigManager()
