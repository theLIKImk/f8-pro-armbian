"""Read official image catalogs and save selectable metadata, without deploying."""
import concurrent.futures
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request

P=Path(__file__).resolve().parents[1]
out=P/'analysis/armbian/official-gpu-baseline-20261029/image-catalogs'
out.mkdir(parents=True,exist_ok=True)
urls=[('archive','https://dl.armbian.com/orangepi5/archive/'),
      ('board','https://www.armbian.com/orangepi-5/'),
      ('releases','https://api.github.com/repos/armbian/os/releases?per_page=15')]
class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k=='href' and v and any(s in v.lower() for s in ['.img','trixie','noble','plasma','kde']):
                self.links.append(v)
def fetch(item):
    name,url=item
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'F8-PRO-Armbian-baseline'})
        with urllib.request.urlopen(request,timeout=40) as response:
            data=response.read();actual=response.url
        (out/(name+'.raw')).write_bytes(data)
        if name=='releases':
            items=json.loads(data)
            selected=[{'tag':i['tag_name'],'published':i['published_at'],
                       'assets':[{'name':a['name'],'bytes':a['size'],
                                  'url':a['browser_download_url'],'digest':a.get('digest')}
                                 for a in i['assets'] if 'Orangepi5_' in a['name']]} for i in items]
        else:
            parser=Links();parser.feed(data.decode('utf-8',errors='replace'));selected=parser.links
        return {'name':name,'url':url,'final_url':actual,
                'sha256':hashlib.sha256(data).hexdigest(),'selected':selected}
    except Exception as error:
        return {'name':name,'url':url,'error':str(error)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    result=list(pool.map(fetch,urls))
(out/'catalog.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
