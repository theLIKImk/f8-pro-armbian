"""Offline SPARC disassembly of the retained firmware array; never edits it."""
import hashlib,json,re,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'local/firmware-analysis/python'))
import capstone
source=P/'armbian/touch/official-6.1.115-f8/f8-pro-r8-shuping-reference.h'
body=source.read_text().split('static const struct fw_data f8_pro_r8_shuping_fw[] = {',1)[1].split('};',1)[0]
entries=[(int(a,16),int(b,16)) for a,b in re.findall(r'\{\s*(0x[0-9a-fA-F]+)\s*,\s*(0x[0-9a-fA-F]+)\s*\}',body)]
page=None;words={};pages=[]
for offset,value in entries:
 if offset==0xf0:page=value;pages.append(value)
 else:
  assert page is not None and offset<128 and offset%4==0
  words[page*128+offset]=value
out=P/'analysis/armbian/touch-rate-firmware';out.mkdir(parents=True,exist_ok=True)
decoder=capstone.Cs(capstone.CS_ARCH_SPARC,capstone.CS_MODE_BIG_ENDIAN)
lines=[]
for addr,value in sorted(words.items()):
 data=struct.pack('>I',value);ins=list(decoder.disasm(data,addr,count=1))
 text=f'{ins[0].mnemonic:10s} {ins[0].op_str}' if ins else '.word'
 lines.append(f'{addr:08x}: {value:08x} {text}')
(out/'firmware.sparc.asm').write_text('\n'.join(lines)+'\n')
(out/'words.json').write_text(json.dumps({hex(k):hex(v) for k,v in words.items()},indent=2)+'\n')
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'serialized_array_sha256':hashlib.sha256(b''.join(struct.pack('<II',a,b) for a,b in entries)).hexdigest(),'word_count':len(words),'pages':pages,'disassembler':'capstone 5.0.6 / SPARC big endian','logical_address_assumption':'page*128+offset; CPU parameter relocation not yet proven','device_changed':False}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'words':len(words),'page_range':[min(pages),max(pages)],'output':str(out)}))
