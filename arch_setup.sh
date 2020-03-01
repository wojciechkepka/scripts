#!/bin/bash

USERNAME='wojtek'
USERHOME="/home/$USERNAME"
GIT_CONF_REPO='https://github.com/wojciechkepka/configs'
GIT_CONF_DIR="$USERHOME/dev/configs"
XDG_CONF_DIR="$USERHOME/.config"
PACKAGE_QUERY_REPO='https://aur.archlinux.org/package-query.git'
YAOURT_REPO='https://aur.archlinux.org/yaourt.git'

BASE_PACKAGES=(
	'alsa-firmware'
	'alsa-utils'
	'amd-ucode'
	'bspwm'
	'ccls'
	'chrony'
	'ctags'
	'dhcpcd'
	'exa' # better ls
	'fd' # better find
	'feh' # Image viewer
	'filezilla'
	'firefox'
	'git'
	'gnome-keyring'
	'gpick' # Color picker
	'htop'
	'i3lock'
	'man-db'
	'man-pages'
	'mupdf'
	'nautilus'
	'neovim'
	'net-tools'
	'noto-fonts-emoji'
	'openssh'
	'perf'
	'picom' # new Compiz
	'pidgin'
	'powerline-fonts'
	'powertop'
	'pulseaudio'
	'python-pip'
	'ranger'
	'redshift'
	'ripgrep'
	'rofi' # menu and app launcher
	'sxhkd' # keybinding daemon
	'termite'
	'tcpdump'
	'thunderbird'
	'tmux'
	'ttf-fira-code'
	'ttf-font-awesome'
	'ttf-hack'
	'unzip'
	'vim'
	'vlc'
	'w3m' # for image display in Ranger
	'wget'
	'xclip'
	'xorg-xinit'
	'xorg-xrandr'
)

AUR_PACKAGES=(
	'font-manager'
	'neovim-plug'
	'polybar'
	'rust-analyzer'
	'ttf-iosevka'
	'vim-plug'
)

################################################################################
check_root() {
	# Check for root permissions
	if [ "$EUID" -ne 0 ]
	  then echo "Please run as root"
	  exit 1
	fi
}
create_user() {
	echo "Creating user $USERNAME"
	useradd -G sudo -m -s /bin/bash $USERNAME
	echo "Enter password for user $USERNAME"
	passwd $USERNAME
}
build_yaourt() {
	# Install necessary packages for yaourt build
	pacman -S --needed base-devel yail git wget

	# Create a temporary dir
	local bld_dir="/tmp/$(date +%s)-yaourt"
	echo "Creating $bld_dir"
	mkdir -p $bld_dir
	cd $bld_dir

	# Clone package query and yaourt
	git clone $PACKAGE_QUERY_REPO
	git clone $YAOURT_REPO

	# Build package-query
	echo "Building package-query"
	cd package-query && makepkg -si
	cd ..

	# Build yaourt
	echo "Building yaourt"
	cd yaourt && makepkg -si
	cd /
}
install_and_run_reflector() {
	pacman -S reflector
	echo "Running reflector"
	reflector --latests 200 --sort rate --save /etc/pacman.d/mirrorlist
}
install_packages() {
	install_and_run_reflector
	command -v yaourt
	if [ $? -eq 0 ]
	then
		build_yaourt
	fi
	echo "Installing base packages"
	yaourt -S "${BASE_PACKAGES[@]}"
	echo "Installing aur packages"
	yaourt -S "${AUR_PACKAGES[@]}"
}
cfg_link() {
	local cfg_file="$1"
	ln -s -v $GIT_CONF_DIR/$cfg_file $USERHOME/$cfg_file
}
install_configs() {
	mkdir -p -v $GIT_CONF_DIR \
		    $XDG_CONF_DIR \
		    $XDG_CONF_DIR/bspwm \
		    $XDG_CONF_DIR/nvim \
		    $XDG_CONF_DIR/polybar \
		    $XDG_CONF_DIR/sxhkd \
		    $XDG_CONF_DIR/termite

	git clone $GIT_CONF_REPO $GIT_CONF_DIR

	cfg_link ".tmux.conf"
	cfg_link ".bashrc"
	cfg_link ".xinitrc"
	cfg_link ".config/bspwm/bspwmrc"
	cfg_link ".config/nvim/init.vim"
	cfg_link ".config/nvim/coc-settings.json"
	cfg_link ".config/polybar/config"
	cfg_link ".config/sxhkd/sxhkdrc"
	cfg_link ".config/termite/config"

	chmod +x -v $GIT_CONF_DIR/.config/bspwm/bspwmrc

	# For bspwm and sxhkd to know where the config is
	echo 'export XDG_CONFIG_DIR=$HOME/.config' >> /etc/profile
}
setup() {
	create_user
	install_packages
	install_configs
}

################################################################################

setup
