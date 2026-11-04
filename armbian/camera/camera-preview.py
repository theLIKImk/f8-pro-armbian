#!/usr/bin/python3
"""User-launched Wayland preview; no boot-time camera activation."""
import argparse
import ctypes as C
import json
import os
import signal
import sys
import time
from pathlib import Path
from PyQt6.QtCore import QProcess,QProcessEnvironment,Qt,QTimer
from PyQt6.QtGui import QImage,QPixmap,QTransform
from PyQt6.QtWidgets import QApplication,QCheckBox,QComboBox,QHBoxLayout,QLabel,QMainWindow,QMessageBox,QPushButton,QVBoxLayout,QWidget

parser=argparse.ArgumentParser()
parser.add_argument('--autostart',action='store_true')
parser.add_argument('--quit-after',type=int,default=0)
parser.add_argument('--snapshot')
parser.add_argument('--media-test-dir')
parser.add_argument('--camera',choices=['back','front'],default='back')
parser.add_argument('--relay',action='store_true')
args=parser.parse_args()

class Window(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('F8 相机 · 拍照与录像');self.resize(900,720)
        self.engine=QProcess(self);self.capture=QProcess(self)
        self.engine.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.engine.readyReadStandardOutput.connect(self.engine_output)
        self.capture.readyReadStandardOutput.connect(self.frames_ready)
        self.capture.readyReadStandardError.connect(self.capture_errors)
        self.engine.errorOccurred.connect(lambda _:self.process_error(self.engine))
        self.capture.errorOccurred.connect(lambda _:self.process_error(self.capture))
        self.engine.finished.connect(self.engine_finished)
        self.capture.finished.connect(self.capture_finished)
        self.buffer=bytearray();self.engine_text='';self.errors='';self.image=None
        self.frames=0;self.stopping=False;self.saved_snapshot=False;self.started_at=None
        self.recorder=QProcess(self);self.record_frames=0;self.record_file=None;self.record_error='';self.record_log='';self.media_test_started=False;self.media_test_done=False
        self.recorder.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.recorder.readyReadStandardOutput.connect(self.record_output)
        self.recorder.finished.connect(self.record_finished)
        self.relayer=QProcess(self);self.relay_frames=0;self.relay_error='';self.relay_log=''
        self.relayer.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.relayer.readyReadStandardOutput.connect(self.relay_output)
        self.relayer.finished.connect(self.relay_finished)
        self.engine_stop_requested=False;self.engine_exit=None;self.capture_exit=None
        self.pixel_lib=C.CDLL('/usr/local/lib/f8-pro/libf8-camera-pixels.so')
        self.convert=self.pixel_lib.f8_nv12_rgb
        self.convert.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint,C.c_uint];self.convert.restype=C.c_int
        self.nv12=C.create_string_buffer(640*480*3//2);self.rgb=C.create_string_buffer(640*480*3)
        self.preview=QLabel('点击“开始预览”');self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(480,360);self.preview.setStyleSheet('background:#111;color:#ddd;border-radius:8px;')
        self.camera_choice=QComboBox();self.camera_choice.addItem('后置摄像头','back');self.camera_choice.addItem('前置摄像头','front')
        self.camera_choice.setCurrentIndex(1 if args.camera=='front' else 0)
        self.relay_box=QCheckBox('兼容中继（供其他相机软件使用）');self.relay_box.setChecked(args.relay)
        self.relay_box.toggled.connect(self.toggle_relay)
        self.state=QLabel('选择镜头后开始预览；停止后可切换镜头')
        self.start_button=QPushButton('开始预览');self.stop_button=QPushButton('停止');self.save_button=QPushButton('拍照')
        self.record_button=QPushButton('开始录像');self.record_button.setEnabled(False);self.record_button.clicked.connect(self.toggle_record)
        self.flip=QCheckBox('旋转 180°')
        # User confirmed this board's rear image is upside down.
        self.flip.setChecked(True)
        self.start_button.clicked.connect(self.start);self.stop_button.clicked.connect(self.stop)
        self.save_button.clicked.connect(self.save_frame);self.flip.toggled.connect(self.draw)
        self.stop_button.setEnabled(False);self.save_button.setEnabled(False)
        self.camera_choice.currentIndexChanged.connect(self.camera_changed)
        buttons=QHBoxLayout()
        for widget in [self.start_button,self.stop_button,self.save_button,self.record_button,self.flip]:buttons.addWidget(widget)
        layout=QVBoxLayout();layout.addWidget(self.camera_choice);layout.addWidget(self.relay_box);layout.addWidget(self.state);layout.addWidget(self.preview,1);layout.addLayout(buttons)
        layout.addWidget(QLabel('640×480 / 14 fps · AVI 录像（无声音）· 后摄对焦尚未启用'))
        container=QWidget();container.setLayout(layout);self.setCentralWidget(container)
        self.status_path=Path(os.environ['XDG_RUNTIME_DIR'])/'f8-camera-preview-status.json'
        self.write_status('idle')
        if args.autostart:QTimer.singleShot(200,self.start)
        if args.quit_after:QTimer.singleShot(args.quit_after*1000,self.close)
    def write_status(self,state):
        self.status_path.write_text(json.dumps({'state':state,'frames':self.frames,'platform':QApplication.platformName(),'camera':self.camera_choice.currentData(),
          'engine_pid':int(self.engine.processId()),'capture_pid':int(self.capture.processId()),
          'last_error':self.errors[-1200:],'engine_log':self.engine_text[-5000:],
          'engine_exit':self.engine_exit,'capture_exit':self.capture_exit,
          'record_file':str(self.record_file) if self.record_file else None,'record_frames':self.record_frames,
          'record_error':self.record_error,'record_log':self.record_log[-1200:],
          'relay_running':self.relayer.state()==QProcess.ProcessState.Running,'relay_frames':self.relay_frames,'relay_error':self.relay_error,'relay_log':self.relay_log[-1200:],
          'media_test_done':self.media_test_done},ensure_ascii=False))
    def process_error(self,process):
        if self.stopping and process.error()==QProcess.ProcessError.Crashed:return
        self.errors+='\n'+process.errorString();self.stop()
    def camera_changed(self):
        self.image=None;self.buffer.clear();self.save_button.setEnabled(False);self.record_button.setEnabled(False)
        self.preview.setText('点击“开始预览”');self.state.setText(self.camera_choice.currentText());self.write_status('idle')
    def start(self):
        if any(p.state()!=QProcess.ProcessState.NotRunning for p in [self.engine,self.capture]):return
        self.stopping=False;self.buffer.clear();self.engine_text='';self.errors='';self.frames=0;self.started_at=time.monotonic()
        self.engine_stop_requested=False;self.engine_exit=None;self.capture_exit=None
        self.camera_choice.setEnabled(False)
        self.start_button.setEnabled(False);self.stop_button.setEnabled(True);self.state.setText('正在启动'+self.camera_choice.currentText()+'…')
        env=QProcessEnvironment.systemEnvironment()
        env.insert('LD_PRELOAD','/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-otp.so')
        env.insert('PYTHONUNBUFFERED','1');self.engine.setProcessEnvironment(env)
        self.engine.start('/usr/bin/python3',['/usr/local/lib/f8-pro/aiq-backend.py','--camera',self.camera_choice.currentData()])
        QTimer.singleShot(7000,self.start_timeout)
    def start_timeout(self):
        if not self.stopping and self.frames==0 and not self.start_button.isEnabled():
            self.errors+='\n摄像头未在预期时间内出图。';self.stop()
    def engine_output(self):
        self.engine_text+=bytes(self.engine.readAllStandardOutput()).decode(errors='replace')
        if 'F8_CAMERA_AIQ_READY ' in self.engine_text and self.engine.state()==QProcess.ProcessState.Running and self.capture.state()==QProcess.ProcessState.NotRunning and not self.stopping:
            line=next(x for x in self.engine_text.splitlines() if x.startswith('F8_CAMERA_AIQ_READY '))
            node=line.split()[-1]
            if not node.startswith('/dev/video') or not node[10:].isdigit():
                self.errors+='Invalid video node';self.stop();return
            capture_args=['-d',node,'--set-fmt-video=width=640,height=480,pixelformat=NV12',
                          '--stream-mmap=4','--stream-poll','--stream-to=-']
            self.capture.start('/usr/bin/v4l2-ctl',capture_args)
    def capture_errors(self):
        self.errors+=bytes(self.capture.readAllStandardError()).decode(errors='replace')
    def frames_ready(self):
        self.buffer.extend(bytes(self.capture.readAllStandardOutput()));size=640*480*3//2
        available=len(self.buffer)//size
        if not available:return
        if self.relay_box.isChecked() and self.relayer.state()==QProcess.ProcessState.NotRunning and not self.stopping:self.start_relay()
        if self.relayer.state()==QProcess.ProcessState.Running:
            if self.relayer.bytesToWrite()>size*14:
                self.relay_error='兼容中继处理过慢，已停止。';self.finish_relay()
            else:self.relayer.write(bytes(self.buffer[:available*size]));self.relay_frames+=available
        if self.recorder.state()==QProcess.ProcessState.Running:
            if self.recorder.bytesToWrite()>size*14:
                self.record_error='录像编码跟不上采集，已停止保存。';self.finish_record()
            else:
                self.recorder.write(bytes(self.buffer[:available*size]));self.record_frames+=available
        frame=bytes(self.buffer[(available-1)*size:available*size]);del self.buffer[:available*size]
        self.nv12.raw=frame
        if self.convert(self.nv12,size,self.rgb,640*480*3,640,480)!=0:
            self.errors+='\n图像格式转换失败';self.stop();return
        self.frames+=available;self.image=QImage(self.rgb.raw,640,480,640*3,QImage.Format.Format_RGB888).copy()
        self.draw();self.save_button.setEnabled(True);self.record_button.setEnabled(True)
        self.state.setText(('录像中 · '+str(self.record_frames//14)+' 秒') if self.recorder.state()==QProcess.ProcessState.Running else self.record_error or self.relay_error or ('预览中 · 兼容中继已开启' if self.relayer.state()==QProcess.ProcessState.Running else '预览中 · 自动曝光 / 白平衡'))
        if args.media_test_dir and self.frames>=15 and not self.media_test_started:
            self.media_test_started=True;self.save_frame();self.toggle_record()
        if args.media_test_dir and self.record_frames>=70 and not self.media_test_done:
            self.finish_record();self.media_test_done=True;self.write_status('media-test-complete')
        if self.frames%14<available:self.write_status('preview')
        if args.snapshot and self.frames>=15 and not self.saved_snapshot:
            self.saved_snapshot=True;self.grab().save(args.snapshot)
    def draw(self):
        if self.image is None:return
        image=self.image.transformed(QTransform().rotate(180)) if self.flip.isChecked() else self.image
        pix=QPixmap.fromImage(image).scaled(self.preview.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        self.preview.setPixmap(pix)
    def resizeEvent(self,event):
        super().resizeEvent(event);self.draw()
    def save_frame(self):
        if self.image is None:return
        folder=Path(args.media_test_dir) if args.media_test_dir else Path.home()/'Pictures/F8Camera';folder.mkdir(parents=True,exist_ok=True)
        file=folder/(time.strftime('%Y%m%d-%H%M%S')+'-'+str(time.time_ns()%1000000000)+'.png')
        image=self.image.transformed(QTransform().rotate(180)) if self.flip.isChecked() else self.image
        if image.save(str(file)):self.state.setText('已保存：'+str(file))
        else:QMessageBox.warning(self,'保存失败','无法保存画面，请检查图片目录。')
    def record_output(self):
        self.record_log+=bytes(self.recorder.readAllStandardOutput()).decode(errors='replace')
        if self.recorder.state()==QProcess.ProcessState.NotRunning and self.recorder.exitCode()!=0:
            self.record_error='录像编码失败：'+self.record_log[-600:]
    def toggle_record(self):
        if self.recorder.state()!=QProcess.ProcessState.NotRunning:self.finish_record();return
        if self.image is None or self.stopping:return
        folder=Path(args.media_test_dir) if args.media_test_dir else Path.home()/'Videos/F8Camera';folder.mkdir(parents=True,exist_ok=True)
        self.record_file=folder/(time.strftime('%Y%m%d-%H%M%S')+'-'+str(time.time_ns()%1000000000)+'.avi')
        self.record_frames=0;self.record_error='';self.record_log=''
        pipeline=['-q','fdsrc','fd=0','!','rawvideoparse','format=nv12','width=640','height=480','framerate=14/1',
                  '!','capssetter','caps=video/x-raw,colorimetry=1:4:16:4']
        if self.flip.isChecked():pipeline+=['!','videoflip','method=rotate-180']
        pipeline+=['!','videoconvert','!','jpegenc','quality=85','!','avimux','!','filesink','location='+str(self.record_file)]
        self.recorder.start('/usr/bin/gst-launch-1.0',pipeline)
        if not self.recorder.waitForStarted(1500):
            self.record_error=self.recorder.errorString();self.state.setText(self.record_error);return
        self.record_button.setText('停止录像');self.flip.setEnabled(False)
    def record_finished(self,code,status):
        self.record_output();self.record_button.setText('开始录像');self.flip.setEnabled(self.relayer.state()==QProcess.ProcessState.NotRunning)
        if code!=0 or status!=QProcess.ExitStatus.NormalExit:
            self.record_error='录像编码失败：'+self.record_log[-600:]
        elif not self.record_file or not self.record_file.exists() or self.record_file.stat().st_size<1024 or not self.record_frames:
            self.record_error='录像没有有效帧，未通过保存检查。'
    def finish_record(self):
        if self.recorder.state()!=QProcess.ProcessState.NotRunning:
            self.recorder.closeWriteChannel()
            if not self.recorder.waitForFinished(8000):
                self.recorder.kill();self.recorder.waitForFinished(1000);self.record_error='录像结束超时，文件未通过保存检查。'
        self.record_output()
        if self.recorder.exitCode()!=0:self.record_error='录像编码失败：'+self.record_log[-600:]
        self.record_button.setText('开始录像');self.flip.setEnabled(self.relayer.state()==QProcess.ProcessState.NotRunning)
        self.state.setText(self.record_error or ('已保存录像：'+str(self.record_file)))
        self.write_status('record-stopped')
    def toggle_relay(self,checked):
        if not checked:self.finish_relay()
        elif self.frames and not self.stopping:self.start_relay()
    def start_relay(self):
        if self.relayer.state()!=QProcess.ProcessState.NotRunning:return
        node=Path('/sys/class/video4linux/video42/name')
        if not node.exists() or node.read_text().strip()!='F8 Camera Relay' or not os.access('/dev/video42',os.W_OK):
            self.relay_error='兼容摄像头未就绪或无访问权限。';self.finish_relay();return
        self.relay_frames=0;self.relay_error='';self.relay_log=''
        pipeline=['-q','fdsrc','fd=0','!','rawvideoparse','format=nv12','width=640','height=480','framerate=14/1','!','capssetter','caps=video/x-raw,colorimetry=1:4:16:4']
        if self.flip.isChecked():pipeline+=['!','videoflip','method=rotate-180']
        pipeline+=['!','videoconvert','!','video/x-raw,format=YUY2','!','v4l2sink','device=/dev/video42','sync=false']
        relay_env=QProcessEnvironment.systemEnvironment();relay_env.insert('LD_PRELOAD','/usr/local/lib/f8-pro/libf8-camera-relay-view.so');self.relayer.setProcessEnvironment(relay_env)
        self.relayer.start('/usr/bin/gst-launch-1.0',pipeline)
        if not self.relayer.waitForStarted(1500):
            self.relay_error=self.relayer.errorString();self.finish_relay();return
        self.flip.setEnabled(False)
    def relay_output(self):
        self.relay_log+=bytes(self.relayer.readAllStandardOutput()).decode(errors='replace')
    def relay_finished(self,code,status):
        self.relay_output()
        if code!=0 or status!=QProcess.ExitStatus.NormalExit:self.relay_error='兼容中继失败：'+self.relay_log[-600:]
        self.relay_box.blockSignals(True);self.relay_box.setChecked(False);self.relay_box.blockSignals(False)
        self.flip.setEnabled(self.recorder.state()==QProcess.ProcessState.NotRunning)
        self.write_status('relay-stopped')
    def finish_relay(self):
        self.relay_box.blockSignals(True);self.relay_box.setChecked(False);self.relay_box.blockSignals(False)
        if self.relayer.state()!=QProcess.ProcessState.NotRunning:
            self.relayer.closeWriteChannel()
            if not self.relayer.waitForFinished(3000):self.relayer.kill();self.relayer.waitForFinished(1000)
        self.flip.setEnabled(self.recorder.state()==QProcess.ProcessState.NotRunning)
    def stop(self):
        self.finish_relay()
        if self.recorder.state()!=QProcess.ProcessState.NotRunning:self.finish_record()
        self.record_button.setEnabled(False)
        self.stopping=True;self.stop_button.setEnabled(False)
        if self.capture.state()!=QProcess.ProcessState.NotRunning:
            try:os.kill(int(self.capture.processId()),signal.SIGINT)
            except ProcessLookupError:pass
            pid=self.capture.processId()
            QTimer.singleShot(2500,lambda:self.capture.kill() if self.capture.processId()==pid and pid else None)
        else:self.stop_engine()
    def stop_engine(self):
        if self.engine.state()!=QProcess.ProcessState.NotRunning:
            if self.engine_stop_requested:return
            self.engine_stop_requested=True
            self.engine.terminate();pid=self.engine.processId()
            QTimer.singleShot(5000,lambda:self.engine.kill() if self.engine.processId()==pid and pid else None)
        else:self.idle()
    def capture_finished(self,code,status):
        self.capture_exit={'code':code,'normal':status==QProcess.ExitStatus.NormalExit}
        self.capture_errors();self.stopping=True;self.stop_engine()
    def engine_finished(self,code,status):
        self.engine_exit={'code':code,'normal':status==QProcess.ExitStatus.NormalExit}
        self.engine_output()
        if self.capture.state()!=QProcess.ProcessState.NotRunning:self.stop()
        else:self.idle()
    def idle(self):
        self.camera_choice.setEnabled(True)
        self.stopping=True;self.start_button.setEnabled(True);self.stop_button.setEnabled(False)
        self.state.setText('已停止' if self.frames else '未能出图，可重试；请关闭其他相机程序。')
        self.write_status('stopped')
    def closeEvent(self,event):
        self.stop()
        if self.capture.state()!=QProcess.ProcessState.NotRunning:
            if not self.capture.waitForFinished(2500):self.capture.kill();self.capture.waitForFinished(1000)
        self.stop_engine()
        if self.engine.state()!=QProcess.ProcessState.NotRunning:
            if not self.engine.waitForFinished(5000):self.engine.kill();self.engine.waitForFinished(1000)
        self.write_status('closed');event.accept()

app=QApplication(sys.argv[:1]);window=Window();window.show();app.exec()
