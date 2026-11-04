// SPDX-License-Identifier: GPL-2.0
/* F8 factory flash-rgb13h: GPIO3_C1, active high, binary output only.
 * Initial integration deliberately exposes bounded pulses, not variable current.
 */
#include <linux/gpio/consumer.h>
#include <linux/gpio/machine.h>
#include <linux/leds.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/workqueue.h>

struct f8_flash {
 struct gpio_desc *enable;
 struct led_classdev led;
 struct delayed_work off_work;
 struct mutex lock;
 bool active,closing,suspended;
 unsigned long last_off;
};
static struct platform_device *board;
static int probe_result=-ENODEV;
static struct gpiod_lookup_table lookup={
 .dev_id="f8-flash",
 .table={GPIO_LOOKUP("gpio3",17,"enable",GPIO_ACTIVE_HIGH),{}}
};
static void off_work(struct work_struct *work)
{
 struct f8_flash *f=container_of(to_delayed_work(work),struct f8_flash,off_work);
 mutex_lock(&f->lock);
 gpiod_set_value_cansleep(f->enable,0);f->active=false;
 f->led.brightness=LED_OFF;f->last_off=jiffies;
 mutex_unlock(&f->lock);
}
static int set_brightness(struct led_classdev *led,enum led_brightness value)
{
 struct f8_flash *f=container_of(led,struct f8_flash,led);
 int ret=0;
 mutex_lock(&f->lock);
 if(value) {
  if(f->closing || f->suspended) {ret=-ENODEV;goto out;}
  if(f->active)goto out; /* Repeated writes cannot extend the pulse. */
  if(time_before(jiffies,f->last_off+msecs_to_jiffies(500))) {ret=-EBUSY;goto out;}
  gpiod_set_value_cansleep(f->enable,1);f->active=true;
  mod_delayed_work(system_wq,&f->off_work,msecs_to_jiffies(500));
 } else {
  gpiod_set_value_cansleep(f->enable,0);
  if(f->active)f->last_off=jiffies;
  f->active=false;cancel_delayed_work(&f->off_work);
 }
out:mutex_unlock(&f->lock);return ret;
}
static enum led_brightness get_brightness(struct led_classdev *led)
{
 struct f8_flash *f=container_of(led,struct f8_flash,led);
 return READ_ONCE(f->active)?1:LED_OFF;
}
static int probe(struct platform_device *pdev)
{
 struct f8_flash *f;int ret;
 f=devm_kzalloc(&pdev->dev,sizeof(*f),GFP_KERNEL);if(!f)return -ENOMEM;
 mutex_init(&f->lock);INIT_DELAYED_WORK(&f->off_work,off_work);
 f->last_off=jiffies-msecs_to_jiffies(500);
 f->enable=devm_gpiod_get(&pdev->dev,"enable",GPIOD_OUT_LOW);
 if(IS_ERR(f->enable))return PTR_ERR(f->enable);
 f->led.name="f8:white:flash";f->led.max_brightness=1;
 f->led.brightness_set_blocking=set_brightness;f->led.brightness_get=get_brightness;
 f->led.flags=LED_CORE_SUSPENDRESUME;
 platform_set_drvdata(pdev,f);
 ret=devm_led_classdev_register(&pdev->dev,&f->led);if(ret)return ret;
 dev_info(&pdev->dev,"GPIO3_C1 ready, off by default, 500ms pulse/cooldown\n");
 return 0;
}
static int probe_record(struct platform_device *pdev)
{probe_result=probe(pdev);return probe_result;}
static void stop(struct f8_flash *f,bool closing)
{
 mutex_lock(&f->lock);f->closing=closing;f->suspended=true;
 gpiod_set_value_cansleep(f->enable,0);f->active=false;f->led.brightness=0;
 mutex_unlock(&f->lock);cancel_delayed_work_sync(&f->off_work);
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
MODULE_DESCRIPTION("F8-PRO binary flash LED with bounded 500ms pulses");
