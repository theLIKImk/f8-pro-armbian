#!/bin/sh
# 上次测试两行空密码导致不匹配，属正常路径。真正改一次验证 root 能否成功：
# （将实际把 f8test 密码设为同一密码不行——需要知道当前密码。改为检查 pam_unix
#  update helper（pam_unix_passwd 在 euid0 时直接写 shadow，为何失败？）
# 关键疑点：Ubuntu 26.04 pam_unix 新版用 pidfd 验证调用者身份！
echo "=== 检查内核 pidfd 支持 ==="
grep -i pidfd /proc/kallsyms 2>/dev/null | head -3
sudo -n sh -c 'grep -ci pidfd /proc/kallsyms'
echo "=== clone3/pidfd_send_signal syscall 可用性 ==="
sudo -n python3 -c "
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
# pidfd_open(0) - probe
r = libc.syscall(434, os.getpid(), 0)
print('pidfd_open(434) ret=', r, 'errno=', ctypes.get_errno())
"
echo "=== journal 中的 pam 报错全量 ==="
sudo -n journalctl --since '-20 min' --no-pager -q 2>/dev/null | grep -iE 'pam|passwd' | tail -15
echo DONE
