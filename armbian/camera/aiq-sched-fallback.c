/* Per-process RKAIQ compatibility: retry denied RT threads as SCHED_OTHER.
 * No device/ISP/IQ data changes. Opt-in env var; never installed globally.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef int (*create_fn)(pthread_t *, const pthread_attr_t *, void *(*)(void *), void *);
int pthread_create(pthread_t *thread, const pthread_attr_t *attr,
                   void *(*start)(void *), void *arg)
{
    create_fn real_create = (create_fn)dlsym(RTLD_NEXT, "pthread_create");
    if (!real_create) return ENOSYS;
    int result = real_create(thread, attr, start, arg);
    const char *enabled = getenv("F8_AIQ_NORMAL_SCHED_FALLBACK");
    if (result != EPERM || !attr || !enabled || strcmp(enabled, "1")) return result;
    int policy = 0, inherit = 0;
    struct sched_param requested = {0}, normal = {0};
    pthread_attr_getschedpolicy(attr, &policy);
    pthread_attr_getinheritsched(attr, &inherit);
    pthread_attr_getschedparam(attr, &requested);
    if (inherit != PTHREAD_EXPLICIT_SCHED || (policy != SCHED_FIFO && policy != SCHED_RR)) return result;
    pthread_attr_t fallback;
    /* glibc attr owns no mutable allocation here; preserve stack/detach/guard
     * and affinity settings, change only the scheduler fields in a copy. */
    memcpy(&fallback, attr, sizeof(fallback));
    if (pthread_attr_setschedpolicy(&fallback, SCHED_OTHER) ||
        pthread_attr_setschedparam(&fallback, &normal)) return result;
    result = real_create(thread, &fallback, start, arg);
    fprintf(stderr, "F8 AIQ pthread EPERM policy=%d priority=%d: SCHED_OTHER retry=%d\n",
            policy, requested.sched_priority, result);
    /* No destroy: this is a shallow copy of the caller's attr. */
    return result;
}
