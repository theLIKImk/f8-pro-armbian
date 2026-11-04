#!/usr/bin/python3 -I
"""Grow only the previously verified F8 p6 ext4, without changing partitions."""
from pathlib import Path
import json,os,stat,subprocess,time

UUID='69056675-4a48-4006-a3f3-5132c00cc6f2'
PARTUUID='614e0000-0000-4b53-8000-1d28000054a9'
START=0x78000
SECTORS=482344960
DEV='/dev/mmcblk0p6'

def plan(info):
    expected={'source':DEV,'fstype':'ext4','uuid':UUID,'partuuid':PARTUUID,'start':START,'sectors':SECTORS,'sector_size':512}
    for k,v in expected.items():
        if info[k]!=v:raise ValueError('Unexpected '+k)
    if info['errors']!=0:raise ValueError('Filesystem error counter is nonzero')
    current=info['blocks']*info['block_size'];target=info['sectors']*512
    if info['block_size']!=4096 or not 0<current<=target:raise ValueError('Unexpected ext4 geometry')
    return {'grow':current<target,'before_bytes':current,'target_bytes':target}

def main():
    assert os.geteuid()==0
    assert Path('/etc/f8-pro-release-r1').is_file()
    assert Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO')
    assert stat.S_ISBLK(Path(DEV).stat().st_mode)
    env=dict(os.environ,LC_ALL='C')
    def get(args):return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,env=env,timeout=15).strip()
    def geometry():
        text=get(['/usr/sbin/dumpe2fs','-h',DEV])
        fields=dict(x.split(':',1) for x in text.splitlines() if ':' in x)
        return {'blocks':int(fields['Block count'].strip()),'block_size':int(fields['Block size'].strip())}
    source,fstype=get(['/usr/bin/findmnt','-n','-o','SOURCE,FSTYPE','--target','/']).split()
    base=Path('/sys/class/block/mmcblk0p6')
    info=dict(source=source,fstype=fstype,uuid=get(['/usr/sbin/blkid','-s','UUID','-o','value',DEV]),partuuid=get(['/usr/sbin/blkid','-s','PARTUUID','-o','value',DEV]),start=int((base/'start').read_text()),sectors=int((base/'size').read_text()),sector_size=int(get(['/usr/sbin/blockdev','--getss',DEV])),errors=int(Path('/sys/fs/ext4/mmcblk0p6/errors_count').read_text()),**geometry())
    decision=plan(info)
    state=Path('/var/lib/f8-pro/root-grow-r1a');state.mkdir(parents=True,exist_ok=True);state.chmod(0o700)
    def save(name,data):
        p=state/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(data,indent=2)+'\n');os.replace(t,p)
    save('before.json',dict(info,**decision))
    if decision['grow']:
        with (state/'resize.log').open('w') as log:
            # No format/partition command; ext4's supported mounted resize path.
            subprocess.run(['/usr/sbin/resize2fs',DEV],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
    after=geometry()
    assert after['blocks']*after['block_size']==decision['target_bytes']
    assert int((base/'start').read_text())==START and int((base/'size').read_text())==SECTORS
    save('complete.json',{'ok':True,'grew':decision['grow'],'filesystem_bytes':after['blocks']*after['block_size'],'partition_table_changed':False,'time':time.time()})
    print('F8 root filesystem uses the full verified p6 partition; no formatting performed')

if __name__=='__main__':main()
