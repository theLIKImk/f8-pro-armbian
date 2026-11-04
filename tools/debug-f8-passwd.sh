#!/bin/sh
# 复现细节：passwd 以 euid=0 运行仍 authentication failure。
# pam_unix passwd:chauthtok 先校验当前密码。日志无 unix_chkpwd 报错。
# 测试 unix_chkpwd 是否也用了 pidfd（新版 shadow/pam helper 可能同样依赖）：
sudo -n /usr/sbin/unix_chkpwd f8test chkexpiry </dev/null; echo "chkexpiry exit=$?"
echo "=== 直接 root 改密测试（不实际修改，回车两次取错误路径） ==="
echo -e '\n\n' | sudo -n passwd f8test 2>&1 | head -5
echo "=== seccomp/ptrace 限制线索：strace 一次 pam_unix helper ==="
sudo -n sh -c 'echo -e "\n\n" | passwd f8test 2>&1' | head -6
echo DONE
