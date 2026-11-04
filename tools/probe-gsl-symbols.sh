#!/bin/sh
# Read only kernel symbol metadata, never live process or kernel memory.
set -eu
awk '$3 == "_text" || $3 == "_stext" || $3 == "_end" || $3 ~ /gsl/ || $3 == "report_data" { print }' /proc/kallsyms
