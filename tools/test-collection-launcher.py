"""Exercise launcher packaging and sudo failure handling with fake collectors.

No hardware collection, package installation, or real sudo command is executed.
Run on Linux: python3 tools/test-collection-launcher.py
"""
from pathlib import Path
import os
import shutil
import subprocess
import tarfile
import tempfile

launcher = Path(__file__).with_name('run-collect.sh')
with tempfile.TemporaryDirectory(prefix='f8-launcher-test-') as temporary:
    base = Path(temporary)
    app = base / 'tool folder with spaces'
    app.mkdir()
    shutil.copyfile(launcher, app / launcher.name)
    collector = app / 'collect-hardware.sh'
    collector.write_text('#!/bin/sh\nset -eu\nmkdir "$1"\nprintf "%s\\n" "$2" >"$1/mode.txt"\n')
    commands = base / 'fake-bin'
    commands.mkdir()
    (commands / 'id').write_text('#!/bin/sh\nprintf "1000\\n"\n')
    (commands / 'sudo').write_text('#!/bin/sh\nexit 1\n')
    for path in commands.iterdir():
        path.chmod(0o755)
    environment = dict(os.environ, PATH=str(commands) + ':' + os.environ['PATH'])
    output = base / 'output parent with spaces'
    output.mkdir()
    run = subprocess.run(['sh', str(app / launcher.name), str(output)],
                         env=environment, capture_output=True, text=True, check=True)
    archives = list(output.glob('*.tar.gz'))
    assert len(archives) == 1, run.stdout
    with tarfile.open(archives[0]) as tar:
        names = tar.getnames()
        note = next(name for name in names if name.endswith('/admin-collection.txt'))
        mode = next(name for name in names if name.endswith('/desktop/mode.txt'))
        assert b'skipped' in tar.extractfile(note).read()
        assert tar.extractfile(mode).read() == b'all\n'
    # A fake privileged collector must receive system mode, never desktop mode.
    (commands / 'sudo').write_text('#!/bin/sh\ncase "$1" in -v|chown) exit 0;; sh) shift; exec sh "$@";; *) exit 2;; esac\n')
    subprocess.run(['sh', str(app / launcher.name), str(output)],
                   env=environment, capture_output=True, text=True, check=True)
    archives = list(output.glob('*.tar.gz'))
    assert len(archives) == 2
    system_archives = 0
    for archive in archives:
        with tarfile.open(archive) as tar:
            matches = [name for name in tar.getnames() if name.endswith('/system/mode.txt')]
            if matches:
                system_archives += 1
                assert tar.extractfile(matches[0]).read() == b'system\n'
    assert system_archives == 1
    # Running as root must stop before invoking any collector or creating output.
    (commands / 'id').write_text('#!/bin/sh\nprintf "0\\n"\n')
    denied = subprocess.run(['sh', str(app / launcher.name), str(output)],
                            env=environment, capture_output=True, text=True)
    assert denied.returncode == 1 and 'without sudo' in denied.stderr
    assert len(list(output.glob('*.tar.gz'))) == 2
print('PASS: spaced paths, sudo denial, separate system mode, repeated runs, root launcher blocked')
