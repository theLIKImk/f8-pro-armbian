#!/bin/bash
wc -l /usr/local/lib/f8-pro/camera-preview.py /usr/local/lib/f8-pro/aiq-backend.py
echo ---
grep -n 'video22\|video31\|mainpath\|rear\|front' /usr/local/lib/f8-pro/aiq-backend.py | head -10
echo ---
grep -n 'video22\|video31\|rear\|front\|后置' /usr/local/lib/f8-pro/camera-preview.py | head -10
echo MARKER_DONE
