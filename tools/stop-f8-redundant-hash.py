"""Stop only the obsolete native pre-finalization hash; disk image is preserved."""
import os
from pathlib import Path
import signal
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        args=(p/'cmdline').read_bytes().split(b'\0')
        pack=any(x.endswith(b'/pack-f8-native-desktop-t1.py') for x in args)
        finalize=any(x.endswith(b'/finalize-f8-desktop-t1.py') for x in args)
        if not (pack or finalize):continue
        if pack:assert b'--resume-fsck-image' in args
        if finalize:
            project=Path(__file__).resolve().parents[1]
            assert not (project/'outputs/armbian/official-f8-desktop-t1/F8_ARMBIAN_NATIVE_DESKTOP_T1.zip.part').exists()
        os.kill(int(p.name),signal.SIGTERM)
        print('Stopped redundant pre-finalization hash; completed ext4 remains intact')
    except OSError:pass
