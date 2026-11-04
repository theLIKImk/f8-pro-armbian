// SPDX-License-Identifier: GPL-2.0-only
#include "LinuxPanthorGpu.h"
#include <QDir>
#include <QFile>
#include <algorithm>

static QByteArray read(const QString &path)
{
    QFile f(path);
    return f.open(QIODevice::ReadOnly) ? f.readAll().trimmed() : QByteArray();
}
LinuxPanthorGpu::LinuxPanthorGpu(const QString &id, const QString &sysPath)
    : GpuDevice(id, QStringLiteral("Mali-G610 (Panfrost)"))
{
    QDir devfreq(sysPath + QStringLiteral("/devfreq"));
    const auto names = devfreq.entryList(QDir::Dirs | QDir::NoDotAndDotDot);
    if (!names.isEmpty()) m_devfreq = devfreq.filePath(names.first());
    QDir thermal(QStringLiteral("/sys/class/thermal"));
    for (const auto &entry : thermal.entryList({QStringLiteral("thermal_zone*")}, QDir::Dirs)) {
        if (read(thermal.filePath(entry + QStringLiteral("/type"))) == "gpu-thermal") {
            m_thermal = thermal.filePath(entry + QStringLiteral("/temp"));
            break;
        }
    }
}
void LinuxPanthorGpu::initialize()
{
    // An UMA GPU has no dedicated VRAM/power counters here. Publish only
    // real measurements; do not report system RAM as dedicated video RAM.
    m_nameProperty = new KSysGuard::SensorProperty(QStringLiteral("name"), QStringLiteral("名称"), name(), this);
    m_usageProperty = new KSysGuard::SensorProperty(QStringLiteral("usage"), QStringLiteral("GPU 使用率"), this);
    m_usageProperty->setUnit(KSysGuard::UnitPercent);
    m_usageProperty->setMin(0); m_usageProperty->setMax(100);
    m_usageProperty->setVariantType(QVariant::Double);
    m_coreFrequencyProperty = new KSysGuard::SensorProperty(QStringLiteral("coreFrequency"), QStringLiteral("GPU 频率"), this);
    m_coreFrequencyProperty->setUnit(KSysGuard::UnitMegaHertz);
    m_coreFrequencyProperty->setVariantType(QVariant::Double);
    m_temperatureProperty = new KSysGuard::SensorProperty(QStringLiteral("temperature"), QStringLiteral("GPU 温度"), this);
    m_temperatureProperty->setUnit(KSysGuard::UnitCelsius);
    m_temperatureProperty->setVariantType(QVariant::Double);
    for (auto sensor : {m_nameProperty, m_usageProperty, m_coreFrequencyProperty, m_temperatureProperty}) sensor->setPrefix(name());
    update();
}
void LinuxPanthorGpu::update()
{
    bool ok = false;
    const double usage = read(m_devfreq + QStringLiteral("/load")).split('@').first().toDouble(&ok);
    m_usageProperty->setValue(ok ? QVariant(std::clamp(usage, 0.0, 100.0)) : QVariant());
    const double hz = read(m_devfreq + QStringLiteral("/cur_freq")).toDouble(&ok);
    m_coreFrequencyProperty->setValue(ok ? QVariant(hz / 1000000.0) : QVariant());
    const double temp = read(m_thermal).toDouble(&ok);
    m_temperatureProperty->setValue(ok ? QVariant(temp / 1000.0) : QVariant());
}
