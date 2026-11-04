"""Execute extracted candidate transport/sequence functions against a fake bus."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

P = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
out = P / 'armbian/touch/candidate-r8-shuping'
work = Path('/var/tmp/f8-pro-armbian/touch-transport-tests')
work.mkdir(parents=True, exist_ok=True)
source = (out / 'gsl3673.c').read_text()


def function(name):
    match = re.search(r'^static[^\n]*\b' + re.escape(name) + r'\([^;]*?\)\n\{', source, re.M)
    assert match, name
    start = match.start()
    pos = source.index('{', match.start())
    depth = 1
    end = pos + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


declaration = re.search(r'struct fw_data\s*\{.*?\};', (P / 'analysis/armbian/source-audit/linux-rockchip/drivers/input/touchscreen/gsl3673.h').read_text(), re.S)[0]
prefix = r'''
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#define I2C_M_TEN 0x10
#define GSL_PAGE_REG 0xf0
#define DMA_TRANS_LEN 32
#define GSL_NOID_VERSION
#define print_info(...) ((void)0)
#define dev_err(...) ((void)0)
struct i2c_client { void *adapter; unsigned short addr, flags; int dev; };
struct i2c_msg { unsigned short addr, flags, len; u8 *buf; };
static int calls, fail_at, short_transfer, bad_memory, algorithm_inits;
static FILE *capture;
static int bus_call(const u8 *bytes, int len, int expected) {
    calls++;
    if (capture && bytes) {
        assert(len <= 129);
        fputc(len & 255, capture); fputc(len >> 8, capture);
        assert(fwrite(bytes, 1, len, capture) == (size_t)len);
    }
    if (calls == fail_at) return short_transfer ? expected - 1 : -EREMOTEIO;
    return expected;
}
static int i2c_transfer(void *adapter, struct i2c_msg *msg, int count) {
    (void)adapter; assert(count == 1);
    return bus_call(msg->buf, msg->len, 1);
}
static int i2c_master_send(struct i2c_client *client, const u8 *buf, int len) {
    (void)client; return bus_call(buf, len, len);
}
static int i2c_master_recv(struct i2c_client *client, u8 *buf, int len) {
    (void)client; memset(buf, bad_memory ? 0 : 0x5a, len);
    return bus_call(NULL, len, len);
}
static void put_unaligned_le32(u32 value, u8 *buf) {
    for (int i=0; i<4; i++) buf[i] = value >> (8*i);
}
static int delays[32], delay_count;
static void msleep(int n) { if (capture) { assert(delay_count < 32); delays[delay_count++] = n; } }
static void mdelay(int n) { msleep(n); }
static int gsl3673_shutdown_low(void) { return 0; }
static int gsl3673_shutdown_high(void) { return 0; }
static void gsl_DataInit(unsigned int *array) { assert(array[1] == 512); algorithm_inits++; }
'''
prefix += declaration + '\n#include "f8-pro-r8-shuping-reference.h"\n'
prefix += '''struct profile { const struct fw_data *firmware; unsigned int firmware_count; unsigned int *algorithm; unsigned short reset_delay_ms[3], startup_delay_ms; };
static struct profile selected = { f8_pro_r8_shuping_fw, 4851, f8_pro_r8_shuping_algorithm, {20,10,10}, 10 };
static struct { struct profile *profile; } ts = { &selected }, *this_ts = &ts;
static int gsl_program_chip(struct i2c_client *client);
'''
names = ['gsl_write_interface', 'gsl_ts_write', 'gsl_ts_read', 'fw2buf', 'gsl_load_fw',
         'test_i2c', 'startup_chip', 'reset_chip', 'clr_reg', 'gsl_program_chip', 'init_chip', 'check_mem_data']
main = r'''
static void fault_matrix(int (*operation)(struct i2c_client *), int expected, int memory) {
    struct i2c_client client = { .addr = 0x40 };
    bad_memory = memory; fail_at = 0; calls = 0;
    assert(operation(&client) == 0); assert(calls == expected);
    for (int mode=0; mode<2; mode++) {
        for (int index=1; index<=expected; index++) {
            fail_at = index; short_transfer = mode; calls = 0;
            int ret = operation(&client);
            assert(ret == (mode ? -EIO : -EREMOTEIO));
            assert(calls == index); /* absolutely no subsequent bus transaction */
        }
    }
}
int main(int argc, char **argv) {
    assert(argc == 2);
    struct i2c_client client = { .addr = 0x40 };
    capture = fopen(argv[1], "wb"); assert(capture);
    assert(gsl_program_chip(&client) == 0); assert(calls == 306);
    assert(algorithm_inits == 2);
    const int expected_delays[] = {20,5,5,20,20,10,10,10,20,10,10,10};
    assert(delay_count == 12);
    assert(memcmp(delays, expected_delays, sizeof(expected_delays)) == 0);
    fclose(capture); capture = NULL;
    fault_matrix(gsl_program_chip, 306, 0);
    fault_matrix(test_i2c, 5, 0);
    fault_matrix(check_mem_data, 2, 0);
    fault_matrix(check_mem_data, 313, 1);
    puts("1252 injected faults stopped at the first failed/short transaction");
    return 0;
}
'''
(work / 'transport-test.c').write_text(prefix + '\n'.join(function(name) for name in names) + main)
reference = P / 'armbian/touch/reference-r8-shuping'
subprocess.run(['gcc', '-std=gnu11', '-O1', '-Wall', '-Wextra', '-Werror', '-Wno-sign-compare',
                '-fsanitize=undefined', '-fno-sanitize-recover=all', '-I' + str(reference),
                str(work / 'transport-test.c'), '-o', str(work / 'transport-test')], check=True)
result = subprocess.check_output([str(work / 'transport-test'), str(work / 'trace.bin')], text=True)
stream = (work / 'trace.bin').read_bytes()
actual = []
pos = 0
while pos < len(stream):
    length = struct.unpack_from('<H', stream, pos)[0]
    pos += 2
    actual.append(stream[pos:pos + length])
    pos += length
reset = [b'\xe0\x88', b'\xe4\x04', b'\xbc' + bytes(4)]
expected = [b'\xe0\x88', b'\x80\x03', b'\xe4\x04', b'\xe0\x00'] + reset
records = list(struct.iter_unpack('<II', (reference / 'firmware-reference.bin').read_bytes()))
for index in range(0, len(records), 33):
    page = records[index:index + 33]
    expected.append(b'\xf0' + struct.pack('<I', page[0][1]))
    expected.append(b'\x00' + b''.join(struct.pack('<I', entry[1]) for entry in page[1:]))
expected += [b'\xe0\x00'] + reset + [b'\xe0\x00']
assert actual == expected and len(actual) == 306
report = {'scope': 'Host C fault injection using extracted candidate functions and a fake bus; no real I2C or timing/algorithm test',
          'candidate_sha256': hashlib.sha256(source.encode()).hexdigest(),
          'ubsan_passed': True, 'success_sequence_messages': len(actual),
          'success_payloads_equal_independent_reference': True, 'injected_faults': 1252,
          'nominal_delay_sequence_ms': [20,5,5,20,20,10,10,10,20,10,10,10],
          'real_elapsed_time_verified': False,
          'negative_errno_preserved': True, 'short_transfer_returns_eio': True,
          'no_bus_transactions_after_first_error': True,
          'covered': names, 'test_output': result.strip()}
(out / 'transport-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
