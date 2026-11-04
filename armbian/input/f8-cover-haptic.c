// SPDX-License-Identifier: GPL-2.0
/* F8 factory wiring: Hall GPIO0_D3, active-low cover; motor GPIO3_C2, active-high.
 * Board-local platform/GPIO lookup avoids rebuilding or replacing the boot image.
 * Report a machine cover switch, not synthetic power keys or an untested lid suspend.
 */
#include <linux/atomic.h>
#include <linux/gpio/consumer.h>
#include <linux/gpio/driver.h>
#include <linux/gpio/machine.h>
#include <linux/input.h>
#include <linux/interrupt.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/of.h>
#include <linux/pinctrl/pinconf-generic.h>
#include <linux/pinctrl/consumer.h>
#include <linux/platform_device.h>
#include <linux/workqueue.h>

struct f8_aux {
 struct gpio_desc *hall,*motor;
 struct input_dev *cover,*haptic;
 struct delayed_work hall_work,off_work;
 struct work_struct motor_work;
 struct mutex motor_lock;
 atomic_t requested;
 int irq;
 bool closing;
};
static struct platform_device *board;
static int probe_result=-ENODEV;
static struct gpiod_lookup_table lookup={
 .dev_id="f8-cover-haptic",
 .table={GPIO_LOOKUP("gpio0",27,"hall",GPIO_ACTIVE_HIGH),
         GPIO_LOOKUP("gpio3",18,"motor",GPIO_ACTIVE_HIGH),{}}
};
static void hall_work(struct work_struct *w)
{
 struct f8_aux *a=container_of(to_delayed_work(w),struct f8_aux,hall_work);
 int raw=gpiod_get_value_cansleep(a->hall);
 if(raw<0 || a->closing)return;
 input_report_switch(a->cover,SW_MACHINE_COVER,!raw);input_sync(a->cover);
}
static irqreturn_t hall_irq(int irq,void *data)
{
 struct f8_aux *a=data;
 if(!a->closing)mod_delayed_work(system_wq,&a->hall_work,msecs_to_jiffies(25));
 return IRQ_HANDLED;
}
static void off_work(struct work_struct *w)
{
 struct f8_aux *a=container_of(to_delayed_work(w),struct f8_aux,off_work);
 mutex_lock(&a->motor_lock);atomic_set(&a->requested,0);
 gpiod_set_value_cansleep(a->motor,0);mutex_unlock(&a->motor_lock);
}
static void motor_work(struct work_struct *w)
{
 struct f8_aux *a=container_of(w,struct f8_aux,motor_work);
 mutex_lock(&a->motor_lock);
 if(!a->closing && atomic_read(&a->requested)) {
  gpiod_set_value_cansleep(a->motor,1);
  mod_delayed_work(system_wq,&a->off_work,msecs_to_jiffies(200));
 } else {gpiod_set_value_cansleep(a->motor,0);cancel_delayed_work(&a->off_work);}
 mutex_unlock(&a->motor_lock);
}
static int play(struct input_dev *dev,void *data,struct ff_effect *effect)
{
 struct f8_aux *a=input_get_drvdata(dev);
 if(a->closing)return -ENODEV;
 atomic_set(&a->requested,!!(effect->u.rumble.strong_magnitude || effect->u.rumble.weak_magnitude));
 schedule_work(&a->motor_work);return 0;
}
static void haptic_close(struct input_dev *dev)
{
 struct f8_aux *a=input_get_drvdata(dev);
 atomic_set(&a->requested,0);cancel_work_sync(&a->motor_work);cancel_delayed_work_sync(&a->off_work);
 mutex_lock(&a->motor_lock);gpiod_set_value_cansleep(a->motor,0);mutex_unlock(&a->motor_lock);
}
static ssize_t hall_raw_show(struct device *dev,struct device_attribute *attr,char *buf)
{
 struct f8_aux *a=dev_get_drvdata(dev);int v=gpiod_get_value_cansleep(a->hall);
 return v<0?v:sysfs_emit(buf,"%d\n",v);
}
static ssize_t motor_active_show(struct device *dev,struct device_attribute *attr,char *buf)
{
 struct f8_aux *a=dev_get_drvdata(dev);int v=gpiod_get_value_cansleep(a->motor);
 return v<0?v:sysfs_emit(buf,"%d\n",v);
}
static DEVICE_ATTR_RO(hall_raw);
static DEVICE_ATTR_RO(motor_active);
static struct attribute *attrs[]={&dev_attr_hall_raw.attr,&dev_attr_motor_active.attr,NULL};
static const struct attribute_group group={.attrs=attrs};
static int probe(struct platform_device *p)
{
 struct f8_aux *a;struct gpio_chip *chip;int ret;
 a=devm_kzalloc(&p->dev,sizeof(*a),GFP_KERNEL);if(!a)return -ENOMEM;
 mutex_init(&a->motor_lock);atomic_set(&a->requested,0);
 INIT_DELAYED_WORK(&a->hall_work,hall_work);INIT_DELAYED_WORK(&a->off_work,off_work);INIT_WORK(&a->motor_work,motor_work);
 a->hall=devm_gpiod_get(&p->dev,"hall",GPIOD_IN);if(IS_ERR(a->hall))return PTR_ERR(a->hall);
 chip=gpiod_to_chip(a->hall);
 if(!chip || !chip->parent || strcmp(dev_name(chip->parent),"fd8a0000.gpio"))return -ENODEV;
 ret=pinctrl_gpio_set_config(desc_to_gpio(a->hall),PIN_CONF_PACKED(PIN_CONFIG_BIAS_PULL_UP,1));if(ret)return ret;
 a->motor=devm_gpiod_get(&p->dev,"motor",GPIOD_OUT_LOW);if(IS_ERR(a->motor))return PTR_ERR(a->motor);
 chip=gpiod_to_chip(a->motor);
 if(!chip || !chip->parent || strcmp(dev_name(chip->parent),"fec40000.gpio"))return -ENODEV;
 a->cover=devm_input_allocate_device(&p->dev);a->haptic=devm_input_allocate_device(&p->dev);
 if(!a->cover || !a->haptic)return -ENOMEM;
 a->cover->name="F8 Hall Cover";a->cover->phys="f8/hall0";a->cover->id.bustype=BUS_HOST;
 input_set_capability(a->cover,EV_SW,SW_MACHINE_COVER);
 a->haptic->name="F8 Haptic Motor";a->haptic->phys="f8/haptic0";a->haptic->id.bustype=BUS_HOST;
 a->haptic->close=haptic_close;input_set_drvdata(a->haptic,a);input_set_capability(a->haptic,EV_FF,FF_RUMBLE);
 ret=input_ff_create_memless(a->haptic,NULL,play);if(ret)return ret;
 ret=input_register_device(a->cover);if(ret)return ret;
 ret=input_register_device(a->haptic);if(ret)return ret;
 platform_set_drvdata(p,a);a->irq=gpiod_to_irq(a->hall);if(a->irq<0)return a->irq;
 ret=devm_request_irq(&p->dev,a->irq,hall_irq,IRQF_TRIGGER_RISING|IRQF_TRIGGER_FALLING,"f8-hall",a);if(ret)return ret;
 ret=devm_device_add_group(&p->dev,&group);if(ret){disable_irq(a->irq);cancel_delayed_work_sync(&a->hall_work);return ret;}
 hall_work(&a->hall_work.work);probe_result=0;
 dev_info(&p->dev,"Hall GPIO0_D3 and motor GPIO3_C2 ready; motor watchdog 200ms\n");return 0;
}
static int remove_device(struct platform_device *p)
{
 struct f8_aux *a=platform_get_drvdata(p);
 a->closing=true;disable_irq(a->irq);cancel_delayed_work_sync(&a->hall_work);haptic_close(a->haptic);return 0;
}
static void shutdown_device(struct platform_device *p){remove_device(p);}
static int probe_record_result(struct platform_device *p){probe_result=probe(p);return probe_result;}
static int suspend_device(struct device *dev)
{
 struct f8_aux *a=dev_get_drvdata(dev);haptic_close(a->haptic);return 0;
}
static SIMPLE_DEV_PM_OPS(pm_ops,suspend_device,NULL);
static struct platform_driver driver={.probe=probe_record_result,.remove=remove_device,.shutdown=shutdown_device,.driver={.name="f8-cover-haptic",.pm=&pm_ops}};
static int __init init_board(void)
{
 const char *model;int ret;
 if(of_property_read_string(of_root,"model",&model) || strncmp(model,"F8-PRO",6))return -ENODEV;
 ret=platform_driver_register(&driver);if(ret)return ret;
 gpiod_add_lookup_table(&lookup);board=platform_device_register_simple("f8-cover-haptic",PLATFORM_DEVID_NONE,NULL,0);
 if(IS_ERR(board)){ret=PTR_ERR(board);goto fail;}
 if(probe_result){ret=probe_result;platform_device_unregister(board);goto fail;}
 return 0;
fail:gpiod_remove_lookup_table(&lookup);platform_driver_unregister(&driver);return ret;
}
static void __exit exit_board(void)
{platform_device_unregister(board);gpiod_remove_lookup_table(&lookup);platform_driver_unregister(&driver);}
module_init(init_board);module_exit(exit_board);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("F8-PRO Hall cover and bounded GPIO force feedback");
