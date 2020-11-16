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
from pathlib import Path
from tempfile import TemporaryDirectory
from util import Command

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ funcs ~~~~~~~~~~~~~|
################################################################################


def lvm_size(vg: str, lv: str) -> int:
    """Returns size in bytes of a given logical volume"""
    cmd = Command("lvs", [f"{vg}/{lv}", "-o", "LV_SIZE", "--noheadings", "--units", "B", "--nosuffix"])
    cmd.safe_run()
    if cmd.exit_code == 0 and cmd.stdout:
        return int(cmd.stdout.strip())

    return 0


def lvm_snapshot(vg: str, lv: str) -> str:
    """Creates a snapshot of a given logical volume"""
    size = lvm_size(vg, lv)
    name = f"{lv}_snapshot_{int(time.time())}"
    Command("lvcreate", ["-L", str(size) + "B", "-s", "-n", name, f"{vg}/{lv}"]).safe_run()
    return name


def lvm_remove(vg: str, lv: str):
    """Removes a logical volume"""
    Command("lvremove", ["-y", "-v", f"{vg}/{lv}"]).safe_run()


def lvm_backup(vg: str, lv: str, out_path: str):
    """Creates a snapshot of a logical volume, mounts it in temporary directory
    creates an tar gzip archive in out_path and cleans up the snapshot afterwards."""
    snapshot = lvm_snapshot(vg, lv)

    with TemporaryDirectory() as tempdir:
        inp_p = Path(tempdir) / snapshot
        out_p = Path(out_path)
        Command("mount", [f"/dev/{vg}/{lv}", str(inp_p)]).safe_run()
        Command("tar", ["-z", "-c", "-v", "-f", str(out_p / snapshot + ".tgz"), str(inp_p / "*")]).safe_run()
        Command("umount", [str(inp_p)]).safe_run()

    lvm_remove(vg, lv)
