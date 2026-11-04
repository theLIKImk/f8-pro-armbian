// SPDX-License-Identifier: GPL-2.0-only
/* Passive fixed-client status. No writes, ADC strobes or fault-latch reads. */
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/of.h>
#include <linux/sysfs.h>

static struct device *target;
static struct module *control_owner;
static ssize_t status_show(struct device *dev, struct device_attribute *attr, char *buf)
{
	static const u8 registers[] = {0x00, 0x02, 0x03, 0x07, 0x0a, 0x0b, 0x11, 0x14};
	struct i2c_client *client = to_i2c_client(dev);
	int values[ARRAY_SIZE(registers)], i, ret;
	device_lock(dev);
	if (!dev->driver || strcmp(dev->driver->name, "f8-otg-vbus")) {
		device_unlock(dev);
		return -ENODEV;
	}
	for (i = 0; i < ARRAY_SIZE(registers); i++) {
		values[i] = i2c_smbus_read_byte_data(client, registers[i]);
		if (values[i] < 0) {
			ret = values[i];
			device_unlock(dev);
			return ret;
		}
	}
	device_unlock(dev);
	return sysfs_emit(buf, "reg00=%02x reg02=%02x reg03=%02x reg07=%02x reg0a=%02x reg0b=%02x reg11_cached=%02x reg14=%02x\n",
			  values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7]);
}
static DEVICE_ATTR_RO(status);
static struct attribute *status_attrs[] = { &dev_attr_status.attr, NULL };
static const struct attribute_group status_group = { .name = "f8_usb_status", .attrs = status_attrs };
static int __init f8_status_init(void)
{
	struct i2c_client *client;
	int ret = -ENODEV;
	target = bus_find_device_by_name(&i2c_bus_type, NULL, "6-006a");
	if (!target)
		return -ENODEV;
	device_lock(target);
	client = to_i2c_client(target);
	if (client->addr != 0x6a || client->adapter->nr != 6 ||
	    !of_device_is_compatible(target->of_node, "f8-pro,otg-vbus-only") ||
	    !target->driver || strcmp(target->driver->name, "f8-otg-vbus"))
		goto unlock;
	control_owner = target->driver->owner;
	if (!try_module_get(control_owner))
		goto unlock;
	ret = sysfs_create_group(&target->kobj, &status_group);
	if (ret)
		module_put(control_owner);
unlock:
	device_unlock(target);
	if (ret) {
		put_device(target);
		target = NULL;
	}
	return ret;
}
static void __exit f8_status_exit(void)
{
	sysfs_remove_group(&target->kobj, &status_group);
	module_put(control_owner);
	put_device(target);
}
module_init(f8_status_init);
module_exit(f8_status_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Passive F8 OTG register status; no charger control");
