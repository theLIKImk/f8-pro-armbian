#!/bin/sh
alsactl --version 2>&1 | head -2
alsactl help 2>&1 | grep -iE 'save|store|monitor' | head -6
echo ---
# rdaemon mode: state saved on exit via kill save_and_quit; test store command form
alsactl store 0 2>&1 | head -2
grep -A3 "name 'PCM Volume'" /var/lib/alsa/asound.state | grep 'value\.'
stat -c '%y' /var/lib/alsa/asound.state
