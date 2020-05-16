#!/bin/bash

THEME="$1"
CONF_REPO_DIR="$HOME/dev/configs"
THEMES=(
	"ayu"
	"gruvbox"
    "solarized"
)

################################################################################

msg() {
	echo $1
	echo "------------------------------------------------------"
}
sd() {
	echo "Replacing $2"
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
link_alacritty() {
	ln -sfv $CONF_REPO_DIR/.config/alacritty/$1.yml $XDG_CONFIG_DIR/alacritty/alacritty.yml	
}
disable_nvim() {
    case "$1" in
        "solarized")
            theme="solarized8_high"
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
            theme="solarized8_high"
            ;;
        *)
            theme="$1"
            ;;
    esac
	sd "s/^\"(colorscheme $1)/\1/g" $XDG_CONFIG_DIR/nvim/init.vim
}
change_gtk_theme() {
	case "$1" in
		"ayu")
            theme="Aritim-Dark"
			;;
		"gruvbox")
            theme="gruvbox-gtk"
			;;
        "solarized")
            theme="Solarized-Dark-Orange"
            ;;
		*)
			echo "No GTK theme for $1"
            return 1
	esac

    sd "s/(gtk-theme-name=).*/\1$theme/g" $XDG_CONFIG_DIR/gtk-3.0/settings.ini
    sd "s/(gtk-theme-name=\").*\"$/\1$theme\"/g" $HOME/.gtkrc-2.0

}
enable_polybar() {
	sd "N;s/(;$1\n);(foreground.*)/\1\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/config
	sd "N;s/(;$1\n);(format-foreground.*)/\1\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/config
	sd "N;s/(;$1\n);(label-focused-underline.*)/\1\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/config
}
disable_polybar() {
	sd "N;s/(;$1\n)(foreground.*)/\1;\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/config
	sd "N;s/(;$1\n)(format-foreground.*)/\1;\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/config
	sd "N;s/(;$1\n)(label-focused-underline.*)/\1;\2/1;$!P;$!D;$D" $XDG_CONFIG_DIR/polybar/config
}
enable_theme() {
	msg "Enabling $1"
	enable_tmux $1
	enable_bashrc $1
	enable_nvim $1
	enable_polybar $1
	link_alacritty $1
	change_gtk_theme $1
    change_wallpaper $1
    pkill panel;$XDG_CONFIG_DIR/bspwm/bspwmrc > /dev/null 2>&1 # restart bspwm
	echo "------------------------------------------------------"
}
disable_theme() {
	msg "Disabling $1"
	disable_tmux $1
	disable_bashrc $1
	disable_nvim $1
	disable_polybar $1
	echo "------------------------------------------------------"
}
change_wallpaper() {
    case "$1" in
        "ayu")
            wallpaper="ayu.jpg"
            ;;
        "gruvbox")
            wallpaper="gruvbox.jpg"
            ;;
        "solarized")
            wallpaper="solarized.png"
            ;;
        *)
            echo "No wallpaper for $1"
            return 1
    esac

    wall="$HOME/wallpapers/$wallpaper"
    echo "Changing wallpaper to $wall"

    wall="${wall//\//\\\/}" # need to escape / for sed to work
    sd "s/(feh --bg-fill).*/\1 $wall)/g" $XDG_CONFIG_DIR/bspwm/bspwmrc
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
