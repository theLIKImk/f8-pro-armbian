from pathlib import Path
import shutil,sys
root=Path(sys.argv[1]);assets=Path(__file__).resolve().parent
gpu=root/'plugins/gpu'
for name in ['LinuxPanthorGpu.h','LinuxPanthorGpu.cpp']:shutil.copyfile(assets/name,gpu/name)
p=gpu/'LinuxBackend.cpp';s=p.read_text();anchor='        if (vendor == amdVendor) {'
if '#include "LinuxPanthorGpu.h"' in s:s=s.replace('''        if (qstrcmp(udev_device_get_driver(pciDevice), "panthor") == 0) {
            gpu = new LinuxPanthorGpu{gpuId, QString::fromUtf8(udev_device_get_syspath(pciDevice))};
        } else if (vendor == amdVendor) {''',anchor).replace('#include "LinuxPanthorGpu.h"\n','')
assert s.count(anchor)==1
s=s.replace('#include "LinuxAmdGpu.h"','#include "LinuxAmdGpu.h"\n#include "LinuxPanthorGpu.h"')
s=s.replace(anchor,'''        if (qstrcmp(udev_device_get_driver(pciDevice), "panthor") == 0) {
            gpu = new LinuxPanthorGpu{gpuId, QString::fromUtf8(udev_device_get_syspath(pciDevice))};
        } else if (vendor == amdVendor) {''');p.write_text(s)
p=root/'plugins/disks/disks.cpp';s=p.read_text();anchor='if (type == Solid::StorageDrive::HardDisk)'
s=s.replace('if (type == Solid::StorageDrive::HardDisk || type == Solid::StorageDrive::SdMmc || type == Solid::StorageDrive::FlashMemory)',anchor)
s=s.replace('if (type == Solid::StorageDrive::HardDisk || type == Solid::StorageDrive::SdMmc)',anchor);assert s.count(anchor)==1
s=s.replace(anchor,'if (type == Solid::StorageDrive::HardDisk || type == Solid::StorageDrive::SdMmc)');p.write_text(s)
