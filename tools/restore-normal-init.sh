#!/bin/sh
# Restore the package's standard init symlink, with a private rollback record.
set -eu
[ "$(id -u)" -eq 0 ] && [ -f /etc/arch-release ] || exit 2
expected=../lib/systemd/systemd
current=$(readlink /usr/bin/init)
case "$current" in
    "$expected"|../libexec/f8-pro/early-init) ;;
    *) echo 'Unexpected init target; refusing modification.' >&2; exit 2 ;;
esac
[ -x /usr/lib/systemd/systemd ] || exit 2
[ "$(nmcli -g 802-11-wireless.cloned-mac-address connection show f8-pro-test-wifi)" = preserve ] || exit 2
grep -q '^wifi.scan-rand-mac-address=no$' /etc/NetworkManager/conf.d/90-f8-pro-mac-preserve.conf || exit 2
umask 077
backup=/var/lib/f8-pro/boot-backup
[ ! -L "$backup" ] || exit 2
mkdir -p "$backup"
chmod 0700 "$backup"
if [ ! -e "$backup/init-link-before-normal.txt" ]; then
    printf '%s\n' "$current" >"$backup/init-link-before-normal.txt"
fi
if [ ! -e "$backup/identity-before-normal.sha256" ]; then
    sha256sum /etc/machine-id /etc/ssh/ssh_host_ed25519_key.pub >"$backup/identity-before-normal.sha256"
fi
if [ "$current" != "$expected" ]; then
    temporary=/usr/bin/.f8-normal-init.new
    [ ! -e "$temporary" ] && [ ! -L "$temporary" ] || exit 2
    ln -s "$expected" "$temporary"
    mv -T -- "$temporary" /usr/bin/init
fi
printf 'Standard init link: '
readlink /usr/bin/init
printf 'Machine/SSH identity comparison: '
sha256sum -c "$backup/identity-before-normal.sha256" >/dev/null
echo PASS
printf 'Wi-Fi MAC policy: preserve, scanning randomization disabled\n'
exit 0
