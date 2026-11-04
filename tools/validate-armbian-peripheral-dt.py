"""Compile the peripheral draft against pinned SoC inputs and compare with vendor DTB.

Run in WSL. Output is a compile-check artifact only; no flashing/device operations.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'analysis/armbian/dt-validation'
KERNEL = BASE / 'analysis/armbian/source-audit/linux-rockchip'
OUT.mkdir(parents=True, exist_ok=True)
audit = json.loads((KERNEL.parent / 'manifest.json').read_text())
for item in audit['files']:
    if item['status'] == 'present':
        path = KERNEL.parent / item['repository'] / item['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], path
includes = ['-I', str(KERNEL / 'include'), '-I', str(KERNEL / 'arch/arm64/boot/dts/rockchip'),
            '-I', str(BASE / 'armbian/dts')]


def compile_dt(source, stem):
    pre = subprocess.run(['cpp', '-nostdinc', '-undef', '-D__DTS__', '-x', 'assembler-with-cpp',
                          *includes, str(source)], capture_output=True, check=True).stdout
    pp = OUT / (stem + '.preprocessed.dts')
    pp.write_bytes(pre)
    dtb = OUT / (stem + '.DO-NOT-FLASH.dtb')
    result = subprocess.run(['dtc', '-I', 'dts', '-O', 'dtb', '-o', str(dtb), str(pp)], capture_output=True)
    log = result.stderr.decode()
    (OUT / (stem + '.log')).write_text(log)
    result.check_returncode()
    warnings = Counter(re.findall(r'Warning \(([^)]+)\): ([^\n]+)', log))
    return dtb, warnings


baseline = OUT / 'soc-only.dts'
baseline.write_text('/dts-v1/;\n#include "rk3588s.dtsi"\n')
_, base_warnings = compile_dt(baseline, 'soc-only')
draft, draft_warnings = compile_dt(BASE / 'armbian/dts/f8-pro-compile-check.dts', 'f8-pro-compile-check')
vendor = BASE / 'vendor/ubuntu-5.10.160/boot-assets/board.dtb'


def prop(dtb, node, key, kind='x'):
    return subprocess.check_output(['fdtget', '-t', kind, str(dtb), node, key], text=True).strip()


comparisons = []
for node, keys in {
    '/backlight': ['brightness-levels', 'default-brightness-level'],
    '/i2c@feab0000/mpu_acc@68': ['reg', 'layout', 'poll_delay_ms', 'mpu-orientation'],
    '/i2c@feab0000/ak8963@f': ['reg', 'layout', 'poll_delay_ms'],
    '/i2c@feac0000/ts@40': ['reg', 'screen_max_x', 'screen_max_y', 'chip_id'],
    '/i2c@fec90000/es8388@11': ['reg', 'assigned-clock-rates'],
}.items():
    for key in keys:
        original, candidate = prop(vendor, node, key), prop(draft, node, key)
        comparisons.append({'node': node, 'property': key, 'equal': original == candidate})
        assert original == candidate, (node, key, original, candidate)
# Read back all original regulator properties, including suspend states.
rails = json.loads((BASE / 'analysis/armbian/power-rail-comparison.json').read_text())['rails']
for rail in rails:
    node = '/spi@feb20000/rk806single@0/regulators/' + rail['rail']
    for sub in ['', '/regulator-state-mem']:
        props = subprocess.check_output(['fdtget', '-p', str(vendor), node + sub], text=True).splitlines()
        for key in props:
            if key == 'phandle':
                continue
            kind = 's' if key == 'regulator-name' else 'x'
            a, b = prop(vendor, node + sub, key, kind), prop(draft, node + sub, key, kind)
            assert a == b, (node + sub, key, a, b)
            comparisons.append({'node': node + sub, 'property': key, 'equal': True})
for node in ['/dsi@fde20000/panel@0', '/dsi@fde20000/panel@0/display-timings/timing0']:
    props = subprocess.check_output(['fdtget', '-p', str(vendor), node], text=True).splitlines()
    for key in props:
        if key in ['phandle', 'status', 'compatible', 'backlight', 'power-supply', 'reset-gpios', 'pinctrl-0', 'pinctrl-names']:
            continue
        a, b = prop(vendor, node, key), prop(draft, node, key)
        assert a == b, (node, key, a, b)
        comparisons.append({'node': node, 'property': key, 'equal': True})
disabled = ['/vcc3v3-lcd0-n', '/dsi@fde20000/panel@0', '/backlight', '/i2c@feac0000/ts@40', '/i2c@fec90000/es8388@11']
for node in disabled:
    assert prop(draft, node, 'status', 's') == 'disabled', node
added = draft_warnings - base_warnings
_, vendor_warnings = compile_dt(BASE / 'analysis/baseline-validation/ubuntu-board.dts', 'vendor-reference')
unexpected = added - vendor_warnings
# Compare graph destinations by path rather than unstable numeric phandles.
links = [
    ('/display-subsystem/route/route-dsi0', 'connect', '/vop@fdd90000/ports/port@2/endpoint@3'),
    ('/dsi@fde20000', 'phys', '/phy@feda0000'),
    ('/dsi@fde20000/ports/port@0/endpoint@0', 'remote-endpoint', '/vop@fdd90000/ports/port@2/endpoint@3'),
    ('/vop@fdd90000/ports/port@2/endpoint@3', 'remote-endpoint', '/dsi@fde20000/ports/port@0/endpoint@0'),
]
for dtb in [vendor, draft]:
    for node, key, destination in links:
        assert prop(dtb, node, key).split()[0] == prop(dtb, destination, 'phandle'), (node, key)
# Panel endpoint layout is simplified in the draft; verify both reciprocal links.
for dtb, panel_path in [(vendor, '/dsi@fde20000/panel@0/ports/port@0/endpoint'),
                        (draft, '/dsi@fde20000/panel@0/ports/port/endpoint')]:
    out_path = '/dsi@fde20000/ports/port@1/endpoint'
    assert prop(dtb, out_path, 'remote-endpoint') == prop(dtb, panel_path, 'phandle')
    assert prop(dtb, panel_path, 'remote-endpoint') == prop(dtb, out_path, 'phandle')
for node in ['/dsi@fde20000/ports/port@0/endpoint@0', '/dsi@fde20000/ports/port@0/endpoint@1']:
    assert prop(vendor, node, 'status', 's') == prop(draft, node, 'status', 's')
assert prop(draft, '/display-subsystem/route/route-dsi0', 'status', 's') == 'disabled'
assert prop(draft, '/dsi@fde20000', 'status', 's') == 'disabled'
for vp in range(4):
    node = f'/vop@fdd90000/ports/port@{vp}'
    for key in ['rockchip,plane-mask', 'rockchip,primary-plane']:
        assert prop(vendor, node, key) == prop(draft, node, key), (node, key)
        comparisons.append({'node': node, 'property': key, 'equal': True})
for dtb in [vendor, draft]:
    assert prop(dtb, '/vop@fdd90000', 'iommus') == prop(dtb, '/iommu@fdd97e00', 'phandle')
    domain = prop(dtb, '/vop@fdd90000', 'power-domains').split()
    assert domain[0] == prop(dtb, '/power-management@fd8d8000/power-controller', 'phandle')
assert prop(vendor, '/vop@fdd90000', 'power-domains').split()[1] == prop(draft, '/vop@fdd90000', 'power-domains').split()[1]
for node in ['/vop@fdd90000', '/iommu@fdd97e00']:
    assert prop(draft, node, 'status', 's') == 'disabled'
node = '/mmc@fe2e0000'
for key in ['max-frequency', 'bus-width', 'no-sdio', 'no-sd', 'non-removable', 'mmc-hs200-1_8v']:
    assert prop(vendor, node, key) == prop(draft, node, key)
    comparisons.append({'node': node, 'property': key, 'equal': True})
assert 'supports-cqe' not in subprocess.check_output(['fdtget', '-p', str(draft), node], text=True).splitlines()
pmic = '/spi@feb20000/rk806single@0'
children = subprocess.check_output(['fdtget', '-l', str(vendor), pmic + '/pinctrl_rk806'], text=True).splitlines()
for child in children:
    node = pmic + '/pinctrl_rk806/' + child
    for key in ['pins', 'function']:
        assert prop(vendor, node, key, 's') == prop(draft, node, key, 's')
        comparisons.append({'node': node, 'property': key, 'equal': True})
assert prop(vendor, pmic, 'pinctrl-names', 's') == prop(draft, pmic, 'pinctrl-names', 's')
for dtb in [vendor, draft]:
    refs = prop(dtb, pmic, 'pinctrl-0').split()
    assert len(refs) == 4
    for index, child in enumerate(['rk806_dvs1_null', 'rk806_dvs2_null', 'rk806_dvs3_null'], 1):
        assert refs[index] == prop(dtb, pmic + '/pinctrl_rk806/' + child, 'phandle')
    assert prop(dtb, pmic, 'pinctrl-1') == prop(dtb, pmic + '/pinctrl_rk806/rk806_dvs1_pwrdn', 'phandle')
for node in ['/i2c@fd880000/rk8602@42', '/i2c@fd880000/rk8603@43']:
    for sub in ['', '/regulator-state-mem']:
        keys = subprocess.check_output(['fdtget', '-p', str(vendor), node + sub], text=True).splitlines()
        for key in keys:
            if key in ['phandle', 'vin-supply']:
                continue
            kind = 's' if key in ['compatible', 'regulator-compatible', 'regulator-name'] else 'x'
            assert prop(vendor, node + sub, key, kind) == prop(draft, node + sub, key, kind)
            comparisons.append({'node': node + sub, 'property': key, 'equal': True})
for cpu, target in [('cpu@0', '/spi@feb20000/rk806single@0/regulators/DCDC_REG2'),
                    ('cpu@400', '/i2c@fd880000/rk8602@42'), ('cpu@600', '/i2c@fd880000/rk8603@43')]:
    for dtb in [vendor, draft]:
        for key in ['cpu-supply', 'mem-supply']:
            assert prop(dtb, '/cpus/' + cpu, key) == prop(dtb, target, 'phandle')
for node in ['/reserved-memory/cma', '/reserved-memory/ramoops@110000']:
    for key in subprocess.check_output(['fdtget', '-p', str(vendor), node], text=True).splitlines():
        kind = 's' if key == 'compatible' else 'x'
        assert prop(vendor, node, key, kind) == prop(draft, node, key, kind)
        comparisons.append({'node': node, 'property': key, 'equal': True})
assert prop(draft, '/gpu@fb000000', 'status', 's') == 'disabled'
assert prop(draft, '/gpu-panthor@fb000000', 'status', 's') == 'disabled'
for node, keys in {
    '/tsadc@fec00000': ['rockchip,hw-tshut-temp', 'rockchip,hw-tshut-mode', 'rockchip,hw-tshut-polarity'],
    '/adc-keys': ['keyup-threshold-microvolt', 'poll-interval'],
    '/adc-keys/vol-up-key': ['linux,code', 'press-threshold-microvolt'],
    '/adc-keys/vol-down-key': ['linux,code', 'press-threshold-microvolt'],
}.items():
    for key in keys:
        assert prop(vendor, node, key) == prop(draft, node, key)
        comparisons.append({'node': node, 'property': key, 'equal': True})
node = '/es8388-sound'
for key in ['rockchip,card-name', 'rockchip,format', 'rockchip,audio-routing']:
    assert prop(vendor, node, key, 's') == prop(draft, node, key, 's')
    comparisons.append({'node': node, 'property': key, 'equal': True})
for dtb in [vendor, draft]:
    assert prop(dtb, node, 'rockchip,cpu') == prop(dtb, '/i2s@fe470000', 'phandle')
    assert prop(dtb, node, 'rockchip,codec') == prop(dtb, '/i2c@fec90000/es8388@11', 'phandle')
assert prop(draft, node, 'status', 's') == 'disabled'
old_amp = prop(vendor, '/i2c@fec90000/es8388@11', 'spk-con-gpio').split()
new_amp = prop(draft, '/es8388-sound', 'spk-con-gpios').split()
assert old_amp[1:] == new_amp[1:]
assert old_amp[0] == prop(vendor, '/pinctrl/gpio@fec50000', 'phandle')
assert new_amp[0] == prop(draft, '/pinctrl/gpio@fec50000', 'phandle')
for node, keys in {
    '/wireless-wlan': ['compatible', 'wifi_chip_type', 'pinctrl-names'],
    '/wireless-bluetooth': ['compatible', 'clock-names', 'pinctrl-names'],
    '/i2c@fec80000/hym8563@51': ['compatible', 'reg', '#clock-cells', 'clock-frequency', 'clock-output-names', 'interrupts', 'wakeup-source'],
    '/pcie@fe190000': ['num-lanes', 'max-link-speed', 'rockchip,skip-scan-in-resume'],
}.items():
    for key in keys:
        kind = 's' if key in ['compatible', 'wifi_chip_type', 'clock-names', 'pinctrl-names', 'clock-output-names'] else 'x'
        assert prop(vendor, node, key, kind) == prop(draft, node, key, kind), (node, key)
        comparisons.append({'node': node, 'property': key, 'equal': True})
for node, key, controller in [
    ('/wireless-wlan', 'WIFI,poweren_gpio', '/pinctrl/gpio@fd8a0000'),
    ('/wireless-wlan', 'WIFI,host_wake_irq', '/pinctrl/gpio@fd8a0000'),
    ('/wireless-bluetooth', 'uart_rts_gpios', '/pinctrl/gpio@fec40000'),
    ('/wireless-bluetooth', 'BT,reset_gpio', '/pinctrl/gpio@fd8a0000'),
    ('/wireless-bluetooth', 'BT,wake_gpio', '/pinctrl/gpio@fd8a0000'),
    ('/wireless-bluetooth', 'BT,wake_host_irq', '/pinctrl/gpio@fd8a0000'),
    ('/pcie@fe190000', 'reset-gpios', '/pinctrl/gpio@fec40000'),
]:
    old, new = prop(vendor, node, key).split(), prop(draft, node, key).split()
    assert old[1:] == new[1:], (node, key)
    for dtb, values in [(vendor, old), (draft, new)]:
        assert values[0] == prop(dtb, controller, 'phandle')
    comparisons.append({'node': node, 'property': key, 'equal': True})
pin_configs = {
    '/pinctrl/hym8563/rtc-int': 'pcfg-pull-up',
    '/pinctrl/wireless-bluetooth/uart9-gpios': 'pcfg-pull-none',
    '/pinctrl/wireless-bluetooth/bt-reset-gpio': 'pcfg-pull-none',
    '/pinctrl/wireless-bluetooth/bt-wake-gpio': 'pcfg-pull-up',
    '/pinctrl/wireless-bluetooth/bt-wake-host-irq': 'pcfg-pull-down',
    '/pinctrl/wireless-wlan/wifi-host-wake-irq': 'pcfg-pull-down',
    '/pinctrl/wireless-wlan/wifi-poweren-gpio': 'pcfg-pull-up',
}
for node, config in pin_configs.items():
    old, new = prop(vendor, node, 'rockchip,pins').split(), prop(draft, node, 'rockchip,pins').split()
    assert old[:3] == new[:3], node
    for dtb, values in [(vendor, old), (draft, new)]:
        assert values[3] == prop(dtb, '/pinctrl/' + config, 'phandle')
    comparisons.append({'node': node, 'property': 'rockchip,pins', 'equal': True})
for dtb in [vendor, draft]:
    assert prop(dtb, '/wireless-bluetooth', 'clocks') == prop(dtb, '/i2c@fec80000/hym8563@51', 'phandle')
    assert prop(dtb, '/i2c@fec80000/hym8563@51', 'interrupt-parent') == prop(dtb, '/pinctrl/gpio@fd8a0000', 'phandle')
    phy = prop(dtb, '/pcie@fe190000', 'phys').split()
    assert phy == [prop(dtb, '/phy@fee00000', 'phandle'), '2']
    assert prop(dtb, '/pcie@fe190000', 'pinctrl-0') == prop(dtb, '/pinctrl/wireless-wlan/wifi-poweren-gpio', 'phandle')
for node in ['/wireless-bluetooth', '/wireless-wlan', '/i2c@fec80000/hym8563@51', '/pcie@fe190000', '/phy@fee00000', '/serial@febc0000']:
    assert prop(draft, node, 'status', 's') == 'disabled'
battery = '/i2c@fec80000/cw2015@62'
charger = '/i2c@fec80000/charger@6a'
for node, keys in {
    battery: ['reg', 'cellwise,battery-profile', 'cellwise,monitor-interval-ms'],
    charger: ['reg', 'interrupts', 'ti,max-input-voltage', 'ti,max-input-current',
              'ti,max-charge-voltage', 'ti,input-current', 'ti,input-current-sdp',
              'ti,input-current-dcp', 'ti,input-current-cdp', 'ti,battery-regulation-voltage',
              'ti,charge-current', 'ti,termination-current', 'ti,precharge-current',
              'ti,minimum-sys-voltage', 'ti,boost-voltage', 'ti,boost-max-current'],
}.items():
    for key in keys:
        assert prop(vendor, node, key) == prop(draft, node, key), (node, key)
        comparisons.append({'node': node, 'property': key, 'equal': True})
    assert prop(draft, node, 'status', 's') == 'disabled'
profile_bytes = subprocess.check_output(['fdtget', '-t', 'bx', str(draft), battery, 'cellwise,battery-profile'], text=True).split()
assert len(profile_bytes) == 64
for dtb in [vendor, draft]:
    assert prop(dtb, battery, 'power-supplies') == prop(dtb, charger, 'phandle')
    assert prop(dtb, charger, 'interrupt-parent') == prop(dtb, '/pinctrl/gpio@fec40000', 'phandle')
    assert prop(dtb, charger, 'extcon') == prop(dtb, '/syscon@fd5d0000/usb2-phy@0', 'phandle')
    assert prop(dtb, charger, 'pinctrl-0') == prop(dtb, '/pinctrl/charger/charger_ok', 'phandle')
    pin = prop(dtb, '/pinctrl/charger/charger_ok', 'rockchip,pins').split()
    assert pin[:3] == ['0', '1d', '0']
    assert pin[3] == prop(dtb, '/pinctrl/pcfg-pull-up', 'phandle')
old, new = prop(vendor, charger, 'otg-mode-en-gpios').split(), prop(draft, charger, 'otg-mode-en-gpios').split()
assert old[1:] == new[1:]
for dtb, values in [(vendor, old), (draft, new)]:
    assert values[0] == prop(dtb, '/pinctrl/gpio@fec50000', 'phandle')
for dtb in [vendor, draft]:
    assert prop(dtb, '/i2c@fd880000', 'pinctrl-0') == prop(dtb, '/pinctrl/i2c0/i2c0m2-xfer', 'phandle')
old_pins = prop(vendor, '/pinctrl/i2c0/i2c0m2-xfer', 'rockchip,pins').split()
new_pins = prop(draft, '/pinctrl/i2c0/i2c0m2-xfer', 'rockchip,pins').split()
for offset in [0, 4]:
    assert old_pins[offset:offset + 3] == new_pins[offset:offset + 3]
    comparisons.append({'node': '/pinctrl/i2c0/i2c0m2-xfer', 'property': 'bank-pin-function-' + str(offset // 4), 'equal': True})
report = {'scope': 'Compilation/property checks only; not a bootable board or hardware validation',
          'cpu_i2c0_mux_matches_vendor': True,
          'kernel_commit': audit['pins']['linux-rockchip'],
          'graph_links_verified': links, 'panel_links_reciprocal': True,
          'vop_iommu_power_references_verified': True,
          'pmic_pinctrl_references_verified': True, 'emmc_cqe_disabled': True,
          'cpu_supply_links_verified': True, 'both_gpu_nodes_disabled': True,
          'speaker_gpio_migration_verified': True,
          'wireless_gpio_phy_clock_references_verified': True,
          'wireless_rtc_pcie_uart_disabled': True,
          'battery_profile_64_bytes_verified': True,
          'charger_vendor_parameters_verified_but_driver_policy_unadapted': True,
          'battery_charger_disabled': True,
          'draft_dtb_sha256': hashlib.sha256(draft.read_bytes()).hexdigest(),
          'vendor_property_comparisons': comparisons, 'unverified_devices_disabled': disabled,
          'soc_warning_count': sum(base_warnings.values()),
          'draft_warning_count': sum(draft_warnings.values()),
          'unexpected_warnings': [{'class': cls, 'message': msg, 'count': count} for (cls, msg), count in unexpected.items()],
          'added_warnings': [{'class': cls, 'message': msg, 'count': count}
                             for (cls, msg), count in added.items()]}
(OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'comparisons_passed': len(comparisons), 'unexpected_warnings': report['unexpected_warnings']}))
