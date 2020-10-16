#!/bin/bash

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
    'newsboat' # rss reader
    'noto-fonts-emoji'
    'nodejs' # for coc
    'npm'
    'ntfs-3g'
    'openssh'
    'openvpn'
    'os-prober'
    'papirus-icon-theme'
    'peek'
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
    'xorg-server'
    'xorg-xinit'
    'xorg-xrandr'
    'zathura' # document viewer with nice dark mode
    'zathura-pdf-mupdf'
)

AUR_PACKAGES=(
    'font-manager'
    'neovim-plug'
    'openvpn-update-resolv-conf'
    'papirus-folders'
    'polybar'
    'rust-analyzer'
    'starship'
    'ttf-iosevka'
    'vim-plug'
)
