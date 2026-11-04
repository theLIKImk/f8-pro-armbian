"""Exercise extracted binding guards and input worker on host fake devices."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
out=P/'armbian/touch/candidate-r8-shuping'
work=Path('/var/tmp/f8-pro-armbian/touch-binding-input-tests')
work.mkdir(parents=True,exist_ok=True)
source=(out/'gsl3673.c').read_text()
def function(name):
    m=re.search(r'^static[^\n]*\b'+name+r'\([^;]*?\)\n\{',source,re.M)
    assert m,name
    pos=source.index('{',m.start())+1
    depth=1
    while depth:
        depth+=(source[pos]=='{')-(source[pos]=='}');pos+=1
    return source[m.start():pos]+'\n'
prefix=r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <pthread.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
#define MAX_CONTACTS 10
#define MAX_FINGERS 10
#define GSL_NOID_VERSION
#define REPORT_DATA_ANDROID_4_0
#define ABS_MT_TRACKING_ID 1
#define MT_TOOL_FINGER 0
#define container_of(p,t,m) ((t*)((char*)(p)-offsetof(t,m)))
#define dev_err(...) ((void)0)
#define print_info(...) ((void)0)
#define DEFINE_MUTEX(n) pthread_mutex_t n=PTHREAD_MUTEX_INITIALIZER
static void mutex_lock(pthread_mutex_t *m) { assert(!pthread_mutex_lock(m)); }
static void mutex_unlock(pthread_mutex_t *m) { assert(!pthread_mutex_unlock(m)); }
struct i2c_client { int id; };
struct work_struct { int dummy; };
struct input_dev { bool slots[11]; int selected, syncs; };
struct gsl_ts_data { int x_index,y_index,id_index,touch_index,data_size; };
struct profile { int max_x,max_y; };
struct gsl_ts { struct i2c_client *client;struct work_struct work;struct input_dev *input;
                struct gsl_ts_data *dd;struct profile *profile;u8 *touch_data; };
struct gsl_touch_info { int x[10],y[10],id[10],finger_num; };
static struct gsl_ts *this_ts;static struct i2c_client *gsl_client;
static u32 id_sign[11];static u8 id_state_flag[11],id_state_old_flag[11];
static u16 x_old[11],y_old[11],x_new,y_new;
static struct gsl_touch_info fixture;
static u8 raw[44];static int read_error,write_fail,write_calls,reports,alg_calls,irq_returns;
static u32 mask;
static u32 get_unaligned_le32(const u8 *p) { return (u32)p[0]|((u32)p[1]<<8)|((u32)p[2]<<16)|((u32)p[3]<<24); }
static int gsl_ts_read(struct i2c_client *c,u8 reg,u8 *data,int size) {
    (void)c;assert(reg==0x80 && size==44);if(read_error)return -EIO;memcpy(data,raw,44);return 44;
}
static int gsl_ts_write(struct i2c_client *c,u8 reg,u8 *data,int size) {
    (void)c;(void)reg;(void)data;assert(size==4);write_calls++;return write_calls==write_fail?-EIO:5;
}
static void gsl_alg_id_main(struct gsl_touch_info *info) {
    alg_calls++;
    for(int i=raw[0];i<10;i++) assert(!info->x[i] && !info->y[i] && !info->id[i]);
    *info=fixture;
}
static u32 gsl_mask_tiaoping(void) { return mask; }
static void input_mt_slot(struct input_dev *in,int slot) { assert(slot>=0 && slot<=10);in->selected=slot; }
static void input_mt_report_slot_state(struct input_dev *in,int tool,bool down) {assert(tool==0);in->slots[in->selected]=down;}
static void input_report_abs(struct input_dev *in,int code,int value) {(void)in;assert(code==1 && value==-1);}
static void input_sync(struct input_dev *in) {in->syncs++;}
static void record_point(u16 x,u16 y,u8 id) {assert(id>=1 && id<=10);x_new=x;y_new=y;}
static void report_data(struct gsl_ts *ts,u16 x,u16 y,u8 pressure,u8 id) {
    assert(x<=800 && y<=1280 && pressure==10 && id>=1 && id<=10);ts->input->slots[id]=true;reports++;
}
static void ts_irq_enable(struct gsl_ts *ts) {(void)ts;irq_returns++;}
'''
names=['gsl_claim_instance','gsl_release_instance','join_bytes','gsl_release_contacts','gsl3673_ts_worker']
# The mutex is declared in the template outside the extracted functions.
prefix+='\nstatic DEFINE_MUTEX(gsl_instance_lock);\n'
main=r'''
static pthread_barrier_t barrier;
struct contender {struct gsl_ts *ts;int result;};
static void *claim(void *p) {struct contender *c=p;pthread_barrier_wait(&barrier);c->result=gsl_claim_instance(c->ts);return NULL;}
static void reset_case(struct gsl_ts *ts) {
    memset(raw,0,sizeof(raw));raw[0]=1;memset(&fixture,0,sizeof(fixture));
    fixture.finger_num=1;fixture.id[0]=1;fixture.x[0]=100;fixture.y[0]=200;
    read_error=write_fail=write_calls=reports=alg_calls=irq_returns=0;mask=0;
    memset(ts->input,0,sizeof(*ts->input));memset(id_state_old_flag,0,sizeof(id_state_old_flag));
}
static void frame(struct gsl_ts *ts) {gsl3673_ts_worker(&ts->work);assert(irq_returns==1);}
int main(void) {
    struct i2c_client a={1},b={2};struct input_dev input={0};u8 buffer[44];
    struct gsl_ts_data dd={6,4,7,0,44};struct profile profile={800,1280};
    struct gsl_ts ts={.client=&a,.input=&input,.touch_data=buffer,.dd=&dd,.profile=&profile},other={.client=&b};
    struct contender ca={&ts,0},cb={&other,0};pthread_t ta,tb;
    pthread_barrier_init(&barrier,NULL,2);pthread_create(&ta,NULL,claim,&ca);pthread_create(&tb,NULL,claim,&cb);
    pthread_join(ta,NULL);pthread_join(tb,NULL);assert((ca.result==0)+(cb.result==0)==1);
    struct gsl_ts *winner=ca.result==0?&ts:&other,*loser=ca.result==0?&other:&ts;
    assert(this_ts==winner && gsl_client==winner->client);gsl_release_instance(loser);assert(this_ts==winner);
    assert(gsl_claim_instance(loser)==-EBUSY);gsl_release_instance(winner);assert(!this_ts && !gsl_client);
    assert(!gsl_claim_instance(&ts));gsl_release_instance(&ts);assert(!this_ts);
    reset_case(&ts);raw[3]=0x80;frame(&ts);assert(reports==1 && input.slots[1]);
    reset_case(&ts);raw[0]=11;input.slots[1]=true;frame(&ts);assert(!alg_calls && !reports && !input.slots[1]);
    for(int n=-1;n<=11;n+=12) {reset_case(&ts);fixture.finger_num=n;input.slots[1]=true;frame(&ts);assert(!reports && !input.slots[1]);}
    const int invalid[][3]={{257,100,200},{0,100,200},{11,100,200},{1,-1,200},{1,100,-1},{1,801,200},{1,100,1281},{1,65536,200}};
    for(unsigned int i=0;i<sizeof(invalid)/sizeof(invalid[0]);i++) {
        reset_case(&ts);fixture.id[0]=invalid[i][0];fixture.x[0]=invalid[i][1];fixture.y[0]=invalid[i][2];
        input.slots[1]=true;id_state_old_flag[1]=1;frame(&ts);assert(!reports && !input.slots[1]);
    }
    reset_case(&ts);fixture.finger_num=2;fixture.id[1]=1;fixture.x[1]=300;fixture.y[1]=400;frame(&ts);assert(reports==1);
    reset_case(&ts);raw[0]=10;fixture.finger_num=10;
    for(int i=0;i<10;i++){fixture.id[i]=i+1;fixture.x[i]=i%2?800:0;fixture.y[i]=i%2?1280:0;}
    frame(&ts);assert(reports==10);
    reset_case(&ts);read_error=1;input.slots[2]=true;frame(&ts);assert(!reports && !input.slots[2]);
    for(int step=1;step<=2;step++){reset_case(&ts);mask=123;write_fail=step;input.slots[2]=true;frame(&ts);assert(write_calls==step && !reports && !input.slots[2]);}
    puts("Binding exclusion/release/rebind and 17 input boundary/error scenarios passed");return 0;
}
'''
(work/'test.c').write_text(prefix+'\n'.join(function(name) for name in names)+main)
subprocess.run(['gcc','-std=gnu11','-O1','-Wall','-Wextra','-Werror','-Wno-sign-compare','-pthread',
    '-fsanitize=undefined','-fno-sanitize-recover=all',str(work/'test.c'),'-o',str(work/'test')],check=True)
result=subprocess.check_output([str(work/'test')],text=True,timeout=30)
report={'scope':'Extracted host functions with fake input/algorithm/devices; not real touch or devres teardown test',
        'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'ubsan_passed':True,
        'concurrent_bind_one_winner':True,'wrong_owner_cannot_release':True,'rebind_after_release':True,
        'input_scenarios':17,'algorithm_mocked':True,'covered':names,'test_output':result.strip()}
(out/'binding-input-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
