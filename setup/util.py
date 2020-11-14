#!/bin/env python
"""
Util

Utility funcs for creating interactive cli scripts
"""
################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ imports ~~~~~~~~~~~|
################################################################################

import sys
import subprocess
import termios
import tty
from typing import List
from pathlib import Path

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ globals ~~~~~~~~~~~|
################################################################################

LBLUE = "\033[1;94m"
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
BWHITE = "\033[1;37m"
NC = "\033[0m"

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ funcs ~~~~~~~~~~~~~|
################################################################################


def eprint(msg: str):
    """Prints a message to stderr in red color."""
    sys.stderr.write(RED + msg + NC)


def inp(msg: str) -> str:
    """Takes input from user printing msg first."""
    sys.stdout.write(BWHITE + msg + CYAN)
    inp = input()
    sys.stdout.write(NC)
    return inp


def inp_or_default(msg: str, default) -> str:
    """Asks user for input printing msg first. If users input is empty uses default as return"""
    x = inp(msg + f"(default - '{YELLOW}{default}{NC}'): ")
    return x if x else default


def run(cmd: str, args: List[str], display=True, quit=False, redirect=False, follow=True):
    """Runs specified cmd with args in a subprocess.
    If redirect is true stdout and stderr will be redirected directly to main processes fd.
    If follow is true the output of subprocess will be printed as it is filled.
    If quit is true and returncode was other than 0 main process exits with returncode.
    If display is false all output will be hidden"""
    s = f"{LBLUE}{cmd} {' '.join(args)}{NC}"
    print(f"{BWHITE}Running{NC} `{s}`")
    try:
        p = (
            subprocess.Popen([cmd] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not redirect
            else subprocess.Popen([cmd] + args, stdout=sys.stdout, stderr=sys.stderr)
        )
        if follow and display:
            sys.stdout.write(GREEN)
            for c in iter(lambda: p.stdout.read(1), b""):
                try:
                    sys.stdout.write(c.decode("utf-8"))
                except:
                    pass
            sys.stderr.write(RED)
            for c in iter(lambda: p.stderr.read(1), b""):
                try:
                    sys.stderr.write(c.decode("utf-8"))
                except:
                    pass
            sys.stdout.write(NC)
            sys.stderr.write(NC)
        else:
            (stdout, stderr) = p.communicate()
            if p.returncode != 0:
                if display and stderr:
                    eprint("ERROR: " + stderr.decode("utf-8"))
            else:
                if display and stdout:
                    sys.stdout.write(GREEN + stdout.decode("utf-8") + NC)

        if p.returncode != 0 and quit:
            sys.exit(p.returncode)

    except Exception as e:
        sys.stderr.write(f"{BWHITE}Failed running command{NC} `{s}` - {RED}{e}{NC}")


def bash(cmd: str, quit=False):
    """Executes a bash script as a subprocess"""
    run("/bin/bash", ["-c", cmd], quit=quit)


def ask_user_yn(msg: str, f, *args, ask=True):
    """Asks user for y/n choice on msg. If the answer is yes calls function f with *args"""
    sys.stdout.write(BWHITE + msg + f" {GREEN}y(es){NC}/{RED}n(o){NC}/{YELLOW}q(uit){NC}: ")
    sys.stdout.flush()
    if ask:
        while True:
            ch = getch()
            if ch == "y":
                sys.stdout.write(CYAN + ch + "\n" + NC)
                f(*args)
                break
            elif ch == "n":
                sys.stdout.write(CYAN + ch + "\n" + NC)
                break
            elif ch == "q":
                sys.stdout.write(CYAN + ch + "\n" + NC)
                raise KeyboardInterrupt
    else:
        sys.stdout.write(CYAN + "y\n" + NC)
        f(*args)


def steps(s, ask=True):
    """Executes a list of steps asking the user for choice on each step"""
    for step in s:
        if len(step) > 2:
            ask_user_yn(step[0], step[1], *step[2:], ask=ask)
        else:
            ask_user_yn(step[0], step[1], ask=ask)


def getch():
    """Gets a raw character from terminal"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def fwrite(p: Path, s: str):
    """Writes s to a file in path p"""
    with open(p, "w") as f:
        print(f"{BWHITE}Writing{NC} `{s}` to {LBLUE}`{str(p)}`{NC}")
        f.write(s)
