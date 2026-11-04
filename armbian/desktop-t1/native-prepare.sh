#!/bin/sh
# First-boot native root setup. No Wi-Fi password or shared host private key in image.
set -eu
test -f /etc/f8-pro-native-desktop-t1
mkdir -p /run/f8 /run/sshd
mkdir -p /etc/NetworkManager/conf.d
printf '[device]\nwifi.scan-rand-mac-address=no\n[connection]\nwifi.cloned-mac-address=preserve\n' >/etc/NetworkManager/conf.d/90-f8-preserve-mac.conf
if ! getent passwd f8test >/dev/null; then
    useradd -m -U -u 1601 -s /bin/bash f8test
    usermod -p '*' f8test
fi
mkdir -p /home/f8test/.ssh
if [ ! -s /home/f8test/.ssh/authorized_keys ]; then
    cp /usr/share/f8-pro/test-authorized-keys /home/f8test/.ssh/authorized_keys
fi
chmod 0700 /home/f8test/.ssh
chmod 0600 /home/f8test/.ssh/authorized_keys
chown -R f8test:f8test /home/f8test/.ssh
mkdir -p /etc/sudoers.d
printf 'f8test ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/f8-live-test
chmod 0440 /etc/sudoers.d/f8-live-test
ssh-keygen -A
cat >/run/f8/sshd_config <<'EOF'
Port 22
ListenAddress 0.0.0.0
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
UsePAM yes
AllowUsers f8test
AuthorizedKeysFile .ssh/authorized_keys
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
Subsystem sftp internal-sftp
PidFile /run/f8/sshd.pid
EOF
visudo -cf /etc/sudoers.d/f8-live-test >/dev/null
sshd -t -f /run/f8/sshd_config
echo 'F8 NATIVE: user and SSH initialized; connect Wi-Fi from desktop on first boot'
