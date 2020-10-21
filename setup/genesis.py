#!/bin/env python

################################################################################

import os
import subprocess
import sys
from pathlib import Path

################################################################################

BASE_PKGS = [
    "base",
    "linux",
    "linux-firmware",
    "lvm2",
    "mdadm",
    "dhcpcd",
    "python",
]


################################################################################


def eprint(msg: str):
    sys.stderr.write(msg)


def run(cmd: str, args: [str], display=True, quit=False):
    print(f"Running `{cmd} {' '.join(args)}`")
    p = subprocess.Popen([cmd] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if p.returncode != 0:
        if display:
            eprint("ERROR: " + stderr.decode("utf-8"))
        if quit:
            sys.exit(1)
    else:
        if display:
            print(stdout.decode("utf-8"))


def bash(cmd: str, quit=False):
    run("/bin/bash", ["-c", cmd], quit=quit)


def ask_user_yn(msg: str, f, *args):
    sys.stdout.write(msg + " y/n: ")
    while True:
        resp = input()
        if resp == "y":
            f(*args)
            return
        elif resp == "n":
            return


################################################################################


def gen_fstab(location: str):
    bash(f"/usr/bin/genfstab -U {location} >> {location}/etc/fstab", quit=True)


def install_pkgs(location: str, pkgs: [str]):
    run("/usr/bin/pacstrap", [location] + pkgs, quit=True)


def arch_chroot(location: str, cmd: str):
    run("/usr/bin/arch-chroot", [location, "/bin/bash", "-c", cmd], quit=True)


def copy_self(location: str):
    current_location = Path(__file__).absolute()
    filename = Path(__file__)

    run("/usr/bin/cp", [current_location, f"{location}/{filename}"])


def init_setup(location: str):
    filename = Path(__file__)

    copy_self(location)
    arch_chroot(location, f"python {filename} setup")


def setup():
    print("Setup!")


################################################################################

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            f"USAGE: \
        {Path(__file__)} <init | setup>"
        )
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        location = input("Enter new installation location: ")
        ask_user_yn("Generate fstab?", gen_fstab, location)
        ask_user_yn("Install base packages?", install_pkgs, location, BASE_PKGS)
        ask_user_yn("Run setup?", arch_chroot, location, f"{Path(__file__)} setup")
        init_setup(location)
    elif cmd == "setup":
        setup()
