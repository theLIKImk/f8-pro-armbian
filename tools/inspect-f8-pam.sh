#!/bin/sh
echo "=== common-password PAM 栈 ==="
grep -v '^#' /etc/pam.d/common-password | grep -v '^$'
echo "=== common-auth（pam_unix 是否用了 pidfd 相关 helper） ==="
grep -v '^#' /etc/pam.d/common-auth | grep -v '^$'
echo "=== unix_chkpwd 权限 ==="
ls -la /usr/sbin/unix_chkpwd /sbin/unix_chkpwd 2>/dev/null
echo "=== pam_unix 模块时间戳 ==="
ls -la /usr/lib/aarch64-linux-gnu/security/pam_unix.so
echo DONE
