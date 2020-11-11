#!/bin/env python

################################################################################

import argparse
import os
import subprocess
import sys
import shutil
import tempfile
import tty
import termios
import traceback
import json
import urllib.request
from pathlib import Path
from typing import List, Dict

################################################################################

LBLUE = "\033[1;94m"
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
BWHITE = "\033[1;37m"
NC = "\033[0m"

################################################################################


FILENAME = Path(__file__)
FULLPATH = FILENAME.absolute()

ARCH_URL = "https://aur.archlinux.org"
PACKAGE_QUERY_REPO = f"{ARCH_URL}/package-query.git"
YAY_REPO = f"{ARCH_URL}/yay.git"
REPO_BASE = "https://github.com/wojciechkepka"
GIT_CONF_REPO = f"{REPO_BASE}/configs"
GIT_SCRIPTS_REPO = f"{REPO_BASE}/scripts"
PKG_URL = "https://wkepka.dev/static/pkgs"

try:
    PKGS = json.loads(urllib.request.urlopen(PKG_URL).read())
except Exception as e:
    sys.stderr.write(f"{BWHITE}Failed to get pkgs data from{NC} `{LBLUE}{PKG_URL}{NC}` - {RED}{e}{NC}\n")
    PGKS: Dict[str, List[str]] = {
        "base": [],
        "community": [],
        "aur": [],
        "coc": [],
    }

LOCALES = ["en_US.UTF-8", "en_GB.UTF-8", "pl_PL.UTF-8"]
LANG = "en_US.UTF-8"
KEYMAP = "pl"
REGION = "Europe"
CITY = "Warsaw"


################################################################################


def eprint(msg: str):
    sys.stderr.write(RED)
    sys.stderr.write(msg)
    sys.stderr.write(NC)


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


################################################################################


class System:
    @staticmethod
    def chmod(flags: str, f: Path):
        run("chmod", [flags, "--verbose", str(f)])

    @staticmethod
    def chown(p: Path, user: str, group: str, recursive=True):
        run(
            "chown",
            ["-R", f"{user}:{group}", str(p)] if recursive else [f"{user}:{group}", str(p)],
        )

    @staticmethod
    def cp(f1: Path, f2: Path):
        run("cp", ["--verbose", str(f1), str(f2)])

    @staticmethod
    def gitclone(repo: str, where=Path("")):
        p = str(where)
        System.install_pkg_if_bin_not_exists("git")
        run("git", ["clone", repo, p] if p else ["clone", repo])

    @staticmethod
    def nvim(cmd: str):
        run("nvim", ["--headless", "-c", f'"{cmd}"'])

    @staticmethod
    def extar(f: Path, to: Path):
        run(
            "tar",
            [
                "--extract",
                f"--file={str(f)}",
                f"--directory={str(to)}",
            ],
        )

    @staticmethod
    def _link(f: Path, to: Path):
        run(
            "ln",
            ["--symbolic", "--force", "--verbose", str(f), str(to)],
        )

    @staticmethod
    def link(base: Path, f: str, out: Path):
        f = f[1:] if f.startswith("/") else f
        System._link(base.joinpath(f), out.joinpath(f))

    @staticmethod
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

        run(
            "useradd",
            args + [user],
            quit=True,
        )

        if not password:
            run("passwd", [user], redirect=True, follow=False)

    @staticmethod
    def bins_exist(bins: List[str]):
        for b in bins:
            if shutil.which(b) is None:
                return False
        return True

    @staticmethod
    def install_pkgs(pkgs: List[str], pkgmngr="/usr/bin/pacman", user="root"):
        run("sudo", ["-u", user, pkgmngr, "--sync", "--noconfirm"] + pkgs)

    @staticmethod
    def install_pkg_if_bin_not_exists(binary: str, pkg=""):
        if not System.bins_exist([binary]):
            System.install_pkgs([pkg if pkg else binary])

    @staticmethod
    def install_sudo():
        System.install_pkg_if_bin_not_exists("sudo")

    @staticmethod
    def install_and_run_reflector():
        System.install_pkg_if_bin_not_exists("reflector")
        run(
            "reflector",
            ["-l", "100", "--sort", "rate", "--save", "/etc/pacman.d/mirrorlist"],
        )

    @staticmethod
    def build_yay():
        System.install_sudo()

        bld_pkgs = ["git", "wget", "go", "fakeroot"]
        if not System.bins_exist(bld_pkgs):
            System.install_pkgs(bld_pkgs)

        with tempfile.TemporaryDirectory() as tmpdir:
            System.gitclone(PACKAGE_QUERY_REPO, Path(f"{tmpdir}/package-query"))
            System.gitclone(YAY_REPO, Path(f"{tmpdir}/yay"))
            System.chown(tmpdir, "nobody", "nobody")

            System.sudo_nopasswd("nobody")
            Path("/.cache/go-build").mkdir(parents=True)
            System.chown("/.cache", "nobody", "nobody")

            bash(f"cd {tmpdir}/package-query && sudo -u nobody makepkg -srci --noconfirm")
            bash(f"cd {tmpdir}/yay && sudo -u nobody makepkg -srci --noconfirm")

            shutil.rmtree("/.cache")
            System.rm_sudo_nopasswd("nobody")

    @staticmethod
    def gen_locale(locales: List[str]):
        with open("/etc/locale.gen", "a+") as f:
            for line in f.readlines():
                for locale in locales:
                    if line.startswith(f"#{locale}"):
                        line = locale

        run("locale-gen", [])

    @staticmethod
    def set_lang(lang: str):
        fwrite(Path("/etc/locale.conf"), "LANG=" + lang)

    @staticmethod
    def set_keymap(keymap: str):
        fwrite(Path("/etc/vconsole.conf"), "KEYMAP=" + keymap)

    @staticmethod
    def setxkbmap(keymap: str):
        if shutil.which("setxkbmap") is not None:
            run("setxkbmap", [keymap])

    @staticmethod
    def set_timezone(region: str, city: str):
        if region and city:
            System._link(Path(f"/usr/share/zoneinfo/{region}/{city}"), Path("/etc/localtime"))

    @staticmethod
    def set_hostname(hostname: str):
        if hostname:
            fwrite(Path("/etc/hostname"), hostname)

    @staticmethod
    def create_hosts():
        fwrite(Path("/etc/hosts"), "127.0.0.1     localhost\n::1           localhost\n")

    @staticmethod
    def sudo_nopasswd(user: str):
        fwrite(Path(f"/etc/sudoers.d/01{user}"), f"{user} ALL=(ALL) NOPASSWD: ALL\n")

    @staticmethod
    def rm_sudo_nopasswd(user: str):
        p = f"/etc/sudoers.d/01{user}"
        if Path(p).exists():
            os.remove(p)


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

    def copy_self(self):
        System.cp(str(FULLPATH), f"{self.location}/{FILENAME}")

    def init_setup(self):
        self.copy_self()
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

        System.create_user(self.username, password=self.password)
        System.sudo_nopasswd(self.username)

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
            System.build_yay()

        if not self.username:
            self.username = inp("Enter username: ")

        System.install_pkgs(pkgs, pkgmngr="yay", user=self.username)

    def install_themes(self):
        if Path(self.theme_dir()).exists():
            shutil.rmtree(self.theme_dir())

        os.makedirs(self.theme_dir())

        git_theme_dir = self.git_conf_dir() / "themes"
        System.extar(git_theme_dir / "Sweet-Dark.tar.xz", self.theme_dir())
        System.extar(git_theme_dir / "Sweet-Purple.tar.xz", self.theme_dir())
        System.extar(git_theme_dir / "Sweet-Teal.tar.xz", self.theme_dir())

        run(
            "unzip",
            [
                str(git_theme_dir / "Solarized-Dark-Orange_2.0.1.zip"),
                "-d",
                str(self.theme_dir()),
            ],
        )
        System.gitclone(f"{REPO_BASE}/gruvbox-gtk", self.theme_dir() / "gruvbox-gtk")
        System.gitclone(f"{REPO_BASE}/Aritim-Dark", self.theme_dir() / "aritim")
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

        System.gitclone(GIT_CONF_REPO, self.git_conf_dir())
        System._link(self.git_conf_dir(), self.userhome / "dev" / "conf")

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
            System.link(self.git_conf_dir(), f, self.userhome)

        global_files = [
            "/etc/lightdm/lightdm.conf",
            "/etc/lightdm/lightdm-gtk-greeter.conf",
            "/etc/mkinitcpio.conf",
            "/usr/share/vim/vimfiles/syntax/notes.vim",
            "/usr/share/vim/vimfiles/ftdetect/notes.vim",
            "/etc/pacman.conf",
        ]

        for f in global_files:
            System.link(self.git_conf_dir(), f, Path("/"))

        System.chmod("+x", self.git_conf_dir() / ".config/bspwm/bspwmrc")

        fwrite(Path("/etc/profile"), "export XDG_CONFIG_DIR=$HOME/.config")

        System.chown(self.git_conf_dir(), self.username, self.username)
        System.chown(self.userhome, self.username, self.username)

    def install_scripts(self):
        scripts_dir = Path("/usr/local/scripts")
        System.gitclone(GIT_SCRIPTS_REPO, scripts_dir)
        System.chown(scripts_dir, self.username, self.username)
        System._link(scripts_dir, self.userhome / "dev" / "scripts")

        p = Path("/etc/profile.d/scripts_path.sh")
        if not p.exists():
            fwrite(p, f"export PATH=$PATH:{str(scripts_dir)}")

    def set_lang(self):
        lang = inp_or_default("Enter system language", LANG) if self.ask else LANG
        System.set_lang(lang)

    def set_keymap(self):
        keymap = inp_or_default("Enter keymap", KEYMAP) if self.ask else KEYMAP
        System.set_keymap(keymap)
        System.setxkbmap(keymap)

    def set_timezone(self):
        region = inp_or_default("Enter region", REGION) if self.ask else REGION
        city = inp_or_default("Enter city", CITY) if self.ask else CITY
        System.set_timezone(region, city)

    def datetime_location_setup(self):
        s = System
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
            System.chown(self.xdg_conf_dir(), self.username, self.username)

    def install_nvim_plugins(self):
        System.install_pkg_if_bin_not_exists("nvim", pkg="neovim")
        self.install_vim_plug()
        p = self.xdg_conf_dir().joinpath("/nvim/init.vim")
        if Path(p).exists():
            System.nvim("PlugInstall|q|q")
        else:
            eprint(f"Missing nvim config file at {p}")

        System.install_pkg_if_bin_not_exists("pip2", "python2-pip")
        System.install_pkg_if_bin_not_exists("pip", "python-pip")
        run("pip", ["install", "neovim"])
        run("pip2", ["install", "neovim"])

    def install_coc_extensions(self):
        for ext in PKGS["coc"]:
            System.nvim(f"CocInstall -sync {ext}|q|q")

    def setup(self):
        steps(
            [
                ("Create user?", self.create_user),
                (
                    "Initialize localization/time/hostname?",
                    self.datetime_location_setup,
                ),
                ("Run Reflector?", System.install_and_run_reflector),
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


################################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="genesis", description="Arch linux setup")
    subparsers = parser.add_subparsers(title="command", dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initial setup like bootstraping packages and generating fstab")
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

    args = parser.parse_args()
    cfg = SetupConfig.from_args(args)

    try:
        if args.command == "init" or args.command == "auto":
            Init(cfg).init()
        elif args.command == "setup":
            Setup(cfg).setup()
    except KeyboardInterrupt:
        print(f"\n{BWHITE}Exiting...{NC}")
        sys.exit(0)
    except Exception as e:
        eprint(f"{BWHITE}Unhandled exception{NC} - {RED}{e}{NC}\n")
        eprint(f"{BWHITE}Traceback:\n{RED}{traceback.format_exc()}{NC}")
        sys.exit(1)
