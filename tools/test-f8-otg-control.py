"""Run the actual C control function against a fake chip, never hardware."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]
source=(P/'armbian/usb/f8_otg_vbus.c').read_text()
start=source.index('static int f8_switch(');brace=source.index('{',start);depth=1;end=brace+1
while depth:
    if source[end]=='{':depth+=1
    elif source[end]=='}':depth-=1
    end+=1
function=source[start:end]
preamble=r'''
#include <assert.h>
#include <stdbool.h>
#include <errno.h>
#include <stdio.h>
#define BIT(n) (1U<<(n))
#define OTG_REG 3
#define OTG_BIT BIT(5)
struct chip { int reg[21]; int gate, writes, failread, failwrite, readbackbad; };
struct f8_otg { struct chip *client; struct chip *gate; };
static int i2c_smbus_read_byte_data(struct chip *p, int reg) {
 if (p->failread) return -EIO;
 if (p->readbackbad && p->writes && reg==3) return -EIO;
 return p->reg[reg];
}
static int i2c_smbus_write_byte_data(struct chip *p,int reg,int value) {
 assert(reg==3); assert(((p->reg[reg]^value)&~OTG_BIT)==0);
 if(p->failwrite) return -EIO;
 p->reg[reg]=value;p->writes++;return 0;
}
static void gpiod_set_value_cansleep(struct chip *p,int value) { p->gate=value; }
'''
main=r'''
int main(void) {
 struct chip c; struct f8_otg p={&c,&c}; int count=0;
 for(int old=0;old<256;old++) {
  if(old&BIT(6))continue;
  c=(struct chip){0};c.reg[3]=old;c.reg[10]=0x70;
  assert(f8_switch(&p,true)==0);assert(c.reg[3]==(old|OTG_BIT));assert(c.gate==1);
  assert(f8_switch(&p,false)==0);assert(c.reg[3]==(old&~OTG_BIT));assert(c.gate==0);count++;
 }
 for(int status=1;status<=6;status++) {
  c=(struct chip){0};c.reg[10]=0x70;c.reg[11]=status<<5;
  assert(f8_switch(&p,true)==-EBUSY);assert(!c.writes&&!c.gate);count++;
 }
 c=(struct chip){0};c.reg[10]=0x70;c.reg[11]=4;
 assert(f8_switch(&p,true)==-EBUSY);assert(!c.writes&&!c.gate);count++;
 for(int voltage=0;voltage<16;voltage++) {
  if(voltage>=5&&voltage<=10)continue;
  c=(struct chip){0};c.reg[10]=voltage<<4;
  assert(f8_switch(&p,true)==-ERANGE);assert(!c.writes&&!c.gate);count++;
 }
 c=(struct chip){0};c.failread=1;c.gate=1;
 assert(f8_switch(&p,false)==-EIO);assert(!c.gate);count++;
 c=(struct chip){0};c.failwrite=1;c.reg[10]=0x70;
 assert(f8_switch(&p,true)==-EIO);assert(!c.gate);count++;
 c=(struct chip){0};c.readbackbad=1;c.reg[10]=0x70;
 assert(f8_switch(&p,true)==-EIO);assert(!c.gate);count++;
 c=(struct chip){0};c.reg[3]=BIT(6);c.reg[10]=0x70;
 assert(f8_switch(&p,true)==-EBUSY);assert(!c.writes&&!c.gate);count++;
 printf("%d",count);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='f8-otg-test-') as tmp:
    path=Path(tmp);(path/'test.c').write_text(preamble+function+main)
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-sign-compare',str(path/'test.c'),'-o',str(path/'test')],check=True)
    count=int(subprocess.check_output([str(path/'test')],text=True))
report={'passed':True,'cases':count,'actual_C_switch_function_tested':True,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'coverage':['Preserve all non-OTG bits','Reject detected input source','Reject unexpected boost voltage','Gate low on I2C read/write/readback failure','No watchdog-reset strobe echo'],'hardware_touched':False}
(P/'outputs/armbian/official-f8-usb-u1-module/control-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
