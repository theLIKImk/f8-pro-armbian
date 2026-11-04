#!/bin/sh
export XMODIFIERS=@im=fcitx
export QT_IM_MODULES='wayland;fcitx;ibus'
unset GTK_IM_MODULE QT_IM_MODULE SDL_IM_MODULE
