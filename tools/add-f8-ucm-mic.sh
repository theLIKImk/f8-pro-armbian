#!/bin/sh
# UCM HiFi.conf 只有 Speaker 输出设备。添加 Microphone 设备节，让 WP 创建 source。
# 备份后追加：
sudo -n cp /usr/share/alsa/ucm2/F8-PRO/HiFi.conf /usr/share/alsa/ucm2/F8-PRO/HiFi.conf.bak-mic
sudo -n tee -a /usr/share/alsa/ucm2/F8-PRO/HiFi.conf > /dev/null <<'EOF'

SectionDevice."Mic" {
    Comment "Built-in Microphone"
    EnableSequence [
        cset "name='Left Channel Capture Volume' 8"
        cset "name='Right Channel Capture Volume' 8"
        cset "name='ALC Capture Function' Stereo"
        cset "name='ALC Capture Max PGA' 7"
        cset "name='ALC Capture Min PGA' 0"
        cset "name='Capture Digital Volume' 192"
        cset "name='Capture Mute' off"
        cset "name='Main Mic' on"
        cset "name='Headset Mic' off"
        cset "name='ADC Data Select' 'Left Right'"
        cset "name='Left PGA Mux' 'DifferentialL'"
        cset "name='Right PGA Mux' 'DifferentialR'"
    ]
    DisableSequence [
        cset "name='Capture Mute' on"
    ]
    Value {
        CapturePriority 200
        CapturePCM "hw:${CardId},0"
        CaptureChannels 2
        CaptureMixerElem "Capture Digital"
    }
}
EOF
echo "=== 重新载入 UCM（重置 card） ==="
sudo -n alsaucm reset 0 2>&1 | head -2
sudo -n alsaucm -c 0 list _devices/HiFi 2>&1 | head -8
echo DONE
