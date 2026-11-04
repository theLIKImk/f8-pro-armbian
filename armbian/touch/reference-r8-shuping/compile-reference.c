typedef unsigned int u32;
struct fw_data
{
    u32 offset : 8;
    u32 : 0;
    u32 val;
};
#include "f8-pro-r8-shuping-reference.h"
_Static_assert(sizeof(struct fw_data) == 8, "fw_data ABI");
_Static_assert(sizeof(f8_pro_r8_shuping_fw) == 38808, "firmware length");
_Static_assert(sizeof(f8_pro_r8_shuping_algorithm) == 2048, "algorithm length");
