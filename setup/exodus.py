#!/bin/env python
"""
backup

module grouping functions related to operating with backups.
"""
################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ imports ~~~~~~~~~~~|
################################################################################

import system
import time
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from util import Command, bash, ExecOpts, DEFAULT_OPTS

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
    name = f"{lv}_snapshot_{int(time.time())}"
    Command("lvcreate", ["-L", str(size) + "B", "-s", "-n", name, f"{vg}/{lv}"], opts=opts).safe_run()
    return name


def lvm_remove(vg: str, lv: str, opts: ExecOpts = DEFAULT_OPTS):
    """Removes a logical volume"""
    Command("lvremove", ["-y", "-v", f"{vg}/{lv}"], opts=opts).safe_run()


def lvm_backup(vg: str, lv: str, out_p: Path):
    """Creates a snapshot of a logical volume, mounts it in temporary directory
    creates an tar gzip archive in out_path and cleans up the snapshot afterwards."""
    opts = ExecOpts(quit=True)
    snapshot = lvm_snapshot(vg, lv, opts=opts)

    with TemporaryDirectory() as tempdir:
        inp_p = Path(tempdir) / snapshot
        inp_p.mkdir(parents=True)
        Command("mount", [f"/dev/{vg}/{snapshot}", str(inp_p)], opts=opts).safe_run()
        bash(f"cd {str(inp_p)} && tar -zcvf {str(out_p / (snapshot + '.tgz'))} ./*", quit=True)
        Command("umount", [str(inp_p)], opts=opts).safe_run()

    lvm_remove(vg, snapshot)


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ main ~~~~~~~~~~~~~~|
################################################################################

if __name__ == "__main__":
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

    args = parser.parse_args()

    if args.command == "lvm":
        lvm_backup(args.vg[0], args.lv[0], args.out[0])
