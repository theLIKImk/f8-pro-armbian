// SPDX-License-Identifier: GPL-2.0
/* Real buffered IIO relay of measured F8 IMU samples; no hardware writes. */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/miscdevice.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/ktime.h>
#include <linux/iio/iio.h>
#include <linux/iio/buffer.h>
#include <linux/iio/kfifo_buf.h>
struct feed { __s32 value[9]; __u32 magnetic_valid; }; /* micro m/s2, micro rad/s; native endian */
struct state { struct mutex lock; struct feed latest; s64 stamp; bool writer; };
static struct iio_dev *relay;
static struct platform_device *pdev;
static int read_sample(struct iio_dev *d,const struct iio_chan_spec *c,int *v,int *v2,long mask)
{
 struct state *s=iio_priv(d);int r=IIO_VAL_INT;
 if(mask==IIO_CHAN_INFO_SCALE){*v=0;if(c->type==IIO_MAGN){*v2=10;return IIO_VAL_INT_PLUS_NANO;}*v2=1;return IIO_VAL_INT_PLUS_MICRO;}
 if(mask==IIO_CHAN_INFO_SAMP_FREQ){*v=20;return IIO_VAL_INT;}
 if(mask!=IIO_CHAN_INFO_RAW)return -EINVAL;
 mutex_lock(&s->lock);
 if(!s->stamp || ktime_get_ns()-s->stamp>1500000000LL || (c->type==IIO_MAGN && !s->latest.magnetic_valid))r=-EAGAIN;
 else *v=s->latest.value[c->scan_index];
 mutex_unlock(&s->lock);return r;
}
static const struct iio_info info={.read_raw=read_sample};
#define CH(t,a,i) { .type=t,.modified=1,.channel2=a,.info_mask_separate=BIT(IIO_CHAN_INFO_RAW),.info_mask_shared_by_type=BIT(IIO_CHAN_INFO_SCALE)|BIT(IIO_CHAN_INFO_SAMP_FREQ),.scan_index=i,.scan_type={.sign='s',.realbits=32,.storagebits=32,.endianness=IIO_CPU} }
static const struct iio_chan_spec channels[]={CH(IIO_ACCEL,IIO_MOD_X,0),CH(IIO_ACCEL,IIO_MOD_Y,1),CH(IIO_ACCEL,IIO_MOD_Z,2),CH(IIO_ANGL_VEL,IIO_MOD_X,3),CH(IIO_ANGL_VEL,IIO_MOD_Y,4),CH(IIO_ANGL_VEL,IIO_MOD_Z,5),CH(IIO_MAGN,IIO_MOD_X,6),CH(IIO_MAGN,IIO_MOD_Y,7),CH(IIO_MAGN,IIO_MOD_Z,8),IIO_CHAN_SOFT_TIMESTAMP(9)};
static const unsigned long masks[]={0x1ff,0};
static ssize_t write_feed(struct file *f,const char __user *buf,size_t n,loff_t *off)
{
 struct feed input;struct state *s=iio_priv(relay);struct { __s32 v[9];s64 stamp __aligned(8); } scan={};int i;
 if(n!=sizeof(input))return -EINVAL;
 if(copy_from_user(&input,buf,n))return -EFAULT;
 for(i=0;i<9;i++)if(input.value[i]>200000000 || input.value[i]<-200000000)return -ERANGE;
 mutex_lock(&s->lock);s->latest=input;s->stamp=ktime_get_ns();memcpy(scan.v,input.value,sizeof(scan.v));scan.stamp=s->stamp;
 if(input.magnetic_valid && iio_buffer_enabled(relay))iio_push_to_buffers(relay,&scan);
 mutex_unlock(&s->lock);return n;
}
static int open_feed(struct inode *inode,struct file *file)
{
 struct state *s=iio_priv(relay);int r=0;mutex_lock(&s->lock);
 if(s->writer)r=-EBUSY;else s->writer=true;
 mutex_unlock(&s->lock);return r;
}
static int close_feed(struct inode *inode,struct file *file)
{
 struct state *s=iio_priv(relay);mutex_lock(&s->lock);s->writer=false;s->stamp=0;mutex_unlock(&s->lock);return 0;
}
static const struct file_operations feed_ops={.owner=THIS_MODULE,.open=open_feed,.release=close_feed,.write=write_feed,.llseek=no_llseek};
static struct miscdevice feeddev={.minor=MISC_DYNAMIC_MINOR,.name="f8-sensor-feed",.fops=&feed_ops,.mode=0600};
static int __init start(void)
{
 struct state *s;int r;
 pdev=platform_device_register_simple("f8-sensor-relay",-1,NULL,0);if(IS_ERR(pdev))return PTR_ERR(pdev);
 relay=devm_iio_device_alloc(&pdev->dev,sizeof(*s));if(!relay){r=-ENOMEM;goto fail;}
 s=iio_priv(relay);mutex_init(&s->lock);relay->name="f8-sensor-relay";relay->info=&info;relay->modes=INDIO_DIRECT_MODE|INDIO_BUFFER_SOFTWARE;relay->channels=channels;relay->num_channels=ARRAY_SIZE(channels);relay->available_scan_masks=masks;
 r=devm_iio_kfifo_buffer_setup(&pdev->dev,relay,NULL);if(r)goto fail;
 r=devm_iio_device_register(&pdev->dev,relay);if(r)goto fail;
 r=misc_register(&feeddev);if(r)goto fail;
 return 0;
fail:platform_device_unregister(pdev);return r;
}
static void __exit stop(void){misc_deregister(&feeddev);platform_device_unregister(pdev);}
module_init(start);module_exit(stop);MODULE_LICENSE("GPL");MODULE_DESCRIPTION("Measured F8 IMU userspace to buffered IIO compatibility relay");
