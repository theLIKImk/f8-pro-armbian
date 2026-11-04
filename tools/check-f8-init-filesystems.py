"""Exercise the real init helper under target ARM64 BusyBox with filesystem fixtures."""
import json
from pathlib import Path
import shlex
import subprocess
import tempfile

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
init = P / 'armbian/initramfs/evaluation-init.sh'
subprocess.run(['sh', '-n', str(init)], check=True)
helpers = init.read_text().split('mkdir -p /dev /proc /sys /run', 1)[0]
busybox = B / 'initramfs-tools/usr/bin/busybox'
assert busybox.is_file()
cases = [
    ('builtin-no-load', 'nodev\toverlay\n\tsquashfs\n',
     'printf called >> CALLS; return 97', 'ensure_fs overlay && ensure_fs squashfs', 0, False),
    ('module-load-failure', '', 'printf called >> CALLS; return 1', 'ensure_fs overlay', 1, True),
    ('module-load-registers-filesystem', '',
     'printf "nodev\\toverlay\\n" > FIXTURE; printf called >> CALLS; return 0', 'ensure_fs overlay', 0, True),
    ('module-success-without-filesystem', '', 'printf called >> CALLS; return 0', 'ensure_fs overlay', 1, True),
    ('nodev-is-not-filesystem', 'nodev\toverlay\n', 'return 97', 'fs_available nodev', 1, False),
]
results = []
with tempfile.TemporaryDirectory(prefix='fs-check-', dir=B) as temp:
    root = Path(temp)
    fixture, calls = root / 'filesystems', root / 'calls'
    for name, contents, loader, command, expected, loaded in cases:
        fixture.write_text(contents)
        if calls.exists():
            calls.unlink()
        code = helpers.replace('/proc/filesystems', shlex.quote(str(fixture)))
        loader = loader.replace('FIXTURE', shlex.quote(str(fixture))).replace('CALLS', shlex.quote(str(calls)))
        code += '\nmodprobe() { ' + loader + '; }\n' + command + '\n'
        result = subprocess.run(['qemu-aarch64-static', str(busybox), 'sh', '-c', code], capture_output=True, text=True)
        assert result.returncode == expected and calls.exists() == loaded, (name, result.returncode, result.stderr)
        results.append({'case': name, 'passed': True})
report = {'scope': 'Target shell helper tests only; no kernel module loaded or filesystem mounted', 'cases': results}
out = P / 'analysis/armbian/initramfs'
out.mkdir(parents=True, exist_ok=True)
(out / 'filesystem-helper-checks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
