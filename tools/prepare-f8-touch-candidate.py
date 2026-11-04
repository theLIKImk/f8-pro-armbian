"""Generate an isolated, unapplied profile patch against the pinned GSL source."""
import difflib
import hashlib
import json
from pathlib import Path
import struct

P = Path(__file__).resolve().parents[1]
src = P / 'analysis/armbian/source-audit/linux-rockchip/drivers/input/touchscreen/gsl3673.c'
original = src.read_text()
candidate = original
out = P / 'armbian/touch/candidate-r8-shuping'
out.mkdir(parents=True, exist_ok=True)


def replace(old, new, expected=1):
    global candidate
    assert candidate.count(old) == expected, (old[:80], candidate.count(old), expected)
    candidate = candidate.replace(old, new)


replace('#include <linux/of_gpio.h>', '#include <linux/of_gpio.h>\n#include <linux/of_device.h>')
profile = '''
/* Offline F8-PRO candidate. GPIO/IRQ, algorithm ABI and PM need hardware review.
 * The evaluation compatible is deliberately distinct from the vendor DT.
 * Existing gslX680_shuping nodes cannot bind this candidate automatically.
 */
#include "f8-pro-r8-shuping-reference.h"
struct gsl_board_profile {
	const struct fw_data *firmware;
	size_t firmware_count;
	unsigned int *algorithm;
	size_t algorithm_count;
	u16 max_x, max_y;
	u16 reset_delay_ms[3], startup_delay_ms;
	const char *irq_gpio_property, *reset_gpio_property;
	bool evaluation;
};
static const struct gsl_board_profile gsl_generic_profile = {
	.firmware = GSL3673_FW,
	.firmware_count = ARRAY_SIZE(GSL3673_FW),
	.algorithm = gsl_config_data_id_3673,
	.algorithm_count = ARRAY_SIZE(gsl_config_data_id_3673),
	.max_x = SCREEN_MAX_X, .max_y = SCREEN_MAX_Y,
	.reset_delay_ms = {5, 5, 5}, .startup_delay_ms = 5,
	.irq_gpio_property = "irq_gpio_number",
	.reset_gpio_property = "rst_gpio_number",
};
static const struct gsl_board_profile gsl_f8_profile = {
	.firmware = f8_pro_r8_shuping_fw,
	.firmware_count = ARRAY_SIZE(f8_pro_r8_shuping_fw),
	.algorithm = f8_pro_r8_shuping_algorithm,
	.algorithm_count = ARRAY_SIZE(f8_pro_r8_shuping_algorithm),
	.max_x = 800, .max_y = 1280,
	.reset_delay_ms = {20, 10, 10}, .startup_delay_ms = 10,
	.irq_gpio_property = "touch-gpio",
	.reset_gpio_property = "reset-gpio",
	.evaluation = true,
};
'''
replace('struct gsl_ts {', profile + '\nstruct gsl_ts {\n\tconst struct gsl_board_profile *profile;')
replace('of_get_named_gpio_flags(np, "irq_gpio_number", 0,', 'of_get_named_gpio_flags(np, this_ts->profile->irq_gpio_property, 0,')
replace('of_get_named_gpio_flags(np, "rst_gpio_number", 0,', 'of_get_named_gpio_flags(np, this_ts->profile->reset_gpio_property, 0,')
replace('\t\tptr_fw = GSL3673_FW;\n\t\tsource_len = ARRAY_SIZE(GSL3673_FW);', '\t\tptr_fw = this_ts->profile->firmware;\n\t\tsource_len = this_ts->profile->firmware_count;')
# Cover startup AND the legacy proc readers/writers, without replacing the
# generic initializer. The F8 candidate does not expose the proc endpoint.
replace('gsl_DataInit(gsl_config_data_id_3673);', 'gsl_DataInit(this_ts->profile->algorithm);')
replace('if (tmp >= 0 && tmp < ARRAY_SIZE(gsl_config_data_id_3673))', 'if (tmp >= 0 && tmp < this_ts->profile->algorithm_count)')
replace('gsl_config_data_id_3673[tmp]', 'this_ts->profile->algorithm[tmp]')
replace('if (tmp1 >= 0 && tmp1 < ARRAY_SIZE(gsl_config_data_id_3673))', 'if (tmp1 >= 0 && tmp1 < this_ts->profile->algorithm_count)')
replace('gsl_config_data_id_3673[tmp1]', 'this_ts->profile->algorithm[tmp1]')
replace('if (x > SCREEN_MAX_X || y > SCREEN_MAX_Y)', 'if (x > ts->profile->max_x || y > ts->profile->max_y)')
replace('SCREEN_MAX_X - x', 'ts->profile->max_x - x')
replace('SCREEN_MAX_Y - y', 'ts->profile->max_y - y')
replace('\t\t\t\tSCREEN_MAX_X, 0, 0);', '\t\t\t\tts->profile->max_x, 0, 0);')
replace('\t\t\t\tSCREEN_MAX_Y, 0, 0);', '\t\t\t\tts->profile->max_y, 0, 0);')
replace('\tts->tp.tp_resume = gsl_ts_late_resume;', '\tts->profile = of_device_get_match_data(&client->dev);\n\tif (!ts->profile)\n\t\tts->profile = &gsl_generic_profile;\n\tts->tp.tp_resume = gsl_ts_late_resume;')
replace('\tgsl3673_init();', '\trc = gsl3673_init();\n\tif (rc < 0)\n\t\tgoto error_mutex_destroy;')
replace('\tproc_create(GSL_CONFIG_PROC_FILE, 0644, NULL,\n\t\t    (const struct proc_ops *)&gsl_seq_fops);', '\tif (!ts->profile->evaluation)\n\t\tproc_create(GSL_CONFIG_PROC_FILE, 0644, NULL,\n\t\t\t    (const struct proc_ops *)&gsl_seq_fops);')
replace('{.compatible = "GSL,GSL3673"},', '{.compatible = "GSL,GSL3673", .data = &gsl_generic_profile},\n\t{.compatible = "f8-pro,gslx680-shuping-eval", .data = &gsl_f8_profile},')
# Transport errors must reach probe/resume, including short positive transfers.
replace('#include <linux/of_device.h>', '#include <linux/of_device.h>\n#include <asm/unaligned.h>')
replace('static u32 gsl_write_interface(', 'static int gsl_write_interface(')
replace('\treturn i2c_transfer(client->adapter, xfer_msg, 1) == 1 ? 0 : -EFAULT;', '\t{\n\t\tint ret = i2c_transfer(client->adapter, xfer_msg, 1);\n\t\treturn ret == 1 ? 0 : (ret < 0 ? ret : -EIO);\n\t}')
replace('\tret = i2c_master_send(client, tmp_buf, bytelen);\n\treturn ret;', '\tret = i2c_master_send(client, tmp_buf, bytelen);\n\treturn ret == bytelen ? ret : (ret < 0 ? ret : -EIO);')
replace('\treturn i2c_master_recv(client, pdata, datalen);', '\tret = i2c_master_recv(client, pdata, datalen);\n\treturn ret == datalen ? ret : (ret < 0 ? ret : -EIO);')
replace('\tu32 *u32_buf = (int *)buf;\n\t*u32_buf = *fw;', '\tput_unaligned_le32(*fw, buf);')
replace('static void gsl_load_fw(', 'static int gsl_load_fw(')
replace('\tu32 source_len;\n\tstruct fw_data const *ptr_fw;', '\tu32 source_len;\n\tint ret;\n\tstruct fw_data const *ptr_fw;')
replace('\t\t\tgsl_write_interface(client, GSL_PAGE_REG, buf, 4);', '\t\t\tret = gsl_write_interface(client, GSL_PAGE_REG, buf, 4);\n\t\t\tif (ret < 0)\n\t\t\t\treturn ret;')
replace('\t\t\t\t\tgsl_write_interface(client, buf[0], buf, cur - buf - 1);', '\t\t\t\t\tret = gsl_write_interface(client, buf[0], buf, cur - buf - 1);\n\t\t\t\t\tif (ret < 0)\n\t\t\t\t\t\treturn ret;')
replace('\t\t\tsend_flag++;\n\t\t}\n\t}\n}\n\nstatic int test_i2c', '\t\t\tsend_flag++;\n\t\t}\n\t}\n\treturn 0;\n}\n\nstatic int test_i2c')
start = candidate.index('static int test_i2c(')
end = candidate.index('static void startup_chip(', start)
candidate = candidate[:start] + '''static int test_i2c(struct i2c_client *client)
{
	u8 read_buf = 0, write_buf = 0x12;
	int ret;
	ret = gsl_ts_read(client, 0xf0, &read_buf, 1);
	if (ret < 0)
		return ret;
	msleep(2);
	ret = gsl_ts_write(client, 0xf0, &write_buf, 1);
	if (ret < 0)
		return ret;
	msleep(2);
	ret = gsl_ts_read(client, 0xf0, &read_buf, 1);
	return ret < 0 ? ret : 0;
}

''' + candidate[end:]
# Turn each register-sequence operation into a checked step. Keep the original
# register values, order and delays; this is error propagation, not timing proof.
for name, next_name in [('startup_chip', 'reset_chip'), ('reset_chip', 'clr_reg'), ('clr_reg', 'init_chip')]:
    start = candidate.index('static void ' + name + '(')
    end = candidate.index('static ' + ('int' if next_name == 'init_chip' else 'void') + ' ' + next_name + '(', start)
    block = candidate[start:end].replace('static void ', 'static int ', 1)
    block = block.replace('{\n', '{\n\tint ret;\n', 1)
    import re
    block = re.sub(r'^(\t)gsl_ts_write\(([^\n]+)\);$', r'\1ret = gsl_ts_write(\2);\n\1if (ret < 0)\n\1\treturn ret;', block, flags=re.M)
    pos = block.rfind('}')
    block = block[:pos] + '\treturn 0;\n' + block[pos:]
    candidate = candidate[:start] + block + candidate[end:]
replace('static int init_chip(struct i2c_client *client)\n', 'static int gsl_program_chip(struct i2c_client *client);\n\nstatic int init_chip(struct i2c_client *client)\n')
replace('\tstruct gsl_ts *ts = i2c_get_clientdata(client);\n\n\tgsl3673_shutdown_low();', '\tgsl3673_shutdown_low();')
replace('\tschedule_work(&ts->download_fw_work);\n\treturn 0;', '\treturn gsl_program_chip(client);')
replace('\tgsl_ts_read(client, 0xb0, read_buf, sizeof(read_buf));', '\trc = gsl_ts_read(client, 0xb0, read_buf, sizeof(read_buf));\n\tif (rc < 0)\n\t\treturn rc;')
start = candidate.index('static void gsl_download_fw_work(')
end = candidate.index('static int  gsl_ts_probe(', start)
candidate = candidate[:start] + '''static int gsl_program_chip(struct i2c_client *client)
{
	int ret;
	ret = clr_reg(client);
	if (ret < 0)
		return ret;
	ret = reset_chip(client);
	if (ret < 0)
		return ret;
	ret = gsl_load_fw(client);
	if (ret < 0)
		return ret;
	ret = startup_chip(client);
	if (ret < 0)
		return ret;
	ret = reset_chip(client);
	if (ret < 0)
		return ret;
	return startup_chip(client);
}

''' + candidate[end:]
replace('\tstruct work_struct download_fw_work;\n', '')
replace('\tINIT_WORK(&ts->download_fw_work, gsl_download_fw_work);\n', '')
replace('\tcancel_work_sync(&ts->download_fw_work);\n', '', expected=2)
replace('\treset_chip(ts->client);\n\tstartup_chip(ts->client);', '\trc = reset_chip(ts->client);\n\tif (rc < 0)\n\t\treturn rc;\n\trc = startup_chip(ts->client);\n\tif (rc < 0)\n\t\treturn rc;')
# Propagate deferred GPIO providers; do not reinterpret OF GPIO flags as IRQ flags.
replace('\tunsigned long irq_flags;', '\tenum of_gpio_flags irq_flags;\n\tint ret;')
replace('(enum of_gpio_flags *)&irq_flags', '&irq_flags')
replace('\tif (!gpio_is_valid(this_ts->irq)) {', '\tif (this_ts->irq < 0)\n\t\treturn this_ts->irq;\n\tif (!gpio_is_valid(this_ts->irq)) {')
replace('\tif (!gpio_is_valid(this_ts->rst)) {', '\tif (this_ts->rst < 0)\n\t\treturn this_ts->rst;\n\tif (!gpio_is_valid(this_ts->rst)) {')
replace('\tif (devm_gpio_request(&this_ts->client->dev, this_ts->rst, NULL) != 0) {', '\tret = devm_gpio_request(&this_ts->client->dev, this_ts->rst, NULL);\n\tif (ret < 0) {')
replace('\t\treturn -EIO;\n\t}\n\tgpio_direction_output(this_ts->rst, 0);', '\t\treturn ret;\n\t}\n\tret = gpio_direction_output(this_ts->rst, 0);\n\tif (ret < 0)\n\t\treturn ret;')
replace('if (this_ts->rst > 1)', 'if (gpio_is_valid(this_ts->rst))', expected=2)
# No framebuffer callback before client/work/IRQ initialization is complete.
replace('\ttp_register_fb(&ts->tp);\n', '')
replace('\tts->flag_activated = true;\n\n\treturn 0;\nerror_init_chip_fail:', '\tts->flag_activated = true;\n\ttp_register_fb(&ts->tp);\n\n\treturn 0;\nerror_init_chip_fail:')
replace('error_init_chip_fail:\nerror_mutex_destroy:\n\ttp_unregister_fb(&ts->tp);', 'error_init_chip_fail:\n\tcancel_work_sync(&ts->work);\n\tdestroy_workqueue(ts->wq);\nerror_mutex_destroy:')
replace('\tclient->irq = gpio_to_irq(ts->irq);', '\tclient->irq = gpio_to_irq(ts->irq);\n\tif (client->irq < 0) {\n\t\trc = client->irq;\n\t\tgoto error_init_chip_fail;\n\t}')
replace('\t\tdev_err(&client->dev, "gsl_probe: request irq failed\\n");\n\t\treturn rc;', '\t\tdev_err(&client->dev, "gsl_probe: request irq failed\\n");\n\t\tgoto error_init_chip_fail;')
replace('\tdevice_init_wakeup(&client->dev, 0);', '\ttp_unregister_fb(&ts->tp);\n\tdevm_free_irq(&client->dev, client->irq, ts);\n\tdevice_init_wakeup(&client->dev, 0);')
replace('\tbool flag_activated;', '\tbool flag_activated;\n\tbool stopping;')
replace('\tif (ts->flag_irq_is_disable) {', '\tif (!ts->stopping && ts->flag_irq_is_disable) {')
replace('static void gsl_ts_remove(struct i2c_client *client)\n{\n\tstruct gsl_ts *ts = i2c_get_clientdata(client);', 'static void gsl_ts_remove(struct i2c_client *client)\n{\n\tstruct gsl_ts *ts = i2c_get_clientdata(client);\n\tunsigned long flags;\n\n\tspin_lock_irqsave(&ts->irq_lock, flags);\n\tts->stopping = true;\n\tspin_unlock_irqrestore(&ts->irq_lock, flags);')
replace('\tts->flag_need_resume = false;\n\treturn gsl_ts_resume(dev);', '\t{\n\t\tint ret = gsl_ts_resume(dev);\n\t\tif (!ret)\n\t\t\tts->flag_need_resume = false;\n\t\treturn ret;\n\t}')
# Archived r8 busy-delay loops imply nominal reset 20/10/10 ms, startup 10 ms.
# Keep generic timings unchanged. These are nominal parameters, not measurements.
start = candidate.index('static int startup_chip(')
end = candidate.index('static int reset_chip(', start)
block = candidate[start:end]
assert block.count('mdelay(5);') == 1
candidate = candidate[:start] + block.replace('mdelay(5);', 'mdelay(this_ts->profile->startup_delay_ms);') + candidate[end:]
start = candidate.index('static int reset_chip(')
end = candidate.index('static int clr_reg(', start)
block = candidate[start:end]
assert block.count('mdelay(5);') == 3
for index in range(3):
    block = block.replace('mdelay(5);', f'mdelay(this_ts->profile->reset_delay_ms[{index}]);', 1)
candidate = candidate[:start] + block + candidate[end:]
# Separate display blanking from system sleep and always release active slots.
replace('#include <linux/of_device.h>', '#include <linux/of_device.h>\n#include <linux/mutex.h>')
replace('\tbool flag_need_resume;', '\tbool system_suspended, display_suspended;\n\tbool quiescing;\n\tstruct mutex state_lock;\n\tstruct notifier_block f8_fb_notifier;')
replace('\tif (!ts->stopping && ts->flag_irq_is_disable) {', '\tif (!ts->stopping && !ts->quiescing && ts->flag_irq_is_disable) {')
replace('\tts->profile = of_device_get_match_data(&client->dev);', '\tmutex_init(&ts->state_lock);\n\tts->profile = of_device_get_match_data(&client->dev);')
start = candidate.index('static int gsl_ts_suspend(')
end = candidate.index('static int gsl_program_chip(struct i2c_client *client)\n{', start)
candidate = candidate[:start] + (P / 'armbian/touch/templates/f8-pm-block.c').read_text() + '\n' + candidate[end:]
replace('\tts->flag_activated = true;\n\ttp_register_fb(&ts->tp);', '''\tts->flag_activated = true;
	if (ts->profile->evaluation) {
		ts->f8_fb_notifier.notifier_call = gsl_f8_fb_event;
		rc = fb_register_client(&ts->f8_fb_notifier);
		if (rc < 0)
			goto error_free_irq;
	} else {
		tp_register_fb(&ts->tp);
	}''')
replace('error_init_chip_fail:\n\tcancel_work_sync(&ts->work);', '''error_free_irq:
	spin_lock_irq(&ts->irq_lock);
	ts->stopping = true;
	spin_unlock_irq(&ts->irq_lock);
	devm_free_irq(&client->dev, client->irq, ts);
error_init_chip_fail:
	cancel_work_sync(&ts->work);''')
replace('\tspin_lock_irqsave(&ts->irq_lock, flags);\n\tts->stopping = true;\n\tspin_unlock_irqrestore(&ts->irq_lock, flags);', '\tmutex_lock(&ts->state_lock);\n\tspin_lock_irqsave(&ts->irq_lock, flags);\n\tts->stopping = true;\n\tspin_unlock_irqrestore(&ts->irq_lock, flags);\n\tmutex_unlock(&ts->state_lock);')
replace('\ttp_unregister_fb(&ts->tp);', '\tif (ts->profile->evaluation)\n\t\tfb_unregister_client(&ts->f8_fb_notifier);\n\telse\n\t\ttp_unregister_fb(&ts->tp);')
# Global algorithm/filter state cannot serve a second instance. Register release
# before GPIO/input/IRQ resources so ownership remains until they are torn down.
replace('static int gsl3673_init(void)', (P / 'armbian/touch/templates/f8-instance-block.c').read_text() + '\nstatic int gsl3673_init(void)')
replace('\ti2c_set_clientdata(client, ts);\n\tthis_ts = ts;\n\tgsl_client = client;', '''\trc = gsl_claim_instance(ts);
	if (rc < 0)
		return rc;
	rc = devm_add_action_or_reset(&client->dev, gsl_release_instance, ts);
	if (rc < 0)
		return rc;
	i2c_set_clientdata(client, ts);''')
replace('#define TPD_PROC_DEBUG', '/* Legacy writable proc debugging is excluded from this candidate. */')
replace('static void gsl3673_ts_worker(struct work_struct *work)', 'static void gsl_release_contacts(struct gsl_ts *ts);\n\nstatic void gsl3673_ts_worker(struct work_struct *work)')
replace('\tu8 id, touches;', '\tu8 id, touches;\n\tbool seen_ids[MAX_CONTACTS + 1] = {false};')
replace('\tstruct gsl_touch_info cinfo;', '\tstruct gsl_touch_info cinfo = {0};')
replace('\t\tdev_err(&ts->client->dev, "read failed\\n");', '\t\tdev_err(&ts->client->dev, "read failed\\n");\n\t\tgsl_release_contacts(ts);')
replace('\ttouches = ts->touch_data[ts->dd->touch_index];', '''\ttouches = ts->touch_data[ts->dd->touch_index];
	if (touches > MAX_CONTACTS) {
		gsl_release_contacts(ts);
		goto schedule;
	}''')
replace('\ttouches = cinfo.finger_num;', '''\tif (cinfo.finger_num < 0 || cinfo.finger_num > MAX_CONTACTS) {
		gsl_release_contacts(ts);
		goto schedule;
	}
	touches = cinfo.finger_num;''')
replace('\t\tid = cinfo.id[i];', '''\t\tif (cinfo.id[i] < 1 || cinfo.id[i] > MAX_CONTACTS ||
		    cinfo.x[i] < 0 || cinfo.y[i] < 0 ||
		    cinfo.x[i] > ts->profile->max_x ||
		    cinfo.y[i] > ts->profile->max_y)
			continue;
	\tid = cinfo.id[i];''')
replace('\t\tif (id >= 1 && id <= MAX_CONTACTS) {', '\t\tif (id >= 1 && id <= MAX_CONTACTS && !seen_ids[id]) {\n\t\t\tseen_ids[id] = true;')
replace('\tcinfo.finger_num = (ts->touch_data[3] << 24) | (ts->touch_data[2] << 16)\n\t\t| (ts->touch_data[1] << 8) | (ts->touch_data[0]);', '\tcinfo.finger_num = (int)get_unaligned_le32(ts->touch_data);')
replace('\t\tgsl_ts_write(ts->client, 0xf0, buf, 4);', '\t\trc = gsl_ts_write(ts->client, 0xf0, buf, 4);\n\t\tif (rc < 0) {\n\t\t\tgsl_release_contacts(ts);\n\t\t\tgoto schedule;\n\t\t}')
replace('\t\tgsl_ts_write(ts->client, 0x8, buf, 4);', '\t\trc = gsl_ts_write(ts->client, 0x8, buf, 4);\n\t\tif (rc < 0) {\n\t\t\tgsl_release_contacts(ts);\n\t\t\tgoto schedule;\n\t\t}')
(out / 'gsl3673.c').write_text(candidate, encoding='utf-8', newline='\n')
(out / 'profile.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), candidate.splitlines(True), fromfile='a/drivers/input/touchscreen/gsl3673.c', tofile='b/drivers/input/touchscreen/gsl3673.c')), encoding='utf-8', newline='\n')
# The inherited upload routine emits 32-word batches. Verify this particular
# table has complete, ordered pages; no I2C operation is performed here.
raw = (P / 'armbian/touch/reference-r8-shuping/firmware-reference.bin').read_bytes()
records = list(struct.iter_unpack('<II', raw))
assert len(records) == 4851 and len(records) % 33 == 0
for index in range(0, len(records), 33):
    page = records[index:index + 33]
    assert page[0][0] == 0xf0
    assert [entry[0] for entry in page[1:]] == list(range(0, 128, 4))
report = {'scope': 'Unapplied isolated driver candidate; no module loaded or board enabled',
          'source_sha256_normalized': hashlib.sha256(original.encode()).hexdigest(),
          'candidate_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
          'firmware_complete_32_word_pages': len(records) // 33,
          'evaluation_compatible': 'f8-pro,gslx680-shuping-eval',
          'vendor_compatible_matches_candidate': False,
          'irq_reset_timing_algorithm_pm_validated': False,
          'frozen_kernel_changed': False}
(out / 'preparation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
