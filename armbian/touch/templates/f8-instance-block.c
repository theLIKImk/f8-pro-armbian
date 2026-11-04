/* The inherited algorithm/filter state is global: permit one bound instance. */
static DEFINE_MUTEX(gsl_instance_lock);

static int gsl_claim_instance(struct gsl_ts *ts)
{
	int ret = 0;

	mutex_lock(&gsl_instance_lock);
	if (this_ts) {
		ret = -EBUSY;
	} else {
		this_ts = ts;
		gsl_client = ts->client;
	}
	mutex_unlock(&gsl_instance_lock);
	return ret;
}

/* Registered before device resources: devres invokes this after their cleanup. */
static void gsl_release_instance(void *data)
{
	struct gsl_ts *ts = data;

	mutex_lock(&gsl_instance_lock);
	if (this_ts == ts) {
		this_ts = NULL;
		gsl_client = NULL;
	}
	mutex_unlock(&gsl_instance_lock);
}
