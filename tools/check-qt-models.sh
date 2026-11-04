set -eu
printf '\nQT MODELS FILES\n'
ls -ld /usr/lib/cmake/Qt6QmlModels /usr/lib/cmake/Qt6QmlModels/* 2>&1 || true
pacman -Ql qt6-declarative | rg 'Qt6QmlModels|libQt6QmlModels' || true
printf '\nMILOU CMAKE CACHE\n'
rg 'Qt6QmlModels|CMAKE_FIND_ROOT|CMAKE_PREFIX_PATH|CMAKE_IGNORE' /home/alarm/f8-pro-builds/milou-6.7.5-3fL8M3hy/src/build/CMakeCache.txt || true
printf '\nQT FILE VERIFICATION\n'
pacman -Qk qt6-declarative
printf '\nLOCKER PROGRESS\n'
tail -n 5 /home/alarm/f8-pro-builds/kscreenlocker-6.7.5-QcPxbB8c/build.log
