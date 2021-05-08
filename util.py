#!/bin/env python
"""
Util

Utility funcs and classes for creating interactive cli scripts
"""
################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ imports ~~~~~~~~~~~|
################################################################################

import sys
import subprocess
import termios
import tty
import traceback
import time
from typing import List, Callable, Any, Optional, IO
from pathlib import Path
from enum import Enum


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ globals ~~~~~~~~~~~|
################################################################################

KILO = 1000.0
MEGA = KILO * KILO
GIGA = MEGA * KILO
TERA = GIGA * KILO


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ classes ~~~~~~~~~~~|
################################################################################


class Color(Enum):
    """Enumeration containing exit codes responsible for adjusting color of terminal output"""

    LBLUE = "\033[1;94m"
    CYAN = "\033[0;36m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    RED = "\033[0;31m"
    BWHITE = "\033[1;37m"
    NC = "\033[0m"

    _enable = True

    def __str__(self):
        if self._enable:
            return self.value

        return ""

    @staticmethod
    def disable():
        for color in COLORS:
            color._enable = False

    @staticmethod
    def enable():
        for color in COLORS:
            color._enable = True


COLORS = [Color.LBLUE, Color.CYAN, Color.GREEN, Color.YELLOW, Color.RED, Color.BWHITE, Color.NC]


class ExecOpts(object):
    """Configuration specifying Command execution

    Command parameters available:
        * display - whether to print stdout and/or stderr after cmd execution (defualt - True)
        * quit - if return code of command after execution is different than 0
                 exits the main process with command return code. (defualt - False)
        * redirect - replace subprocess's stdin, stdout, stderr with main processes fd's. (default - False)
        * follow - display commands output reading from subprocess stdout/stderr character
                   by character. (default - True)
        * collect - if set to False stdout and stderr wont be collected (default - True)
    """

    def __init__(
        self,
        display: bool = True,
        quit: bool = False,
        redirect: bool = False,
        follow: bool = True,
        collect: bool = True,
    ):
        self.display = display
        self.quit = quit
        self.redirect = redirect
        self.follow = follow
        self.collect = collect


DEFAULT_OPTS = ExecOpts()


class Command(object):
    """Command is a wrapper for running commands in a subprocess providing some utility
    parameters allowing adjustment of command execution.
    """

    def __init__(self, cmd: str, args: List[str], opts: ExecOpts = DEFAULT_OPTS):
        self.cmd = cmd
        self.args = args
        self.opts = opts

        self.subprocess = None
        self.exit_code = None
        self.stdout = None
        self.stderr = None

    def _subprocess(self) -> subprocess.Popen:
        if not self.opts.redirect:
            return subprocess.Popen([self.cmd] + self.args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            return subprocess.Popen([self.cmd] + self.args, stdout=sys.stdout, stderr=sys.stderr)

    def _follow_stdout(self):
        try:
            if self.opts.display:
                outw(Color.GREEN)
            self.stdout = ""
            for c in iter(lambda: self.subprocess.stdout.read(1), b""):
                try:
                    ch = c.decode("utf-8")
                    if self.opts.collect:
                        self.stdout += ch
                    outw(ch, flush=False)
                except:
                    pass
            sys.stderr.flush()
        finally:
            if self.opts.display:
                outw(Color.NC)

    def _follow_stderr(self):
        try:
            if self.opts.display:
                errw(Color.RED)
            self.stderr = ""
            for c in iter(lambda: self.subprocess.stderr.read(1), b""):
                try:
                    ch = c.decode("utf-8")
                    if self.opts.collect:
                        self.stderr += ch
                    errw(ch, flush=False)
                except:
                    pass
            sys.stderr.flush()
        finally:
            if self.opts.display:
                errw(Color.NC)

    def _run_follow(self):
        self.subprocess = self._subprocess()
        self._follow_stdout()
        self._follow_stderr()
        self.subprocess.communicate()
        self.exit_code = self.subprocess.returncode

    def _run(self):
        self.subprocess = self._subprocess()
        (self.stdout, self.stderr) = map(
            lambda x: "" if x is None else x.decode("utf-8"), self.subprocess.communicate()
        )
        self.exit_code = self.subprocess.returncode
        if self.exit_code != 0:
            if self.opts.display and self.stderr:
                eprint("ERROR: " + self.stderr)
        else:
            if self.opts.display and self.stdout:
                outw(Color.GREEN, self.stdout, Color.NC)

    def __repr__(self):
        return f"{Color.LBLUE}{self.cmd} {' '.join(self.args)}{Color.NC}"

    def run(self):
        """Runs this command in a subprocess."""
        print(f"{Color.BWHITE}Running{Color.NC} `{self}`")

        if self.opts.follow:
            self._run_follow()
        else:
            self._run()

        if self.opts.quit and self.exit_code != 0:
            sys.exit(self.exit_code)

    def safe_run(self, reraise=True):
        """Wrapper for run function catching all exceptions and printing them to stderr.
        By default the command output will be followed character by character and displayed on screen,
        if there is an exception in this process it will be printed to stderr and reraised.
        If reraise is True caught exceptions will be reraised.
        If there is any exception and quit is True then the program will terminate with
        exit code 1."""
        try:
            self.run()
        except Exception as e:
            if self.opts.display:
                errw(f"{Color.BWHITE}Failed running command{Color.NC} `{self}` - {Color.RED}{e}{Color.NC}")

            if reraise:
                raise

            if self.opts.quit:
                sys.exit(1)


class Step(object):
    """Step is a represantion of a setup step. Each step has a message that is printed to user as
    a y/n question. If the users answer is yes, function func will be called with
    args."""

    def __init__(self, message: str, func: Callable, *args: Any):
        self.message = message
        self.func = func
        self.args = [*args]

    def run(self, ask: bool = True):
        """If ask is set to True the user will be prompted for a y/n answer on
        whether to execute this step, otherwise the step will be automatically executed."""
        if self.args:
            ask_user_yn(self.message, self.func, *self.args, ask=ask)
        else:
            ask_user_yn(self.message, self.func, ask=ask)


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ funcs ~~~~~~~~~~~~~|
################################################################################


def _w(fd: IO, *items: Any, flush: bool = True):
    """Writes all items to specified file descriptor and flushes the fd if flush is set
    to True."""
    fd.write("".join([item.__str__() for item in items]))
    if flush:
        fd.flush()


def errw(*items: Any, flush: bool = True):
    """Writes out all items to stderr converting them to string. If flush is set to True
    stderr will be flushed after the write."""
    _w(sys.stderr, *items, flush=flush)


def outw(*items: Any, flush: bool = True):
    """Writes out all items to stdout converting them to string. If flush is set to True
    stdout will be flushed after the write."""
    _w(sys.stdout, *items, flush=flush)


def eprint(msg: str):
    """Prints a message to stderr in red color."""
    errw(Color.RED, msg, Color.NC)


def inp(msg: str) -> str:
    """Takes input from user printing msg first."""
    outw(Color.BWHITE, msg, Color.CYAN)
    inp = input()
    outw(Color.NC)
    return inp


def inp_or_default(msg: str, default: str) -> str:
    """Asks user for input printing msg first. If users input is empty uses default as return."""
    x = inp(msg + f"(default - '{Color.YELLOW}{default}{Color.NC}'): ")
    return x if x else default


def bash(cmd: str, quit=False):
    """Executes a bash script as a subprocess."""
    Command("/bin/bash", ["-c", cmd], opts=ExecOpts(quit=quit)).run()


def ask_user_yn(msg: str, f: Callable, *args: Any, ask=True):
    """Asks user for y/n choice on msg. If the answer is yes calls function f with *args."""
    outw(Color.BWHITE, msg, f" {Color.GREEN}y(es){Color.NC}/{Color.RED}n(o){Color.NC}/{Color.YELLOW}q(uit){Color.NC}: ")
    if ask:
        while True:
            ch = getch()
            if ch == "y":
                outw(Color.CYAN, ch, "\n", Color.NC)
                f(*args)
                break
            elif ch == "n":
                outw(Color.CYAN, ch, "\n", Color.NC)
                break
            elif ch == "q":
                outw(Color.CYAN, ch, "\n", Color.NC)
                raise KeyboardInterrupt
    else:
        outw(Color.CYAN, "y\n", Color.NC)
        f(*args)


def getch():
    """Gets a raw character from stdin."""
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
        print(f"{Color.BWHITE}Writing{Color.NC} `{s}` to {Color.LBLUE}`{str(p)}`{Color.NC}")
        f.write(s)


def conv_b(_bytes: int) -> str:
    """Converts input _bytes to a display string showing scaled unit with two decimal places.
    For example:
        s = conv_b(1201)
        assert s == "1.20 KB"
    """
    if _bytes <= KILO:
        return f"{_bytes:.2f} B"
    elif KILO < _bytes <= MEGA:
        return f"{_bytes / KILO:.2f} KB"
    elif MEGA < _bytes <= GIGA:
        return f"{_bytes / MEGA:.2f} MB"
    elif GIGA < _bytes <= TERA:
        return f"{_bytes / GIGA:.2f} GB"
    else:
        return f"{_bytes / TERA:.2f} TB"


def measure(func: Callable, *args: Any, **kwargs: Any) -> (Any, float):
    """Measures execution time of func by calling it with *args and **kwargs.
    Returns a tuple consisting of return value of function and execution time as float."""
    start = time.time()
    ret = func(*args, **kwargs)
    end = time.time()

    return (ret, end - start)


def run_steps(steps: List[Step], ask=True):
    """Executes a list of steps asking the user for choice on each step and catching
    exceptions on each step. If ask is set to False all steps will be executed automatically."""
    for step in steps:
        try:
            step.run(ask=ask)
        except Exception:
            s = f"{Color.LBLUE}{step.func.__name__}({' '.join(step.args[1:])}){Color.NC}"
            errw(
                f"{Color.BWHITE}Failed executing step{Color.NC} `{s}` -\n{Color.RED}{traceback.format_exc()}{Color.NC}"
            )


def catch_errs(func: Callable, *args: Any, **kwargs: Any):
    """Executes specified func with args and kwargs cathing KeyboardInterrupt and exiting with
    return code 0 or catching unhandled exceptions and exiting with return code 1."""
    try:
        func(*args, **kwargs)
    except KeyboardInterrupt:
        print(f"\n{Color.BWHITE}Exiting...{Color.NC}")
        sys.exit(0)
    except Exception:
        eprint(f"{Color.BWHITE}Unhandled exception{Color.NC}\n")
        eprint(f"{traceback.format_exc()}")
        sys.exit(1)
