#!/bin/bash

THEME="$1"
CONF_REPO_DIR="$HOME/dev/configs"
THEMES=(
    "ayu"
    "gruvbox"
    "solarized"
    "nord"
    "xbliss"
)

################################################################################

msg() {
    echo $1
    echo "------------------------------------------------------"
}
sd() {
    echo "Replacing $2"
    [ ! -z $DEBUG ] && echo -e "\tusing pattern '$1'"
    sed -r -i --follow-symlinks -e "$1" $2
}
enable_tmux() {
    sd "s/^#(set.*#$1)/\1/g" $HOME/.tmux.conf
}
disable_tmux() {
    sd "s/^(set.*#$1)/#\1/g" $HOME/.tmux.conf
}
enable_bashrc() {
    sd "s/^#(export PS1.*#$1)/\1/g" $HOME/.bashrc
}
disable_bashrc() {
    sd "s/^(export PS1.*#$1)/#\1/g" $HOME/.bashrc
}
enable_starship() {
    sd "N;s/(#xbliss\n)#(style = .*)/\1\2/1;$!P;$!D" ~/.config/starship.toml
}
disable_starship() {
    sd "N;s/(#xbliss\n)(style = .*)/\1\#\2/1;$!P;$!D" ~/.config/starship.toml
}
change_alacritty() {
    sd "s/(colors: \*).*/\1$1/g" $XDG_CONFIG_DIR/alacritty/alacritty.yml
}
disable_nvim() {
    case "$1" in
        "solarized")
            theme="solarized8_flat"
            ;;
        *)
            theme="$1"
            ;;
    esac
    sd "s/^(colorscheme $1)/\"\1/g" $XDG_CONFIG_DIR/nvim/init.vim
}
enable_nvim() {
    case "$1" in
        "solarized")
            theme="solarized8_flat"
            ;;
        *)
            theme="$1"
            ;;
    esac
    sd "s/^\"(colorscheme $1)/\1/g" $XDG_CONFIG_DIR/nvim/init.vim
}
change_gtk_theme() {
    case "$1" in
        "ayu" | "nord")
            theme="Aritim-Dark"
            ;;
        "gruvbox")
            theme="gruvbox-gtk"
            ;;
        "solarized")
            theme="Solarized-Dark-Orange"
            ;;
        "xbliss")
            theme="Dracula"
            ;;
        *)
            echo "No GTK theme for $1"
            return 1
    esac

    sd "s/(gtk-theme-name=).*/\1$theme/g" $XDG_CONFIG_DIR/gtk-3.0/settings.ini
    sd "s/(gtk-theme-name=\").*\"$/\1$theme\"/g" $HOME/.gtkrc-2.0
    sd "s/^(theme-name=).*/\1$theme/g" /etc/configs/etc/lightdm/lightdm-gtk-greeter.conf

}
enable_polybar() {
    sd "N;s/(;$1\n);(foreground.*)/\1\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/config.ini
    sd "N;s/(;$1\n);(format-foreground.*)/\1\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/modules.ini
    sd "N;s/(;$1\n);(label-focused-underline.*)/\1\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/modules.ini

    case "$1" in
        "xbliss")
            bg="xbliss-bg"
            ;;
        "solarized")
            bg="solarized-bg"
            ;;
        *)
            bg="common-bg"
            ;;
    esac

    sd "s/^(background =).*$/\1 \${colors.$bg}/1" $XDG_CONFIG_DIR/polybar/config.ini
}
disable_polybar() {
    sd "N;s/(;$1\n)(foreground.*)/\1;\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/config.ini
    sd "N;s/(;$1\n)(format-foreground.*)/\1;\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/modules.ini
    sd "N;s/(;$1\n)(label-focused-underline.*)/\1;\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/modules.ini
}
enable_theme() {
    msg "Enabling $1"
    enable_tmux $1
    enable_bashrc $1
    enable_nvim $1
    enable_polybar $1
    enable_starship $1
    change_alacritty $1
    change_gtk_theme $1
    change_wallpaper $1
    echo "------------------------------------------------------"
}
disable_theme() {
    msg "Disabling $1"
    disable_tmux $1
    disable_bashrc $1
    disable_nvim $1
    disable_polybar $1
    disable_starship $1
    echo "------------------------------------------------------"
}
change_wallpaper() {
    case "$1" in
        "ayu")
            horizontal="ayu.png"
            vertical="crosshair.jpg"
            ;;
        "gruvbox")
            horizontal="gruvbox.jpg"
            vertical="gruvbox_vertical.jpg"
            ;;
        "solarized")
            horizontal="solarized_arch.png"
            vertical="solarized_arch_vertical.png"
            ;;
        "nord")
            horizontal="nord_arch.png"
            vertical="nord_arch_vertical.png"
            ;;
        "xbliss")
            horizontal="xbliss_arch.png"
            vertical="xbliss_arch_vertical.png"
            ;;
        *)
            echo "No wallpaper for $1"
            return 1
    esac

    vertical="$HOME/wallpapers/$vertical"
    horizontal="$HOME/wallpapers/$horizontal"
    echo "Changing wallpaper to $horizontal and $vertical"

    horizontal="${horizontal//\//\\\/}" # need to escape / for sed to work
    vertical="${vertical//\//\\\/}"
    sd "s/(feh --bg-fill).*/\1 $vertical --bg-fill $horizontal/g" $XDG_CONFIG_DIR/bspwm/bspwmrc
    sd "s/(background=).*( # horizontal)/\1$horizontal\2/g" /etc/configs/etc/lightdm/lightdm-gtk-greeter.conf
    sd "s/(background=).*( # vertical)/\1$vertical\2/g" /etc/configs/etc/lightdm/lightdm-gtk-greeter.conf
}

################################################################################

if [[ " ${THEMES[@]} " =~ " $THEME " ]]
then
    msg "Changing theme to $THEME"
    for theme in "${THEMES[@]}"
    do
        if [[ ! $theme == $THEME ]]
        then
            disable_theme $theme
        else
            enable_theme $theme
            pkill panel;$XDG_CONFIG_DIR/bspwm/bspwmrc > /dev/null 2>&1 # restart bspwm
            tmux source-file $HOME/.tmux.conf
        fi
    done
else
    echo "Unsupported theme $THEME"
    echo -e "Available themes: \n${THEMES[@]}"
    exit 1
fi

echo "Run this commands to source files in current terminal:"
echo -e "\ttmux source-file ~/.tmux.conf"
echo -e "\t. ~/.bashrc"
echo "To achieve full effects kill xorg with:"
echo -e "\tpkill xinit"
echo "And start a new session with:"
echo -e "\tstartx"
