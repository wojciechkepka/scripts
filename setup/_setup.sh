#!/bin/bash

USERNAME=""
USERHOME="/home/$USERNAME"
GIT_CONF_REPO='https://github.com/wojciechkepka/configs'
GIT_CONF_DIR="$USERHOME/dev/configs"
XDG_CONF_DIR="$USERHOME/.config"
THEME_DIR="$USERHOME/.themes"
ICONS_DIR="$USERHOME/.icons"

PACKAGE_QUERY_REPO='https://aur.archlinux.org/package-query.git'
YAY_REPO='https://aur.archlinux.org/yay.git'

HOSTNAME=""
################################################################################

. ./_packages.sh
. ./_common.sh
. ./_post_setup.sh

trap ctrl_c INT

check_root() {
    # Check for root permissions
    if [ "$EUID" -ne 0 ]
      then notify "Please run as root"
      exit 1
    fi
}
create_user() {
    echo "Enter username: "
    read USERNAME
    USERHOME="/home/$USERNAME"
    notify "Creating user $USERNAME"
    useradd --groups wheel --create-home --shell /bin/bash $USERNAME
    echo "Enter password for user $USERNAME"
    passwd $USERNAME
    create_home_dirs
    install_sudo

    echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/01user
    chmod 440 /etc/sudoers.d/01user
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

    chown -R $USERNAME:$USERNAME $bld_dir

    # Build package-query
    notify "Building package-query"
    cd package-query && sudo -u $USERNAME makepkg -si
    cd ..

    # Build yay
    notify "Building yay"
    cd yay && sudo -u $USERNAME makepkg -si
    cd /
}
install_sudo() {
    command -v sudo
    if [ $? -eq 1 ]
    then
        notify "Installing sudo"
        pacman --sync --noconfirm sudo
    fi
    if [ ! -f /etc/sudoers.d/01wheel ]
    then
        notify "Enabling sudo for group wheel"
        echo "%wheel ALL=(ALL) ALL" > /etc/sudoers.d/01wheel
        chmod 440 /etc/sudoers.d/01wheel
    fi
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
}
cfg_link() {
    local cfg_file="$1"
    ln --symbolic --force --verbose $GIT_CONF_DIR/$cfg_file $USERHOME/$cfg_file
}
etc_link() {
    local cfg_file="$1"
    ln --symbolic --force --verbose $GIT_CONF_DIR$cfg_file $cfg_file
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
                      $XDG_CONF_DIR/zathura \
                      $USERHOME/.newsboat


    git clone $GIT_CONF_REPO $GIT_CONF_DIR
    
    conf_files=(
        ".bashrc"
        ".gtkrc-2.0"
        ".newsboat"
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
        ".config/starship.toml"
    )

    for file in "${conf_files[@]}"
    do
        cfg_link $file
    done

    etc_files=(
        "/etc/lightdm/lightdm.conf"
        "/etc/lightdm/lightdm-webkit2-greeter.conf"
        "/etc/mkinitcpio.conf"
    )

    for file in "${etc_files[@]}"
    do
        etc_link $file
    done

    chmod +x --verbose $GIT_CONF_DIR/.config/bspwm/bspwmrc

    # For bspwm and sxhkd to know where the config is
    echo 'export XDG_CONFIG_DIR=$HOME/.config' >> /etc/profile
}
################################################################################

generate_locale() {
   sed -r -i -e "s/#(en_US.UTF-8)/\1/g" /etc/locale.gen
   sed -r -i -e "s/#(pl_PL.UTF-8)/\1/g" /etc/locale.gen
   locale-gen
}
set_lang() {
    local lang="$1"
    echo "LANG=$lang" > /etc/locale.conf
}
set_keymap() {
    local keymap="$1"
    echo "KEYMAP=$keymap" > /etc/vconsole.conf
}
set_timezone() {
    local region="$1"
    local city="$2"
    ln -sfv /usr/share/zoneinfo/$region/$city /etc/localtime
    if [ $? == 0 ]
    then
        hwclock --systohc
    fi
}
set_hostname() {
    echo "Enter hostname: "
    read HOSTNAME
    echo $HOSTNAME > /etc/hostname
}
create_hosts() {
    echo "127.0.0.1     localhost
::1         localhost" > /etc/hosts
}

################################################################################

setup() {
    create_hosts
    generate_locale
    set_lang "en_US.UTF-8"
    set_keymap "pl"
    set_timezone "Europe" "Warsaw"
    set_hostname

    ask "Create user?" create_user
    ask "Install Packages?" install_packages
    ask "Install configs?" install_configs
    ask "Install themes?" install_themes
    ask "Run post setup?" post_setup

    chown --recursive $USERNAME:$USERNAME $USERHOME
}

setup
