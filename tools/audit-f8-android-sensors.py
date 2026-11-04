"""Read-only Android sparse super/LP/ext4 sensor inventory, no image extraction or writes."""
import bisect,hashlib,json,re,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import Package,Ext4,fdt,pretty
class Sparse:
 def __init__(self,pkg):
  self.pkg=pkg;h=pkg.read('super',0,28)
  magic,major,minor,fh,ch,bs,blocks,count,crc=struct.unpack('<I4H4I',h)
  assert magic==0xed26ff3a and major==1 and ch>=12
  self.size=bs*blocks;self.parts=[];pos=fh;logical=0
  for _ in range(count):
   h=pkg.read('super',pos,ch);kind,_,n,total=struct.unpack_from('<2H2I',h);length=n*bs;payload=pos+ch
   assert kind in [0xcac1,0xcac2,0xcac3,0xcac4]
   if kind==0xcac1:assert total-ch==length
   if length:self.parts.append((logical,logical+length,kind,payload))
   logical+=length;pos+=total
  assert logical==self.size;self.starts=[a[0] for a in self.parts]
 def read(self,off,n):
  assert 0<=off and off+n<=self.size
  out=bytearray()
  while n:
   a,b,kind,payload=self.parts[bisect.bisect_right(self.starts,off)-1];take=min(n,b-off)
   if kind==0xcac1:out+=self.pkg.read('super',payload+off-a,take)
   elif kind==0xcac2:
    pattern=self.pkg.read('super',payload,4);shift=(off-a)%4;out+=(pattern*((take+shift+3)//4))[shift:shift+take]
   else:out+=bytes(take)
   off+=take;n-=take
  return bytes(out)
class Logical:
 def __init__(self,sparse,segments):self.sparse=sparse;self.segments=segments;self.size=sum(x[1]*512 for x in segments)
 def read(self,name,off,n):
  assert 0<=off and off+n<=self.size;out=bytearray();logical=0
  for kind,sectors,physical in self.segments:
   length=sectors*512
   if off<logical+length and n:
    delta=max(0,off-logical);take=min(n,length-delta)
    out+=self.sparse.read(physical*512+delta,take) if kind==0 else bytes(take)
    off+=take;n-=take
   logical+=length
  assert n==0;return bytes(out)
def inventory():
 source=Path(r'D:\Netdisk\Other\F8-PRO\update-ANDROID12.img');pkg=Package(source);s=Sparse(pkg)
 geo=s.read(4096,4096);assert struct.unpack_from('<I',geo)[0]==0x616c4467
 maxsize,slots,bs=struct.unpack_from('<3I',geo,40)
 offset=4096*3;head=s.read(offset,128);assert struct.unpack_from('<I',head)[0]==0x414c5030
 hsize=struct.unpack_from('<I',head,8)[0];tablesize=struct.unpack_from('<I',head,44)[0]
 tables=s.read(offset+hsize,tablesize);assert hashlib.sha256(tables).digest()==head[48:80]
 po,pn,ps=struct.unpack_from('<3I',head,80);eo,en,es=struct.unpack_from('<3I',head,92)
 partitions={}
 for i in range(pn):
  entry=tables[po+i*ps:po+(i+1)*ps];name=entry[:36].split(b'\0')[0].decode();attr,first,num,group=struct.unpack_from('<4I',entry,36)
  ext=[]
  for j in range(first,first+num):
   sectors,kind,physical,device=struct.unpack_from('<QIQI',tables,eo+j*es);assert device==0 and kind in [0,1];ext.append((kind,sectors,physical))
  partitions[name]={'attributes':attr,'segments':ext,'bytes':sum(x[1]*512 for x in ext)}
 O=P/'analysis/armbian/android-sensor-audit-20261103';O.mkdir(parents=True,exist_ok=True)
 report={'source':str(source),'source_bytes':source.stat().st_size,'sparse_expanded_bytes':s.size,'partitions':partitions,'android_files':{},'selected_files':[],'dt_nodes':{}}
 for name,part in partitions.items():
  if name not in ['vendor','odm','system','system_ext','product'] or not part['bytes']:continue
  mapped=Logical(s,part['segments'])
  try:fs=Ext4(mapped,name)
  except AssertionError:report['android_files'][name]={'filesystem_magic':mapped.read(name,1024,64).hex()};continue
  items=list(fs.walk());selected=[]
  for path,ino,kind in items:
   if kind!=1:continue
   low=path.lower()
   match=(('sensor' in low and ('/hw/' in low or '/etc/' in low or '/bin/hw/' in low or low.endswith(('.xml','.json','.conf','.rc','.so')))) or (low.endswith('/manifest.xml') and '/vintf/' in low) or low.endswith('/build.prop'))
   if not match:continue
   try:data=fs.content(ino,limit=32*1024*1024)
   except ValueError:continue
   dest=O/name/path.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
   info={'partition':name,'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
   if data[:4]==b'\x7fELF':
    strings=[x.decode(errors='replace') for x in re.findall(rb'[ -~]{5,}',data)]
    info['sensor_strings']=[x for x in strings if re.search(r'android\.sensor\.|accelerom|gyrosc|magnet|orientation|gravity|linear.accel|rotation.vector|step.counter|step.detector|significant.motion|proximity|light.sensor|mpu|ak896|em309|pickup|tilt.detector',x,re.I) and len(x)<400]
   selected.append(info)
  report['android_files'][name]={'file_count':len(items),'selected':selected};report['selected_files']+=selected
 # Verify DTBs directly against this exact source image, not an old extraction.
 boot=pkg.read('boot');at=0;index=0
 while True:
  at=boot.find(b'\xd0\x0d\xfe\xed',at)
  if at<0:break
  try:
   length=struct.unpack_from('>I',boot,at+4)[0];blob=boot[at:at+length];nodes=fdt(blob)
   if 'compatible' in nodes.get('/',{}):
    name=f'dtb-{index}.dtb';index+=1
    (O/name).write_bytes(blob)
    report['dt_nodes'][name]={'sha256':hashlib.sha256(blob).hexdigest(),'nodes':{n:{k:pretty(v) for k,v in props.items()} for n,props in nodes.items() if re.search(r'mpu|gyro|compass|ak896|em309|mma7660|light@|proximity|hall-mh248|pressure|acceler',n+' '+str(props.get('compatible','')),re.I)}}
  except (AssertionError,ValueError,struct.error):pass
  at+=4
 (O/'inventory.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'partitions':{k:v['bytes'] for k,v in partitions.items()},'selected_count':len(report['selected_files']),'output':str(O)}))
if __name__=='__main__':inventory()
