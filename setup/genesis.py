#!/bin/env python

################################################################################

import os
import subprocess
import sys
import shutil
import tempfile
import tty
import termios
import json
import urllib.request
from pathlib import Path

################################################################################


FILENAME = Path(__file__)
FULLPATH = FILENAME.absolute()

ARCH_URL = "https://aur.archlinux.org"
PACKAGE_QUERY_REPO = f"{ARCH_URL}/package-query.git"
YAY_REPO = f"{ARCH_URL}/yay.git"
REPO_BASE = "https://github.com/wojciechkepka"
GIT_CONF_REPO = f"{REPO_BASE}/configs"
PKG_URL = "https://wkepka.dev/static/pkgs"
PKGS = json.loads(urllib.request.urlopen(PKG_URL).read())

LOCALES = ["en_US.UTF-8", "en_GB.UTF-8", "pl_PL.UTF-8"]
LANG = "en_US.UTF-8"
KEYMAP = "pl"
REGION = "Europe"
CITY = "Warsaw"


################################################################################

BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
BWHITE = "\033[1;37m"
NC = "\033[0m"


def eprint(msg: str):
    sys.stderr.write(RED)
    sys.stderr.write(msg)
    sys.stdout.write(NC)


def inp(msg: str) -> str:
    sys.stdout.write(CYAN + msg + BWHITE)
    inp = input()
    sys.stdout.write(NC)
    return inp


def inp_or_default(msg: str, default):
    x = inp(msg + f"(default - '{default}'): ")
    return x if x else default


def run(cmd: str, args: [str], display=True, quit=False, redirect=False, follow=True):
    print(f"Running `{cmd} {' '.join(args)}`")
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
                sys.stdout.write(c.decode("utf-8"))
            except:
                pass
        sys.stdout.write(NC)
    else:
        (stdout, stderr) = p.communicate()
        if p.returncode != 0:
            if display and stderr:
                eprint("ERROR: " + stderr.decode("utf-8"))
            if quit:
                sys.exit(1)
        else:
            if display and stdout:
                sys.stdout.write(GREEN)
                print(stdout.decode("utf-8"))
                sys.stdout.write(NC)


def bash(cmd: str, quit=False):
    run("/bin/bash", ["-c", cmd], quit=quit)


def ask_user_yn(msg: str, f, *args):
    sys.stdout.write(CYAN + msg + f" {GREEN}y(es){NC}/{RED}n(o){NC}/{YELLOW}q(uit){NC}: ")
    sys.stdout.flush()
    while True:
        ch = getch()
        if ch == "y":
            sys.stdout.write(BWHITE + ch + "\n" + NC)
            f(*args)
            break
        elif ch == "n":
            sys.stdout.write(BWHITE + ch + "\n" + NC)
            break
        elif ch == "q":
            sys.stdout.write(BWHITE + ch + "\n" + NC)
            raise KeyboardInterrupt


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


################################################################################


class System(object):
    @staticmethod
    def chmod(flags: str, f: str):
        run("chmod", [flags, "--verbose", f])

    @staticmethod
    def cp(f1: str, f2: str):
        run("cp", ["--verbose", f1, f2])

    @staticmethod
    def mkdir(d: str):
        if not Path(d).exists():
            os.makedirs(d)

    @staticmethod
    def gitclone(repo: str, where=""):
        System.install_pkg_if_bin_not_exists("git")
        run("git", ["clone", repo, where] if where else ["clone", repo])

    @staticmethod
    def nvim(cmd: str):
        run("nvim", ["-c", f'"{cmd}"'])

    @staticmethod
    def extar(f: str, to: str):
        run(
            "tar",
            [
                "--extract",
                f"--file={f}",
                f"--directory={to}",
            ],
        )

    @staticmethod
    def _link(f: str, to: str):
        run(
            "ln",
            ["--symbolic", "--force", "--verbose", f, to],
        )

    @staticmethod
    def link(base: str, f: str, out: str):
        System._link(f"{base}/{f}", f"{out}/{f}")

    @staticmethod
    def create_user(user: str):
        run(
            "useradd",
            [
                "--groups",
                "wheel",
                "--create-home",
                "--shell",
                "/bin/bash",
                user,
            ],
            quit=True,
        )
        run("passwd", [user], redirect=True, follow=False)

    @staticmethod
    def bins_exist(bins: [str]):
        for b in bins:
            if shutil.which(b) is None:
                return False
        return True

    @staticmethod
    def install_pkgs(pkgs):
        run("/usr/bin/pacman", ["--sync", "--noconfirm"] + pkgs)

    @staticmethod
    def install_pkg_if_bin_not_exists(pkg):
        if not System.bins_exist([pkg]):
            System.install_pkgs([pkg])

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
            System.gitclone(PACKAGE_QUERY_REPO, f"{tmpdir}/package-query")
            System.gitclone(YAY_REPO, f"{tmpdir}/yay")
            run("chown", ["-R", "nobody:nobody", tmpdir])

            System.sudo_nopasswd("nobody")
            System.mkdir(f"/.cache")
            System.mkdir(f"/.cache/go-build")
            run("chown", ["-R", "nobody:nobody", "/.cache"])

            bash(f"cd {tmpdir}/package-query && sudo -u nobody makepkg -srci --noconfirm")
            bash(f"cd {tmpdir}/yay && sudo -u nobody makepkg -srci --noconfirm")

            os.remove("/.cache")
            System.rm_sudo_nopasswd("nobody")

    @staticmethod
    def gen_locale(locales: [str]):
        with open("/etc/locale.gen", "a+") as f:
            for line in f.readlines():
                for locale in locales:
                    if line.startswith(f"#{locale}"):
                        line = locale

        run("locale-gen", [])

    @staticmethod
    def set_lang(lang: str):
        with open("/etc/locale.conf", "w+") as f:
            f.write("LANG=" + lang)

    @staticmethod
    def set_keymap(keymap: str):
        with open("/etc/vconsole.conf", "w+") as f:
            f.write("KEYMAP=" + keymap)

    @staticmethod
    def setxkbmap(keymap: str):
        if shutil.which("setxkbmap") is not None:
            run("setxkbmap", [keymap])

    @staticmethod
    def set_timezone(region: str, city: str):
        if region and city:
            System._link(f"/usr/share/zoneinfo/{region}/{city}", "/etc/localtime")

    @staticmethod
    def set_hostname(hostname: str):
        if hostname:
            with open("/etc/hostname", "w+") as f:
                f.write(hostname)

    @staticmethod
    def create_hosts():
        with open("/etc/hosts", "w+") as f:
            f.write("127.0.0.1      localhost")
            f.write("::1            localhost")

    @staticmethod
    def sudo_nopasswd(user: str):
        with open(f"/etc/sudoers.d/01{user}", "w+") as f:
            f.write(f"{user} ALL=(ALL) NOPASSWD: ALL\n")

    @staticmethod
    def rm_sudo_nopasswd(user: str):
        p = f"/etc/sudoers.d/01{user}"
        if Path(p).exists():
            os.remove(p)


class Init(object):
    def __init__(self, location: str):
        self.location = location

    def gen_fstab(self):
        bash(
            f"/usr/bin/genfstab -U {self.location} >> {self.location}/etc/fstab",
            quit=True,
        )

    def install_pkgs(self, pkgs: [str]):
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
        self.arch_chroot(f"/usr/bin/python {FILENAME} setup")


class Setup(object):
    def __init__(self):
        self.username = ""
        self.userhome = ""
        self.setup()

    def git_conf_dir(self) -> str:
        return f"{self.userhome}/dev/configs"

    def xdg_conf_dir(self) -> str:
        return f"{self.userhome}/.config"

    def theme_dir(self) -> str:
        return f"{self.userhome}/.themes"

    def icons_dir(self) -> str:
        return f"{self.userhome}/.icons"

    def create_user(self):
        self.username = inp("Enter username: ")
        self.userhome = f"/home/{self.username}"

        System.create_user(self.username)
        System.sudo_nopasswd(self.username)

    def create_home_dirs(self):
        dirs = [
            f"{self.userhome}/screenshots",
            f"{self.userhome}/wallpapers",
            f"{self.userhome}/Downloads",
            f"{self.userhome}/Documents",
            self.theme_dir(),
            self.icons_dir(),
        ]

        for d in dirs:
            System.mkdir(d)

    def install_pkgs(self, pkgs: [str]):
        ask_user_yn("Run Reflector?", System.install_and_run_reflector)
        if shutil.which("yay") is None:
            System.build_yay()

        if not self.username:
            self.username = inp("Enter username: ")

        run("sudo", ["-u", self.username, "yay", "-S", "--noconfirm"] + pkgs)

    def install_themes(self):
        if Path(self.theme_dir()).exists():
            shutil.rmtree(self.theme_dir())

        os.makedirs(self.theme_dir())

        System.extar(self.git_conf_dir() + "/themes/Sweet-Dark.tar.xz", self.theme_dir())
        System.extar(self.git_conf_dir() + "/themes/Sweet-Purple.tar.xz", self.theme_dir())
        System.extar(self.git_conf_dir() + "/themes/Sweet-Teal.tar.xz", self.theme_dir())
        run(
            "unzip",
            [
                f"{self.git_conf_dir()}/themes/Solarized-Dark-Orange_2.0.1.zip",
                "-d",
                self.theme_dir(),
            ],
        )
        System.gitclone(
            f"{REPO_BASE}/gruvbox-gtk",
            f"{self.theme_dir()}/gruvbox-gtk",
        )
        System.gitclone(f"{REPO_BASE}/Aritim-Dark", f"{self.theme_dir()}/aritim")
        run("mv", [f"{self.theme_dir()}/aritim/GTK", f"{self.theme_dir()}/Aritim-Dark"])
        shutil.rmtree(f"{self.theme_dir()}/aritim")

    def install_configs(self):
        conf_dirs = [
            self.git_conf_dir(),
            self.xdg_conf_dir(),
            "/etc/lightdm",
            f"{self.xdg_conf_dir()}/alacritty",
            f"{self.xdg_conf_dir()}/bspwm",
            f"{self.xdg_conf_dir()}/nvim",
            f"{self.xdg_conf_dir()}/polybar",
            f"{self.xdg_conf_dir()}/sxhkd",
            f"{self.xdg_conf_dir()}/termite",
            f"{self.xdg_conf_dir()}/gtk-3.0",
            f"{self.xdg_conf_dir()}/dunst",
            f"{self.xdg_conf_dir()}/rofi",
            f"{self.xdg_conf_dir()}/picom",
            f"{self.xdg_conf_dir()}/zathura",
            f"{self.userhome}/.newsboat",
        ]

        for d in conf_dirs:
            System.mkdir(d)

        System.gitclone(GIT_CONF_REPO, self.git_conf_dir())

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

        etc_files = [
            "/etc/lightdm/lightdm.conf",
            "/etc/lightdm/lightdm-webkit2-greeter.conf",
            "/etc/mkinitcpio.conf",
        ]

        for f in etc_files:
            System.link(self.git_conf_dir(), f, "/")

        System.chmod("+x", f"{self.git_conf_dir()}/.config/bspwm/bspwmrc")

        with open("/etc/profile", "a") as f:
            f.write("export XDG_CONFIG_DIR=$HOME/.config")

    def set_lang(self):
        lang = inp_or_default("Enter system language", LANG)
        System.set_lang(lang)

    def set_keymap(self):
        keymap = inp_or_default("Enter keymap", KEYMAP)
        System.set_keymap(keymap)
        System.setxkbmap(keymap)

    def set_timezone(self):
        region = inp_or_default("Enter region", REGION)
        city = inp_or_default("Enter city", CITY)
        System.set_timezone(region, city)

    def datetime_location_setup(self):
        s = System
        s.gen_locale(LOCALES)
        self.set_lang()
        self.set_keymap()
        self.set_timezone()
        hostname = inp("Enter hostname: ")
        s.set_hostname(hostname)
        s.create_hosts()

    def install_nvim_plugins(self):
        System.install_pkg_if_bin_not_exists("nvim")
        p = self.xdg_conf_dir() + "/nvim/init.vim"
        if Path(p).exists():
            System.nvim("PlugInstall|q|q")
        else:
            eprint(f"Missing nvim config file at {p}")

    def install_coc_extensions(self):
        for ext in PKGS["coc"]:
            System.nvim(f"CocInstall -sync {ext}|q")

    def setup(self):
        ask_user_yn("Create user?", self.create_user)
        ask_user_yn("Initialize localization/time/hostname?", self.datetime_location_setup)
        ask_user_yn("Install community packages?", self.install_pkgs, PKGS["community"])
        ask_user_yn("Install AUR packages?", self.install_pkgs, PKGS["aur"])
        ask_user_yn("Install configs?", self.install_configs)
        ask_user_yn("Install themes?", self.install_themes)
        ask_user_yn("Install nvim plugins?", self.install_nvim_plugins)
        ask_user_yn("Install coc extensions?", self.install_coc_extensions)


################################################################################

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            f"USAGE: \
        {FILENAME} <init | setup>"
        )
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == "init":
            location = inp("Enter new installation location: ")
            init = Init(location)
            ask_user_yn("Generate fstab?", init.gen_fstab)
            ask_user_yn("Install base packages?", init.install_pkgs, PKGS["base"])
            ask_user_yn("Run setup?", init.init_setup)
        elif cmd == "setup":
            Setup()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)
    except Exception as e:
        eprint(f"Unhandled exception - {e}")
        sys.exit(1)
