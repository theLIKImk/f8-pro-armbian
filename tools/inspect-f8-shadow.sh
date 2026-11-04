#!/bin/sh
# 关键发现：pidfd_open 可用（ret=4）！内核支持 pidfd。
# 那么 polkit 报 "Pidfd not supported" 另有原因——但不影响，setuid fallback 已工作。
# passwd 失败也另找原因。日志显示 passwd[3087] authentication failure; euid=0。
# root 改 f8test 密码不需要旧密码！pam_unix chauthtok 的 preliminary check 是
# "authentication failure"——即第一次（as root）调用还是走了 current password 校验？
# 不对：root 改他人密码不问 current。问 current 说明用户自己跑的 passwd。
# 用户报"输入passwd后报错"——是 f8test 自己改自己密码。自己改自己需要旧密码，
# pam_unix 会用 unix_chkpwd 校验。unix_chkpwd 是 setgid shadow（正常）。
# 失败可能是：helper 通信或 shadow 文件本身问题。检查 shadow 内容开头：
sudo -n head -c 100 /etc/shadow | cat -v; echo
echo "=== f8test 条目 ==="
sudo -n grep f8test /etc/shadow | cut -c1-30
echo "=== 尝试让用户自己交互改（发给用户操作）==="
echo DONE
