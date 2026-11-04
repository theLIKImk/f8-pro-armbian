sudo -n dmesg | grep -E 'rkcif-mipi-lvds2' | grep -vE 'sensor info|update sensor' | head -20
echo MARKER_DONE
