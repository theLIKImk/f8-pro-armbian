# 原生桌面验收完成，音频 A1 候选（2026-10-30）

**最新覆盖：A1已刷并成功注册声卡，桌面/SSH/持久化通过；测试无声音但整机马达振动。查明背光PWM14 m0误占原厂振动器脚，A2仅修复背光复用已打包，用户已进Loader待刷boot。见 armbian-native-audio-a2.md。扬声器未通过，不重复播放；电池暂缓。**

用户确认T1r2启动成功，要求继续适配、暂时跳过电池。现在SSH 192.0.2.227 f8test 已通过物理日志公钥验证；新known_hosts为 /var/tmp/f8-pro-armbian/desktop-t1-known-hosts，alias=f8-desktop-t1。原r6 host pin不适用。交互连接可用 tools/Connect-F8-Desktop.ps1 -Address 192.0.2.227（当前已注册公钥，无需重复插日志盘）。旧通用ZIP里的首次连接助手仍要求日志盘，不必重打包。

## 当前已验收基线

T1r2新boot_id a9526f75-027f-45fd-aff1-bbd74006ab79，内核6.1.115-vendor-rk35xx，p6 ext4 rw、UUID匹配；SDDM运行、状态页inactive，96-f8-status-handoff.conf运行文件哈希与候选一致；0系统失败单元。KDE Wayland、KWin Mali-G610/Mesa硬件渲染、屏幕键盘available/enabled均已验证。T1r2 preflight已备份原版本并更新cold_boot_verified。证据 local/hardware/armbian-native-desktop-t1r2-success-20261030-01/ 下 nonbattery-baseline.json、native-acceptance-firstboot.json、audio-baseline.json。

已在 /var/lib/f8-pro/native-persistence-check.json 写入首个boot_id，等待下次重启后verify-f8-native-desktop.sh验证持久化；不能重复运行record-f8-native-acceptance.py覆盖首测文件。Wi-Fi与SSH当前正常，后续重启需重验。背光节点brightness=actual=21/max255，尚未进行额外亮度调节验收；蓝牙服务运行但无HCI设备，未适配完成。

## 电池明确暂缓

不适配电量采样、充电、PD，不改相关寄存器/策略。已有电源服务保持原配置；本轮只查询其服务状态，没有主动采样电池或改电池设置。

## 音频问题和修复

当前没有ALSA声卡。声卡/ES8388 codec/I2S节点原来均禁用；内核已内置ROCKCHIP_I2S_TDM、MULTICODECS、ES8323、ES8328_I2C，暂不需要另编内核。

物理对照 analysis/armbian/audio-wiring-20261030.json：原厂与当前 CPU地址fe470000、12.288MHz MCLK、时钟ID、I2C7、codec MCLK、GPIO4_A2及扬声器GPIO4_A5匹配；唯一不同为I2S默认引脚组。当前默认含GPIO1_D0/D1，而这两根已由I2C7功能9占用。A1改为原厂GPIO1_C5、C3、D4、C7四根，精确匹配函数和pull/Schmitt配置；实时pinmux确认新增音频所需GPIO均未占用。

A1只修改DT四个属性：I2S pinctrl-0，以及I2S、codec、声卡三个status。其余整个DT树逐项相同，包含电池节点。内核、ramdisk（含T1r2交接修复）、resource逐字节不变。没有测试播放或用户空间混音器写入；启用后codec驱动会自行初始化硬件，因此还需要上机注册与路由验证。

候选 outputs/armbian/official-f8-native-audio-a1/BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A1.img，49426544字节，SHA256 7ed3dab57aa6eb84ddc13e50b1d58104815962a5c18e7d7f09e46f876a76f2e7。FIT、变更范围、原厂引脚和Windows实际文件SHA/容量校验均通过；**尚未刷入，音频尚未验证**。

## 下一步

用户进入Loader，只刷boot 0x00008000；rootfs/Loader/Recovery不勾选，不擦除Flash。回退为已验收T1r2 BOOT（同一地址），不需要恢复根分区。

重启后先验桌面/Wi-Fi/SSH，再读取/proc/asound/cards、aplay -l、codec驱动绑定与dmesg；声卡注册后读取ALSA/PipeWire控制项，选择适当小音量做短播放测试。尚未安排自动扬声器播放，不将“有声卡”当成“扬声器已出声”。同时重新运行verify-f8-native-desktop.sh保存新编号输出，以确认跨boot_id持久化。蓝牙/背光/方向随后，电池仍暂缓。

构建 tools/build-f8-native-audio-a1.py 已完成，不要重跑；工具audit-f8-audio-wiring.py和capture-f8-audio-baseline.py可用于理解证据，已有记录不要覆盖。
