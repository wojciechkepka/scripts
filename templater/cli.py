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
from pathlib import Path
from typing import Dict

sys.path.append("../")
from util import catch_errs
from templater import Templater

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ classes ~~~~~~~~~~~|
################################################################################

Variables = Dict[str, Dict[str, str]]


class TempalterCli(object):
    @staticmethod
    def __parser():
        parser = argparse.ArgumentParser("templater", description="CLI tool to manage themes and color schemes.")
        subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

        render_parser = subparsers.add_parser("render", help="Render a file")
        render_parser.add_argument("file", nargs=1, type=Path, help="File to render")
        render_parser.add_argument(
            "variables", nargs=1, type=Path, help="File containing a map of values for each theme"
        )
        render_parser.add_argument("theme", nargs=1, type=str, help="Theme that will be used to render this file")

        return parser

    def __init__(self):
        self.args = self.__parser().parse_args()

    @staticmethod
    def _read_variables_file(location: Path) -> Variables:
        with location.open() as f:
            var = json.load(f)
            if isinstance(var, dict):
                return var

        return {}

    def __render(self):
        with open(self.args.file[0], "r") as f:
            text = f.read()
            variables = self._read_variables_file(self.args.variables[0])
            print(Templater(text, variables[self.args.theme[0]]).render())

    def _process_args(self):
        if self.args.command == "render":
            self.__render()

    def main(self):
        catch_errs(self._process_args)


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ main ~~~~~~~~~~~~~~|
################################################################################


if __name__ == "__main__":
    TempalterCli().main()
