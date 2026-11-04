# KDE 系统监视器磁盘与 GPU 读数修复 K1（2026-11-02）

## 已完成、已验收

用户报告 KDE 任务管理器/系统监视器不能读取磁盘和GPU。原生插件修复后，普通用户D-Bus实际数据、受控16MiB写入和4秒GPU负载测试通过，用户确认“磁盘和 GPU 都显示正常”。只重载ksystemstats与系统监视器窗口，未刷BOOT/改内核/重启KDE桌面；本轮未做整机冷启动复测。

## 两个根因

1. KDE 6.6.6 GPU Linux后端仅识别AMD/Intel/NVIDIA的PCI厂商，RK3588 Panthor是platform设备，没有GPU对象。原始D-Bus无gpu路径；普通用户可读devfreq/load、cur_freq及thermal温度，实际驱动已正常工作。[上游GPU后端](https://github.com/KDE/ksystemstats/blob/v6.6.6/plugins/gpu/LinuxBackend.cpp)
2. 磁盘插件只接受Solid StorageDrive::HardDisk，明确排除了eMMC所属SdMmc类型。UDisks正常、root分区已挂载、/proc/diskstats和sysfs统计可读，但D-Bus仅有disk/all空聚合，没有具体卷。[上游磁盘过滤](https://github.com/KDE/ksystemstats/blob/v6.6.6/plugins/disks/disks.cpp)

overview.page本来使用gpu/all/usage和disk非all的used路径，配置正确，不需要重置用户页面。

## 修复内容

- 原GPU插件保留AMD/Intel/NVIDIA后端，增加LinuxPanthorGpu。通过DRM父设备driver=panthor识别，动态发现其devfreq和gpu-thermal；发布gpu/gpuN/name、usage、coreFrequency（MHz）、temperature（°C），原有gpu/all/usage自动聚合，兼容原概览页。
- 普通用户读取devfreq的load百分比、cur_freq和thermal毫摄氏度，不需要root采集服务、chmod sysfs或开启profiling。GPU profiling仍为0。
- Mali采用共享内存，插件没有提供不存在的独立显存/功耗数据，不把全部系统RAM伪装成显存。原AllGpus聚合VRAM项可能无数据，这不代表GPU使用率修复失败；每进程GPU内存/占用统计不在本次验收范围。
- 磁盘插件在HardDisk之外接受SdMmc，原有USB、挂载监听、容量/读写逻辑保留。没有改分区、格式化或挂载行为。

## 构建与安装

源包固定KDE/ksystemstats v6.6.6，保存于vendor/kde-ksystemstats-6.6.6/source.tar.gz，哈希见产物manifest。自有补丁与构建代码位于armbian/kde/ksystemstats/：LinuxPanthorGpu.h/.cpp、patch-source.py、build-native.py；GPL标注保留。

平板原生g++编译，仅apt-get download并提取Qt/KF/ksysguard开发包到 `/var/tmp/f8-pro-ksystemstats-k1/deps`，**未安装整套开发包**。构建服务f8-ksystemstats-build已成功结束。构建时修正了moc编译参数、补齐Qt QML头文件，并匹配实际Solid枚举SdMmc（此版本没有FlashMemory），旧失败日志保留，不是运行时硬件故障。

安装工具tools/install-f8-ksystemstats-k1.py先检查ELF动态符号、备份原文件，使用dpkg-divert保存发行版插件到 `/usr/lib/f8-pro/ksystemstats-distribution/`，修复库安装回标准Qt插件目录。原版不放在插件搜索目录内，避免重复加载。后端重启后必须同时发布GPU和具体磁盘used传感器，否则自动尝试回退。安装前备份及result.json在 `/var/lib/f8-pro/ksystemstats-k1/`。

两个已安装/已导出ARM64库：

| 文件 | 字节 | SHA256 |
| --- | ---: | --- |
| ksystemstats_plugin_gpu.so | 136632 | 8e14e485233c28f44951ee875c7ab2f6d02a90f93f316a8e68d417b67ee20123 |
| ksystemstats_plugin_disk.so | 134976 | 05ab211ece3bfaa2235d8b9b9c981b2d0bd78d9292da9e03374a0103a913229f |

保留产物 `outputs/armbian/f8-kde-monitor-k1/`。当前ksystemstats6.6.6、libksysguard6.6.5、Qt6.10.2、Solid6.24；包更新不会直接覆盖本地divert文件，但KDE/Qt版本变化后仍需核对兼容并重建。根fs配置脚本已集成两个库、版本/哈希检查与离线divert；真实dpkg-divert --root隔离/恢复测试通过。尚未重新构建完整ROOTFS。

## 实际数据验证

以UID1602普通用户持有D-Bus订阅，读取原KDE sensorData：

- 根文件系统total=242956578816字节，与statvfs完全一致；used约18.2GB、free约224.7GB，写入16MiB时used增长相应数值。
- 受控写入期间write约11.69MB/s，read约9.30MB/s，负载后速率可归零。
- GPU使用率29/48→67/78/81/89%，随后13→0%；频率500/1000MHz在负载后回200MHz，温度48–52.7°C有实时变化。
- GPU/all和gpu/gpu0使用率一致，显示值来自真实硬件统计，不是固定假值。

probe临时文件已删除，无录音/相机数据采集。用于订阅测试的脚本在armbian/kde/ksystemstats/sensor-probe.py，平板暂存 `/usr/local/lib/f8-pro/kde-sensor-probe.py`，不设开机启动。当前用户原有overview.page没有改写，重开窗口后用户验收成功。

证据local/hardware：ksystemstats-before01、dev01、sensors01、build-status04、install01、values01、probe01、monitor-open01、artifacts01等JSON。analysis/linux-issues-20261102/kde-sensors-before.json保存原传感器清单。日志里的network helper抓包权限不足是另一个问题，本次未修改其权限。

## 回退

如确需回退，先停止普通用户plasma-ksystemstats.service，确认待删文件哈希为上表修复库，再逐个删除这两个固定文件；使用dpkg-divert --local --remove --rename --divert原版路径 标准插件路径恢复发行版，最后重启普通用户服务。不要删除整个Qt插件目录或全局取消其他diversion。安装工具内含对应失败回滚逻辑。
