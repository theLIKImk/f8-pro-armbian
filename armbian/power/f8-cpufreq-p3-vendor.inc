/* GPL-2.0: RK3588 callbacks from Armbian/Rockchip rockchip-cpufreq.c.
 * Copyright (c) 2016 Fuzhou Rockchip Electronics Co., Ltd.
 * Local reference: linux-rockchip-config, not a replacement kernel Image.
 */
static int rk3588_get_soc_info(struct device *dev, struct device_node *np,
			       int *bin, int *process)
{
	int ret = 0;
	u8 value = 0;

	if (!bin)
		return 0;

	if (of_property_match_string(np, "nvmem-cell-names",
				     "specification_serial_number") >= 0) {
		ret = rockchip_nvmem_cell_read_u8(np,
						  "specification_serial_number",
						  &value);
		if (ret) {
			dev_err(dev,
				"Failed to get specification_serial_number\n");
			return ret;
		}
		/* RK3588M */
		if (value == 0xd)
			*bin = 1;
		/* RK3588J */
		else if (value == 0xa)
			*bin = 2;
	}
	if (of_property_match_string(np, "nvmem-cell-names", "customer_demand") >= 0) {
		ret = rockchip_nvmem_cell_read_u8(np, "customer_demand", &value);
		if (ret) {
			dev_err(dev, "Failed to get customer_demand\n");
			return ret;
		}
		if (value == 0x3)
			*bin = 4;
	}
	if (*bin < 0)
		*bin = 0;
	dev_info(dev, "bin=%d\n", *bin);

	return ret;
}

static int rk3588_change_length(struct device *dev, struct device_node *np,
				struct rockchip_opp_info *opp_info)
{
	struct clk *clk;
	unsigned long old_rate;
	unsigned int low_len_sel;
	u32 opp_flag = 0;
	int ret = 0;

	if (opp_info->volt_sel < 0)
		return 0;

	clk = clk_get(dev, NULL);
	if (IS_ERR(clk)) {
		dev_warn(dev, "failed to get cpu clk\n");
		return PTR_ERR(clk);
	}

	/* RK3588 low speed grade should change to low length */
	if (of_property_read_u32(np, "rockchip,pvtm-low-len-sel",
				 &low_len_sel))
		goto out;
	if (opp_info->volt_sel > low_len_sel)
		goto out;
	opp_flag = OPP_LENGTH_LOW;

	old_rate = clk_get_rate(clk);
	ret = clk_set_rate(clk, old_rate | opp_flag);
	if (ret) {
		dev_err(dev, "failed to change length\n");
		goto out;
	}
	clk_set_rate(clk, old_rate);
out:
	clk_put(clk);

	return ret;
}

static int rk3588_set_supported_hw(struct device *dev, struct device_node *np,
				   struct rockchip_opp_info *opp_info)
{
	int bin = opp_info->bin;

	if (!of_property_read_bool(np, "rockchip,supported-hw"))
		return 0;

	if (bin < 0)
		bin = 0;

	/* SoC Version */
	opp_info->supported_hw[0] = BIT(bin);
	/* Speed Grade */
	opp_info->supported_hw[1] = BIT(opp_info->volt_sel);

	return 0;
}

static int rk3588_set_soc_info(struct device *dev, struct device_node *np,
			       struct rockchip_opp_info *opp_info)
{
	rk3588_change_length(dev, np, opp_info);
	rk3588_set_supported_hw(dev, np, opp_info);

	return 0;
}

static int rk3588_cpu_set_read_margin(struct device *dev,
				      struct rockchip_opp_info *opp_info,
				      u32 rm)
{
	if (!opp_info->volt_rm_tbl)
		return 0;
	if (rm == opp_info->current_rm || rm  == UINT_MAX)
		return 0;

	dev_dbg(dev, "set rm to %d\n", rm);
	if (opp_info->grf) {
		regmap_write(opp_info->grf, 0x20, 0x001c0000 | (rm << 2));
		regmap_write(opp_info->grf, 0x28, 0x003c0000 | (rm << 2));
		regmap_write(opp_info->grf, 0x2c, 0x003c0000 | (rm << 2));
		regmap_write(opp_info->grf, 0x30, 0x00200020);
		udelay(1);
		regmap_write(opp_info->grf, 0x30, 0x00200000);
	}
	if (opp_info->dsu_grf) {
		regmap_write(opp_info->dsu_grf, 0x20, 0x001c0000 | (rm << 2));
		regmap_write(opp_info->dsu_grf, 0x28, 0x003c0000 | (rm << 2));
		regmap_write(opp_info->dsu_grf, 0x2c, 0x003c0000 | (rm << 2));
		regmap_write(opp_info->dsu_grf, 0x30, 0x001c0000 | (rm << 2));
		regmap_write(opp_info->dsu_grf, 0x38, 0x001c0000 | (rm << 2));
		regmap_write(opp_info->dsu_grf, 0x18, 0x40004000);
		udelay(1);
		regmap_write(opp_info->dsu_grf, 0x18, 0x40000000);
	}

	opp_info->current_rm = rm;

	return 0;
}

