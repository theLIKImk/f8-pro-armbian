"""Record R4 PID1 and RAM overlay evidence from preserved hardware logs."""
import hashlib
import json
from pathlib import Path
import re

P = Path(__file__).resolve().parents[1]
logs = P / 'local/hardware/armbian-6.1-r4-20261029-01'
def read(name):
    return (logs / name).read_text(encoding='utf-8')

assert 'mode=systemd' in read('RESULT.TXT')
assert read('PID1.TXT').startswith('systemd\n')
assert '/usr/lib/systemd/systemd' in read('PID1.TXT')
assert 'VERSION_CODENAME=trixie' in read('OSREL.TXT')
assert read('CPUONLINE.TXT').strip() == '0-7'
assert 'ActiveState=active' in read('TARGET.TXT')
assert 'systemd 257' in read('SYSVER.TXT')
mounts = {line.split()[1]: line.split() for line in read('MOUNTS.TXT').splitlines()}
assert mounts['/'][2] == 'overlay'
assert 'upperdir=/run/f8-overlay/upper' in mounts['/'][3]
assert mounts['/run'][2] == 'tmpfs'
assert mounts['/run/f8/container'][0] == '/dev/mmcblk0p6'
assert {'ro', 'norecovery'} <= set(mounts['/run/f8/container'][3].split(','))
assert mounts['/run/f8/lower'][2] == 'squashfs'
assert 'ro' in mounts['/run/f8/lower'][3].split(',')
assert 'rootfs.squashfs: OK' in read('STEPS.TXT')
journal = read('JOURNAL.TXT')
dmesg = read('DMESG.TXT')
assert 'status=200/CHDIR' in journal
assert 'systemd-resolved.service' in read('FAILED.TXT')
assert read('SYSSTATE.TXT').strip() == 'degraded'
assert 'initcall rockchip_cpufreq_driver_init blacklisted' in dmesg
report = {
    'date': '2026-10-29', 'host_volume_observed': 'F: F861R4',
    'scope': 'Real Trixie systemd PID1/basic target in RAM overlay; one failed DNS service',
    'candidate_sha256': '6adc48f275c1d42ea84287591e276a761e514b54d78fde232ff8b7bbd5c64b6c',
    'systemd_pid1_started': True, 'systemd_version': '257.13-1~deb13u1',
    'evaluation_target_active': True, 'system_state': 'degraded',
    'failed_unit': 'systemd-resolved.service', 'failed_unit_exit': '200/CHDIR',
    'online_cpus': '0-7', 'original_container_readonly_no_journal_replay': True,
    'squashfs_sha256_checked_on_target': True, 'overlay_upper_in_ram': True,
    'root_mounts': {key: mounts[key] for key in ['/', '/run', '/run/f8/container', '/run/f8/lower']},
    'panic_or_oops_in_snapshot': bool(re.search(r'Kernel panic|Oops:', dmesg)),
    'suspected_permission_cause': 'init umask 077 creates overlay upper as 0700; target root mode was not captured',
    'desktop_started': False, 'network_ssh_tested': False, 'charging_tested': False,
    'dvfs_or_stress_tested': False, 'original_boot_restored_after_r4': False,
    'files': [{'name': f.name, 'bytes': f.stat().st_size,
               'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
              for f in sorted(logs.glob('*.TXT'))],
}
(logs / 'test-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k: report[k] for k in ['systemd_pid1_started', 'evaluation_target_active', 'system_state', 'failed_unit_exit', 'panic_or_oops_in_snapshot']}, ensure_ascii=False))
