"""Run extracted PM/contact/IRQ functions with pthread locks and fake hardware."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

P = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
out = P / 'armbian/touch/candidate-r8-shuping'
work = Path('/var/tmp/f8-pro-armbian/touch-pm-tests')
work.mkdir(parents=True, exist_ok=True)
source = (out / 'gsl3673.c').read_text()
def function(name):
    match = re.search(r'^static[^\n]*\b' + name + r'\([^;]*?\)\n\{', source, re.M)
    assert match, name
    pos = source.index('{', match.start()) + 1
    depth = 1
    while depth:
        depth += (source[pos] == '{') - (source[pos] == '}')
        pos += 1
    return source[match.start():pos] + '\n'

prefix = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#define __maybe_unused
#define MAX_CONTACTS 10
#define MT_TOOL_FINGER 0
#define FB_EVENT_BLANK 9
#define FB_BLANK_UNBLANK 0
#define NOTIFY_DONE 0
#define NOTIFY_OK 1
#define NOTIFY_STOP_MASK 0x8000
#define container_of(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
static int notifier_from_errno(int err) { return err ? NOTIFY_STOP_MASK | (NOTIFY_OK-err) : NOTIFY_OK; }
struct mutex { pthread_mutex_t lock; };
static void mutex_lock(struct mutex *m) { assert(!pthread_mutex_lock(&m->lock)); }
static void mutex_unlock(struct mutex *m) { assert(!pthread_mutex_unlock(&m->lock)); }
#define spin_lock_irqsave(m,f) do { (f)=0; assert(!pthread_mutex_lock(m)); } while(0)
#define spin_unlock_irqrestore(m,f) do { (void)(f); assert(!pthread_mutex_unlock(m)); } while(0)
struct device { void *data; };
static void *dev_get_drvdata(struct device *d) { return d->data; }
struct i2c_client { int irq; struct device dev; };
struct input_dev { bool slots[11]; int slot, syncs, released; };
struct work_struct { int dummy; };
struct tp_device { int dummy; };
struct notifier_block { int dummy; };
struct fb_event { void *data; };
struct gsl_ts {
    struct mutex state_lock;
    pthread_mutex_t irq_lock;
    struct i2c_client *client;
    struct input_dev *input;
    struct work_struct work;
    struct tp_device tp;
    struct notifier_block f8_fb_notifier;
    bool stopping, quiescing, system_suspended, display_suspended, flag_activated;
    int flag_irq_is_disable;
};
static struct gsl_ts *current;
static uint32_t id_sign[11];
static uint8_t id_state_flag[11], id_state_old_flag[11];
static uint16_t x_old[11], y_old[11], x_new, y_new;
static int irq_enables, irq_disables, lows, highs, fail_stage, reset_calls;
static bool slow_hardware;
static void ts_irq_enable(struct gsl_ts *ts);
static void enable_irq(int irq) { assert(irq==17); irq_enables++; }
static void disable_irq_nosync(int irq) { assert(irq==17); irq_disables++; }
static void synchronize_irq(int irq) { assert(irq==17); assert(current->quiescing); }
static void cancel_work_sync(struct work_struct *work) {
    (void)work;
    int before=irq_enables;
    ts_irq_enable(current); /* emulate a worker completing while suspend drains */
    assert(irq_enables==before);
}
static void input_mt_slot(struct input_dev *in, int slot) { assert(slot>=0 && slot<=10); in->slot=slot; }
static void input_mt_report_slot_state(struct input_dev *in, int tool, bool down) {
    assert(tool==MT_TOOL_FINGER && !down);
    in->slots[in->slot]=false; in->released++;
}
static void input_sync(struct input_dev *in) { in->syncs++; }
static void gsl3673_shutdown_low(void) { lows++; }
static void gsl3673_shutdown_high(void) {
    assert(!current->system_suspended && !current->display_suspended); highs++;
}
static void mdelay(int ms) { assert(ms==5); }
static int reset_chip(struct i2c_client *client) {
    (void)client; reset_calls++;
    assert(!current->system_suspended && !current->display_suspended);
    if (slow_hardware) usleep(10);
    return fail_stage==1 ? -EIO : 0;
}
static int startup_chip(struct i2c_client *client) { (void)client; return fail_stage==2 ? -EIO : 0; }
static int check_mem_data(struct i2c_client *client) { (void)client; return fail_stage==3 ? -EIO : 0; }
'''
names = ['ts_irq_disable', 'ts_irq_enable', 'gsl_release_contacts', 'gsl_suspend_locked',
         'gsl_resume_locked', 'gsl_set_suspend_reason', 'gsl_ts_pm_suspend', 'gsl_ts_pm_resume',
         'gsl_ts_early_suspend', 'gsl_ts_late_resume', 'gsl_f8_fb_event']
main = r'''
static void assert_released(struct gsl_ts *ts) {
    for(int i=0;i<11;i++) {
        assert(!ts->input->slots[i]);
        assert(!id_sign[i] && !id_state_flag[i] && !id_state_old_flag[i] && !x_old[i] && !y_old[i]);
    }
    assert(!x_new && !y_new);
}
static void *events(void *argument) {
    bool system=(bool)(uintptr_t)argument;
    for(int i=0;i<1000;i++) {
        assert(!gsl_set_suspend_reason(current,system,true));
        assert(!gsl_set_suspend_reason(current,system,false));
    }
    return NULL;
}
int main(void) {
    struct i2c_client client={.irq=17};
    struct input_dev input={0};
    struct gsl_ts ts={.state_lock={PTHREAD_MUTEX_INITIALIZER},.irq_lock=PTHREAD_MUTEX_INITIALIZER,
                      .client=&client,.input=&input,.flag_activated=true};
    current=&ts; client.dev.data=&ts;
    memset(input.slots,1,sizeof(input.slots));
    memset(id_sign,0xa5,sizeof(id_sign)); memset(id_state_flag,0xa5,sizeof(id_state_flag));
    memset(id_state_old_flag,0xa5,sizeof(id_state_old_flag));
    memset(x_old,0xa5,sizeof(x_old)); memset(y_old,0xa5,sizeof(y_old)); x_new=y_new=42;
    assert(!gsl_ts_early_suspend(&ts.tp)); assert_released(&ts);
    assert(input.released==11 && input.syncs==1 && ts.quiescing && !ts.flag_activated);
    assert(irq_disables==1 && irq_enables==0);
    assert(!gsl_ts_early_suspend(&ts.tp)); assert(input.syncs==1 && lows==1);
    assert(!gsl_ts_pm_suspend(&client.dev));
    assert(!gsl_ts_late_resume(&ts.tp)); assert(!ts.flag_activated && highs==0);
    assert(!gsl_ts_pm_resume(&client.dev)); assert(ts.flag_activated && irq_enables==1);
    assert(!gsl_ts_pm_suspend(&client.dev)); assert(!gsl_ts_early_suspend(&ts.tp));
    assert(!gsl_ts_pm_resume(&client.dev)); assert(!ts.flag_activated);
    assert(!gsl_ts_late_resume(&ts.tp)); assert(ts.flag_activated);
    for(int stage=1;stage<=3;stage++) {
        assert(!gsl_ts_pm_suspend(&client.dev)); fail_stage=stage;
        int before=irq_enables;
        assert(gsl_ts_pm_resume(&client.dev)==-EIO);
        assert(ts.system_suspended && ts.quiescing && !ts.flag_activated);
        assert(irq_enables==before);
        fail_stage=0; assert(!gsl_ts_pm_resume(&client.dev)); assert(ts.flag_activated);
    }
    int blank=4; struct fb_event event={.data=&blank};
    assert(gsl_f8_fb_event(&ts.f8_fb_notifier,0,&event)==NOTIFY_DONE);
    assert(gsl_f8_fb_event(&ts.f8_fb_notifier,FB_EVENT_BLANK,NULL)==NOTIFY_DONE);
    assert(gsl_f8_fb_event(&ts.f8_fb_notifier,FB_EVENT_BLANK,&event)==NOTIFY_OK);
    blank=0; fail_stage=2;
    assert(gsl_f8_fb_event(&ts.f8_fb_notifier,FB_EVENT_BLANK,&event)==notifier_from_errno(-EIO));
    assert(ts.display_suspended && !ts.flag_activated);
    fail_stage=0;
    assert(gsl_f8_fb_event(&ts.f8_fb_notifier,FB_EVENT_BLANK,&event)==NOTIFY_OK);
    assert(ts.flag_activated && !ts.display_suspended);
    slow_hardware=true;
    pthread_t a,b;
    assert(!pthread_create(&a,NULL,events,(void *)(uintptr_t)true));
    assert(!pthread_create(&b,NULL,events,(void *)(uintptr_t)false));
    assert(!pthread_join(a,NULL)); assert(!pthread_join(b,NULL));
    assert(!ts.system_suspended && !ts.display_suspended && ts.flag_activated && !ts.quiescing);
    assert_released(&ts);
    ts.stopping=true; int before=reset_calls;
    assert(gsl_set_suspend_reason(&ts,true,true)==-ENODEV);
    assert(reset_calls==before);
    ts.flag_irq_is_disable=1; before=irq_enables; ts_irq_enable(&ts); assert(irq_enables==before);
    puts("PM ordering, release, retry, notifier, IRQ guards and 4000 concurrent requests passed");
    return 0;
}
'''
(work / 'pm-test.c').write_text(prefix + '\n'.join(function(name) for name in names) + main)
subprocess.run(['gcc','-std=gnu11','-O1','-Wall','-Wextra','-Werror','-pthread',
                '-fsanitize=undefined','-fno-sanitize-recover=all',str(work / 'pm-test.c'),
                '-o',str(work / 'pm-test')],check=True)
result = subprocess.check_output([str(work / 'pm-test')],text=True,timeout=30)
report={'scope':'Extracted PM functions on host pthread locks/fake hardware; no kernel scheduler, real IRQ, display or power test',
        'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(), 'ubsan_passed':True,
        'all_11_slots_released_without_fake_press':True, 'filter_state_cleared':True,
        'display_system_orderings_checked':2, 'resume_failure_stages_retried':3,
        'notifier_error_and_identical_event_retry_checked':True,
        'quiescing_and_stopping_block_worker_irq_enable':True,
        'concurrent_pm_requests':4000, 'covered':names,'test_output':result.strip()}
(out / 'pm-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
