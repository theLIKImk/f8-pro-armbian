"""Record unported vendor charger policy; does not change or load a driver."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

P = Path(__file__).resolve().parents[1]
S = Path('/var/tmp/f8-pro-armbian/linux-rockchip-config')
driver = S / 'drivers/power/supply/bq25890_charger.c'
text = driver.read_text()
vendor = P / 'vendor/ubuntu-5.10.160/boot-assets/board.dtb'
node = '/i2c@fec80000/charger@6a'
keys = subprocess.check_output(['fdtget', '-p', str(vendor), node], text=True).splitlines()
array = text.split('} props[] = {', 1)[1].split('\n\t};', 1)[0]
parsed = set(re.findall(r'\{"([^"]+)",\s*(?:true|false),', array))
assert len(parsed) == 10
properties = []
for key in keys:
    if not key.startswith('ti,') or key == 'ti,usb-charger-detection':
        continue
    cells = subprocess.check_output(['fdtget', '-t', 'u', str(vendor), node, key], text=True).split()
    assert len(cells) == 1
    properties.append({'property': key, 'vendor_value': int(cells[0]), 'parsed_by_target_u32_table': key in parsed})
missing = [item['property'] for item in properties if not item['parsed_by_target_u32_table']]
assert 'ti,max-charge-voltage' in missing and 'ti,input-current-sdp' in missing
tcpm = (S / 'drivers/usb/typec/tcpm/tcpm.c').read_text()
for field in ['CURRENT_NOW', 'CURRENT_MAX', 'VOLTAGE_NOW', 'VOLTAGE_MAX']:
    assert 'POWER_SUPPLY_PROP_' + field in tcpm
report = {
    'scope': 'Static source/property audit, not charging/USB-C validation; nodes remain disabled',
    'driver_sha256': hashlib.sha256(driver.read_bytes()).hexdigest(),
    'vendor_parameters': properties, 'vendor_limits_not_parsed_by_target': missing,
    'vendor_extcon_property_read_by_target': '"extcon"' in text,
    'vendor_otg_mode_en_gpio_read_by_target': '"otg-mode-en' in text,
    'target_otg_regulator_match': 'usb-otg-vbus',
    'target_regulator_skipped_if_legacy_usb_phy_exists': True,
    'pd_notify_properties_present_in_tcpm': True,
    'unresolved': [
        'Preserve board input/charge limits across initialization, power_supply writes and PD notifications',
        'Vendor max-charge-voltage is 4200000 but battery-regulation-voltage is 4400000; effective vendor policy not established',
        'PD worker maps negotiated current to both IINLIM and ICHG without the vendor limit properties',
        'Vendor charger pinctrl GPIO0_D5 differs from interrupt-parent GPIO3_D5; bank not resolved by live IRQ listing',
        'Vendor FUSB302 VBUS regulator and charger OTG pin must be adapted together; no source-mode enable yet',
        'FUSB302 connector port@1 contains remoteAudioService.java-endpoint rather than standard remote-endpoint',
    ],
}
assert '"usb-otg-vbus"' in text
output = P / 'analysis/armbian/charger-policy-audit.json'
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
