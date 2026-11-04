// SPDX-License-Identifier: GPL-2.0-only
/* F8 board OTG regulator only. Never reset or initialize the charger. */
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/gpio/consumer.h>
#include <linux/mutex.h>
#include <linux/regulator/driver.h>
#include <linux/regulator/of_regulator.h>

#define OTG_REG 0x03
#define OTG_BIT BIT(5)
struct f8_otg {
	struct i2c_client *client;
	struct gpio_desc *gate;
	struct mutex lock;
};

/* Call with lock held. Preserve every bit except OTG_CONFIG. */
static int f8_switch(struct f8_otg *p, bool on)
{
	int old, ret, status, voltage;

	if (!on)
		gpiod_set_value_cansleep(p->gate, 0);
	old = i2c_smbus_read_byte_data(p->client, OTG_REG);
	if (old < 0)
		return old;
	/* Do not echo the self-clearing watchdog-reset strobe back to the chip. */
	if (old & BIT(6))
		return -EBUSY;
	if (on) {
		status = i2c_smbus_read_byte_data(p->client, 0x0b);
		if (status < 0)
			return status;
		/* Never enable against a detected incoming source. */
		if (((status >> 5) & 7) != 0 && ((status >> 5) & 7) != 7)
			return -EBUSY;
		if ((status & BIT(2)) && !(old & OTG_BIT))
			return -EBUSY;
		voltage = i2c_smbus_read_byte_data(p->client, 0x0a);
		if (voltage < 0)
			return voltage;
		/* Existing boost setting must already be nominal 5V (4.87-5.19V). */
		if ((voltage >> 4) < 5 || (voltage >> 4) > 10)
			return -ERANGE;
	}
	ret = i2c_smbus_write_byte_data(p->client, OTG_REG,
				      on ? old | OTG_BIT : old & ~OTG_BIT);
	if (ret < 0)
		return ret;
	ret = i2c_smbus_read_byte_data(p->client, OTG_REG);
	if (ret < 0 || ret != (on ? old | OTG_BIT : old & ~OTG_BIT)) {
		/* On failure, leave the board gate low and try to clear OTG only. */
		gpiod_set_value_cansleep(p->gate, 0);
		if (on) {
			int now = i2c_smbus_read_byte_data(p->client, OTG_REG);
			if (now >= 0)
				i2c_smbus_write_byte_data(p->client, OTG_REG, now & ~OTG_BIT);
		}
		return ret < 0 ? ret : -EIO;
	}
	if (on)
		gpiod_set_value_cansleep(p->gate, 1);
	return 0;
}

static int f8_enable(struct regulator_dev *rdev)
{
	struct f8_otg *p = rdev_get_drvdata(rdev);
	int ret;
	mutex_lock(&p->lock);
	ret = f8_switch(p, true);
	mutex_unlock(&p->lock);
	return ret;
}
static int f8_disable(struct regulator_dev *rdev)
{
	struct f8_otg *p = rdev_get_drvdata(rdev);
	int ret;
	mutex_lock(&p->lock);
	ret = f8_switch(p, false);
	mutex_unlock(&p->lock);
	return ret;
}
static int f8_enabled(struct regulator_dev *rdev)
{
	struct f8_otg *p = rdev_get_drvdata(rdev);
	int ret;
	mutex_lock(&p->lock);
	ret = i2c_smbus_read_byte_data(p->client, OTG_REG);
	if (ret >= 0) {
		int gate = gpiod_get_value_cansleep(p->gate);
		ret = gate < 0 ? gate : !!(ret & OTG_BIT) && gate;
	}
	mutex_unlock(&p->lock);
	return ret;
}
static const struct regulator_ops f8_ops = {
	.enable = f8_enable, .disable = f8_disable, .is_enabled = f8_enabled,
};
static const struct regulator_desc f8_desc = {
	.name = "f8_usb_otg_vbus", .of_match = "usb-otg-vbus",
	.regulators_node = "regulators", .type = REGULATOR_VOLTAGE,
	.owner = THIS_MODULE, .ops = &f8_ops,
	.fixed_uV = 5000000, .n_voltages = 1, .enable_time = 20000,
};
static int f8_probe(struct i2c_client *client, const struct i2c_device_id *id)
{
	struct regulator_config cfg = {};
	struct regulator_dev *rdev;
	struct f8_otg *p;
	int ret;
	if (!i2c_check_functionality(client->adapter, I2C_FUNC_SMBUS_BYTE_DATA))
		return -EOPNOTSUPP;
	if (client->addr != 0x6a)
		return -ENODEV;
	ret = i2c_smbus_read_byte_data(client, 0x14);
	if (ret < 0)
		return ret;
	if (((ret >> 3) & 7) != 3)
		return -ENODEV;
	ret = i2c_smbus_read_byte_data(client, OTG_REG);
	if (ret < 0)
		return ret;
	if (ret & OTG_BIT)
		return -EBUSY;
	ret = i2c_smbus_read_byte_data(client, 0x07);
	if (ret < 0)
		return ret;
	/* This board baseline has watchdog disabled; do not reprogram it. */
	if (ret & GENMASK(5, 4))
		return -EBUSY;
	p = devm_kzalloc(&client->dev, sizeof(*p), GFP_KERNEL);
	if (!p)
		return -ENOMEM;
	p->client = client;
	mutex_init(&p->lock);
	p->gate = devm_gpiod_get(&client->dev, "otg-mode-en", GPIOD_OUT_LOW);
	if (IS_ERR(p->gate))
		return PTR_ERR(p->gate);
	i2c_set_clientdata(client, p);
	cfg.dev = &client->dev;
	cfg.driver_data = p;
	cfg.of_node = client->dev.of_node;
	rdev = devm_regulator_register(&client->dev, &f8_desc, &cfg);
	if (IS_ERR(rdev))
		return PTR_ERR(rdev);
	dev_info(&client->dev, "OTG-only regulator ready; charger settings preserved\n");
	return 0;
}
static void f8_shutdown(struct i2c_client *client)
{
	struct f8_otg *p = i2c_get_clientdata(client);
	int ret;
	mutex_lock(&p->lock);
	ret = f8_switch(p, false);
	mutex_unlock(&p->lock);
	if (ret)
		dev_err(&client->dev, "OTG disable failed: %d\n", ret);
}
static const struct of_device_id f8_match[] = {
	{ .compatible = "f8-pro,otg-vbus-only" }, {}
};
MODULE_DEVICE_TABLE(of, f8_match);
static struct i2c_driver f8_driver = {
	.driver = { .name = "f8-otg-vbus", .of_match_table = f8_match },
	.probe = f8_probe, .remove = f8_shutdown, .shutdown = f8_shutdown,
};
module_i2c_driver(f8_driver);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("F8 Type-C 5V OTG regulator, no charger initialization");
