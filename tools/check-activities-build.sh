set -eu
printf '\nBUILD PROCESSES\n'
pgrep -af 'makepkg|cmake --build|cc1plus|lto1' | head -n 12 || true
printf '\nBUILD LOG\n'
tail -n 12 /home/alarm/f8-pro-builds/plasma-activities-6.7.5-Cl4QcUFV/build.log 2>/dev/null || true
