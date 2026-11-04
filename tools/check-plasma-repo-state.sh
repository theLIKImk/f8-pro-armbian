set -eu
printf '\nINSTALLED LOCAL COMPONENTS\n'
pacman -Q plasma-activities layer-shell-qt knighttime kwayland kdecoration
printf '\nNEXT UPGRADE PLAN (READ ONLY)\n'
pacman -Spu --print-format '%n %v'
printf '\nLIBPLASMA BUILD\n'
tail -n 5 /home/alarm/f8-pro-builds/libplasma-6.7.5-UB1Aj9Ih/build.log
