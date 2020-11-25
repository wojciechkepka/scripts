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
import yaml
from pathlib import Path
from typing import Dict, Optional, Any

sys.path.append("../")
from util import catch_errs
from templater import Templater

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ classes ~~~~~~~~~~~|
################################################################################

Config = Dict[str, Any]
ThemesConfig = Dict[str, Dict[str, str]]


class TempalterCli(object):
    @staticmethod
    def __parser():
        parser = argparse.ArgumentParser("templater", description="CLI tool to manage themes and color schemes.")
        subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

        render_parser = subparsers.add_parser("render", help="Render a file")
        render_parser.add_argument("file", nargs=1, type=Path, help="File to render")
        render_parser.add_argument("config", nargs=1, type=Path, help="File containing configuration for themes etc.")
        render_parser.add_argument("theme", nargs=1, type=str, help="Theme that will be used to render this file")

        run_parser = subparsers.add_parser("run", help="Run templater with config file rendering all specified files")
        run_parser.add_argument("config", nargs=1, type=Path, help="File containing configuration for themes etc.")
        run_parser.add_argument("theme", nargs=1, type=str, help="Theme that will be used to render all files")

        return parser

    def __init__(self):
        self.args = self.__parser().parse_args()

    @staticmethod
    def _read_config_file(location: Path) -> Config:
        with location.open() as f:
            var = yaml.load(f, Loader=yaml.Loader)
            if isinstance(var, dict):
                return var

        return {}

    @staticmethod
    def _get_theme(theme: str, config: Config) -> Dict[str, str]:
        if "themes" in config.keys():
            themes = config["themes"]
            if theme in themes and isinstance(themes[theme], dict):
                return config["themes"][theme]

        return {}

    def __render(self):
        with open(self.args.file[0], "r") as f:
            text = f.read()
            config = self._read_config_file(self.args.config[0])
            theme = self._get_theme(self.args.theme[0], config)
            print(Templater(text, theme).render())

    def __run(self):
        config = self._read_config_file(self.args.config[0])
        theme = self._get_theme(self.args.theme[0], config)
        if "files" in config.keys():
            for (inp_p, out_p) in config["files"].items():
                print(f"Processing file {inp_p}")
                f = open(inp_p, "r")
                text = f.read()
                f.close()

                with open(out_p, "w") as f:
                    f.write(Templater(text, theme).render())

    def _process_args(self):
        if self.args.command == "render":
            self.__render()
        elif self.args.command == "run":
            self.__run()

    def main(self):
        catch_errs(self._process_args)


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ main ~~~~~~~~~~~~~~|
################################################################################


if __name__ == "__main__":
    TempalterCli().main()
