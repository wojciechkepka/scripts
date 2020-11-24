#!/usr/bin/env python
"""
templater

CLI tool to manage themes and configurations with multiple color schemes.
"""
################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ imports ~~~~~~~~~~~|
################################################################################

import json
import argparse
import sys

sys.path.append("../")
from util import catch_errs

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ classes ~~~~~~~~~~~|
################################################################################


class TempalterCli(object):
    @staticmethod
    def __parser():
        parser = argparse.ArgumentParser("templater", description="CLI tool to manage themes and color schemes.")
        subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

        set_parser = subparsers.add_parser("set", help="Set a theme")
        set_parser.add_argument("theme", nargs=1, help="Theme to set")

        return parser

    def __init__(self):
        self.args = self.__parser().parse_args()

    def __set(self):
        pass

    def _process_args(self):
        if self.args.command == "set":
            self.__set()

    def main(self):
        catch_errs(self._process_args)


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ main ~~~~~~~~~~~~~~|
################################################################################


if __name__ == "__main__":
    TempalterCli().main()
