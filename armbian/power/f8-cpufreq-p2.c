// SPDX-License-Identifier: GPL-2.0-only
/* F8 P2 bring-up only: SCMI clocks, fixed existing voltage, 816..1200 MHz.
 * No PMIC writes, OPP/PVTM calibration, register pokes or automatic loading.
 * This deliberately does not implement the final full-speed RK3588 DVFS path.
 */
#include <linux/module.h>
#include <linux/clk.h>
#include <linux/cpu.h>
#include <linux/cpufreq.h>
#include <linux/of.h>
#include <linux/regulator/consumer.h>
#include <linux/slab.h>
#include <linux/thermal.h>

struct f8_cluster {
	struct regulator *supply;
	unsigned int minimum_uv;
};
static struct thermal_zone_device *soc_temp;
static struct cpufreq_frequency_table f8_rates[] = {
	{ .frequency = 816000 },
	{ .frequency = 1008000 },
	{ .frequency = 1200000 },
	{ .frequency = CPUFREQ_TABLE_END },
};

static int f8_target(struct cpufreq_policy *p, unsigned int index)
{
	struct f8_cluster *c = p->driver_data;
	unsigned long rate;
	int temp, uv, ret;
	if (index >= ARRAY_SIZE(f8_rates) - 1)
		return -EINVAL;
	rate = (unsigned long)f8_rates[index].frequency * 1000;
	if (rate > 816000000) {
		uv = regulator_get_voltage(c->supply);
		if (uv < c->minimum_uv)
			return -ERANGE;
		ret = thermal_zone_get_temp(soc_temp, &temp);
		/* Fail closed for missing sensors or outside this trial's range. */
		if (ret || temp < 15000 || temp >= 70000)
			return ret ? ret : -EBUSY;
	}
	return clk_set_rate(p->clk, rate);
}

static int f8_init_policy(struct cpufreq_policy *p)
{
	struct device *dev = get_cpu_device(p->cpu);
	struct f8_cluster *c;
	unsigned int first, last, i;
	unsigned long rate;
	int ret;
	if (!dev || p->cpu >= 8)
		return -ENODEV;
	first = p->cpu < 4 ? 0 : (p->cpu < 6 ? 4 : 6);
	last = first == 0 ? 3 : first + 1;
	c = kzalloc(sizeof(*c), GFP_KERNEL);
	if (!c)
		return -ENOMEM;
	c->minimum_uv = first == 0 ? 750000 : 800000;
	c->supply = regulator_get(dev, "cpu");
	if (IS_ERR(c->supply)) {
		ret = PTR_ERR(c->supply);
		goto free;
	}
	if (regulator_get_voltage(c->supply) < c->minimum_uv) {
		ret = -ERANGE;
		goto supply;
	}
	p->clk = clk_get(dev, NULL);
	if (IS_ERR(p->clk)) {
		ret = PTR_ERR(p->clk);
		goto supply;
	}
	rate = clk_get_rate(p->clk);
	/* Require the known boot state; never force an unknown initial clock. */
	if (rate != 816000000) {
		ret = -EINVAL;
		goto clock;
	}
	cpumask_clear(p->cpus);
	for (i = first; i <= last; ++i)
		cpumask_set_cpu(i, p->cpus);
	p->driver_data = c;
	p->freq_table = f8_rates;
	p->cpuinfo.transition_latency = 40000;
	p->suspend_freq = 816000;
	p->dvfs_possible_from_any_cpu = true;
	return 0;
clock:
	clk_put(p->clk);
supply:
	regulator_put(c->supply);
free:
	kfree(c);
	return ret;
}

static int f8_exit_policy(struct cpufreq_policy *p)
{
	struct f8_cluster *c = p->driver_data;
	int ret = clk_set_rate(p->clk, 816000000);
	if (ret)
		pr_err("f8-cpufreq-p2: could not restore cpu%u to 816MHz: %d\n", p->cpu, ret);
	clk_put(p->clk);
	regulator_put(c->supply);
	kfree(c);
	return 0;
}

static struct cpufreq_driver f8_driver = {
	.name = "f8-p2-fixedvolt",
	.flags = CPUFREQ_IS_COOLING_DEV | CPUFREQ_HAVE_GOVERNOR_PER_POLICY,
	.verify = cpufreq_generic_frequency_table_verify,
	.target_index = f8_target,
	.get = cpufreq_generic_get,
	.init = f8_init_policy,
	.exit = f8_exit_policy,
	.suspend = cpufreq_generic_suspend,
	.attr = cpufreq_generic_attr,
};

static int __init f8_start(void)
{
	struct device_node *chosen;
	struct of_phandle_args args;
	const char *trial;
	unsigned int i;
	int ret;
	if (!of_machine_is_compatible("rockchip,rk3588s-tablet-f12-v11") ||
	    num_possible_cpus() != 8)
		return -ENODEV;
	chosen = of_find_node_by_path("/chosen");
	if (!chosen)
		return -ENODEV;
	ret = of_property_read_string(chosen, "f8-cpu-trial", &trial);
	if (!ret && strcmp(trial, "p2-fixedvolt-1200mhz"))
		ret = -ENODEV;
	of_node_put(chosen);
	if (ret)
		return ret;
	for (i = 0; i < 8; ++i) {
		struct device *cpu = get_cpu_device(i);
		struct device_node *parent;
		u32 protocol;
		if (!cpu)
			return -ENODEV;
		ret = of_parse_phandle_with_args(cpu->of_node, "clocks", "#clock-cells", 0, &args);
		if (ret)
			return ret;
		parent = of_get_parent(args.np);
		ret = args.args_count == 1 &&
		      args.args[0] == (i < 4 ? 0 : (i < 6 ? 2 : 3)) &&
		      !of_property_read_u32(args.np, "reg", &protocol) && protocol == 0x14 &&
		      parent && of_device_is_compatible(parent, "arm,scmi-smc") ? 0 : -EINVAL;
		of_node_put(parent);
		of_node_put(args.np);
		if (ret)
			return ret;
	}
	soc_temp = thermal_zone_get_zone_by_name("soc-thermal");
	if (IS_ERR(soc_temp))
		return PTR_ERR(soc_temp);
	ret = cpufreq_register_driver(&f8_driver);
	if (!ret)
		pr_info("f8-cpufreq-p2: manual fixed-voltage 816/1008/1200MHz trial registered\n");
	return ret;
}
static void __exit f8_stop(void)
{
	cpufreq_unregister_driver(&f8_driver);
}
module_init(f8_start);
module_exit(f8_stop);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("F8 P2 manual limited CPU frequency trial; not full vendor DVFS");
