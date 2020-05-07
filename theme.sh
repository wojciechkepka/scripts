#!/bin/bash

THEME="$1"
CONF_REPO_DIR="/home/wojtek/dev/configs"
THEMES=(
	"ayu"
	"gruvbox"
)

################################################################################
sd() {
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
	sd "s/^(colorscheme $1)/\"\1/g" $XDG_CONFIG_DIR/nvim/init.vim
}
enable_nvim() {
	sd "s/^\"(colorscheme $1)/\1/g" $XDG_CONFIG_DIR/nvim/init.vim
}
change_gtk3_theme() {
	case "$1" in
		"ayu")
			sd "s/(gtk-theme-name=).*/\1Aritim-Dark/g" $XDG_CONFIG_DIR/gtk-3.0/settings.ini
			;;
		"gruvbox")
			echo "gothere"
			sd "s/(gtk-theme-name=).*/\1gruvbox-git/g" $XDG_CONFIG_DIR/gtk-3.0/settings.ini
			;;
		*)
			echo "No GTK theme for $1"
	esac

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
	echo "Enabling $1"
	enable_tmux $1
	enable_bashrc $1
	enable_nvim $1
	enable_polybar $1
	link_alacritty $1
	change_gtk3_theme $1
}
disable_theme() {
	echo "Disabling $1"
	disable_tmux $1
	disable_bashrc $1
	disable_nvim $1
	disable_polybar $1
}

################################################################################

if [[ " ${THEMES[@]} " =~ " $THEME " ]]
then
	echo "Changing theme to $THEME"
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
	echo "------------------------"
	echo -e "Available themes: \n${THEMES[@]}"
	exit 1
fi

echo "------------------------------------------------------"
echo "Run this commands to source files in current terminal:"
echo -e "\ttmux source-file ~/.tmux.conf"
echo -e "\t. ~/.bashrc"
echo "To achieve full effects kill xorg and start a new session with 'startx'"
