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
import traceback
import time
from pathlib import Path
from typing import Dict, Optional, Any
from tempfile import TemporaryDirectory

sys.path.append(str(Path(__file__).absolute().parent.parent) + "/")
from util import catch_errs, Color, eprint, Command, bash, ExecOpts
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
        self.config = self._read_config_file(self.args.config[0])
        self.theme = self._get_theme(self.args.theme[0])
        self.defaults = self._get_theme("default") if "default" in self.config["themes"].keys() else {}

    @staticmethod
    def _read_config_file(location: Path) -> Config:
        try:
            with location.open() as f:
                var = yaml.load(f, Loader=yaml.Loader)
                if isinstance(var, dict):
                    return var
        except yaml.YAMLError as e:
            eprint(f"Invalid configuration file at {Color.BWHITE}`{location}`{Color.RED} - {e}")
            sys.exit(1)
        except Exception as e:
            eprint(f"Failed reading configuration file from {Color.BWHITE}`{location}`{Color.RED}` - {e}")
            sys.exit(1)

        return {}

    def _get_theme(self, theme: str) -> Dict[str, str]:
        if "themes" not in self.config.keys():
            eprint(f"Missing {Color.BWHITE}`themes`{Color.RED} in configuration")
            sys.exit(1)

        themes = self.config["themes"]

        if theme not in themes:
            eprint(f"Missing theme {Color.BWHITE}`{theme}`{Color.RED} in configuration")
            sys.exit(1)

        if not isinstance(themes[theme], dict):
            eprint(
                f"Invalid configuration for {Color.BWHITE}`{theme}`{Color.RED}"
                " - theme configuration should be a key value map of strings"
            )
            sys.exit(1)

        return self.config["themes"][theme]

    def _render_file(self, file: Path) -> str:
        with open(file, "r") as f:
            text = f.read()
            return Templater(text, self.theme, default=self.defaults).render()

    def __render(self):
        print(self._render_file(self.args.file[0]))

    def __run(self):
        if "files" not in self.config.keys():
            eprint(f"Missing {Color.BWHITE}`files`{Color.NC} in configuration")
            sys.exit(1)

        with TemporaryDirectory() as tempdir:
            try:
                for (inp_p, out_p) in self.config["files"].items():
                    p = Path(out_p)

                    if p.is_dir():
                        eprint(f"Output path {Color.YELLOW}`{out_p}`{Color.RED} is a directory, skipping.\n")
                        continue

                    if p.exists():
                        print(
                            f"{Color.BWHITE}Backing up {Color.YELLOW}`{p}`{Color.BWHITE}, file already exists.{Color.NC}"
                        )
                        Command(
                            "cp", [out_p, str(Path(tempdir) / p.name)], opts=ExecOpts(follow=False, display=False)
                        ).safe_run()

                    print(
                        f"{Color.BWHITE}Rendering {Color.YELLOW}`{inp_p}`{Color.RED} ~~~~~> {Color.YELLOW}`{out_p}`{Color.NC}"
                    )
                    try:
                        rendered = self._render_file(Path(inp_p))
                        with open(out_p, "w") as f:
                            f.write(rendered)
                    except Exception as e:
                        eprint(f"Failed rendering file {Color.YELLOW}`{inp_p}`{Color.RED} - {e}\n")
            finally:
                print(f"{Color.BWHITE}Creating archive of backed up configs{Color.NC}")
                bash(
                    f"export START=$PWD && cd {tempdir} && tar -zcf $START/templater_backup_{int(time.time())}.tgz . > /dev/null 2>&1"
                )

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
