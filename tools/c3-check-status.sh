#!/bin/bash
# 查编译状态汇总
if [ -f /tmp/c3-build.log ]; then
  echo "LOG_FOUND $(stat -c %s /tmp/c3-build.log) bytes"
  grep -E 'gc5035|ov8858' /tmp/c3-build.log | head -4
  tail -4 /tmp/c3-build.log
else
  echo LOG_MISSING
  find /root /var/tmp -name 'c3-build.log' -mmin -90 2>/dev/null | head -3
fi
echo ---
ps aux | grep -cE 'aarch64.*gcc' || true
Image=/var/tmp/f8-pro-armbian/kernel-config-build/arch/arm64/boot/Image
stat -c '%y %s' "$Image"
