"""Run one quiet A3 test after verified runtime clock and pin checks."""
import argparse,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
dest=P/'local/hardware/armbian-native-audio-a3-20261101-01'
parser=argparse.ArgumentParser()
parser.add_argument('--trial',choices=['01','02'],default='01')
trial=parser.parse_args().trial
d=json.loads((dest/'silent-clock-01.json').read_text())
assert d['aplay']['exit']==0 and d['restore']['exit']==0
assert any(re.search(r'i2s0_mclkout_to_io\s+1\s+1',s) for s in d['i2s_clocks'])
assert json.loads((dest/'dt.json').read_text())['codec_clock_uses_io_provider']
out=dest/('softtone-'+trial+'.json');runner=dest/('softtone-'+trial+'-runner.sh')
assert not out.exists() and not runner.exists()
text=(P/'local/hardware/armbian-native-audio-a2-20261030-01/softtone-01-runner.sh').read_text().replace('f8-audio-a2-softtone-01','f8-audio-a3-softtone-'+trial)
anchor="assert Path('/run/user/1601').stat().st_uid==1601\n"
assert text.count(anchor)==1
text=text.replace(anchor,anchor+"assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=="+repr(d['boot_id'])+"\n")
runner.write_text(text)
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1600:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({k:d.get(k) for k in ['boot_id','play','restore','duration_seconds','wave_peak','stream_volume']},indent=2))
