"""Versioned U3 baseline or guarded module trial, preserving U2 evidence."""
import argparse,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('action',choices=['baseline','load']);p.add_argument('--revision',choices=['u3','u4','u4r1','u5'],default='u3');a=p.parse_args()
dest=P/('local/hardware/armbian-native-usb-20261101/'+a.revision);dest.mkdir(exist_ok=True)
def capture(name,text=None,script=None):
    out=dest/(name+'.json');assert not out.exists(),'Preserve evidence'
    if text is not None:
        script=dest/(name+'-runner.sh');assert not script.exists();script.write_text(text)
    r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(script),'--sudo'],capture_output=True,text=True,timeout=100)
    if r.returncode:
        out.with_suffix('.ssh-error.txt').write_text(r.stderr[-3000:]);raise RuntimeError(r.stderr[-1600:])
    d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');return d
if a.action=='baseline':
    text=(P/'local/hardware/armbian-native-usb-20261101/u2/identity-runner.sh').read_text()
    anchor="dt=Path('/sys/firmware/devicetree/base')\n";assert text.count(anchor)==1
    text=text.replace(anchor,anchor+"assert (dt/'chosen/f8-usb-trial').read_bytes()==b'u3\\0'\ntcpc=dt/'i2c@fec80000/fusb302@22'\nassert (tcpc/'port/endpoint').exists() and not (tcpc/'connector/ports').exists()\nassert (tcpc/'port/endpoint/remote-endpoint').read_bytes()==(dt/'usbdrd3_0/usb@fc000000/port/endpoint/phandle').read_bytes()\nassert (tcpc/'port/endpoint/phandle').read_bytes()==(dt/'usbdrd3_0/usb@fc000000/port/endpoint/remote-endpoint').read_bytes()\n")
    if a.revision in ['u4','u4r1','u5']:
        text=text.replace("b'u3\\0'","b'"+a.revision+"\\0'").replace("and not (tcpc/'connector/ports').exists()","and (tcpc/'connector/ports').exists()")
        anchor="module=Path('/usr/libexec/f8-pro/f8_otg_vbus_u2.ko')\n"
        assert text.count(anchor)==1
        text=text.replace(anchor,"phy=dt/'syscon@fd5d0000/usb2-phy@0'\nassert (phy/'orientation-switch').exists() and (phy/'otg-port/rockchip,typec-vbus-det').exists()\nassert (phy/'port/endpoint/remote-endpoint').read_bytes()==(tcpc/'connector/ports/port@0/endpoint/phandle').read_bytes()\nassert (phy/'port/endpoint/phandle').read_bytes()==(tcpc/'connector/ports/port@0/endpoint/remote-endpoint').read_bytes()\n"+anchor)
    if a.revision=='u5':
        anchor="module=Path('/usr/libexec/f8-pro/f8_otg_vbus_u2.ko')\n"
        text=text.replace(anchor,"assert (phy/'otg-port/rockchip,sel-pipe-phystatus').exists()\n"+anchor)
    d=capture('identity',text=text);print(json.dumps({'identity':d}),flush=True)
    d=capture('desktop',text=(P/'tools/verify-f8-native-desktop.sh').read_text().replace(",'f8-live-power'",''));print(json.dumps({'desktop':d}),flush=True)
    d=capture('backlight',script=P/'tools/read-f8-backlight-ownership.sh');print(json.dumps({'backlight':d}),flush=True)
    if a.revision in ['u4r1','u5']:
        d=capture('phy-before-module',script=P/'tools/read-f8-u3-phy.sh');print(json.dumps({'phy':d}),flush=True)
        assert any('fd5d0000' in n for n in d['phy_instances']), 'USB2 PHY still missing'
        assert d['phy_otg_mode'].strip()=='otg', 'Unexpected PHY mode'
        assert d['typec_mux_devices'], 'Orientation provider still missing'
    d=capture('usb-before-module',script=P/'tools/read-f8-usb-runtime.sh');print(json.dumps({'usb':{k:d.get(k) for k in ['boot_id','typec','deferred']}}),flush=True)
else:
    identity=json.loads((dest/'identity.json').read_text());assert not identity['module_loaded']
    text=(P/'tools/load-f8-u2-otg.sh').read_text()
    old='1ca22167-5a98-4f7e-b17c-fec65cd72d5b';assert text.count(old)==1
    text=text.replace(old,identity['boot_id']).replace('usb-u2-load01','usb-'+a.revision+'-load01').replace('98-f8-usb-u2.conf','98-f8-usb-'+a.revision+'.conf')
    d=capture('module-load01',text=text);print(json.dumps({k:d.get(k) for k in ['boot_id','insmod','module_loaded','bindings','deferred','usb_log','udisks_after','failed_units']},indent=2),flush=True)
