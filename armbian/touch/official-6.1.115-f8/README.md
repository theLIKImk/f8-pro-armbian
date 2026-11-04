# F8 专用触摸模块：官方 6.1.115 ABI

2026-10-29。由已审查r8/shuping候选派生，专用I2C驱动名f8-gsl-shuping，唯一OF匹配f8-pro,gslx680-shuping-eval，不再注册通用GSL匹配或platform:gsl_ts别名。无匹配配置就返回ENODEV，不回退通用固件。原候选、原厂数组与已测G2均保留。

f8_gsl_shuping.ko：91680字节，SHA256 bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d。

现有headers来源为Armbian26.8.3，同名6.1.115；不冒称来自已测26.8.1镜像。新模块48个导入符号（含module_layout）逐项与官方26.8.1实际模块的版本CRC一致，actual-official-abi.json记录每项参照模块。未跳过或强制忽略版本检查。

算法按官方GSL模块的方式私有链接gsl_point_id.c，不调用内核中未导出的同名算法函数。算法源码来自固定85233a85参考树，SHA72ccf0b5e4a81e93e11c218104644dcd9dd0e80fa51fda2d0c7f83500d668915。新模块与官方模块gsl_version_id函数字节相同；两者及原厂5.10归档Image返回版本0x20140421。版本一致不等于全部算法行为等价，硬件仍需验证。

完整模块链接后，板级4851项固件38808字节与512个u32配置2048字节逐字节匹配原厂提取数据。保留原候选同步上传/错误传递、复位20/10/10ms及startup10ms、IRQ/PM保护和输入边界检查。原始范围800×1280，交给Wayland按1200×1920显示模式映射；未强改原始坐标。

检查文件：module-check.json、actual-official-abi.json、algorithm-version-check.json、build.log、modinfo.txt。构建日志只有缺少vmlinux而跳过BTF的提示，不影响正常模块链接。没有加载模块或写控制器；首次硬件短测见docs/armbian-official-touch-g3-test.md。
