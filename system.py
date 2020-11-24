#!/bin/env python
"""
System

Functions providing easier api to interacting with linux
"""
################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ imports ~~~~~~~~~~~|
################################################################################

import shutil
import os
import sys
from tempfile import TemporaryDirectory
from typing import List
from pathlib import Path
from util import Command, fwrite, bash, ExecOpts

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ globals ~~~~~~~~~~~|
################################################################################

ARCH_URL = "https://aur.archlinux.org"
PACKAGE_QUERY_REPO = f"{ARCH_URL}/package-query.git"
YAY_REPO = f"{ARCH_URL}/yay.git"

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ funcs ~~~~~~~~~~~~~|
################################################################################


def chmod(flags: str, f: Path):
    Command("chmod", [flags, "--verbose", str(f)]).safe_run()


def chown(p: Path, user: str, group: str, recursive=True):
    Command(
        "chown",
        ["-R", f"{user}:{group}", str(p)] if recursive else [f"{user}:{group}", str(p)],
    ).safe_run()


def cp(f1: Path, f2: Path):
    Command("cp", ["--verbose", str(f1), str(f2)]).safe_run()


def gitclone(repo: str, where=Path("")):
    p = str(where)
    install_pkg_if_bin_not_exists("git")
    Command("git", ["clone", repo, p] if p else ["clone", repo]).safe_run()


def nvim(cmd: str):
    Command("nvim", ["--headless", "-c", f'"{cmd}"']).safe_run()


def extar(f: Path, to: Path):
    Command(
        "tar",
        [
            "--extract",
            f"--file={str(f)}",
            f"--directory={str(to)}",
        ],
    ).safe_run()


def _link(f: Path, to: Path):
    Command(
        "ln",
        ["--symbolic", "--force", "--verbose", str(f), str(to)],
    ).safe_run()


def link(base: Path, f: str, out: Path):
    f = f[1:] if f.startswith("/") else f
    _link(base.joinpath(f), out.joinpath(f))


def create_user(user: str, password=""):
    args = [
        "--groups",
        "wheel",
        "--create-home",
        "--shell",
        "/bin/bash",
    ]

    if password:
        args += ["--password", password]

    Command(
        "useradd",
        args + [user],
        opts=ExecOpts(quit=True),
    ).safe_run()

    if not password:
        Command("passwd", [user], opts=ExecOpts(redirect=True, follow=False)).safe_run()


def bins_exist(bins: List[str]):
    for b in bins:
        if shutil.which(b) is None:
            return False
    return True


def install_pkgs(pkgs: List[str], pkgmngr="/usr/bin/pacman", user="root"):
    Command("sudo", ["-u", user, pkgmngr, "--sync", "--noconfirm"] + pkgs).safe_run()


def install_pkg_if_bin_not_exists(binary: str, pkg=""):
    if not bins_exist([binary]):
        install_pkgs([pkg if pkg else binary])


def install_sudo():
    install_pkg_if_bin_not_exists("sudo")


def install_and_run_reflector():
    install_pkg_if_bin_not_exists("reflector")
    Command(
        "reflector",
        ["-l", "100", "--sort", "rate", "--save", "/etc/pacman.d/mirrorlist"],
    ).safe_run()


def build_yay():
    install_sudo()

    bld_pkgs = ["git", "wget", "go", "fakeroot"]
    if not bins_exist(bld_pkgs):
        install_pkgs(bld_pkgs)

    with TemporaryDirectory() as tmpdir:
        gitclone(PACKAGE_QUERY_REPO, Path(f"{tmpdir}/package-query"))
        gitclone(YAY_REPO, Path(f"{tmpdir}/yay"))
        chown(tmpdir, "nobody", "nobody")

        sudo_nopasswd("nobody")
        Path("/.cache/go-build").mkdir(parents=True)
        chown("/.cache", "nobody", "nobody")

        bash(f"cd {tmpdir}/package-query && sudo -u nobody makepkg -srci --noconfirm")
        bash(f"cd {tmpdir}/yay && sudo -u nobody makepkg -srci --noconfirm")

        shutil.rmtree("/.cache")
        rm_sudo_nopasswd("nobody")


def gen_locale(locales: List[str]):
    with open("/etc/locale.gen", "a+") as f:
        for line in f.readlines():
            for locale in locales:
                if line.startswith(f"#{locale}"):
                    line = locale

    Command("locale-gen", []).safe_run()


def set_lang(lang: str):
    fwrite(Path("/etc/locale.conf"), "LANG=" + lang)


def set_keymap(keymap: str):
    fwrite(Path("/etc/vconsole.conf"), "KEYMAP=" + keymap)


def set_timezone(region: str, city: str):
    if region and city:
        _link(Path(f"/usr/share/zoneinfo/{region}/{city}"), Path("/etc/localtime"))


def set_hostname(hostname: str):
    if hostname:
        fwrite(Path("/etc/hostname"), hostname)


def create_hosts():
    fwrite(Path("/etc/hosts"), "127.0.0.1     localhost\n::1           localhost\n")


def sudo_nopasswd(user: str):
    fwrite(Path(f"/etc/sudoers.d/01{user}"), f"{user} ALL=(ALL) NOPASSWD: ALL\n")


def rm_sudo_nopasswd(user: str):
    p = f"/etc/sudoers.d/01{user}"
    if Path(p).exists():
        os.remove(p)


def systemctl_enable(service: str):
    Command("systemctl", ["enable", service]).safe_run()
