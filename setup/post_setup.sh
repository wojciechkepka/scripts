#!/bin/bash

COC_EXTENSIONS=(
    'coc-html'
    'coc-css'
    'coc-docker'
    'coc-rust-analyzer'
    'coc-python'
    'coc-yaml'
    'coc-json'
)
NVIM_CONF="$HOME/.config/nvim/init.vim"

################################################################################
. ./common.sh

trap ctrl_c INT

check_nvim() {
    notify "Checking if nvim exists"
    command -v nvim > /dev/null
    if [ $? -eq 1 ]
    then
        echo "Nvim not installed"
        exit 1
    fi
}

install_nvim_pluggins() {
    notify "Installing nvim plugins"
    if [[ -f "$NVIM_CONF" ]]
    then
        nvim -c "PlugInstall|q|q"
    else
        echo "Missing nvim configuration file at $NVIM_CONF"
    fi

}

install_coc_extensions() {
    notify "Installing coc extensions"
    for ext in  "${COC_EXTENSIONS[@]}"
    do
        nvim -c "CocInstall -sync $ext|q"
        if [ $? != 0 ]
        then
            echo "Failed to install $ext"
        fi
    done
}

post_main() {
    check_nvim
    ask "Install nvim plugins?" install_nvim_pluggins
    ask "Install coc extensions?" install_coc_extensions
}

################################################################################

post_main
