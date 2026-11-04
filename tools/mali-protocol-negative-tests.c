/* Exercise rejection paths without handing a valid request to the GPU driver. */
#include <wayland-client.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static const struct wl_interface *buffer_types[8] = {&wl_buffer_interface, NULL, NULL, NULL, NULL, NULL, NULL, NULL};
static const struct wl_message requests[] = {{"create_buffer", "niiuuuuh", buffer_types}, {"auth", "u", NULL}};
static const struct wl_message events[] = {{"alloc_device", "s", NULL}};
static const struct wl_interface mali_interface = {"mali_buffer_sharing", 5, 2, requests, 1, events};
struct state { struct wl_proxy *mali; };

static void device(void *data, struct wl_proxy *proxy, const char *name)
{
    (void)data; (void)proxy; (void)name;
}
static const struct { void (*alloc_device)(void *, struct wl_proxy *, const char *); } mali_listener = {device};

static void global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
    struct state *state = data;
    if (!strcmp(interface, mali_interface.name)) {
        state->mali = wl_registry_bind(registry, name, &mali_interface, version < 5 ? version : 5);
        wl_proxy_add_listener(state->mali, (void (**)(void))&mali_listener, NULL);
    }
}
static void removed(void *data, struct wl_registry *registry, uint32_t name)
{
    (void)data; (void)registry; (void)name;
}
static const struct wl_registry_listener registry_listener = {global, removed};

struct test_case {
    const char *name;
    int32_t width, height;
    uint32_t stride, format, opaque0, opaque1;
    int auth;
};

static int run(const struct test_case *test)
{
    struct wl_display *display = wl_display_connect(NULL);
    if (!display) return 0;
    struct state state = {0};
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, &state);
    struct wl_proxy *buffer = NULL;
    int passed = 0;
    if (wl_display_roundtrip(display) < 0 || !state.mali || wl_display_roundtrip(display) < 0) goto done;
    if (test->auth) {
        wl_proxy_marshal(state.mali, 1, 0u);
    } else {
        int fd = open("/dev/null", O_RDONLY);
        if (fd < 0) goto done;
        buffer = wl_proxy_marshal_constructor_versioned(state.mali, 0, &wl_buffer_interface, 1,
                    NULL, test->width, test->height, test->stride, test->format,
                    test->opaque0, test->opaque1, fd);
        close(fd);
    }
    wl_display_roundtrip(display);
    const struct wl_interface *error_interface = NULL;
    uint32_t object_id = 0;
    wl_display_get_protocol_error(display, &error_interface, &object_id);
    passed = wl_display_get_error(display) == EPROTO && error_interface
        && !strcmp(error_interface->name, mali_interface.name);
    printf("F8_MALI_NEGATIVE case=%s rejected=%d object=%u\n", test->name, passed, object_id);
done:
    if (buffer) wl_proxy_destroy(buffer);
    if (state.mali) wl_proxy_destroy(state.mali);
    wl_registry_destroy(registry);
    wl_display_disconnect(display);
    return passed;
}

int main(void)
{
    const uint32_t abgr = 0x34324241;
    const struct test_case tests[] = {
        {"zero-width", 0, 64, 256, abgr, 0, 0, 0},
        {"oversized-height", 64, 8193, 256, abgr, 0, 0, 0},
        {"short-stride", 64, 64, 4, abgr, 0, 0, 0},
        {"unknown-format", 64, 64, 256, 0, 0, 0, 0},
        {"opaque-parameter-0", 64, 64, 256, abgr, 1, 0, 0},
        {"opaque-parameter-1", 64, 64, 256, abgr, 0, 1, 0},
        {"drm-authentication", 0, 0, 0, 0, 0, 0, 1},
    };
    unsigned passed = 0, total = sizeof(tests) / sizeof(tests[0]);
    for (unsigned i = 0; i < total; i++) passed += run(&tests[i]);
    printf("F8_MALI_NEGATIVE passed=%u total=%u\n", passed, total);
    return passed == total ? 0 : 1;
}
