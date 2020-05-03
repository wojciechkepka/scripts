#!/bin/bash

USERNAME='wojtek'
USERHOME="/home/$USERNAME"
GIT_CONF_REPO='https://github.com/wojciechkepka/configs'
GIT_CONF_DIR="$USERHOME/dev/configs"
XDG_CONF_DIR="$USERHOME/.config"
THEME_DIR="$USERHOME/.themes"
ICONS_DIR="$USERHOME/.icons"

PACKAGE_QUERY_REPO='https://aur.archlinux.org/package-query.git'
YAY_REPO='https://aur.archlinux.org/yay.git'

BASE_PACKAGES=(
	'alacritty' # <3<3<3
	'alsa-firmware'
	'alsa-utils'
	'amd-ucode'
	'bspwm'
	'ccls'
	'chrony'
	'ctags'
	'dhcpcd'
	'dunst' #notification server
	'exa' # better ls
	'fd' # better find
	'feh' # Image viewer
	'filezilla'
	'firefox'
	'flameshot' # Lightweight screenshot tool
	'git'
	'gnome-keyring'
	'gpick' # Color picker
	'htop'
	'i3lock'
	'iw' # WIFI
	'iwd'
	'libnotify'
	'man-db'
	'man-pages'
	'mupdf'
	'nautilus'
	'neovim'
	'net-tools'
	'noto-fonts-emoji'
	'openssh'
	'perf'
	'picom' # new compton
	'pidgin'
	'powerline-fonts'
	'powertop'
	'pulseaudio'
	'python-pip'
	'ranger'
	'redshift'
	'ripgrep'
	'rofi' # menu and app launcher
	'sudo'
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
notify() {
	local msg="$1"
	echo "################################################################################"
	echo "INFO: $msg"
	echo "################################################################################"
}
check_root() {
	# Check for root permissions
	if [ "$EUID" -ne 0 ]
	  then notify "Please run as root"
	  exit 1
	fi
}
create_user() {
	notify "Creating user $USERNAME"
	useradd --groups sudo --create-home --shell /bin/bash $USERNAME
	echo "Enter password for user $USERNAME"
	passwd $USERNAME
	create_home_dirs
}
create_home_dirs() {
	mkdir --parents --verbose $USERHOME/screenshots \
				  $USERHOME/wallpapers \
}
build_yaourt() {
	# Install necessary packages for yaourt build
	pacman --sync --needed base-devel yail git wget

	# Create a temporary dir
	local bld_dir="/tmp/$(date +%s)-yaourt"
	notify "Creating $bld_dir"
	mkdir --parents $bld_dir
	cd $bld_dir

	# Clone package query and yaourt
	git clone $PACKAGE_QUERY_REPO
	git clone $YAOURT_REPO

	# Build package-query
	notify "Building package-query"
	cd package-query && makepkg -si
	cd ..

	# Build yaourt
	notify "Building yaourt"
	cd yaourt && makepkg -si
	cd /
}
install_and_run_reflector() {
	pacman --sync reflector
	notify "Running reflector"
	reflector -l 100 --sort rate --save /etc/pacman.d/mirrorlist
}
install_packages() {
	install_and_run_reflector
	command -v yaourt
	if [ $? -eq 0 ]
	then
		build_yaourt
	fi
	notify "Installing base packages"
	yaourt -S --noconfirm "${BASE_PACKAGES[@]}"
	notify "Installing aur packages"
	yaourt -S --noconfirm "${AUR_PACKAGES[@]}"
}
cfg_link() {
	local cfg_file="$1"
	ln --symbolic -verbose $GIT_CONF_DIR/$cfg_file $USERHOME/$cfg_file
}
install_themes() {
	notify "Installing themes"
	mkdir --parents --verbose $THEME_DIR \
				  $ICONS_DIR
	
	tar --extract --file=$GIT_CONF_REPO/Sweet-Dark.tar.xz --directory=$THEME_DIR
	tar --extract --file=$GIT_CONF_REPO/Sweet-Purple.tar.xz --directory=$ICONS_DIR
}
install_configs() {
	notify "Installing configs"
	mkdir --parents --verbose $GIT_CONF_DIR \
				  $XDG_CONF_DIR \
		    		  $XDG_CONF_DIR/alacritty \
		    		  $XDG_CONF_DIR/bspwm \
		    		  $XDG_CONF_DIR/nvim \
		    		  $XDG_CONF_DIR/polybar \
		    		  $XDG_CONF_DIR/sxhkd \
		    		  $XDG_CONF_DIR/termite \
		    		  $XDG_CONF_DIR/gtk-3.0 \
		    		  $XDG_CONF_DIR/dunst

	git clone $GIT_CONF_REPO $GIT_CONF_DIR

	cfg_link ".tmux.conf"
	cfg_link ".bashrc"
	cfg_link ".xinitrc"
	cfg_link ".gtkrc-2.0"
	cfg_link ".config/alacritty/alacritty"
	cfg_link ".config/bspwm/bspwmrc"
	cfg_link ".config/nvim/init.vim"
	cfg_link ".config/nvim/coc-settings.json"
	cfg_link ".config/polybar/config"
	cfg_link ".config/sxhkd/sxhkdrc"
	cfg_link ".config/termite/config"
	cfg_link ".config/dunst/dunstrc"
	cfg_link ".config/gtk-3.0/settings.ini"
	cfg_link ".config/gtk-3.0/gtk.css"

	chmod +x --verbose $GIT_CONF_DIR/.config/bspwm/bspwmrc

	# For bspwm and sxhkd to know where the config is
	echo 'export XDG_CONFIG_DIR=$HOME/.config' >> /etc/profile
}
setup() {
	create_user
	install_packages
	install_configs
	install_themes

	chown --recursive $USERNAME:$USERNAME $USERHOME
}

################################################################################

setup
