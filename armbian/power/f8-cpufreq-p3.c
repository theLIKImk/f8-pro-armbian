// SPDX-License-Identifier: GPL-2.0
/* F8 deferred RK3588 DVFS bring-up. Calls the running kernel's Rockchip OPP
 * implementation with per-cluster callbacks rather than the skipped global
 * Rockchip cpufreq initializer/notifier. No automatic module loading.
 */
#include <linux/module.h>
#include <linux/clk.h>
#include <linux/cpu.h>
#include <linux/cpufreq.h>
#include <linux/delay.h>
#include <linux/of.h>
#include <linux/pm_opp.h>
#include <linux/regmap.h>
#include <linux/regulator/consumer.h>
#include <linux/thermal.h>
#include <soc/rockchip/rockchip_opp_select.h>

static unsigned int max_little_khz = 1200000;
static unsigned int max_big_khz = 1200000;
module_param(max_little_khz, uint, 0444);
module_param(max_big_khz, uint, 0444);
struct f8_full_cluster {
	struct device *dev;
	struct rockchip_opp_info info;
	struct cpufreq_frequency_table *table;
	struct regulator *restore_supply;
	int boot_uv;
	bool table_ready;
};
static struct f8_full_cluster clusters[3];
static struct thermal_zone_device *soc_temp;
static const unsigned int leaders[] = {0, 4, 6};
static unsigned int slot(unsigned int cpu) { return cpu < 4 ? 0 : cpu < 6 ? 1 : 2; }
#include "f8-cpufreq-p3-vendor.inc"

static int f8_config_regulators(struct device *dev, struct dev_pm_opp *old,
		struct dev_pm_opp *new, struct regulator **regs, unsigned int count)
{
	if (dev->id < 0 || dev->id >= 8 || clusters[slot(dev->id)].dev != dev)
		return -EINVAL;
	return rockchip_opp_config_regulators(dev, old, new, regs, count,
					   &clusters[slot(dev->id)].info);
}
static const struct rockchip_opp_data f8_opp_data = {
	.get_soc_info = rk3588_get_soc_info,
	.set_soc_info = rk3588_set_soc_info,
	.set_read_margin = rk3588_cpu_set_read_margin,
	.config_regulators = f8_config_regulators,
};
static int f8_target(struct cpufreq_policy *p, unsigned int index)
{
	struct f8_full_cluster *c = p->driver_data;
	unsigned long rate = (unsigned long)p->freq_table[index].frequency * 1000;
	int ret, temp;
	if (rate > clk_get_rate(c->info.clk)) {
		ret = thermal_zone_get_temp(soc_temp, &temp);
		if (ret || temp < 15000 || temp >= 70000)
			return ret ? ret : -EBUSY;
	}
	rockchip_opp_dvfs_lock(&c->info);
	ret = dev_pm_opp_set_rate(c->dev, rate);
	rockchip_opp_dvfs_unlock(&c->info);
	return ret;
}
static int f8_policy_init(struct cpufreq_policy *p)
{
	unsigned int n = slot(p->cpu), first = leaders[n], last = n ? first + 1 : 3, i;
	struct f8_full_cluster *c = &clusters[n];
	if (!c->table_ready || !c->info.clk)
		return -ENODEV;
	cpumask_clear(p->cpus);
	for (i = first; i <= last; ++i)
		cpumask_set_cpu(i, p->cpus);
	p->driver_data = c;
	p->clk = c->info.clk;
	p->freq_table = c->table;
	p->cpuinfo.transition_latency = 40000;
	p->suspend_freq = 816000;
	p->dvfs_possible_from_any_cpu = true;
	return 0;
}
static int f8_policy_exit(struct cpufreq_policy *p)
{
	struct f8_full_cluster *c = p->driver_data;
	int ret = dev_pm_opp_set_rate(c->dev, 816000000);
	if (ret)
		pr_err("f8-cpufreq-p3: restore cpu%u failed: %d\n",p->cpu,ret);
	return 0;
}
static struct cpufreq_driver f8_driver = {
	.name = "f8-p3-rk-opp",
	.flags = CPUFREQ_IS_COOLING_DEV | CPUFREQ_HAVE_GOVERNOR_PER_POLICY,
	.verify = cpufreq_generic_frequency_table_verify,
	.target_index = f8_target, .get = cpufreq_generic_get,
	.init = f8_policy_init, .exit = f8_policy_exit,
	.suspend = cpufreq_generic_suspend, .attr = cpufreq_generic_attr,
};
static void cleanup(void)
{
	int i;
	for (i = 2; i >= 0; --i) {
		struct f8_full_cluster *c = &clusters[i];
		if (c->table_ready) {
			u32 rm;
			dev_pm_opp_set_rate(c->dev,816000000);
			/* Leave the original boot voltage/margin for the P2 fallback. */
			if (!IS_ERR_OR_NULL(c->restore_supply) && c->boot_uv > 0) {
				int ret = regulator_set_voltage(c->restore_supply,c->boot_uv,c->boot_uv);
				if (!ret && !rockchip_get_read_margin(c->dev,&c->info,c->boot_uv,&rm))
					rockchip_set_read_margin(c->dev,&c->info,rm,true);
			}
			dev_pm_opp_free_cpufreq_table(c->dev,&c->table);
			rockchip_uninit_opp_table(c->dev,&c->info);
			c->table_ready=false;
		}
		if (!IS_ERR_OR_NULL(c->restore_supply)) {
			regulator_put(c->restore_supply);c->restore_supply=NULL;
		}
	}
}
static int __init f8_start(void)
{
	struct device_node *chosen;
	const char *marker;
	int i,ret;
	if (!of_machine_is_compatible("rockchip,rk3588s-tablet-f12-v11") || num_possible_cpus()!=8)
		return -ENODEV;
	chosen=of_find_node_by_path("/chosen");
	if (!chosen)return -ENODEV;
	ret=of_property_read_string(chosen,"f8-cpu-trial",&marker);
	if (!ret && strcmp(marker,"p2-fixedvolt-1200mhz"))ret=-ENODEV;
	of_node_put(chosen);if(ret)return ret;
	if (max_little_khz<1200000 || max_little_khz>1800000 || max_big_khz<1200000 || max_big_khz>2400000)
		return -EINVAL;
	soc_temp=thermal_zone_get_zone_by_name("soc-thermal");
	if (IS_ERR(soc_temp))return PTR_ERR(soc_temp);
	for (i=0;i<3;++i) {
		struct f8_full_cluster *c=&clusters[i];
		unsigned int j, ceiling=i ? max_big_khz : max_little_khz;
		c->dev=get_cpu_device(leaders[i]);if(!c->dev){ret=-ENODEV;goto fail;}
		c->restore_supply=regulator_get(c->dev,"cpu");
		if(IS_ERR(c->restore_supply)){ret=PTR_ERR(c->restore_supply);goto fail;}
		c->boot_uv=regulator_get_voltage(c->restore_supply);
		if(c->boot_uv<=0){ret=-EINVAL;goto fail;}
		c->info.data=&f8_opp_data;
		ret=rockchip_init_opp_table(c->dev,&c->info,NULL,"cpu");
		if(ret)goto fail;
		c->table_ready=true;
		ret=dev_pm_opp_init_cpufreq_table(c->dev,&c->table);
		if(ret)goto fail;
		for(j=0;c->table[j].frequency!=CPUFREQ_TABLE_END;++j)
			if(c->table[j].frequency>ceiling)c->table[j].frequency=CPUFREQ_ENTRY_INVALID;
		pr_info("f8-cpufreq-p3: cpu%u bin=%d grade=%d ceiling=%u\n",leaders[i],c->info.bin,c->info.volt_sel,ceiling);
	}
	ret=cpufreq_register_driver(&f8_driver);if(ret)goto fail;
	return 0;
fail:
	pr_err("f8-cpufreq-p3: init failed: %d\n",ret);cleanup();return ret;
}
static void __exit f8_stop(void){cpufreq_unregister_driver(&f8_driver);cleanup();}
module_init(f8_start);module_exit(f8_stop);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("F8 deferred RK3588 full OPP DVFS trial, manual load only");
