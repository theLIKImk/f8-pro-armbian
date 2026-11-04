"""Validate and preserve R5 hardware permission/service acceptance evidence."""
import hashlib
import json
from pathlib import Path
import re

P = Path(__file__).resolve().parents[1]
logs = P/'local/hardware/armbian-6.1-r5-20261029-01'
def read(name):
    return (logs/name).read_text(encoding='utf-8')

assert 'mode=systemd' in read('RESULT.TXT')
assert read('PID1.TXT').startswith('systemd\n')
assert '/usr/lib/systemd/systemd' in read('PID1.TXT')
assert 'VERSION_CODENAME=trixie' in read('OSREL.TXT')
assert read('CPUONLINE.TXT').strip() == '0-7'
assert 'ActiveState=active' in read('TARGET.TXT')
assert read('SYSSTATE.TXT').strip() == 'running'
assert '0 loaded units listed.' in read('FAILED.TXT')
assert '755 0:0 /' in read('PERMS.TXT').splitlines()
assert '644 0:0 /usr/lib/systemd/system/f8-pro-ssh-hostkeys.service' in read('PERMS.TXT')
for unit in ['f8-evaluation.target', 'f8-evaluation-report.timer', 'f8-evaluation-report.service']:
    line = next(s for s in read('STEPS.TXT').splitlines() if s.endswith('/'+unit))
    assert line.startswith('-rw-r--r--')
assert read('NONROOT.TXT').rstrip().endswith('exit_code=0')
assert 'User=systemd-resolve' in read('RESOLVED.TXT')
assert 'ActiveState=active' in read('RESOLVED.TXT')
assert 'SubState=running' in read('RESOLVED.TXT')
assert 'Result=success' in read('RESOLVED.TXT')
assert 'Started systemd-resolved.service' in read('DNSLOG.TXT')
journal = read('JOURNAL.TXT')
dmesg = read('DMESG.TXT')
assert 'status=200/CHDIR' not in journal
assert 'marked world-' not in journal and 'marked executable' not in journal
assert 'initcall rockchip_cpufreq_driver_init blacklisted' in dmesg
mounts = {line.split()[1]: line.split() for line in read('MOUNTS.TXT').splitlines()}
assert mounts['/'][2] == 'overlay'
assert 'upperdir=/run/f8-overlay/upper' in mounts['/'][3]
assert mounts['/run'][2] == 'tmpfs'
assert mounts['/run/f8/container'][0] == '/dev/mmcblk0p6'
assert {'ro', 'norecovery'} <= set(mounts['/run/f8/container'][3].split(','))
assert mounts['/run/f8/lower'][2] == 'squashfs'
assert 'ro' in mounts['/run/f8/lower'][3].split(',')
assert 'rootfs.squashfs: OK' in read('STEPS.TXT')
report = {
    'date': '2026-10-29', 'host_volume_observed': 'F: F861R5',
    'scope': 'RAM overlay PID1/basic target permissions and nonroot service acceptance',
    'candidate_sha256': '57334c1970a7d17fc31c56ed524f1980c6e13babc2a63a6095f756b81d485d3c',
    'systemd_pid1_started': True, 'system_state': 'running', 'failed_unit_count': 0,
    'evaluation_target_active': True, 'online_cpus': '0-7', 'root_mode': '0755',
    'injected_unit_modes': '0644', 'legacy_hostkey_unit_mode': '0644',
    'nonroot_service_read_exit_code': 0, 'resolved_service_active_running': True,
    'dns_network_resolution_tested': False,
    'original_container_readonly_no_journal_replay': True,
    'squashfs_sha256_checked_on_target': True, 'overlay_upper_in_ram': True,
    'panic_or_oops_in_snapshot': bool(re.search(r'Kernel panic|Oops:', dmesg)),
    'snapshot_last_kernel_message_seconds': 38.163117,
    'drm_mali_devices_present': False, 'regulatory_database_file_present': False,
    'desktop_started': False, 'network_ssh_tested': False, 'charging_tested': False,
    'dvfs_or_stress_tested': False, 'original_boot_restore_confirmed_after_r5': False,
    'files': [{'name': f.name, 'bytes': f.stat().st_size,
               'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
              for f in sorted(logs.glob('*.TXT'))],
}
(logs/'test-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k: report[k] for k in ['system_state', 'failed_unit_count', 'root_mode', 'nonroot_service_read_exit_code', 'resolved_service_active_running', 'panic_or_oops_in_snapshot']}, ensure_ascii=False))
