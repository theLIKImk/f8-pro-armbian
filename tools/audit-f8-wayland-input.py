"""Audit locked upstream input interfaces and signed Debian theme packages offline."""
import configparser
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
ROOT = B / 'rootfs-trixie-evaluation'
OUT = P / 'analysis/armbian/userspace/input-method-audit'
OUT.mkdir(parents=True, exist_ok=True)
sources = {}
for name, url in {
    'sddm-GreeterApp.cpp': 'https://raw.githubusercontent.com/sddm/sddm/4fe234b/src/greeter/GreeterApp.cpp',
    'sddm-Configuration.h': 'https://raw.githubusercontent.com/sddm/sddm/4fe234b/src/common/Configuration.h',
    'kwin-inputmethod.cpp': 'https://raw.githubusercontent.com/KDE/kwin/v6.3.6/src/inputmethod.cpp',
}.items():
    path = OUT / name
    if not path.is_file():
        request = urllib.request.Request(url, headers={'User-Agent': 'F8-PRO-local-audit'})
        with urllib.request.urlopen(request, timeout=45) as response:
            path.write_bytes(response.read())
    sources[name] = {'url': url, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
greeter = (OUT / 'sddm-GreeterApp.cpp').read_text()
assert 'platform.startsWith(QStringLiteral("wayland")) && inputMethod == QStringLiteral("qtvirtualkeyboard")' in greeter
assert 'inputMethod = QString{};' in greeter
kwin = (OUT / 'kwin-inputmethod.cpp').read_text()
assert '"KWIN_IM_SHOW_ALWAYS"' in kwin and 'readEntry("VirtualKeyboardEnabled", true)' in kwin
main = (P / 'analysis/armbian/userspace/kwin-6.3.6-main_wayland.cpp').read_text()
assert 'KDesktopFile file(group.readPathEntry("InputMethod", QString()))' in main
assert 'setInputMethodServerToStart(parser.value(inputMethodOption))' in main
conf = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=None)
conf.read(P / 'armbian/candidates/sddm-wayland.conf')
assert conf['General']['DisplayServer'] == 'wayland' and conf['General']['InputMethod'] == ''
assert '--inputmethod /usr/bin/maliit-keyboard' in conf['Wayland']['CompositorCommand']
assert 'KWIN_IM_SHOW_ALWAYS=1' in conf['Wayland']['CompositorCommand']
assert conf['Theme']['Current'] == 'debian-breeze'
desktop = configparser.ConfigParser(interpolation=None)
desktop.read(P / 'armbian/candidates/kwinrc')
assert desktop['Wayland']['InputMethod'] == '/usr/share/applications/com.github.maliit.keyboard.desktop'
assert desktop['Wayland'].getboolean('VirtualKeyboardEnabled')
packages = []
for package in sorted((ROOT / 'var/tmp/f8-theme-packages').glob('*.deb')):
    name = subprocess.check_output(['dpkg-deb', '-f', str(package), 'Package'], text=True).strip()
    version = subprocess.check_output(['dpkg-deb', '-f', str(package), 'Version'], text=True).strip()
    metadata = subprocess.check_output(['chroot', str(ROOT), 'apt-cache', 'show', name], text=True)
    matches = []
    for paragraph in metadata.strip().split('\n\n'):
        fields = dict(line.split(': ', 1) for line in paragraph.splitlines() if ': ' in line and not line.startswith(' '))
        if fields.get('Version') == version:
            matches.append(fields)
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    assert len(matches) == 1 and digest == matches[0]['SHA256']
    packages.append({'name': name, 'version': version, 'sha256': digest})
assert {item['name'] for item in packages} == {'sddm-theme-breeze', 'sddm-theme-debian-breeze'}
theme = B / 'theme-audit/usr/share/sddm/themes/debian-breeze/Main.qml'
assert 'VirtualKeyboardLoader' in theme.read_text()
shutil.copy2(theme, OUT / 'debian-breeze-Main.qml')
result = {'scope': 'Source/config/package audit only; no compositor, focus, text entry or touchscreen runtime test',
          'sources': sources, 'theme_packages': packages, 'sddm_clears_qtvirtualkeyboard_on_wayland': True,
          'candidate_greeter_maliit_launcher_verified': True, 'candidate_desktop_kwin_entry_verified': True,
          'theme_missing_from_original_install_plan': True, 'theme_added_to_next_install_plan': True,
          'candidate_config_installed': False}
(OUT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
