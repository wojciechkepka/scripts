#!/bin/env python

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
    sys.stderr.write(RED + msg + NC)


def inp(msg: str) -> str:
    sys.stdout.write(BWHITE + msg + CYAN)
    inp = input()
    sys.stdout.write(NC)
    return inp


def inp_or_default(msg: str, default) -> str:
    x = inp(msg + f"(default - '{YELLOW}{default}{NC}'): ")
    return x if x else default


def run(cmd: str, args: List[str], display=True, quit=False, redirect=False, follow=True):
    s = f"{LBLUE}{cmd} {' '.join(args)}{NC}"
    print(f"{BWHITE}Running{NC} `{s}`")
    try:
        p = (
            subprocess.Popen([cmd] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not redirect
            else subprocess.Popen([cmd] + args, stdout=sys.stdout, stderr=sys.stderr)
        )
        if follow:
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
                if quit:
                    sys.exit(p.returncode)
            else:
                if display and stdout:
                    sys.stdout.write(GREEN)
                    sys.stdout.write(stdout.decode("utf-8"))
                    sys.stdout.write(NC)
    except Exception as e:
        sys.stderr.write(f"{BWHITE}Failed running command{NC} `{s}` - {RED}{e}{NC}")


def bash(cmd: str, quit=False):
    run("/bin/bash", ["-c", cmd], quit=quit)


def ask_user_yn(msg: str, f, *args, ask=True):
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
    for step in s:
        if len(step) > 2:
            ask_user_yn(step[0], step[1], *step[2:], ask=ask)
        else:
            ask_user_yn(step[0], step[1], ask=ask)


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def fwrite(p: Path, s: str):
    with open(p, "w") as f:
        print(f"{BWHITE}Writing{NC} `{s}` to {LBLUE}`{str(p)}`{NC}")
        f.write(s)
