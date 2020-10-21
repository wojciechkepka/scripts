#!/bin/env python

################################################################################

import os
import subprocess
import sys

################################################################################

BASE_PKGS = [
    "base",
    "linux",
    "linux-firmware",
    "lvm2",
    "mdadm",
    "dhcpcd",
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

def arch_chroot(location: str):
    run("/usr/bin/arch-chroot", [location], quit=True)

################################################################################

if __name__ == "__main__":
    location = input("Enter new installation location: ")
    ask_user_yn("Generate fstab?", gen_fstab, location)
    ask_user_yn("Install base packages?", install_pkgs, location, BASE_PKGS)
    ask_user_yn("Run setup?", arch_chroot, location)
    run("ls", ["-l"])

