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
    'bat'
    'bspwm'
    'ccls'
    'chrony'
    'ctags'
    'dhcpcd'
    'dkms'
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
    'iw' # WIFI
    'iwd'
    'libimobiledevice'
    'libnotify'
    'lightdm'
    'lightdm-webkit2-greeter'
    'lightdm-webkit-theme-litarval'
    'linux-headers'
    'lvm2'    
    'man-db'
    'man-pages'
    'mupdf'
    'nautilus'
    'neovim'
    'net-tools'
    'noto-fonts-emoji'
    'nodejs' # for coc
    'npm'
    'ntfs-3g'
    'openssh'
    'os-prober'
    'perf'
    'perl-cgi'
    'picom' # new compton
    'pidgin'
    'pidgin-libnotify'
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
    'sysstat'
    'termite'
    'tcpdump'
    'thunderbird'
    'tmux'
    'ttf-fira-code'
    'ttf-font-awesome'
    'ttf-hack'
    'unzip'
    'usbutils'
    'vim'
    'vlc'
    'w3m' # for image display in Ranger
    'wget'
    'xclip'
    'xorg-xinit'
    'xorg-xrandr'
    'zathura' # document viewer with nice dark mode
    'zathura-pdf-mupdf'
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
. ./common.sh

trap ctrl_c INT

check_root() {
    # Check for root permissions
    if [ "$EUID" -ne 0 ]
      then notify "Please run as root"
      exit 1
    fi
}
create_user() {
    notify "Creating user $USERNAME"
    useradd --groups wheel --create-home --shell /bin/bash $USERNAME
    echo "Enter password for user $USERNAME"
    passwd $USERNAME
    create_home_dirs
    install_sudo
}
create_home_dirs() {
    mkdir --parents --verbose $USERHOME/screenshots \
                              $USERHOME/wallpapers \
                              $USERHOME/Downloads \
                              $USERHOME/Documents
}
build_yay() {
    # Install necessary packages for yay build
    pacman --sync --needed --noconfirm base-devel git wget go

    # Create a temporary dir
    local bld_dir="/tmp/$(date +%s)-yay"
    notify "Creating $bld_dir"
    mkdir --parents $bld_dir
    cd $bld_dir

    # Clone package query and yay
    git clone $PACKAGE_QUERY_REPO
    git clone $YAY_REPO

    # Build package-query
    notify "Building package-query"
    cd package-query && makepkg -si
    cd ..

    # Build yay
    notify "Building yay"
    cd yay && makepkg -si
    cd /
}
install_sudo() {
    notify "Installing sudo"
    command -v sudo
    if [ $? -eq 1 ]
    then
        pacman --sync --noconfirm sudo
    fi
    notify "Enabling sudo for group wheel"
    echo "%wheel ALL=(ALL) ALL" > /etc/sudoers.d/01wheel
    chmod 440 /etc/sudoers.d/01wheel
}
install_and_run_reflector() {
    command -v reflector
    if [ $? -eq 1 ]
    then
        pacman --sync --noconfirm reflector
    fi
    notify "Running reflector"
    reflector -l 100 --sort rate --save /etc/pacman.d/mirrorlist
}
install_packages() {
    ask "Run reflector?" install_and_run_reflector
    command -v yay
    if [ $? -eq 1 ]
    then
        build_yay
    fi
    notify "Installing base packages"
    sudo -u $USERNAME yay -S --noconfirm "${BASE_PACKAGES[@]}"
    notify "Installing aur packages"
    sudo -u $USERNAME yay -S --noconfirm "${AUR_PACKAGES[@]}"
}
cfg_link() {
    local cfg_file="$1"
    ln --symbolic --verbose $GIT_CONF_DIR/$cfg_file $USERHOME/$cfg_file
}
etc_link() {
    local cfg_file="$1"
    ln --symbolic --verbose $GIT_CONF_DIR$cfg_file $cfg_file
}
install_themes() {
    notify "Installing themes"
    mkdir --parents --verbose $THEME_DIR \
                              $ICONS_DIR
    
    tar --extract --file=$GIT_CONF_DIR/themes/Sweet-Dark.tar.xz --directory=$THEME_DIR
    tar --extract --file=$GIT_CONF_DIR/icon_themes/Sweet-Purple.tar.xz --directory=$ICONS_DIR
    tar --extract --file=$GIT_CONF_DIR/icon_themes/Sweet-Teal.tar.xz --directory=$ICONS_DIR
    unzip $GIT_CONF_DIR/themes/Solarized-Dark-Orange_2.0.1.zip -d $THEME_DIR
    git clone https://github.com/wojciechkepka/gruvbox-gtk $THEME_DIR/gruvbox-gtk
    git clone https://github.com/wojciechkepka/Aritim-Dark $THEME_DIR/Aritim-dark
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
                      $XDG_CONF_DIR/dunst \
                      $XDG_CONF_DIR/rofi \
                      $XDG_CONF_DIR/picom \
                      $XDG_CONF_DIR/zathura

    git clone $GIT_CONF_REPO $GIT_CONF_DIR
    
    conf_files=(
        ".bashrc"
        ".gtkrc-2.0"
        ".tmux.conf"
        ".xinitrc"
        ".Xresources"
        ".config/alacritty/alacritty.yml"
        ".config/bspwm/bspwmrc"
        ".config/nvim/init.vim"
        ".config/nvim/coc-settings.json"
        ".config/polybar/colors.ini"
        ".config/polybar/config.ini"
        ".config/polybar/modules.ini"
        ".config/sxhkd/sxhkdrc"
        ".config/termite/config"
        ".config/dunst/dunstrc"
        ".config/gtk-3.0/settings.ini"
        ".config/gtk-3.0/gtk.css"
        ".config/picom/picom.conf"
        ".config/rofi/config.rasi"
        ".config/zathura/zathurarc"
    )

    for file in "${conf_files[@]}"
    do
        cfg_link $file
    done

    etc_files=(
        "/etc/lightdm/lightdm.conf"
        "/etc/lightdm/lightdm-webkit2-greeter.conf"
    )

    for file in "${etc_files[@]}"
    do
        etc_link $file
    done

    chmod +x --verbose $GIT_CONF_DIR/.config/bspwm/bspwmrc

    # For bspwm and sxhkd to know where the config is
    echo 'export XDG_CONFIG_DIR=$HOME/.config' >> /etc/profile
}
setup() {
    ask "Create user?" create_user
    ask "Install Packages?" install_packages
    ask "Install configs?" install_configs
    ask "Install themes?" install_themes

    chown --recursive $USERNAME:$USERNAME $USERHOME
}

################################################################################

setup
