ls ~/Pictures/F8Camera/ 2>/dev/null | head -6
echo M1
systemctl is-active f8-camera-start.service
echo M2
ls ~/Pictures/F8Camera/*.png 2>/dev/null | wc -l
echo MARKER_DONE
