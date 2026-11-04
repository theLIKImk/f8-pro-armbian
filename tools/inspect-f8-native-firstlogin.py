"""Read public offline first-login configuration; never edit a built image."""
from pathlib import Path
root=Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs')
paths=list((root/'etc/profile.d').glob('*'))+list((root/'usr/lib/armbian').glob('*'))
for p in paths:
    if not p.is_file():continue
    try:lines=p.read_text().splitlines()
    except (UnicodeError,OSError):continue
    if any('Create root password' in s or 'not_logged_in_yet' in s or 'firstlogin' in s.lower() for s in lines):
        print('\nFILE',p.relative_to(root))
        for i,line in enumerate(lines):
            if any(x in line.lower() for x in ['create root','not_logged','firstlogin','return','exit','user','password']):
                print(str(i+1)+': '+line[:220])
for rel in ['etc/systemd/system/default.target','etc/systemd/system/getty@tty1.service.d',
 'etc/systemd/system/f8-desktop.target','etc/systemd/system/f8-live-prepare.service','etc/systemd/system/sddm.service.d/90-f8-desktop.conf']:
    p=root/rel;print('\nCONFIG',rel)
    if p.is_symlink():print('SYMLINK',p.readlink())
    elif p.is_dir():
        for f in p.iterdir():
            if f.is_file():print(f.name,f.read_text())
    elif p.is_file():print(p.read_text())
    else:print('absent')
