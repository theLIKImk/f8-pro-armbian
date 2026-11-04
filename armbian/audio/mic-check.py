#!/usr/bin/python3
"""Local-only microphone A/B capture; never sends audio or persists mixer edits."""
import array,json,math,os,signal,subprocess,time,wave
from pathlib import Path
from PyQt6.QtCore import QTimer,Qt
from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QLabel,QPushButton,QHBoxLayout

CONTROLS=['ALC Capture Function','ALC Capture Max PGA','ADC Data Select','Left Channel Capture Volume','Right Channel Capture Volume']
def get(name):
    text=subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
    return next(x.split('values=',1)[1].strip() for x in text.splitlines() if ': values=' in x)
def setctl(name,value):subprocess.run(['amixer','-q','-c','0','cset','name='+name,str(value)],check=True,capture_output=True)
def rms(data):return math.sqrt(sum(x*x for x in data)/max(1,len(data)))
def analyze(path):
    with wave.open(str(path),'rb') as w:
        rate=w.getframerate();channels=w.getnchannels();assert w.getsampwidth()==2 and channels==2
        a=array.array('h',w.readframes(w.getnframes()))
    results=[]
    for ch in range(channels):
        values=a[ch::channels]
        parts={label:values[int(start*rate):int(end*rate)] for label,start,end in [('quiet_before',2.5,5.5),('speech',6.5,9.5),('quiet_after',10.5,13.5)]}
        levels={label:rms(data) for label,data in parts.items()};noise=max(levels['quiet_before'],levels['quiet_after'])
        steady=values[int(2.5*rate):int(13.5*rate)]
        results.append({'channel':ch,'rms':levels,'dbfs':{n:20*math.log10(max(v,1e-6)/32768) for n,v in levels.items()},'speech_quiet_difference_db':20*math.log10(max(levels['speech'],1e-6)/max(noise,1e-6)),'clipped_fraction':sum(abs(x)>=32760 for x in steady)/max(1,len(steady))})
    if len(a)/channels/rate<13:raise ValueError('有效录音不足13秒，请重新测试。')
    return {'file':str(path),'duration':len(a)/channels/rate,'channels':results}

class Window(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('F8 麦克风对比测试');self.resize(700,490)
        self.original={n:get(n) for n in CONTROLS};self.process=None;self.playback=None;self.result={};self.last=None
        self.folder=Path.home()/'.cache/f8-mic-check-20261102';self.folder.mkdir(exist_ok=True);self.folder.chmod(0o700)
        saved=self.folder/'results.json'
        if saved.exists():self.result=json.loads(saved.read_text()).get('trials',{})
        layout=QVBoxLayout(self)
        text=QLabel('每次录音约14秒：准备2秒 → 安静4秒 → 正常说话4秒 → 安静4秒。\n两次请使用相同距离、音量和测试话。音频只保存在本机。');text.setWordWrap(True);layout.addWidget(text)
        self.phase=QLabel('准备好后点击“1. 录原设置”');self.phase.setWordWrap(True);self.phase.setAlignment(Qt.AlignmentFlag.AlignCenter);self.phase.setStyleSheet('font-size:25px; padding:20px');layout.addWidget(self.phase)
        row=QHBoxLayout();self.buttons=[]
        for mode,label in [('baseline','1. 录原设置'),('fixed','2. 固定增益'),('left','3. 左声道降噪声测试')]:
            b=QPushButton(label);b.clicked.connect(lambda checked=False,m=mode:self.start(m));self.buttons.append(b);row.addWidget(b)
        layout.addLayout(row)
        self.play=QPushButton('回放最近录音（原始音量）');self.play.clicked.connect(self.listen);self.play.setEnabled(False);layout.addWidget(self.play)
        for mode,label in [('baseline','等响度回放：原设置'),('fixed','等响度回放：固定增益'),('left','等响度回放：左声道测试')]:
            b=QPushButton(label);b.clicked.connect(lambda checked=False,m=mode:self.listen_equal(m));layout.addWidget(b)
        self.summary=QLabel('测试期间只临时调整输入增益；每次结束会恢复原值。\n降低录音音量不等同于提高信噪比，请同时比较语音清晰度。');self.summary.setWordWrap(True);layout.addWidget(self.summary)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.setInterval(100)
    def restore(self):
        for name,value in self.original.items():setctl(name,value)
    def start(self,mode):
        if self.process:return
        if self.playback and self.playback.poll() is None:self.playback.terminate()
        self.restore();self.mode=mode;self.adjusted=False;self.stop_sent=False
        self.path=self.folder/(mode+'-'+str(time.time_ns())+'.wav')
        self.error_path=self.folder/'record-error.txt'
        self.error_log=self.error_path.open('w');self.error_path.chmod(0o600)
        self.process=subprocess.Popen(['pw-record','--rate','48000','--channels','2','--format','s16',str(self.path)],stdout=subprocess.DEVNULL,stderr=self.error_log)
        self.started=time.monotonic()
        for b in self.buttons:b.setEnabled(False)
        self.play.setEnabled(False);self.timer.start()
    def tick(self):
        elapsed=time.monotonic()-self.started
        try:
            if elapsed>=1 and not self.adjusted:
                if self.mode=='fixed':
                    setctl('ALC Capture Function','Off');setctl('Left Channel Capture Volume','5');setctl('Right Channel Capture Volume','5')
                elif self.mode=='left':
                    setctl('ALC Capture Function','Left');setctl('ALC Capture Max PGA','5')
                    setctl('Left Channel Capture Volume','8');setctl('Right Channel Capture Volume','0')
                    setctl('ADC Data Select','Left Left')
                self.adjusted=True
            if elapsed<2:label='准备中';remain=2-elapsed
            elif elapsed<6:label='请保持安静';remain=6-elapsed
            elif elapsed<10:label='请用正常音量说测试话';remain=10-elapsed
            else:label='请再次保持安静';remain=max(0,14-elapsed)
            self.phase.setText(label+'\n'+str(math.ceil(remain))+' 秒')
            if self.process.poll() is None and elapsed>=14 and not self.stop_sent:
                self.process.send_signal(signal.SIGINT);self.stop_sent=True
            if self.process.poll() is not None:
                self.timer.stop();exitcode=self.process.returncode;self.process=None;self.error_log.close();self.restore()
                # This installed pw-cat returns 1 even for a successful
                # sample-count stop. Accept it only after our deliberate
                # timed SIGINT and after validating the complete WAV below.
                if exitcode not in [0,130,-2] and not (exitcode==1 and self.stop_sent):raise ValueError('录音程序退出 '+str(exitcode)+'：'+self.error_path.read_text(errors='replace')[-1000:])
                self.path.chmod(0o600);result=analyze(self.path)
                if result['duration']>16:raise ValueError('录音时序异常，请重新测试。')
                result['recorder_exit']=exitcode;result['timed_stop']=self.stop_sent
                self.result[self.mode]=result;self.last=self.path
                (self.folder/'results.json').write_text(json.dumps({'trials':self.result,'mixer_restored':True},indent=2)+'\n');(self.folder/'results.json').chmod(0o600)
                self.phase.setText('本次录音完成；输入增益已恢复')
                self.summary.setText('\n'.join(f"声道{x['channel']+1}：安静 {x['dbfs']['quiet_after']:.1f} dBFS，语音/静音差 {x['speech_quiet_difference_db']:.1f} dB" for x in result['channels']))
                for b in self.buttons:b.setEnabled(True)
                self.play.setEnabled(True)
        except Exception as e:
            self.timer.stop()
            if self.process:
                self.process.send_signal(signal.SIGINT);self.process.wait(timeout=5);self.process=None
            self.restore();self.phase.setText('测试未完成：'+str(e))
            for b in self.buttons:b.setEnabled(True)
    def listen(self):
        if self.last:self.playback=subprocess.Popen(['pw-play','--volume','0.25',str(self.last)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def listen_equal(self,mode):
        if self.process:return
        if mode not in self.result:self.phase.setText('此项尚无录音，请先录制');return
        if self.playback and self.playback.poll() is None:self.playback.terminate()
        result=self.result[mode];src=Path(result['file'])
        if src.parent!=self.folder or not src.is_file():return
        with wave.open(str(src),'rb') as w:
            rate=w.getframerate();assert w.getnchannels()==2 and w.getsampwidth()==2
            samples=array.array('h',w.readframes(w.getnframes()))[0::2]
        # Same speech RMS for fair comparison; exclude startup pop and use
        # the actual speech-bearing left channel. Originals stay unchanged.
        level=result['channels'][0]['rms']['speech'];gain=min(64,4000/max(level,1))
        data=samples[int(2*rate):int(13.5*rate)]
        data=array.array('h',(round(max(-26000,min(26000,x*gain))) for x in data))
        dest=self.folder/'compare-left.wav'
        with wave.open(str(dest),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data.tobytes())
        dest.chmod(0o600)
        self.playback=subprocess.Popen(['pw-play','--volume','0.25',str(dest)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.phase.setText('正在等响度回放左声道（跳过启动段）\n原始录音和系统麦克风音量未改')
    def closeEvent(self,e):
        self.timer.stop()
        if self.process:self.process.send_signal(signal.SIGINT);self.process.wait(timeout=5)
        if self.playback and self.playback.poll() is None:self.playback.terminate()
        self.restore();e.accept()

if __name__=='__main__':
    app=QApplication([]);app.setStyleSheet('QPushButton {min-height:42px;padding:8px;} QLabel {font-size:17px;}')
    window=Window()
    signal.signal(signal.SIGTERM,lambda signum,frame:window.close())
    heartbeat=QTimer();heartbeat.timeout.connect(lambda:None);heartbeat.start(250)
    window.show();app.exec()
