set -eu
printf '\nCACHE\n'
grep -E 'Qt6QmlModels|CMAKE_FIND_ROOT|CMAKE_PREFIX_PATH|CMAKE_IGNORE' /home/alarm/f8-pro-builds/milou-6.7.5-3fL8M3hy/src/build/CMakeCache.txt || true
out=$(mktemp -d /tmp/f8-milou-cmake-XXXXXXXX)
set +e
cmake -S /home/alarm/f8-pro-builds/milou-6.7.5-3fL8M3hy/src/milou-6.7.5 -B "$out" -DBUILD_TESTING=OFF --debug-find-pkg=Qt6QmlModels >"$out/config.log" 2>&1
result=$?
set -e
grep -A 10 -B 5 'Qt6QmlModelsConfig\|considered\|NOT FOUND\|Error' "$out/config.log" | head -n 160 || true
printf '\nDEBUG_RESULT=%s\nDEBUG_DIRECTORY=%s\n' "$result" "$out"
