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
import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from util import Command, bash, ExecOpts, DEFAULT_OPTS, Color, outw, conv_b, eprint

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
    size = lvm_size(vg, lv, opts=opts)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = f"{lv}_snapshot_{timestamp}"
    Command("lvcreate", ["-L", str(size) + "B", "-s", "-n", name, f"{vg}/{lv}"], opts=opts).safe_run()
    return name


def lvm_remove(vg: str, lv: str, opts: ExecOpts = DEFAULT_OPTS):
    """Removes a logical volume"""
    Command("lvremove", ["-y", f"{vg}/{lv}"], opts=opts).safe_run()


def lvm_backup(vg: str, lv: str, out_p: Path) -> Path:
    """Creates a snapshot of a logical volume, mounts it in temporary directory
    creates an tar gzip archive in out_path and cleans up the snapshot afterwards.
    Returns a path to final archive containing backed up files."""
    opts = ExecOpts(quit=True)
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
                bash(f"cd {str(inp_p)} && tar -I pigz -cvf {str(out_p)} ./*", quit=True)
            finally:
                Command("umount", [f"/dev/{vg}/{snapshot}"], opts=opts).safe_run()
    finally:
        if "snapshot" in locals():
            lvm_remove(vg, snapshot)

    return out_p


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ classes ~~~~~~~~~~~|
################################################################################


class Exodus(object):
    @staticmethod
    def __parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="exodus", description="Backup utility")
        subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

        lvm_parser = subparsers.add_parser("lvm")
        lvm_parser.add_argument(
            "vg",
            nargs=1,
            type=str,
            help="Name of volume group containing the logical volume to backup",
        )
        lvm_parser.add_argument("lv", nargs=1, type=str, help="Logical volume to backup")
        lvm_parser.add_argument("out", nargs=1, type=Path, help="Output path where final archive will be stored")

        return parser

    def __init__(self):
        self.args = self.__parser().parse_args()

    def main(self):
        try:
            if self.args.command == "lvm":
                start = time.time()
                out = lvm_backup(self.args.vg[0], self.args.lv[0], self.args.out[0])
                end = time.time()
                outw("~" * 50, "\n")
                outw(Color.BWHITE, "Finished backup in: ", Color.YELLOW, f"{end - start:.2f}", "s", Color.NC, "\n")
                outw(Color.BWHITE, "Final backup size: ", Color.YELLOW, conv_b(out.stat().st_size), Color.NC, "\n")
                outw(Color.BWHITE, "Output file: ", Color.YELLOW, out, Color.NC)
        except KeyboardInterrupt:
            print(f"\n{Color.BWHITE}Exiting...{Color.NC}")
            sys.exit(0)
        except Exception:
            eprint(f"{Color.BWHITE}Unhandled exception{Color.NC}\n")
            eprint(f"{Color.RED}{traceback.format_exc()}{Color.NC}")
            sys.exit(1)


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ main ~~~~~~~~~~~~~~|
################################################################################

if __name__ == "__main__":
    Exodus().main()
