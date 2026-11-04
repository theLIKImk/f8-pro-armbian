// SPDX-License-Identifier: GPL-2.0
/* F8 EM30918: raw ambient intensity and PS ADC. No invented lux/cm mapping. */
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/mutex.h>
#include <linux/iio/iio.h>
#include <linux/iio/sysfs.h>
#include <linux/pm.h>
struct em { struct i2c_client *client; struct mutex lock; u8 saved; };
#define F8_MODE 0x86 /* PS 15mA / 100ms, ALS enabled, normal range/mode. */
static int em_read(struct iio_dev *indio, const struct iio_chan_spec *ch,
                   int *val, int *val2, long mask)
{
 struct em *s=iio_priv(indio);int lo,hi;
 if(mask!=IIO_CHAN_INFO_RAW)return -EINVAL;
 mutex_lock(&s->lock);
 lo=i2c_smbus_read_byte_data(s->client,9);hi=i2c_smbus_read_byte_data(s->client,10);
 mutex_unlock(&s->lock);
 if(lo<0)return lo;if(hi<0)return hi;
 *val=lo|((hi&15)<<8);return IIO_VAL_INT;
}
static ssize_t proximity_raw_show(struct device *dev,struct device_attribute *attr,char *buf)
{
 struct em *s=iio_priv(dev_to_iio_dev(dev));int v;
 mutex_lock(&s->lock);v=i2c_smbus_read_byte_data(s->client,8);mutex_unlock(&s->lock);
 return v<0?v:sysfs_emit(buf,"%d\n",v);
}
static IIO_DEVICE_ATTR_RO(proximity_raw,0);
static struct attribute *em_attrs[]={&iio_dev_attr_proximity_raw.dev_attr.attr,NULL};
static const struct attribute_group em_group={.attrs=em_attrs};
static const struct iio_info em_info={.read_raw=em_read,.attrs=&em_group};
static const struct iio_chan_spec em_channels[]={{.type=IIO_INTENSITY,.info_mask_separate=BIT(IIO_CHAN_INFO_RAW)}};
static int em_probe(struct i2c_client *client)
{
 struct iio_dev *indio;struct em *s;int id,ret,old;
 id=i2c_smbus_read_byte_data(client,0);if(id<0)return id;
 if(id!=0x31)return -ENODEV;
 old=i2c_smbus_read_byte_data(client,1);if(old<0)return old;
 indio=devm_iio_device_alloc(&client->dev,sizeof(*s));if(!indio)return -ENOMEM;
 s=iio_priv(indio);s->client=client;s->saved=old;mutex_init(&s->lock);
 i2c_set_clientdata(client,indio);indio->name="f8-em30918";
 indio->modes=INDIO_DIRECT_MODE;indio->info=&em_info;
 indio->channels=em_channels;indio->num_channels=ARRAY_SIZE(em_channels);
 ret=i2c_smbus_write_byte_data(client,1,F8_MODE);if(ret<0)return ret;
 ret=i2c_smbus_read_byte_data(client,1);
 if(ret!=F8_MODE){i2c_smbus_write_byte_data(client,1,s->saved);return ret<0?ret:-EIO;}
 ret=devm_iio_device_register(&client->dev,indio);
 if(ret)i2c_smbus_write_byte_data(client,1,s->saved);
 return ret;
}
static void em_remove(struct i2c_client *client)
{
 struct em *s=iio_priv(i2c_get_clientdata(client));
 mutex_lock(&s->lock);i2c_smbus_write_byte_data(client,1,s->saved);mutex_unlock(&s->lock);
}
static int em_suspend(struct device *dev)
{
 struct em *s=iio_priv(i2c_get_clientdata(to_i2c_client(dev)));int r;
 mutex_lock(&s->lock);r=i2c_smbus_write_byte_data(s->client,1,0);mutex_unlock(&s->lock);return r;
}
static int em_resume(struct device *dev)
{
 struct em *s=iio_priv(i2c_get_clientdata(to_i2c_client(dev)));int r;
 mutex_lock(&s->lock);r=i2c_smbus_write_byte_data(s->client,1,F8_MODE);mutex_unlock(&s->lock);return r;
}
static SIMPLE_DEV_PM_OPS(em_pm,em_suspend,em_resume);
static const struct i2c_device_id em_ids[]={{"f8-em30918",0},{}};
MODULE_DEVICE_TABLE(i2c,em_ids);
static struct i2c_driver em_driver={.driver={.name="f8-em30918",.pm=&em_pm},.probe_new=em_probe,.remove=em_remove,.id_table=em_ids};
module_i2c_driver(em_driver);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("F8 identified EM30918 raw ALS and low-current proximity ADC");
