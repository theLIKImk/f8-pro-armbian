#!/bin/sh
# Runs after systemd basic.target with /proc, /dev and /run available.
set -eu
r=/
c=/run/f8/container
echo 'F8SETUP: network profiles'
mkdir -p "$r/run/f8/hostkeys" "$r/etc/NetworkManager/system-connections" "$r/etc/NetworkManager/conf.d"
count=0
for file in "$c"/etc/NetworkManager/system-connections/*; do
    [ -f "$file" ] && [ ! -L "$file" ] || continue
    cp "$file" "$r/etc/NetworkManager/system-connections/${file##*/}"
    chmod 0600 "$r/etc/NetworkManager/system-connections/${file##*/}"
    count=$((count+1))
done
[ "$count" -gt 0 ] || { echo 'No archived Wi-Fi profile'; exit 1; }
printf '[device]\nwifi.scan-rand-mac-address=no\n[connection]\nwifi.cloned-mac-address=preserve\n' >"$r/etc/NetworkManager/conf.d/90-f8-preserve-mac.conf"
echo 'F8SETUP: test account'
if ! chroot "$r" /usr/bin/getent passwd f8test >/dev/null; then
    chroot "$r" /usr/sbin/useradd -m -U -u 1601 -s /bin/bash f8test
fi
chroot "$r" /usr/sbin/usermod -p '*' f8test
mkdir -p "$r/home/f8test/.ssh"
[ -s "$c/home/alarm/.ssh/authorized_keys" ] && [ ! -L "$c/home/alarm/.ssh/authorized_keys" ]
cp "$c/home/alarm/.ssh/authorized_keys" "$r/home/f8test/.ssh/authorized_keys"
chmod 0700 "$r/home/f8test/.ssh"
chmod 0600 "$r/home/f8test/.ssh/authorized_keys"
echo 'F8SETUP: public-key ownership'
chroot "$r" chown -R f8test:f8test /home/f8test/.ssh
mkdir -p "$r/etc/sudoers.d" "$r/run/sshd"
printf 'f8test ALL=(ALL) NOPASSWD: ALL\n' >"$r/etc/sudoers.d/f8-live-test"
chmod 0440 "$r/etc/sudoers.d/f8-live-test"
cat >"$r/run/f8/sshd_config" <<'EOF'
Port 22
ListenAddress 0.0.0.0
HostKey /run/f8/hostkeys/ssh_host_ed25519_key
HostKey /run/f8/hostkeys/ssh_host_rsa_key
HostKey /run/f8/hostkeys/ssh_host_ecdsa_key
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
echo 'F8SETUP: preserve host identity'
count=0
for kind in ed25519 rsa ecdsa; do
    src="$c/etc/ssh/ssh_host_${kind}_key"
    [ -f "$src" ] && [ ! -L "$src" ] || continue
    cp "$src" "$r/run/f8/hostkeys/"
    chmod 0600 "$r/run/f8/hostkeys/ssh_host_${kind}_key"
    count=$((count+1))
done
[ "$count" -gt 0 ] || { echo 'No archived SSH host identity'; exit 1; }
echo 'F8SETUP: validate SSH'
chroot "$r" /usr/sbin/visudo -cf /etc/sudoers.d/f8-live-test >/dev/null
chroot "$r" /usr/sbin/sshd -t -f /run/f8/sshd_config
echo 'Private network/SSH material copied into RAM; no credentials logged'
