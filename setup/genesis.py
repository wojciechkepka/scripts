#!/bin/env python
"""
Genesis

automated arch linux installation customized to my needs.
"""
################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ imports ~~~~~~~~~~~|
################################################################################

import argparse
import os
import sys
import traceback
import json
import shutil
import urllib.request
import system
from pathlib import Path
from typing import List, Dict
from util import *

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ config ~~~~~~~~~~~~|
################################################################################

REPO_BASE = "https://github.com/wojciechkepka"
GIT_CONF_REPO = f"{REPO_BASE}/configs"
GIT_SCRIPTS_REPO = f"{REPO_BASE}/scripts"
PKG_URL = "https://wkepka.dev/static/pkgs"

LOCALES = ["en_US.UTF-8", "en_GB.UTF-8", "pl_PL.UTF-8"]
LANG = "en_US.UTF-8"
KEYMAP = "pl"
REGION = "Europe"
CITY = "Warsaw"

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ globals ~~~~~~~~~~~|
################################################################################

FILENAME = Path(__file__)
FULLPATH = FILENAME.absolute()

################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ packages ~~~~~~~~~~|
################################################################################

try:
    PKGS = json.loads(urllib.request.urlopen(PKG_URL).read())
except Exception as e:
    sys.stderr.write(f"{BWHITE}Failed to get pkgs data from{NC} `{LBLUE}{PKG_URL}{NC}` - {RED}{e}{NC}\n")
    PGKS: Dict[str, List[str]] = {
        "base": ["base", "base-devel", "linux", "linux-firmware", "lvm2", "mdadm", "dhcpcd"],
        "community": [],
        "aur": [],
        "coc": [],
    }


################################################################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ setup~~~~~~~~~~~~~~|
################################################################################


class SetupConfig(object):
    def __init__(self, location="", user="", password="", hostname="", auto=False):
        self.location = location
        self.user = user
        self.password = password
        self.hostname = hostname
        self.auto = auto

    @staticmethod
    def from_args(args: argparse.Namespace):
        if args.command == "init":
            return SetupConfig(location=args.location)
        elif args.command == "setup":
            return SetupConfig(user=args.user, password=args.password, hostname=args.hostname, auto=args.auto)
        elif args.command == "auto":
            return SetupConfig(
                location=args.location, user=args.user, password=args.password, hostname=args.hostname, auto=args.auto
            )
        else:
            return SetupConfig()

    def as_args_str(self, location=True, user=True, password=True, hostname=True, auto=True) -> str:
        s = " "
        if location:
            s += f"--location {self.location} "
        if user:
            s += f"--user {self.user} "
        if password:
            s += f"--password {self.password} "
        if hostname:
            s += f"--hostname {self.hostname} "
        if auto:
            s += "--auto "

        return s


class Init(object):
    def __init__(self, cfg: SetupConfig):
        self.location = cfg.location
        self.cfg = cfg

    def gen_fstab(self):
        bash(
            f"/usr/bin/genfstab -U {self.location} >> {self.location}/etc/fstab",
            quit=True,
        )

    def pacstrap(self, pkgs: List[str]):
        run("/usr/bin/pacstrap", [self.location] + pkgs, quit=True)

    def arch_chroot(self, cmd: str):
        run(
            "/usr/bin/arch-chroot",
            [self.location, "/bin/bash", "-c", cmd],
            quit=True,
            redirect=True,
            follow=False,
        )

    def archive_scripts(self):
        run("zip", ["-r", f"{self.location}/{FILENAME}", f"{FULLPATH.parent}/*"])

    def init_setup(self):
        self.archive_scripts()
        cmd = f"/usr/bin/python {FILENAME} setup"
        if self.cfg.auto:
            cmd += self.cfg.as_args_str(location=False)

        self.arch_chroot(cmd)

    def init(self):
        steps(
            [
                ("Install base packages?", self.pacstrap, PKGS["base"]),
                ("Generate fstab?", self.gen_fstab),
                ("Run setup?", self.init_setup),
            ],
            ask=not self.cfg.auto,
        )


class Setup(object):
    def __init__(self, cfg: SetupConfig):
        self.username = cfg.user if cfg.user else ""
        self.userhome = Path(f"/home/{self.username}") if self.username else Path("")
        self.password = cfg.password
        self.hostname = cfg.hostname
        self.ask = not cfg.auto

    def git_conf_dir(self) -> Path:
        return Path("/etc/configs")

    def xdg_conf_dir(self) -> Path:
        return self.userhome / ".config"

    def theme_dir(self) -> Path:
        return self.userhome / ".themes"

    def icons_dir(self) -> Path:
        return self.userhome / ".icons"

    def create_user(self):
        if not self.username:
            self.username = inp("Enter username: ")
            self.userhome = Path(f"/home/{self.username}")

        system.create_user(self.username, password=self.password)
        system.sudo_nopasswd(self.username)

    def create_home_dirs(self):
        dirs = [
            self.userhome / "screenshots",
            self.userhome / "wallpapers",
            self.userhome / "Downloads",
            self.userhome / "Documents",
            self.userhome / "dev",
            self.theme_dir(),
            self.icons_dir(),
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def install_pkgs(self, pkgs: List[str]):
        if shutil.which("yay") is None:
            system.build_yay()

        if not self.username:
            self.username = inp("Enter username: ")

        system.install_pkgs(pkgs, pkgmngr="yay", user=self.username)

    def install_themes(self):
        if Path(self.theme_dir()).exists():
            shutil.rmtree(self.theme_dir())

        os.makedirs(self.theme_dir())

        git_theme_dir = self.git_conf_dir() / "themes"
        system.extar(git_theme_dir / "Sweet-Dark.tar.xz", self.theme_dir())
        system.extar(git_theme_dir / "Sweet-Purple.tar.xz", self.theme_dir())
        system.extar(git_theme_dir / "Sweet-Teal.tar.xz", self.theme_dir())

        run(
            "unzip",
            [
                str(git_theme_dir / "Solarized-Dark-Orange_2.0.1.zip"),
                "-d",
                str(self.theme_dir()),
            ],
        )
        system.gitclone(f"{REPO_BASE}/gruvbox-gtk", self.theme_dir() / "gruvbox-gtk")
        system.gitclone(f"{REPO_BASE}/Aritim-Dark", self.theme_dir() / "aritim")
        run("mv", [str(self.theme_dir() / "aritim/GTK"), str(self.theme_dir() / "Aritim-Dark")])
        shutil.rmtree(str(self.theme_dir() / "aritim"))

    def install_configs(self):
        conf_dirs = [
            self.git_conf_dir(),
            self.xdg_conf_dir(),
            Path("/etc/lightdm"),
            Path("/usr/share/backgrounds"),
            Path("/usr/share/vim/vimfiles/ftdetect"),
            Path("/usr/share/vim/vimfiles/syntax"),
            self.xdg_conf_dir() / "alacritty",
            self.xdg_conf_dir() / "bspwm",
            self.xdg_conf_dir() / "nvim",
            self.xdg_conf_dir() / "polybar",
            self.xdg_conf_dir() / "sxhkd",
            self.xdg_conf_dir() / "termite",
            self.xdg_conf_dir() / "gtk-3.0",
            self.xdg_conf_dir() / "dunst",
            self.xdg_conf_dir() / "rofi",
            self.xdg_conf_dir() / "picom",
            self.xdg_conf_dir() / "zathura",
            self.userhome / "newsboat",
        ]

        for d in conf_dirs:
            d.mkdir(parents=True, exist_ok=True)

        system.gitclone(GIT_CONF_REPO, self.git_conf_dir())
        system._link(self.git_conf_dir(), self.userhome / "dev" / "conf")

        conf_files = [
            ".bashrc",
            ".gtkrc-2.0",
            ".gitconfig",
            ".newsboat",
            ".tmux.conf",
            ".xinitrc",
            ".Xresources",
            ".config/alacritty/alacritty.yml",
            ".config/bspwm/bspwmrc",
            ".config/nvim/init.vim",
            ".config/nvim/coc-settings.json",
            ".config/polybar/colors.ini",
            ".config/polybar/config.ini",
            ".config/polybar/modules.ini",
            ".config/sxhkd/sxhkdrc",
            ".config/termite/config",
            ".config/dunst/dunstrc",
            ".config/gtk-3.0/settings.ini",
            ".config/gtk-3.0/gtk.css",
            ".config/picom/picom.conf",
            ".config/rofi/config.rasi",
            ".config/zathura/zathurarc",
            ".config/starship.toml",
        ]

        for f in conf_files:
            system.link(self.git_conf_dir(), f, self.userhome)

        global_files = [
            "/etc/lightdm/lightdm.conf",
            "/etc/lightdm/lightdm-gtk-greeter.conf",
            "/etc/mkinitcpio.conf",
            "/usr/share/vim/vimfiles/syntax/notes.vim",
            "/usr/share/vim/vimfiles/ftdetect/notes.vim",
            "/etc/pacman.conf",
        ]

        for f in global_files:
            system.link(self.git_conf_dir(), f, Path("/"))

        system.chmod("+x", self.git_conf_dir() / ".config/bspwm/bspwmrc")

        fwrite(Path("/etc/profile"), "export XDG_CONFIG_DIR=$HOME/.config")

        system.chown(self.git_conf_dir(), self.username, self.username)
        system.chown(self.userhome, self.username, self.username)

    def install_scripts(self):
        scripts_dir = Path("/usr/local/scripts")
        system.gitclone(GIT_SCRIPTS_REPO, scripts_dir)
        system.chown(scripts_dir, self.username, self.username)
        system._link(scripts_dir, self.userhome / "dev" / "scripts")

        p = Path("/etc/profile.d/scripts_path.sh")
        if not p.exists():
            fwrite(p, f"export PATH=$PATH:{str(scripts_dir)}")

    def set_lang(self):
        lang = inp_or_default("Enter system language", LANG) if self.ask else LANG
        system.set_lang(lang)

    def set_keymap(self):
        keymap = inp_or_default("Enter keymap", KEYMAP) if self.ask else KEYMAP
        system.set_keymap(keymap)

    def set_timezone(self):
        region = inp_or_default("Enter region", REGION) if self.ask else REGION
        city = inp_or_default("Enter city", CITY) if self.ask else CITY
        system.set_timezone(region, city)

    def datetime_location_setup(self):
        s = system
        s.gen_locale(LOCALES)
        self.set_lang()
        self.set_keymap()
        self.set_timezone()
        if not self.hostname and self.ask:
            self.hostname = inp("Enter hostname: ")
        s.set_hostname(self.hostname)
        s.create_hosts()

    def install_vim_plug(self):
        f = self.xdg_conf_dir().joinpath("nvim/autoload/plug.vim")
        url = "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim"
        if not f.exists():
            bash(f"curl -fLo {f} --create-dirs {url}")
            system.chown(self.xdg_conf_dir(), self.username, self.username)

    def install_nvim_plugins(self):
        system.install_pkg_if_bin_not_exists("nvim", pkg="neovim")
        self.install_vim_plug()
        p = self.xdg_conf_dir().joinpath("/nvim/init.vim")
        if Path(p).exists():
            system.nvim("PlugInstall|q|q")
        else:
            eprint(f"Missing nvim config file at {p}")

        system.install_pkg_if_bin_not_exists("pip2", "python2-pip")
        system.install_pkg_if_bin_not_exists("pip", "python-pip")
        run("pip", ["install", "neovim"])
        run("pip2", ["install", "neovim"])

    def install_coc_extensions(self):
        for ext in PKGS["coc"]:
            system.nvim(f"CocInstall -sync {ext}|q|q")

    def setup(self):
        steps(
            [
                ("Create user?", self.create_user),
                (
                    "Initialize localization/time/hostname?",
                    self.datetime_location_setup,
                ),
                ("Run Reflector?", system.install_and_run_reflector),
                ("Install community packages?", self.install_pkgs, PKGS["community"]),
                ("Install AUR packages?", self.install_pkgs, PKGS["aur"]),
                ("Install configs?", self.install_configs),
                ("Install scripts?", self.install_scripts),
                ("Install themes?", self.install_themes),
                ("Install nvim plugins?", self.install_nvim_plugins),
                ("Install coc extensions?", self.install_coc_extensions),
            ],
            ask=self.ask,
        )


class Genesis(object):
    def __init__(self):
        args = Genesis.parser().parse_args()
        self.cmd = args.command
        self.cfg = SetupConfig.from_args(args)

    @staticmethod
    def parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="genesis", description="Arch linux setup")
        subparsers = parser.add_subparsers(title="command", dest="command", required=True)

        init_parser = subparsers.add_parser(
            "init", help="Initial setup like bootstraping packages and generating fstab"
        )
        init_parser.add_argument("-l", "--location", dest="location", help="Setup location", required=True)
        setup_parser = subparsers.add_parser(
            "setup", help="Post setup including user creation, localization, packages, configs..."
        )
        setup_parser.add_argument("-u", "--user", dest="user", default="", help="Specify a user for setup")
        setup_parser.add_argument("-p", "--password", dest="password", default="", help="Users password")
        setup_parser.add_argument("--hostname", dest="hostname", default="")
        setup_parser.add_argument("-a", "--auto", dest="auto", action="store_true")

        auto_parser = subparsers.add_parser(
            "auto", help="Automated install where all parameters are specified upfront. All answers will be yes."
        )
        auto_parser.add_argument("-l", "--location", dest="location", help="Setup location", required=True)
        auto_parser.add_argument("-u", "--user", dest="user", help="Specify a user for setup", required=True)
        auto_parser.add_argument("-p", "--password", dest="password", help="Password for user", required=True)
        auto_parser.add_argument("--hostname", dest="hostname", help="Hostname of this system", required=True)

        return parser

    def main(self):
        try:
            if self.cmd == "init" or self.cmd == "auto":
                Init(self.cfg).init()
            elif self.cmd == "setup":
                Setup(self.cfg).setup()
        except KeyboardInterrupt:
            print(f"\n{BWHITE}Exiting...{NC}")
            sys.exit(0)
        except Exception:
            eprint(f"{BWHITE}Unhandled exception{NC}\n")
            eprint(f"{RED}{traceback.format_exc()}{NC}")
            sys.exit(1)


################################################################################

if __name__ == "__main__":
    Genesis().main()
