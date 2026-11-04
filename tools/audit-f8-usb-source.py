import json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
S=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config')
out=P/'analysis/armbian/usb-source-20261101';out.mkdir(exist_ok=True)
report={}
for rel in ['drivers/usb/typec/tcpm/fusb302.c','drivers/usb/typec/tcpm/tcpm.c','drivers/usb/roles/class.c','drivers/usb/dwc3/drd.c','drivers/power/supply/bq25890_charger.c','Documentation/devicetree/bindings/usb/fcs,fusb302.yaml']:
    src=S/rel
    if not src.exists():continue
    text=src.read_text();(out/src.name).write_text(text)
    lines=text.splitlines();indexes=set()
    for i,line in enumerate(lines):
        if re.search(r'vbus-supply|set_vbus|vbus_on|usb-otg-vbus|IS_ERR_OR_NULL\(bq->usb_phy\)|int-n-gpios|devm_regulator_get|usb_role_switch',line):indexes.update(range(max(0,i-4),min(len(lines),i+12)))
    report[rel]='\n'.join(str(i+1)+': '+lines[i] for i in sorted(indexes))
(out/'contexts.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
