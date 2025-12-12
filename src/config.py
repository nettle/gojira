"""
Config parser
"""

import ast
import logging
import os


class Config(object):
    """
    Configuration class based on Python AST (Abstract Syntax Tree)
    """
    def __init__(self, config=None):
        """ Init config """
        self._config = None
        if isinstance(config, str):
            self.parse(config)

    def load(self, filename):
        """ Load config from file """
        if not os.path.exists(filename):
            logging.error("Config file '%s' does not exist", filename)
            return False
        with open(filename, "r") as config_file:
            config = config_file.read()
            return self.parse(config)
        return False

    def parse(self, config):
        """ Parse config from text """
        try:
            self._config = ast.literal_eval(config)
            return True
        except (SyntaxError, ValueError) as exception:
            logging.error("Invalid config: %s", exception)
            return False

    def get_config(self):
        """ Return config data """
        return self._config

    def get_value(self, key, section=None, default=""):
        """ Return value by key and section """
        if section and section in self.get_config():
            values = self.get_config()[section]
            if isinstance(values, dict):
                if key in values:
                    return values[key]
            return values
        else:
            if key in self.get_config():
                return self.get_config()[key]
        return default
