#!/bin/sh
pactl list cards | sed -n '/Profile/,/^		/p' | head -30
echo ---
pactl list cards | grep -iE 'Active Profile|profile:' | head -10
echo DONE
