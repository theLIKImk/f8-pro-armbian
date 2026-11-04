#!/bin/sh
amixer -c 0 scontrols | grep -iE 'mic|main'
echo DONE
