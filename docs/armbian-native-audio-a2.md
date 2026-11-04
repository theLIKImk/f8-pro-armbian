# A1 声卡注册；发现背光PWM误驱动振动器；A2修复（2026-10-30）

2026-11-01更新：A2已实际刷入并冷启动通过。用户确认不再振动且屏幕亮度正常变化；SSH核对GPIO4_B2=pwm14m1、GPIO3_C2空闲，桌面/键盘/持久化正常。音频短音仅有咔哒声，尚未通过。当前仍A2在线192.0.2.227；下一候选及测试方法见 [A3记录](armbian-native-audio-a3.md)。下方Loader/待刷A2为历史记录。

当前用户已进入Loader，停止了运行中的A1 Linux；A2尚未刷入。用户明确暂缓电池，相关配置未改，不再沿用旧“平板SSH在线”状态。

## 本轮实机进展

A1 boot_id 63020aed-3343-41d3-b9ee-8cccf098d820。ES8388设备7-0011成功绑定ES8323，ALSA card0和PCM0注册，PipeWire创建Built-in Audio Stereo输出。桌面/SSH保持，持久化标记从T1r2跨boot_id保存验证通过。证据 local/hardware/armbian-native-audio-a1-20261030-01/。

屏幕键盘available=true，enabled=false；用户明确确认触摸输入时仍能正常弹出，属于策略状态，勿强制改用户键盘偏好。验收脚本已改为只强制要求available，enabled按实际记录；未伪造true。

播放试验01因/run/f8目录权限导致pw-play无法读测试文件，没有播放；已恢复混音器。试验02改用/run/user/1601下的可读文件，临时OUT2开、Output2=24(-9dB)、两秒淡入淡出音，pw-play退出0，之后按备份恢复。用户确认没听到声音，只有整机明显马达振动。因此**声卡注册通过不等于扬声器已通过，audio_playback_verified仍false**。

已停止进一步音频播放，临时关闭Speaker和OUT2，spk switch读回off、GPIO133低。没有强制切换GPIO来试探扬声器。之后用户进入Loader；以上临时混音器设置未持久化，重启后仍需重新检查。

## 明确定位的PWM问题

原厂Ubuntu与Android共5份DTB均规定：

- 振动器GPIO3_C2（gpio@fec40000，pin18）。
- 背光PWM14控制器febf0020，m1 GPIO4_B2，function11，周期20000ns。
- 扬声器控制GPIO4_A5，与原厂振动器引脚不同。

当前实机却是PWM14 m0占用GPIO3_C2，GPIO4_B2空闲；亮度31/255。即“背光”驱动正在输出到原厂振动器脚。这是此前背光移植遗漏的mux配置，T1r2和A1均有此旧问题，A1仅修改音频并未新增它。不能再仅以振动认定音频信号或扬声器GPIO错误。

证据 analysis/armbian/audio-factory-variants-20261030.json、backlight-motor-audit-20261030.json，及实机 quiet-gpio-01.json、backlight-motor-ownership.json。

## A2候选

outputs/armbian/official-f8-native-audio-a2/BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A2.img

49426612字节，SHA256 bd7277d09b7928ef554960986ab14076292a57a247aac59d13bd57bd2f7376ec。

基于A1，只改变PWM14 pinctrl-0，并补入原树裁掉的pwm14m1-pins节点；GPIO4_B2的函数和pinconf精确匹配原厂。原厂背光周期及enable GPIO匹配且保持不变，亮度默认值不改。内核、ramdisk、resource逐字节不变，音频A1和T1r2修复保留，电池节点不改。其余DT字节属性逐项一致，FIT/DT增长内存边界/Windows文件SHA与分区容量通过。**A2冷启动、停振、亮度与实际出声尚待验证**。

构建 tools/build-f8-native-audio-a2.py 已完成，不要重跑。Canonical DTS f8-pro-peripherals.dtsi也补上pwm14m1_pins引用，未来自编内核仍需重跑完整编译验证；不能部署旧compile-check DTB。

## 下一步

用户已在Loader，只刷A2到boot 0x00008000，不勾rootfs/Loader/Recovery、不擦除Flash。重启先确认不再振动、桌面可用；然后用已信任SSH 192.0.2.227（如DHCP变化则新IP）读pinmux，期望GPIO4_B2=pwm14m1、GPIO3_C2不再由PWM14占用，检查背光小幅调节。不要先重复扬声器播放。

停振与背光确认后，再检查音频路径并做新的编号短低音量试验；既有01/02输出不可覆盖。若仍无声，需要继续I2S/codec/功放路由验证，不盲目提高音量或翻转GPIO。实际扬声器仍未验收，电池继续暂缓。
