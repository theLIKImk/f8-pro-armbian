#!/bin/bash
# C3 编译监控：等到 Image 生成或出错
KB=/var/tmp/f8-pro-armbian/kernel-config-build
for i in $(seq 1 60); do
  if [ -f /tmp/c3-build.log ] && grep -qE 'Error|error:' /tmp/c3-build.log | head -1; then
    echo "BUILD_ERROR:"
    grep -E 'Error|error:' /tmp/c3-build.log | head -5
    exit 1
  fi
  if ls -la "$KB/arch/arm64/boot/Image" 2>/dev/null && [ "$KB/arch/arm64/boot/Image" -nt "$KB/.config" ]; then
    echo "IMAGE_READY"
    ls -la "$KB/arch/arm64/boot/Image"
    exit 0
  fi
  sleep 30
done
echo "TIMEOUT_30MIN"
tail -5 /tmp/c3-build.log
