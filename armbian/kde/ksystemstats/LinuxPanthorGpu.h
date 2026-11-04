// SPDX-License-Identifier: GPL-2.0-only
#pragma once
#include "GpuDevice.h"

class LinuxPanthorGpu : public GpuDevice
{
public:
    LinuxPanthorGpu(const QString &id, const QString &sysPath);
    void initialize() override;
    void update() override;
private:
    QString m_devfreq;
    QString m_thermal;
};
