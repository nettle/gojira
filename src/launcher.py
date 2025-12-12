""" Launcher """

import argparse
import logging

import component
import config
import gerrit


PROGNAME = "gojira"
EXAMPLES = """
examples:

   FIXME!!!
"""
CONFIG_FILE = PROGNAME + ".cfg"


class Launcher:
    """ Main launcher: parse argument and run application """
    def __init__(self):
        """ Launcher constructor """
        self.options = None
        self.command = None

    def common_arguments(self, parser, add_help=False):
        """ Add common arguments """
        group = parser.add_argument_group("global options")
        if add_help:
            group.add_argument(
                "-h", "--help",
                action="help",
                help="show this help message and exit")
        group.add_argument(
            "-v", "--verbosity",
            default=0,
            action="count",
            help="increase output verbosity (e.g., -v or -vv)")
        group.add_argument(
            "--config",
            default=CONFIG_FILE,
            help=f"config file (default: {CONFIG_FILE})")
        group.add_argument(
            "--log-format",
            default=f"[{PROGNAME}] %(levelname)5s: %(message)s",
            help=argparse.SUPPRESS)

    def parse_arguments(self):
        """ Parse command line arguments or show help """
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            add_help=False,
            prog=PROGNAME,
            description=__doc__,
            epilog=EXAMPLES)
        subparsers = parser.add_subparsers(
            title="commands",
            dest="command")

        # Argument parser for Gerrit
        parser_gerrit = subparsers.add_parser(
            "gerrit",
            help="Run Gerrit statistics")
        gerrit.add_arguments(parser_gerrit)
        self.common_arguments(parser_gerrit)

        # Argument parser for Jira
        parser_jira = subparsers.add_parser(
            "jira",
            help="Run Jira statistics")
        component.add_arguments(parser_jira)
        self.common_arguments(parser_jira)

        self.common_arguments(parser, add_help=True)

        self.options = parser.parse_args()
        self.command = self.options.command
        if self.options.verbosity >= 2:
            log_level = logging.DEBUG
        elif self.options.verbosity >= 1:
            log_level = logging.INFO
        else:
            log_level = logging.WARN
        logging.basicConfig(level=log_level, format=self.options.log_format)

        logging.debug("Options: %s", self.options)
        logging.debug("Command: %s", self.command)

        config_file = config.Config()
        if config_file.load(self.options.config):
            logging.info("Using configuration from: %s", self.options.config)
            config_data = config_file.get_config()
            logging.debug("Config: %s", config_data)
            if "team" in config_data:
                self.options.team = config_data["team"]
            if self.command == "gerrit" and "gerrit" in config_data:
                if "url" in config_data["gerrit"]:
                    self.options.url = config_data["gerrit"]["url"]
            if self.command == "jira" and "jira" in config_data:
                if "url" in config_data["jira"]:
                    self.options.url = config_data["jira"]["url"]
                if "project" in config_data["jira"]:
                    self.options.project = config_data["jira"]["project"]
                if "component" in config_data["jira"]:
                    self.options.component = config_data["jira"]["component"]
                if "prefix" in config_data["jira"]:
                    self.options.prefix = config_data["jira"]["prefix"]
            logging.debug("Updated: %s", self.options)


    def run(self):
        """ Parse arguments and run the command """
        self.parse_arguments()
        if self.command == "gerrit":
            logging.info("Running Gerrit statistics...")
            gerrit.run(self.options)
        elif self.command == "jira":
            logging.info("Running Jira statistics...")
            component.run(self.options)
        else:
            logging.error("Unrecognized command: %s", self.command)
        return 0
