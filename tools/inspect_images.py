"""Read-only RKFW/RKAF, FDT and ext4 inspection. Never writes input images."""
import argparse, hashlib, json, pathlib, re, struct

def u32(b, o=0): return struct.unpack_from('<I', b, o)[0]
def z(b): return b.split(b'\0', 1)[0].decode('utf-8', 'replace')

class Package:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.f = self.path.open('rb')
        h = self.f.read(102)
        assert h[:4] == b'RKFW'
        self.base = u32(h, 33)
        self.f.seek(self.base)
        h = self.f.read(2048)
        assert h[:4] == b'RKAF'
        self.entries = {}
        for i in range(u32(h, 136)):
            e = h[140 + i*112:252 + i*112]
            off, flash, sectors, size = struct.unpack_from('<4I', e, 96)
            assert self.base + off + size <= self.path.stat().st_size
            self.entries[z(e[:32])] = dict(path=z(e[32:96]), offset=self.base+off,
                                          flash_sector=flash, size=size)
    def read(self, name, offset=0, size=None):
        e = self.entries[name]
        if size is None: size = e['size'] - offset
        assert 0 <= offset <= e['size'] and 0 <= size <= e['size']-offset
        self.f.seek(e['offset'] + offset)
        return self.f.read(size)

def fdt(data):
    magic, total, st, strings, _, version, _, _, nstrings, nstruct = struct.unpack_from('>10I', data)
    assert magic == 0xd00dfeed and total <= len(data)
    p, stack, nodes = st, [], {}
    while p < st+nstruct:
        token = struct.unpack_from('>I', data, p)[0]; p += 4
        if token == 1:
            end = data.index(0, p); stack.append(data[p:end].decode()); p = (end+4)&~3
            nodes['/'.join(stack) or '/'] = {}
        elif token == 2: stack.pop()
        elif token == 3:
            size, nameoff = struct.unpack_from('>II', data, p); p += 8
            name = z(data[strings+nameoff:strings+nstrings]); raw = data[p:p+size]
            nodes['/'.join(stack) or '/'][name] = raw
            p = (p+size+3)&~3
        elif token == 4: pass
        elif token == 9: break
        else: raise ValueError('invalid FDT token')
    return nodes

def pretty(raw):
    if not raw: return True
    if raw[-1:] == b'\0' and all(c in (0,9,10,13) or 32 <= c < 127 for c in raw):
        return raw.rstrip(b'\0').decode().split('\0')
    return raw.hex()

class Ext4:
    def __init__(self, package, name):
        self.pkg, self.name = package, name
        self.sb = self.read(1024,1024)
        assert self.sb[56:58] == b'\x53\xef'
        self.bs = 1024 << u32(self.sb,24)
        self.ipg = u32(self.sb,40)
        self.isize = struct.unpack_from('<H',self.sb,88)[0]
        self.descsize = max(32,struct.unpack_from('<H',self.sb,254)[0])
        self.gdt = (2 if self.bs==1024 else 1)*self.bs
    def read(self, off, size): return self.pkg.read(self.name,off,size)
    def inode(self, ino):
        group, idx = divmod(ino-1,self.ipg)
        d = self.read(self.gdt+group*self.descsize,self.descsize)
        table = u32(d,8) | ((u32(d,40)<<32) if self.descsize>=64 else 0)
        return self.read(table*self.bs+idx*self.isize,self.isize)
    def extents(self, node):
        magic, entries, _, depth = struct.unpack_from('<4H',node)
        assert magic == 0xf30a, 'non-extent inode is unsupported'
        for i in range(entries):
            e=node[12+i*12:24+i*12]
            if depth:
                _, lo, hi = struct.unpack_from('<IIH',e)
                yield from self.extents(self.read((lo|(hi<<32))*self.bs,self.bs))
            else:
                logical, length, hi, lo = struct.unpack('<IHHI',e)
                # ext4 encodes 32768 initialized blocks as 0x8000.
                unwritten = length > 32768
                count = length-32768 if unwritten else length
                yield logical,count,(hi<<32)|lo,unwritten
    def content(self, ino, limit=32*1024*1024):
        n=self.inode(ino); size=u32(n,4)|(u32(n,108)<<32)
        if size>limit: raise ValueError('file exceeds extraction limit')
        mode=struct.unpack_from('<H',n)[0]
        if mode&0xf000==0xa000 and size<=60: return n[40:40+size]
        out=bytearray(size)
        if not size: return bytes(out)
        if not u32(n,32)&0x80000: raise ValueError('non-extent inode is unsupported')
        for logical,count,physical,unwritten in self.extents(n[40:100]):
            start=logical*self.bs; length=min(count*self.bs,size-start)
            if length>0 and not unwritten: out[start:start+length]=self.read(physical*self.bs,length)
        return bytes(out)
    def ls(self, ino):
        b=self.content(ino); p=0
        while p+8<=len(b):
            child,rec,nlen,kind=struct.unpack_from('<IHBB',b,p)
            if rec<8 or p+rec>len(b): raise ValueError('invalid directory record')
            name=b[p+8:p+8+nlen].decode('utf-8','replace')
            if child and name not in ('.','..'): yield name,child,kind
            p+=rec
    def lookup(self, path):
        ino=2
        for part in pathlib.PurePosixPath(path).parts:
            if part=='/': continue
            ino=next(i for n,i,k in self.ls(ino) if n==part)
        return ino
    def walk(self, ino=2, prefix=''):
        for name,child,kind in self.ls(ino):
            path=prefix+'/'+name
            yield path,child,kind
            if kind==2: yield from self.walk(child,path)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('output'); a=ap.parse_args()
    out=pathlib.Path(a.output); out.mkdir(parents=True,exist_ok=True)
    summary={}
    for image in pathlib.Path(a.source).glob('*.img'):
        pkg=Package(image); dest=out/image.stem; dest.mkdir(exist_ok=True)
        summary[image.name]=pkg.entries
        (dest/'partitions.json').write_text(json.dumps(pkg.entries,indent=2),encoding='utf-8')
        for name in ('parameter','package-file'):
            (dest/(name+'.txt')).write_text(pkg.read(name).decode('utf-8','replace'),encoding='utf-8')
        boot=pkg.read('boot'); (dest/'boot-header.json').write_text(json.dumps({'magic':boot[:16].hex(),'size':len(boot)}))
        # FDT containers may contain nested DTBs and external FIT payloads.
        start=0; index=0
        while True:
            start=boot.find(b'\xd0\x0d\xfe\xed',start)
            if start<0: break
            try:
                size=struct.unpack_from('>I',boot,start+4)[0]
                nodes=fdt(boot[start:start+size])
                if 'compatible' in nodes.get('/',{}):
                    (dest/f'dtb-{index}.dtb').write_bytes(boot[start:start+size])
                    readable={n:{k:pretty(v) for k,v in props.items() if k!='data'} for n,props in nodes.items()}
                    (dest/f'dtb-{index}.json').write_text(json.dumps(readable,indent=2),encoding='utf-8'); index+=1
                elif start==0:
                    (dest/'fit.json').write_text(json.dumps({n:{k:pretty(v) for k,v in props.items() if k!='data'} for n,props in nodes.items()},indent=2),encoding='utf-8')
            except (ValueError,struct.error,AssertionError): pass
            start+=4
        print(image.name, 'DTBs',index)
        if 'rootfs' in pkg.entries:
            fs=Ext4(pkg,'rootfs'); items=list(fs.walk())
            (dest/'rootfs-files.txt').write_text('\n'.join(p for p,_,_ in items),encoding='utf-8')
            selected=[]
            for path,ino,kind in items:
                if kind!=1: continue
                if (path in ('/etc/os-release','/etc/lsb-release','/etc/fstab','/etc/modules','/var/lib/dpkg/status')
                    or path.startswith(('/etc/X11/','/etc/modprobe.d/','/etc/modules-load.d/','/etc/udev/rules.d/','/etc/alsa/','/etc/pulse/','/etc/systemd/system/','/boot/'))
                    or ('/lib/firmware/' not in path and re.search(r'(libmali|panfrost|panthor|rkisp|rkaiq|asound|rotation|rotate|bluetooth|wifi)',path,re.I) and path.endswith(('.conf','.service','.sh','.rules','.json','.state')))):
                    try:
                        data=fs.content(ino)
                        target=dest/'rootfs-selected'/path.lstrip('/'); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data); selected.append(path)
                    except ValueError: pass
            (dest/'selected-files.txt').write_text('\n'.join(selected),encoding='utf-8')
            print('Rootfs files',len(items),'selected',len(selected))
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')

if __name__=='__main__': main()
