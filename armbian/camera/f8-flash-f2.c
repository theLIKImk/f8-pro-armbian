// SPDX-License-Identifier: GPL-2.0
/* F8 GPIO3_C1: software PWM brightness, steady light, blink and bounded lease. */
#include <linux/gpio/consumer.h>
#include <linux/gpio/machine.h>
#include <linux/hrtimer.h>
#include <linux/leds.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/spinlock.h>
#include <linux/workqueue.h>

enum flash_mode { MODE_OFF,MODE_PULSE,MODE_STEADY,MODE_BLINK };
struct f8_flash {
 struct gpio_desc *enable;
 struct led_classdev led;
 struct hrtimer pwm;
 struct delayed_work phase_work,expiry_work;
 struct mutex io_lock,lock;
 spinlock_t pwm_lock;
 unsigned int duty,level,on_ms,off_ms;
 enum flash_mode mode;
 unsigned long deadline;
 bool high,phase_on,closing,suspended;
 u64 edges;
};
static struct platform_device *board;
static int probe_result=-ENODEV;
static struct gpiod_lookup_table lookup={
 .dev_id="f8-flash",
 .table={GPIO_LOOKUP("gpio3",17,"enable",GPIO_ACTIVE_HIGH),{}}
};
static enum hrtimer_restart pwm_tick(struct hrtimer *timer)
{
 struct f8_flash *f=container_of(timer,struct f8_flash,pwm);
 unsigned long flags;unsigned int ns;
 spin_lock_irqsave(&f->pwm_lock,flags);
 if(!f->duty || f->duty>=100) {
  gpiod_set_value(f->enable,f->duty>=100);spin_unlock_irqrestore(&f->pwm_lock,flags);
  return HRTIMER_NORESTART;
 }
 f->high=!f->high;gpiod_set_value(f->enable,f->high);f->edges++;
 /* 1kHz average PWM. GPIO must be non-sleeping; probe enforces this. */
 ns=(f->high?f->duty:100-f->duty)*10000;
 hrtimer_forward_now(timer,ns_to_ktime(ns));
 spin_unlock_irqrestore(&f->pwm_lock,flags);return HRTIMER_RESTART;
}
/* Called with the control mutex, never from the hrtimer callback. */
static void output(struct f8_flash *f,unsigned int duty)
{
 unsigned long flags;
 hrtimer_cancel(&f->pwm);
 spin_lock_irqsave(&f->pwm_lock,flags);
 f->duty=duty;f->high=!!duty;gpiod_set_value(f->enable,f->high);
 spin_unlock_irqrestore(&f->pwm_lock,flags);
 f->led.brightness=duty;
 if(duty && duty<100)hrtimer_start(&f->pwm,ns_to_ktime(duty*10000),HRTIMER_MODE_REL);
}
static void phase_work(struct work_struct *work)
{
 struct f8_flash *f=container_of(to_delayed_work(work),struct f8_flash,phase_work);
 mutex_lock(&f->lock);
 if(f->mode==MODE_BLINK && !f->closing && !f->suspended) {
  f->phase_on=!f->phase_on;output(f,f->phase_on?f->level:0);
  mod_delayed_work(system_wq,&f->phase_work,msecs_to_jiffies(f->phase_on?f->on_ms:f->off_ms));
 }
 mutex_unlock(&f->lock);
}
static void expiry_work(struct work_struct *work)
{
 struct f8_flash *f=container_of(to_delayed_work(work),struct f8_flash,expiry_work);
 mutex_lock(&f->lock);
 if(f->mode!=MODE_OFF) {
  if(time_before(jiffies,f->deadline))mod_delayed_work(system_wq,&f->expiry_work,f->deadline-jiffies);
  else {f->mode=MODE_OFF;cancel_delayed_work(&f->phase_work);output(f,0);}
 }
 mutex_unlock(&f->lock);
}
static int configure(struct f8_flash *f,enum flash_mode mode,unsigned int level,unsigned int on,unsigned int off)
{
 int ret=0;
 if(mode!=MODE_OFF && (level<1 || level>100))return -EINVAL;
 if(mode==MODE_BLINK && (on<100 || on>5000 || off<100 || off>5000))return -EINVAL;
 mutex_lock(&f->io_lock);
 cancel_delayed_work_sync(&f->phase_work);cancel_delayed_work_sync(&f->expiry_work);
 mutex_lock(&f->lock);
 if(mode!=MODE_OFF && (f->closing || f->suspended)){ret=-ENODEV;goto done;}
 f->mode=mode;f->level=level;f->on_ms=on;f->off_ms=off;f->phase_on=true;
 output(f,mode==MODE_OFF?0:level);
 if(mode!=MODE_OFF) {
  unsigned int duration=mode==MODE_PULSE?500:5000;
  f->deadline=jiffies+msecs_to_jiffies(duration);
  mod_delayed_work(system_wq,&f->expiry_work,msecs_to_jiffies(duration));
  if(mode==MODE_BLINK)mod_delayed_work(system_wq,&f->phase_work,msecs_to_jiffies(on));
 }
done:mutex_unlock(&f->lock);mutex_unlock(&f->io_lock);return ret;
}
static int set_brightness(struct led_classdev *led,enum led_brightness value)
{
 struct f8_flash *f=container_of(led,struct f8_flash,led);
 /* The standard brightness write is still a finite pulse by default. */
 return configure(f,value?MODE_PULSE:MODE_OFF,value,500,500);
}
static enum led_brightness get_brightness(struct led_classdev *led)
{return READ_ONCE(container_of(led,struct f8_flash,led)->duty);}
static ssize_t control_store(struct device *dev,struct device_attribute *attr,const char *buf,size_t count)
{
 struct f8_flash *f=dev_get_drvdata(dev);char command[16],extra;
 unsigned int level=0,on=500,off=500;enum flash_mode mode;int fields,ret;
 fields=sscanf(buf,"%15s %u %u %u %c",command,&level,&on,&off,&extra);
 if(fields==1 && !strcmp(command,"keepalive")) {
  mutex_lock(&f->io_lock);mutex_lock(&f->lock);
  if(f->mode==MODE_STEADY || f->mode==MODE_BLINK) {
   f->deadline=jiffies+msecs_to_jiffies(5000);
   mod_delayed_work(system_wq,&f->expiry_work,msecs_to_jiffies(5000));
  }
  mutex_unlock(&f->lock);mutex_unlock(&f->io_lock);return count;
 }
 if(fields==1 && !strcmp(command,"off"))mode=MODE_OFF;
 else if(fields==2 && !strcmp(command,"pulse"))mode=MODE_PULSE;
 else if(fields==2 && !strcmp(command,"steady"))mode=MODE_STEADY;
 else if(fields==4 && !strcmp(command,"blink"))mode=MODE_BLINK;
 else return -EINVAL;
 ret=configure(f,mode,level,on,off);return ret?ret:count;
}
static DEVICE_ATTR_WO(control);
static ssize_t state_show(struct device *dev,struct device_attribute *attr,char *buf)
{
 struct f8_flash *f=dev_get_drvdata(dev);const char *names[]={"off","pulse","steady","blink"};
 unsigned long flags;u64 edges;unsigned int duty;ssize_t n;
 mutex_lock(&f->lock);spin_lock_irqsave(&f->pwm_lock,flags);
 edges=f->edges;duty=f->duty;spin_unlock_irqrestore(&f->pwm_lock,flags);
 n=sysfs_emit(buf,"mode=%s level=%u output=%u on_ms=%u off_ms=%u pwm_edges=%llu lease_ms=%u\n",
  names[f->mode],f->level,duty,f->on_ms,f->off_ms,edges,
  f->mode!=MODE_OFF && time_before(jiffies,f->deadline)?jiffies_to_msecs(f->deadline-jiffies):0);
 mutex_unlock(&f->lock);return n;
}
static DEVICE_ATTR_RO(state);
static struct attribute *attrs[]={&dev_attr_control.attr,&dev_attr_state.attr,NULL};
static const struct attribute_group group={.attrs=attrs};
static int probe(struct platform_device *pdev)
{
 struct f8_flash *f;int ret;
 f=devm_kzalloc(&pdev->dev,sizeof(*f),GFP_KERNEL);if(!f)return -ENOMEM;
 mutex_init(&f->lock);mutex_init(&f->io_lock);spin_lock_init(&f->pwm_lock);
 INIT_DELAYED_WORK(&f->phase_work,phase_work);INIT_DELAYED_WORK(&f->expiry_work,expiry_work);
 hrtimer_init(&f->pwm,CLOCK_MONOTONIC,HRTIMER_MODE_REL);f->pwm.function=pwm_tick;
 f->enable=devm_gpiod_get(&pdev->dev,"enable",GPIOD_OUT_LOW);
 if(IS_ERR(f->enable))return PTR_ERR(f->enable);
 if(gpiod_cansleep(f->enable))return -EOPNOTSUPP;
 f->led.name="f8:white:flash";f->led.max_brightness=100;
 f->led.brightness_set_blocking=set_brightness;f->led.brightness_get=get_brightness;
 platform_set_drvdata(pdev,f);
 ret=devm_led_classdev_register(&pdev->dev,&f->led);if(ret)return ret;
 ret=devm_device_add_group(&pdev->dev,&group);if(ret)return ret;
 dev_info(&pdev->dev,"GPIO3_C1 PWM/steady/blink ready, off by default, 5s lease\n");return 0;
}
static int probe_record(struct platform_device *pdev)
{probe_result=probe(pdev);return probe_result;}
static void stop(struct f8_flash *f,bool closing)
{
 mutex_lock(&f->io_lock);
 cancel_delayed_work_sync(&f->phase_work);cancel_delayed_work_sync(&f->expiry_work);
 mutex_lock(&f->lock);f->closing=closing;f->suspended=true;f->mode=MODE_OFF;output(f,0);
 mutex_unlock(&f->lock);mutex_unlock(&f->io_lock);
}
static int remove_device(struct platform_device *pdev)
{stop(platform_get_drvdata(pdev),true);return 0;}
static void shutdown_device(struct platform_device *pdev)
{stop(platform_get_drvdata(pdev),true);}
static int suspend_device(struct device *dev)
{stop(dev_get_drvdata(dev),false);return 0;}
static int resume_device(struct device *dev)
{
 struct f8_flash *f=dev_get_drvdata(dev);
 mutex_lock(&f->lock);f->suspended=false;mutex_unlock(&f->lock);return 0;
}
static SIMPLE_DEV_PM_OPS(pm_ops,suspend_device,resume_device);
static struct platform_driver driver={.probe=probe_record,.remove=remove_device,
 .shutdown=shutdown_device,.driver={.name="f8-flash",.pm=&pm_ops}};
static int __init init_board(void)
{
 const char *model;int ret;
 if(of_property_read_string(of_root,"model",&model) || strncmp(model,"F8-PRO",6))return -ENODEV;
 ret=platform_driver_register(&driver);if(ret)return ret;
 gpiod_add_lookup_table(&lookup);
 board=platform_device_register_simple("f8-flash",PLATFORM_DEVID_NONE,NULL,0);
 if(IS_ERR(board)){ret=PTR_ERR(board);goto fail;}
 if(probe_result){ret=probe_result;platform_device_unregister(board);goto fail;}
 return 0;
fail:gpiod_remove_lookup_table(&lookup);platform_driver_unregister(&driver);return ret;
}
static void __exit exit_board(void)
{platform_device_unregister(board);gpiod_remove_lookup_table(&lookup);platform_driver_unregister(&driver);}
module_init(init_board);module_exit(exit_board);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("F8-PRO PWM flash LED, steady/blink and renewable watchdog");
