#!/bin/sh
echo "=== wpctl status 完整 ==="
wpctl status
echo "=== ucm proc ==="
ls /proc/asound/card0/ | head
echo DONE
