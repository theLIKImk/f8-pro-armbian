# G2 实测：开源 GPU、内屏和限时 Wayland 窗口通过

2026-10-29。确认F:卷标F8AG2，30份日志已复制到local/hardware/armbian-official-g2-20261029-01/；summarize-f8-official-g2.py检查实际证据并生成逐文件哈希与test-result.json。用户明确看到测试弹窗，稍后自动关闭，并报告屏幕似乎可显示终端输出。

## 已通过范围

- 官方Armbian内核6.1.115-vendor-rk35xx和官方用户态运行；系统running，0失败单元，原分区ro,norecovery、SquashFS只读、写入RAM overlay。
- Panthor加载和G610固件初始化成功，固件报告git sha 95a25d71030715381f33105394285e1dcc860a65。实际渲染节点/dev/dri/renderD129。
- EGL探针vendor=Mesa、renderer=Mali-G610 MC4 (Panfrost)、OpenGL ES3.1 Mesa26.0.3；software_renderer=false，无libMali。RGBA8像素读回[64,128,191,255]，gl_error=0、hardware_accepted=true。
- rockchip-drm card0-DSI-1 connected/enabled，1200×1920；VOP VP2实际设置160MHz，DSI四lane启用。GPU实际频率/唯一可用档为200MHz，不是性能测试。
- logind创建type=wayland的f8gpu会话，测试服务启动/停止成功，用户确认实物弹窗。约25秒后由测试脚本主动停止，所以窗口自动消失是预期行为。
- 内核42.084912秒切换到150×120字符的彩色framebuffer console，注册fb0 rockchipdrmfb。这与用户可见屏幕终端文字相符，不是外接UART串口收发验收。

GPU供电轨仍会在33.518313秒被unused清理关闭；但G2在GPU电源域加入gpu-supply后，随后正确启用供电、Panthor成功加载并完成渲染，不再出现G1电源域上电panic。没有修改电压约束或禁用panic保护。本轮没有外部电压测量。

## 仍须保留的边界

KWin的标准输出随tty输入走屏幕，WAYLAND.TXT只保留systemd/PAM会话记录，没有独立落盘的compositor renderer字符串。不能把EGL探针的renderer直接当KWin查询结果。下一候选应显式StandardOutput=journal/StandardError=journal，在触摸测试时同时补采。

触摸在G2设备树中明确disabled，无法触摸是当前测试范围，尚未接入驱动；不是触摸硬件故障。下一步接入F8 r8/shuping专用固件与匹配官方内核的触摸驱动，并验证IRQ/复位、原始800×1280坐标到竖屏1200×1920的映射及多点。旧6.1.172候选对象不能直接装进官方6.1.115。

VOP供电/DVFS回退、panel bpc0、额外overlay plane、RGA聚合、早期监管数据库、AppArmor fusermount告警仍在。无panic/Oops的kernel快照至154.665秒，不是长期稳定、DVFS、休眠或完整Plasma/SDDM验收。充电和触摸仍禁用，无网络SSH。

G2根镜像和boot保留为已测基线；后续候选另命名，勿覆盖。日志已保全，可只刷原BOOT恢复使用/充电。截至此记录尚未确认本次回退，无后台任务。
