"""Read only input axis metadata and OF compatible; never reads input events."""
import json
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parents[1]
remote = '''import fcntl,json,os,struct
from pathlib import Path
items=[]
for event in Path('/sys/class/input').glob('event*'):
    name=(event/'device/name').read_text().strip()
    if 'gsl' not in name.lower():
        continue
    fd=os.open('/dev/input/'+event.name,os.O_RDONLY|os.O_NONBLOCK)
    axes={}
    try:
        for label,axis in [('ABS_MT_POSITION_X',0x35),('ABS_MT_POSITION_Y',0x36)]:
            raw=fcntl.ioctl(fd,0x80000000|(24<<16)|(ord('E')<<8)|(0x40+axis),bytes(24))
            _,minimum,maximum,fuzz,flat,resolution=struct.unpack('6i',raw)
            axes[label]={'minimum':minimum,'maximum':maximum,'fuzz':fuzz,'flat':flat,'resolution':resolution}
    finally:
        os.close(fd)
    items.append({'event':event.name,'name':name,'axes':axes})
compatible=Path('/sys/bus/i2c/devices/4-0040/of_node/compatible').read_bytes()
print(json.dumps({'compatible':[x.decode() for x in compatible.split(bytes([0])) if x],'devices':items}))
'''
command = ['wsl', '-d', 'rg35xx-build', '-u', 'root', '--', 'ssh',
           '-i', '/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519',
           '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', '-o', 'IdentitiesOnly=yes',
           '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts',
           'alarm@192.168.1.227', 'sudo -n python3 -']
result = subprocess.run(command, input=remote, capture_output=True, text=True, encoding='utf-8', timeout=100)
assert result.returncode == 0, 'Read-only metadata query failed: ' + result.stderr[-300:]
data = json.loads(result.stdout)
assert data['devices'] and data['compatible'] == ['gslX680_shuping']
data['scope'] = 'Read-only EVIOCGABS metadata/OF compatible; no event reads, writes or controller firmware access'
(P / 'analysis/armbian/touch-input-metadata.json').write_text(json.dumps(data, indent=2) + '\n')
print(json.dumps(data, indent=2))
