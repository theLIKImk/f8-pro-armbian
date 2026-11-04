/* Diagnostic only: observe public Wayland global registration metadata. */
#define _GNU_SOURCE
#include <wayland-server-core.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>

static struct wl_global *(*original)(struct wl_display *, const struct wl_interface *,
                                    int, void *, wl_global_bind_func_t);
static pthread_once_t once = PTHREAD_ONCE_INIT;

static void resolve(void)
{
    original = dlsym(RTLD_NEXT, "wl_global_create");
}

static void describe(const char *kind, const struct wl_message *messages, int count)
{
    for (int i = 0; i < count && i < 64; i++) {
        const struct wl_message *message = &messages[i];
        fprintf(stderr, "F8_MALI_PROTOCOL %s opcode=%d name=%s signature=%s types=",
                kind, i, message->name, message->signature);
        unsigned argument = 0;
        for (const char *p = message->signature; *p; p++) {
            if (strchr("iufsonah", *p)) {
                const struct wl_interface *type = message->types ? message->types[argument] : NULL;
                fprintf(stderr, "%s%s", argument ? "," : "", type ? type->name : "-");
                argument++;
            }
        }
        fprintf(stderr, "\n");
    }
}

struct wl_global *wl_global_create(struct wl_display *display,
                                   const struct wl_interface *interface, int version,
                                   void *data, wl_global_bind_func_t bind)
{
    pthread_once(&once, resolve);
    if (strcmp(interface->name, "mali_buffer_sharing") == 0) {
        fprintf(stderr, "F8_MALI_PROTOCOL interface=%s version=%d registered=%d methods=%d events=%d\n",
                interface->name, interface->version, version, interface->method_count, interface->event_count);
        describe("request", interface->methods, interface->method_count);
        describe("event", interface->events, interface->event_count);
    }
    return original ? original(display, interface, version, data, bind) : NULL;
}
