#!/bin/env python
"""
exodus

CLI utility to create and manage backups.
"""
################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ imports ~~~~~~~~~~~|
################################################################################

import system
import time
import argparse
import time
import traceback
import sys
import system
import json
import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from util import Command, bash, ExecOpts, DEFAULT_OPTS, Color, outw, conv_b, eprint, measure
from typing import Any

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ funcs ~~~~~~~~~~~~~|
################################################################################


def lvm_size(vg: str, lv: str, opts: ExecOpts = DEFAULT_OPTS) -> int:
    """Returns size in bytes of a given logical volume"""
    cmd = Command("lvs", [f"{vg}/{lv}", "-o", "LV_SIZE", "--noheadings", "--units", "B", "--nosuffix"], opts=opts)
    cmd.safe_run()
    if cmd.exit_code == 0 and cmd.stdout:
        return int(cmd.stdout.strip())

    return 0


def lvm_snapshot(vg: str, lv: str, opts: ExecOpts = DEFAULT_OPTS) -> str:
    """Creates a snapshot of a given logical volume"""
    size = lvm_size(vg, lv, ExecOpts(quit=True))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = f"{vg}-{lv}_snapshot_{timestamp}"
    Command("lvcreate", ["-L", str(size) + "B", "-s", "-n", name, f"{vg}/{lv}"], opts=opts).safe_run()
    return name


def lvm_remove(vg: str, lv: str, opts: ExecOpts = DEFAULT_OPTS):
    """Removes a logical volume"""
    Command("lvremove", ["-y", f"{vg}/{lv}"], opts=opts).safe_run()


def lvm_backup(vg: str, lv: str, out_p: Path, verbose: bool = True) -> Path:
    """Creates a snapshot of a logical volume, mounts it in temporary directory
    creates an tar gzip archive in out_path and cleans up the snapshot afterwards.
    Returns a path to final archive containing backed up files."""
    opts = ExecOpts(quit=True, collect=False)
    system.install_pkg_if_bin_not_exists("tar")
    system.install_pkg_if_bin_not_exists("pigz")
    try:
        snapshot = lvm_snapshot(vg, lv, opts=opts)
        out_p = out_p / (snapshot + ".tgz")

        with TemporaryDirectory() as tempdir:
            inp_p = Path(tempdir) / snapshot
            inp_p.mkdir(parents=True)
            try:
                Command("mount", [f"/dev/{vg}/{snapshot}", str(inp_p)], opts=opts).safe_run()
                flags = "-cvf" if verbose else "-cf"
                bash(f"cd {str(inp_p)} && tar -I pigz {flags} {str(out_p)} ./*", quit=True)
            finally:
                Command("umount", [f"/dev/{vg}/{snapshot}"], opts=opts).safe_run()
    finally:
        if "snapshot" in locals():
            lvm_remove(vg, snapshot)

    return out_p


def _print_backup_result(device: str, outfile: Path, time: float):
    outw("~" * 50, "\n")
    outw(Color.RED, device, Color.NC, "\n")
    outw("\t", Color.BWHITE, "Finished backup in: ", Color.YELLOW, f"{time:.2f}", "s", Color.NC, "\n")
    outw("\t", Color.BWHITE, "Final backup size: ", Color.YELLOW, conv_b(outfile.stat().st_size), Color.NC, "\n")
    outw("\t", Color.BWHITE, "Output file: ", Color.YELLOW, outfile, Color.NC, "\n")


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ classes ~~~~~~~~~~~|
################################################################################


class Exodus(object):
    @staticmethod
    def __parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="exodus", description="Backup utility")
        subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)
        parser.add_argument("--verbose", dest="verbose", action="store_true")
        parser.add_argument("--no-color", dest="no_color", action="store_true")

        lvm_parser = subparsers.add_parser("lvm")
        lvm_parser.add_argument(
            "vg",
            nargs=1,
            type=str,
            help="Name of volume group containing the logical volume to backup",
        )
        lvm_parser.add_argument("lv", nargs=1, type=str, help="Logical volume to backup")
        lvm_parser.add_argument("out", nargs=1, type=Path, help="Output path where final archive will be stored")

        backup_parser = subparsers.add_parser("backup")
        backup_parser.add_argument("config", nargs=1, type=Path, help="Location of config file")

        return parser

    def __init__(self):
        self.args = self.__parser().parse_args()

    def __lvm(self):
        vg = self.args.vg[0]
        lv = self.args.lv[0]
        (out, t) = measure(lvm_backup, vg, lv, self.args.out[0], verbose=self.args.verbose)
        _print_backup_result(f"{vg}/{lv}", out, t)

    @staticmethod
    def __backup_validate_conf(conf: Any):
        if not isinstance(conf, dict):
            eprint("Invalid configuration file - file is not a json map")
            exit(1)

        if not "devices" in conf.keys():
            eprint("Invalid configuration file - missing `devices` field")
            exit(1)
        else:
            if not isinstance(conf["devices"], list):
                eprint("Invalid configuration file - `devices` field should be a list")
                exit(1)

            for device in conf["devices"]:
                if not isinstance(device, dict):
                    eprint("Invalid device in configuration - not a map")
                    pass
                if not "name" in device.keys():
                    eprint("Invalid device in configuration - missing `name` field")
                if not "vol-group" in device.keys():
                    eprint("Invalid device in configuration - missing `vol-group` field")

        if not "output_path" in conf.keys():
            eprint(f"Invalid configuration file - missing `output_path` field")
            exit(1)
        else:
            if not isinstance(conf["output_path"], str):
                eprint(f"Invalid configuration file - `output_path` should be a string")
                exit(1)

    def __backup(self):
        """Runs all backups specified in config file.
        Current format is a json file with multiple logical volumes in a list.
        For example:
        {
            "output_path": "/mnt/backup",
            "devices":  [
                    {
                        "name": "root",
                        "vol-group": "vgsystem"
                    },
                    {
                        "name": "home",
                        "vol-group": "vghome"
                    }
            ]
        }
        """
        with self.args.config[0].open("r") as f:
            conf = json.load(f)
            self.__backup_validate_conf(conf)
            results = []

            for device in conf["devices"]:
                results.append(
                    measure(
                        lvm_backup,
                        device["vol-group"],
                        device["name"],
                        Path(conf["output_path"]),
                        verbose=self.args.verbose,
                    )
                )

            for ((out, t), device) in zip(results, conf["devices"]):
                _print_backup_result(f"{device['vol-group']}/{device['name']}", out, t)

    def main(self):
        try:
            if self.args.no_color == True:
                Color.disable()

            if self.args.command == "lvm":
                self.__lvm()
            elif self.args.command == "backup":
                self.__backup()
        except KeyboardInterrupt:
            print(f"\n{Color.BWHITE}Exiting...{Color.NC}")
            sys.exit(0)
        except Exception:
            eprint(f"{Color.BWHITE}Unhandled exception{Color.NC}\n")
            eprint(f"{traceback.format_exc()}")
            sys.exit(1)


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ main ~~~~~~~~~~~~~~|
################################################################################

if __name__ == "__main__":
    Exodus().main()
