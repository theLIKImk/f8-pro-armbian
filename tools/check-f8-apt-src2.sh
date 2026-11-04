#!/bin/sh
cat /etc/apt/sources.list.d/*.sources 2>/dev/null | head -15
cat /etc/apt/sources.list 2>/dev/null | grep -v '^#' | grep -v '^$' | head -5
echo "---"
ls /var/lib/apt/lists/ | grep -i contents | head -5
echo DONE
