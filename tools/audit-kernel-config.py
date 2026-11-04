"""Check documented systemd 261 requirements against the recovered vendor config.

This is a static prerequisite check, not a boot or systemd service test.
"""
import json
from pathlib import Path

project = Path(__file__).resolve().parent.parent
config = {}
for line in (project / 'analysis/update-UBUNTU20.04/kernel.config').read_text().splitlines():
    if line.startswith('CONFIG_') and '=' in line:
        name, value = line.split('=', 1)
        config[name] = value
required = '''DEVTMPFS CGROUPS INOTIFY_USER SIGNALFD TIMERFD EPOLL UNIX SYSFS PROC_FS FHANDLE NET_NS USER_NS'''.split()
result = {
    'reference': 'https://github.com/systemd/systemd/blob/v261/README',
    'vendor_kernel': '5.10.160',
    'systemd_version_in_rootfs': '261.2-1',
    'upstream_minimum_kernel': '5.10',
    'upstream_recommended_kernel': '5.14',
    'kernel_version_meets_minimum': True,
    'kernel_version_meets_recommended': False,
    'required_config': {'CONFIG_' + name: config.get('CONFIG_' + name, 'n') for name in required},
    'legacy_sysfs_disabled': config.get('CONFIG_SYSFS_DEPRECATED', 'n') == 'n',
    'userspace_firmware_helper_disabled': config.get('CONFIG_FW_LOADER_USER_HELPER', 'n') == 'n',
    'uevent_helper_path': config.get('CONFIG_UEVENT_HELPER_PATH', '(option absent)'),
    'rt_group_sched': config.get('CONFIG_RT_GROUP_SCHED', 'n'),
    'hardware_boot_tested': False,
    'notes': [
        'This checks the general and namespace requirements, not every optional systemd feature.',
        'Linux 5.10 is below the recommended baseline; systemd may set old-kernel taint.',
        'Runtime fallback behavior and cgroup v2 mounting still require an actual boot.',
    ],
}
result['required_config_present'] = all(value == 'y' for value in result['required_config'].values())
target = project / 'analysis/systemd-kernel-compatibility.json'
target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
