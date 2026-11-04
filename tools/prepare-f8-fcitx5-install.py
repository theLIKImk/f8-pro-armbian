"""Generate the stdin-only SSH deployment payload; credentials are never embedded."""
from pathlib import Path
import base64,hashlib,json
P=Path(__file__).resolve().parents[1];p=P/'outputs/armbian/f8-fcitx5-r1/f8-fcitx5-r1.tar.gz';data=p.read_bytes()
m=json.loads((p.parent/'manifest.json').read_text());assert all(x['mode']&0o022==0 for x in m['files'].values())
s="import os,json,base64,tarfile,io,hashlib\nfrom pathlib import Path\nassert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'\n"
s+='b=base64.b64decode('+repr(base64.b64encode(data).decode())+')\nassert hashlib.sha256(b).hexdigest()=='+repr(hashlib.sha256(data).hexdigest())+'\n'
s+="p=Path('/var/tmp/f8-pro-fcitx5-r1');p.mkdir(exist_ok=True,mode=0o700);p.chmod(0o700)\nwith tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:t.extractall(p,filter='data')\n"
s+=(P/'tools/install-f8-fcitx5-root.py').read_text(encoding='utf-8-sig').split("if __name__=='__main__':")[0]
s+="\nprint(json.dumps(install('/',p,'likimk'),indent=2))\n"
(P/'local/hardware/install-f8-fcitx5-generated.py').write_text(s,encoding='utf-8')
print('Payload ready',len(s))
