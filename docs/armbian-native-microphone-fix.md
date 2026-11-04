# F8-PRO 麦克风修复（2026-11-01）

> 2026-11-02：本文旧Stereo/MaxPGA7配置已由用户试听验收的左声道方案替代。当前为ALC Left、MaxPGA5、Left8、Right0、ADC Left Left，已保存UCM和asound.state并通过音频服务重载/重新捕获检查。见 [最新杂音修复记录](armbian-linux-issues-20261102.md)。不要再运行下列历史固化脚本覆盖新值。

## 结果

用户验收：语音录音正常（修复前录到本底 RMS 5–15，修复后语音 RMS 3500–9300），桌面应用可见 Built-in Microphone，重启后自动恢复（用户确认）。

## 三层根因与修复

### 1. 模拟捕获增益静默（主根因）

ES8323 捕获链的模拟增益 `Left/Right Channel Capture Volume`（0–8）一直为 0，信号在模拟级即被静默。之前调数字增益（`Capture Digital`）、PGA、ALC 均无效——增益在模拟级之后。

修复：`amixer -c 0 sset 'Left Channel' 8`、`sset 'Right Channel' 8`，并 `alsactl store 0` 固化到 `/var/lib/alsa/asound.state`，开机经 `alsa-restore` 自动恢复。

### 2. UCM 缺输入设备定义

`/usr/share/alsa/ucm2/F8-PRO/HiFi.conf` 原本只有 `SectionDevice.Speaker`。新增 `SectionDevice.Mic`：

- EnableSequence 含完整捕获链：Left/Right Channel=8、ALC Capture Function=Stereo、ALC Capture Max PGA=7、Capture Digital Volume=192、Capture Mute=off、ADC Data Select=Left Right、PGA Mux=DifferentialL/R
- Value：`CapturePCM "hw:${CardId},0"`、CaptureChannels 2、CaptureMixerElem "Capture Digital"
- 原文件备份 `HiFi.conf.bak-mic`

注意：`Main Mic`/`Headset Mic` 控件在 UCM cset 中执行失败（原因未深究，控件本身存在且手工 amixer 可设），已从序列中移除，依赖 asound.state 固化默认值。

### 3. WirePlumber ACP 模式枚举不出 capture profile

WP 默认 `api.alsa.use-acp=true`，ACP 对这块 dailink 双向单 PCM 枚举不到输入 profile，即使 UCM 有 Mic 设备也不建 source。

修复：新增 `/usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf`：

```
monitor.alsa.properties = {
  api.alsa.use-acp = false
  api.alsa.use-ucm = true
}
```

重启 `wireplumber` 后创建 `alsa_input.platform-es8388-sound.HiFi__Mic__source`。

## 排查过程中的有用结论

- alsaucm 每次调用是独立进程，`open` 状态不保留；验证 UCM 需 `alsaucm -b -` 单进程批处理（open → set _verb → set _enadev）。
- UCM 名以 `conf.d/<dir>/<file>.conf` 的文件名（去后缀）为准：`rockchip,es8388-codec`。
- 增益无效 ≠ 麦克风坏：先排查模拟级增益和偏置，再看数字级。
- 捕获启动瞬间有爆音（削波），属正常现象，分析时应跳过第一段。

## 修改文件清单

- `/var/lib/alsa/asound.state`（捕获增益固化，alsactl store）
- `/usr/share/alsa/ucm2/F8-PRO/HiFi.conf`（新增 Mic 设备节，备份 .bak-mic）
- `/usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf`（新建，强制 UCM 模式）

## 相关工具脚本（本地 tools/）

- inspect-f8-mic.sh / test-f8-mic-capture.sh / tune-f8-mic-gain.sh / test-f8-mic-lrchannel.sh — 采集与调参
- save-f8-mic-default.sh — 固化捕获默认
- add-f8-ucm-mic.sh / fix-f8-ucm-seq2.sh — UCM 修改
- force-f8-ucm3.sh — WP UCM 模式配置
- verify-f8-mic-reboot.sh — 重启后验证
