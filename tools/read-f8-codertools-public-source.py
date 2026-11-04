import json,urllib.request,re,base64
from pathlib import Path
u='https://www.codertools.net/tools/motion-sensor-test.php?lang=zh';out={}
try:
 r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36','Accept-Language':'zh-CN,zh;q=0.9'}),timeout=15);b=r.read();out={'status':r.status,'body':base64.b64encode(b).decode()}
except Exception as e:out={'error':str(e)}
print(json.dumps(out))
