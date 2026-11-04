"""Read-only flash GPIO, kernel and device-tree inventory; no GPIO requests."""
import json,os,subprocess,shutil
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
def run(a):
 try:
  r=subprocess.run(a,capture_output=True,text=True,timeout=10);return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
dt=Path('/sys/firmware/devicetree/base');nodes={}
for p in dt.rglob('*'):
 if p.is_dir() and any(x in p.name.lower() for x in ['flash','rgb13','leds','ov8858']):
  nodes[str(p.relative_to(dt))]={q.name:q.read_bytes().hex() for q in p.iterdir() if q.is_file()}
o={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'kernel':os.uname().release,'nodes':nodes,'tools':{n:shutil.which(n) for n in ['gpioinfo','gpioset','gpioget','dtc','v4l2-ctl']}}
o['leds']={p.name:{q.name:q.read_text(errors='replace') for q in p.iterdir() if q.name in ['brightness','max_brightness','trigger']} for p in Path('/sys/class/leds').glob('*')}
o['gpio_chips']={p.name:{q.name:q.read_text() for q in p.iterdir() if q.name in ['base','label','ngpio']} for p in Path('/sys/class/gpio').glob('gpiochip*')}
o['gpio_debug']=run(['cat','/sys/kernel/debug/gpio'])
o['pin113']={str(p):'\n'.join(l for l in p.read_text(errors='replace').splitlines() if 'pin 113 ' in l or 'gpio3-17' in l) for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins')}
cfg=Path('/boot/config-'+os.uname().release)
o['config']='\n'.join(l for l in cfg.read_text().splitlines() if any(x in l for x in ['RGB13','LEDS_GPIO','LEDS_CLASS_FLASH','VIDEO_V4L2','GPIO_CDEV','LEDS_SYSCON'])) if cfg.exists() else None
mods=Path('/lib/modules')/os.uname().release
o['flash_modules']=[str(p) for p in mods.rglob('*.ko*') if any(x in p.name.lower() for x in ['rgb13','flash','leds-gpio'])]
o['logs']=run(['dmesg','--level=err,warn'])
o['logs']['stdout']='\n'.join(l for l in o['logs'].get('stdout','').splitlines() if any(x in l.lower() for x in ['flash','rgb13','gpio','led']))
o['camera_units']=run(['systemctl','list-units','--all','--no-legend','f8*camera*'])
print(json.dumps(o,indent=2))
