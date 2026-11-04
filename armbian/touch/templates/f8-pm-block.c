/* Inserted into the isolated candidate, never the frozen kernel source. */
static void gsl_release_contacts(struct gsl_ts *ts)
{
	int i;

	for (i = 0; i <= MAX_CONTACTS; i++) {
		input_mt_slot(ts->input, i);
		input_mt_report_slot_state(ts->input, MT_TOOL_FINGER, false);
	}
	input_sync(ts->input);
	memset(id_sign, 0, sizeof(id_sign));
	memset(id_state_flag, 0, sizeof(id_state_flag));
	memset(id_state_old_flag, 0, sizeof(id_state_old_flag));
	memset(x_old, 0, sizeof(x_old));
	memset(y_old, 0, sizeof(y_old));
	x_new = y_new = 0;
}

/* state_lock serializes display/system PM; input work never takes this lock. */
static int gsl_suspend_locked(struct gsl_ts *ts)
{
	unsigned long flags;

	if (!ts->flag_activated)
		return 0;
#ifdef GSL_MONITOR
	cancel_delayed_work_sync(&gsl_monitor_work);
#endif
	spin_lock_irqsave(&ts->irq_lock, flags);
	ts->quiescing = true;
	spin_unlock_irqrestore(&ts->irq_lock, flags);
	ts_irq_disable(ts);
	synchronize_irq(ts->client->irq);
	cancel_work_sync(&ts->work);
	gsl_release_contacts(ts);
	gsl3673_shutdown_low();
	ts->flag_activated = false;
	return 0;
}

static int gsl_resume_locked(struct gsl_ts *ts)
{
	unsigned long flags;
	int ret;

	if (ts->flag_activated)
		return 0;
	gsl3673_shutdown_high();
	mdelay(5);
	ret = reset_chip(ts->client);
	if (ret < 0)
		goto error_quiesce;
	ret = startup_chip(ts->client);
	if (ret < 0)
		goto error_quiesce;
	ret = check_mem_data(ts->client);
	if (ret < 0)
		goto error_quiesce;
	spin_lock_irqsave(&ts->irq_lock, flags);
	ts->quiescing = false;
	spin_unlock_irqrestore(&ts->irq_lock, flags);
	ts->flag_activated = true;
	ts_irq_enable(ts);
#ifdef GSL_MONITOR
	queue_delayed_work(gsl_monitor_workqueue, &gsl_monitor_work, 300);
#endif
	return 0;
error_quiesce:
	gsl3673_shutdown_low();
	return ret;
}

static int gsl_set_suspend_reason(struct gsl_ts *ts, bool system, bool suspend)
{
	bool *reason, previous;
	int ret;

	mutex_lock(&ts->state_lock);
	if (ts->stopping) {
		ret = -ENODEV;
		goto out;
	}
	reason = system ? &ts->system_suspended : &ts->display_suspended;
	previous = *reason;
	*reason = suspend;
	if (ts->system_suspended || ts->display_suspended)
		ret = gsl_suspend_locked(ts);
	else
		ret = gsl_resume_locked(ts);
	if (ret < 0)
		*reason = previous;
out:
	mutex_unlock(&ts->state_lock);
	return ret;
}

static int __maybe_unused gsl_ts_pm_suspend(struct device *dev)
{
	return gsl_set_suspend_reason(dev_get_drvdata(dev), true, true);
}

static int __maybe_unused gsl_ts_pm_resume(struct device *dev)
{
	return gsl_set_suspend_reason(dev_get_drvdata(dev), true, false);
}

static int gsl_ts_early_suspend(struct tp_device *tp_d)
{
	struct gsl_ts *ts = container_of(tp_d, struct gsl_ts, tp);
	return gsl_set_suspend_reason(ts, false, true);
}

static int gsl_ts_late_resume(struct tp_device *tp_d)
{
	struct gsl_ts *ts = container_of(tp_d, struct gsl_ts, tp);
	return gsl_set_suspend_reason(ts, false, false);
}

/* F8 callback has no optimistic status cache: errors can be retried. */
static int gsl_f8_fb_event(struct notifier_block *self, unsigned long action,
			   void *data)
{
	struct gsl_ts *ts = container_of(self, struct gsl_ts, f8_fb_notifier);
	struct fb_event *event = data;
	int ret;

	if (action != FB_EVENT_BLANK || !event || !event->data)
		return NOTIFY_DONE;
	ret = gsl_set_suspend_reason(ts, false,
			*(int *)event->data != FB_BLANK_UNBLANK);
	return notifier_from_errno(ret);
}
