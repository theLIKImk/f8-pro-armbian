"""Meaningful offline checks of stable identities and private network rendering."""
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True

project = Path(__file__).resolve().parent.parent


def load(name, path):
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


network = load('f8_network', project / 'tools/inject-test-network.py')
bluetooth = load('f8_bluetooth', project / 'rootfs-overlay/usr/libexec/f8-pro/bluetooth-init')
first = bluetooth.address('0123456789abcdef0123456789abcdef')
assert first == bluetooth.address('0123456789abcdef0123456789abcdef')
assert first != bluetooth.address('1123456789abcdef0123456789abcdef')
assert int(first[:2], 16) & 3 == 2
for invalid in ('', '0' * 32, 'invalid'):
    try:
        bluetooth.address(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid machine-id accepted')
known = network.render_profile({'ssid': 'IEEE', 'psk': 'password'})
assert b'f42c6fc52df0ebef9ebb4b90b38a5f902e83fe1b135a70e23aed762e9710a12e' in known
assert b'password' not in known
for invalid in ({'ssid': '', 'psk': ''}, {'ssid': 'x', 'psk': 'short'}, {'ssid': 'x\n[section]', 'psk': 'password'}):
    try:
        network.render_profile(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid network input accepted')
root = Path('/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging')
for ssid in ('IEEE', ' Test; 网络 '):
    profile = network.render_profile({'ssid': ssid, 'psk': 'password'})
    result = subprocess.run(['chroot', str(root), '/usr/bin/nmcli', '--offline',
                             'connection', 'modify', 'connection.id', 'f8-pro-test-wifi'],
                            input=profile, capture_output=True)
    if result.returncode:
        raise RuntimeError('Target NetworkManager rejected a synthetic profile')
    import re
    expected = re.search(rb'(?m)^psk=([0-9a-f]{64})$', profile)
    actual = re.search(rb'(?m)^psk=([0-9a-f]{64})$', result.stdout)
    assert expected and actual and expected.group(1) == actual.group(1)
print('PASS: stable local-unicast Bluetooth addresses, WPA vector, invalid inputs, target offline profile parsing')
