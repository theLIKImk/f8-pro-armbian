#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
systemctl --user is-active wireplumber pipewire
journalctl --user -u wireplumber --since '-3 min' --no-pager 2>/dev/null | grep -iE 'error|fail|ucm|alsa' | tail -15
echo DONE
