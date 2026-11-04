set -eu
printf '\nKWIN BUILD\n'
tail -n 6 /home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G/build.log
printf '\nSTYLE BUILD\n'
tail -n 5 /home/alarm/f8-pro-builds/qqc2-breeze-style-6.7.5-VX3Q2G9L/build.log
printf '\nMEMORY\n'
head -n 3 /proc/meminfo
