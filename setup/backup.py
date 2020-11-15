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
from util import run, run_ret

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ funcs ~~~~~~~~~~~~~|
################################################################################


def lvm_size(vg: str, lv: str) -> int:
    """Returns size in bytes of a given logical volume"""
    result = run_ret("lvs", [f"{vg}/{lv}", "-o", "LV_SIZE", "--noheadings", "--units", "B", "--nosuffix"])
    if not result.is_err() and result.stdout:
        return int(result.stdout.strip())

    return 0


def lvm_snapshot(vg: str, lv: str) -> str:
    """Creates a snapshot of a given logical volume"""
    size = lvm_size(vg, lv)
    name = f"{lv}_snapshot_{int(time.time())}"
    run("lvcreate", ["-L", str(size) + "B", "-s", "-n", name, f"{vg}/{lv}"])
    return name


def lvm_remove(vg: str, lv: str):
    """Removes a logical volume"""
    run("lvremove", ["-y", "-v", f"{vg}/{lv}"])


def lvm_backup(vg: str, lv: str, out_path: str):
    """Creates a snapshot of a logical volume, mounts it in temporary directory
    creates an tar gzip archive in out_path and cleans up the snapshot afterwards."""
    snapshot = lvm_snapshot(vg, lv)

    with TemporaryDirectory() as tempdir:
        inp_p = Path(tempdir) / snapshot
        out_p = Path(out_path)
        run("mount", [f"/dev/{vg}/{lv}", str(inp_p)])
        run("tar", ["-z", "-c", "-v", "-f", str(out_p / snapshot + ".tgz"), str(inp_p / "*")])
        run("umount", [str(inp_p)])

    lvm_remove(vg, lv)
